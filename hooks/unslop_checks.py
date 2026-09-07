"""Explainable prose rules for Unslop."""

from __future__ import annotations

import re
import statistics
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .unslop_core import (
    WORD_RE,
    Document,
    Finding,
    Span,
    TextUnit,
    normalize_space,
)


def cluster_offsets(
    document: Document, offsets: Sequence[int], max_occurrences: int, window_words: int
) -> list[list[int]]:
    if len(offsets) <= max_occurrences:
        return []
    ordered = sorted(set(offsets))
    indices = [document.word_index_at(offset) for offset in ordered]
    clusters: list[list[int]] = []
    left = 0
    right = 0
    while right < len(ordered):
        while left < right and indices[right] - indices[left] > window_words:
            left += 1
        if right - left + 1 > max_occurrences:
            cluster, cursor = finish_cluster(
                ordered, indices, left, right, window_words
            )
            clusters.append(cluster)
            right = cursor
            left = right
        else:
            right += 1
    return clusters


def finish_cluster(
    ordered: Sequence[int],
    indices: Sequence[int],
    left: int,
    right: int,
    window_words: int,
) -> tuple[list[int], int]:
    cluster = list(ordered[left : right + 1])
    cursor = right + 1
    while cursor < len(ordered) and indices[cursor] - indices[left] <= window_words:
        cluster.append(ordered[cursor])
        cursor += 1
    return cluster, cursor


def phrase_checker(
    entries: Sequence[tuple[str, str, str | None]],
) -> Callable[[Document, Mapping[str, Any]], list[Finding]]:
    compiled = [
        (re.compile(pattern, re.IGNORECASE), message, suggestion)
        for pattern, message, suggestion in entries
    ]

    def check(document: Document, _: Mapping[str, Any]) -> list[Finding]:
        candidates: list[Finding] = []
        for pattern, message, suggestion in compiled:
            for match in pattern.finditer(document.visible):
                candidates.append(
                    Finding(match.start(), match.end(), message, suggestion)
                )
        findings: list[Finding] = []
        for finding in sorted(
            candidates, key=lambda item: (item.start, -(item.end - item.start))
        ):
            if any(
                finding.start < existing.end and existing.start < finding.end
                for existing in findings
            ):
                continue
            findings.append(finding)
        return findings

    return check


def chatbot_residue(document: Document, _: Mapping[str, Any]) -> list[Finding]:
    pattern = re.compile(
        r"\bas an AI(?: language)? model\b|\bknowledge cutoff\b|\bas of my last (?:update|training)\b|"
        r"\bI (?:cannot|can't|do not|don't) (?:browse the internet|access real[- ]time)\b|"
        r"\boaicite\b|\bcontentReference\b|\battributableIndex\b|\bturn\d+(?:search|news|image|view)\d+\b|"
        r"[?&]utm_source=(?:chatgpt|openai)\b",
        re.IGNORECASE,
    )
    return [
        Finding(
            m.start(),
            m.end(),
            "Chatbot or generated-citation residue remains in the prose.",
            "Remove the artifact and verify the surrounding claim.",
        )
        for m in pattern.finditer(document.visible)
    ]


def negative_parallelism(
    document: Document, options: Mapping[str, Any]
) -> list[Finding]:
    patterns = [
        re.compile(
            r"\b(?:this|that|it|[A-Z][A-Za-z0-9' -]{0,35})\s+(?:isn't|is not|wasn't|was not)\s+(?:just\s+)?[^.!?\n]{2,100}[.!?]\s+(?:it(?:'s| is| was)|this is|that(?:'s| is))\s+[^.!?\n]{2,120}",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot\s+(?:just\s+)?[^,.;!?\n]{2,80},?\s+(?:but|rather)\s+[^.;!?\n]{2,110}",
            re.IGNORECASE,
        ),
    ]
    spans: list[Span] = []
    for pattern in patterns:
        spans.extend(
            Span(match.start(), match.end())
            for match in pattern.finditer(document.visible)
        )
    spans.sort(key=lambda item: (item.start, -(item.end - item.start)))
    deduped: list[Span] = []
    for span in spans:
        if not any(
            span.start < existing.end and existing.start < span.end
            for existing in deduped
        ):
            deduped.append(span)
    max_count = int(options.get("max", 1))
    window = int(options.get("window_words", 500))
    return [
        Finding(
            cluster[max_count],
            next(
                (span.end for span in deduped if span.start == cluster[-1]),
                cluster[-1] + 1,
            ),
            f"{len(cluster)} contrast reframes appear within {window} words; repeated 'not X, but Y' structure starts to sound manufactured.",
            "State at least one positive claim directly, or keep only the strongest contrast.",
        )
        for cluster in cluster_offsets(
            document, [span.start for span in deduped], max_count, window
        )
    ]


def no_chain(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_items", 3))
    pattern = re.compile(
        r"\bno\s+[^,.;:!?\n]{1,45}(?:\s*,\s*no\s+[^,.;:!?\n]{1,45})+", re.IGNORECASE
    )
    findings: list[Finding] = []
    for match in pattern.finditer(document.visible):
        count = len(re.findall(r"\bno\s+", match.group(0), re.IGNORECASE))
        if count >= minimum:
            findings.append(
                Finding(
                    match.start(),
                    match.end(),
                    f"A {count}-item 'no X, no Y' chain performs emphasis without adding evidence.",
                    "Replace the chain with the specific positive claim.",
                )
            )
    return findings


def question_answer(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    offsets: list[int] = []
    ends: dict[int, int] = {}
    max_answer = int(options.get("answer_max_words", 5))
    for first, second in zip(document.sentences, document.sentences[1:]):
        if document.section_at(first.start) != document.section_at(second.start):
            continue
        if (
            first.text.rstrip().endswith("?")
            and second.word_count <= max_answer
            and not second.text.rstrip().endswith("?")
        ):
            offsets.append(first.start)
            ends[first.start] = second.end
    max_count = int(options.get("max", 1))
    window = int(options.get("window_words", 400))
    return [
        Finding(
            cluster[max_count],
            ends.get(cluster[-1], cluster[-1] + 1),
            f"{len(cluster)} staged question-and-short-answer turns appear within {window} words.",
            "Turn at least one question into a direct statement.",
        )
        for cluster in cluster_offsets(document, offsets, max_count, window)
    ]


def question_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    offsets = [
        sentence.start
        for sentence in document.sentences
        if sentence.text.rstrip().endswith("?")
    ]
    max_count = int(options.get("max", 3))
    window = int(options.get("window_words", 500))
    return [
        Finding(
            cluster[max_count],
            cluster[-1] + 1,
            f"{len(cluster)} questions appear within {window} words; the passage is interrogating the reader instead of explaining.",
            "Keep the question that creates useful tension and state the others directly.",
        )
        for cluster in cluster_offsets(document, offsets, max_count, window)
    ]


def echoed_clause_finding(
    sentence: TextUnit, document: Document, minimum: int, maximum: int
) -> Finding | None:
    raw = document.structural[sentence.start : sentence.end]
    pieces = [
        normalize_space(piece)
        for piece in re.split(r"\s*(?:,|;)\s*(?:(?:and|or)\s+)?", raw)
    ]
    pieces = [piece for piece in pieces if len(WORD_RE.findall(piece)) >= 3]
    if not minimum <= len(pieces) <= maximum:
        return None
    prefixes: dict[str, int] = {}
    suffixes: dict[str, int] = {}
    for piece in pieces:
        words = [match.group(0).lower() for match in WORD_RE.finditer(piece)]
        if len(words) < 3:
            continue
        prefixes[" ".join(words[:2])] = prefixes.get(" ".join(words[:2]), 0) + 1
        suffixes[" ".join(words[-2:])] = suffixes.get(" ".join(words[-2:]), 0) + 1
    repeated_prefix = next(
        (key for key, count in prefixes.items() if count >= minimum), None
    )
    repeated_suffix = next(
        (key for key, count in suffixes.items() if count >= minimum), None
    )
    repeated = repeated_prefix or repeated_suffix
    if not repeated or re.search(r"\d", repeated):
        return None
    position = "opening" if repeated_prefix else "ending"
    return Finding(
        sentence.start,
        sentence.end,
        f"{len(pieces)} parallel clauses repeat the {position} '{repeated}'.",
        "Keep the parallelism only if the rhythm earns its space; otherwise combine the clauses or vary the syntax.",
    )


def echoed_clauses(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_clauses", 3))
    maximum = int(options.get("maximum_clauses", 5))
    return [
        finding
        for sentence in document.sentences
        if (finding := echoed_clause_finding(sentence, document, minimum, maximum))
        is not None
    ]


def is_tricolon(raw: str) -> bool:
    if raw.count(",") != 2:
        return False
    if not re.search(r",\s*(?:and|or)\s+", raw, re.IGNORECASE):
        return False
    parts = [
        part
        for part in re.split(r",\s*(?:and|or\s+)?|\s+(?:and|or)\s+", raw)
        if normalize_space(part)
    ]
    return len(parts) == 3 and all(
        1 <= len(WORD_RE.findall(part)) <= 8 for part in parts
    )


def tricolon_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    spans: list[Span] = []
    pattern = re.compile(
        r":\s*[^,.;!?\n]{1,36},\s*[^,.;!?\n]{1,36},\s*(?:and|or)\s+[^.;!?\n]{1,48}",
        re.IGNORECASE,
    )
    spans.extend(
        Span(m.start(), m.end()) for m in pattern.finditer(document.structural)
    )
    for sentence in document.sentences:
        raw = document.structural[sentence.start : sentence.end]
        if is_tricolon(raw):
            spans.append(Span(sentence.start, sentence.end))
    spans.sort(key=lambda item: item.start)
    max_count = int(options.get("max", 3))
    window = int(options.get("window_words", 750))
    return [
        Finding(
            cluster[max_count],
            cluster[-1] + 1,
            f"{len(cluster)} three-part rhetorical lists appear within {window} words.",
            "Vary the list length or convert one list into a concrete example.",
        )
        for cluster in cluster_offsets(
            document, [span.start for span in spans], max_count, window
        )
    ]


def opener_key(text: str) -> str | None:
    words = [
        match.group(0).lower().replace("’", "'") for match in WORD_RE.finditer(text)
    ]
    return " ".join(words[:2]) if len(words) >= 2 else None


def windowed_opener_group(
    keys: Sequence[str | None],
    units: Sequence[TextUnit],
    consumed: set[int],
    start: int,
    end: int,
    minimum: int,
) -> tuple[str, list[tuple[int, TextUnit]]] | None:
    pairs = [
        (index, units[index])
        for index in range(start, end)
        if keys[index] is not None and index not in consumed
    ]
    groups: dict[str, list[tuple[int, TextUnit]]] = {}
    for index, unit in pairs:
        key = keys[index]
        if key is not None:
            groups.setdefault(key, []).append((index, unit))
    return next(
        (
            (key, matches)
            for key, matches in groups.items()
            if len(matches) >= minimum and matches[0][0] == start
        ),
        None,
    )


def repeated_openers(
    units: Sequence[TextUnit], consecutive: int, window_units: int, window_count: int
) -> list[tuple[str, list[TextUnit]]]:
    results: list[tuple[str, list[TextUnit]]] = []
    keys = [opener_key(unit.text) for unit in units]
    consumed: set[int] = set()
    index = 0
    while index < len(units):
        key = keys[index]
        if key is None:
            index += 1
            continue
        end = index + 1
        while end < len(units) and keys[end] == key:
            end += 1
        if end - index >= consecutive:
            results.append((key, list(units[index:end])))
            consumed.update(range(index, end))
        index = end
    for start in range(len(units)):
        end = min(len(units), start + window_units)
        group = windowed_opener_group(keys, units, consumed, start, end, window_count)
        if group is None:
            continue
        key, pairs = group
        results.append((key, [unit for _, unit in pairs]))
        consumed.update(index for index, _ in pairs)
    return results


def sentence_openers(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    groups: list[tuple[str, list[TextUnit]]] = []
    for section in document.units_by_section(document.sentences):
        groups.extend(
            repeated_openers(
                section,
                int(options.get("consecutive", 3)),
                int(options.get("window_sentences", 8)),
                int(options.get("window_count", 5)),
            )
        )
    return [
        Finding(
            units[1].start,
            units[-1].end,
            f"{len(units)} sentences repeatedly open with '{key}'.",
            "Merge a sentence or vary the grammatical opening unless the repetition is deliberate anaphora.",
        )
        for key, units in groups
    ]


def paragraph_openers(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    groups: list[tuple[str, list[TextUnit]]] = []
    for section in document.units_by_section(document.paragraphs):
        groups.extend(
            repeated_openers(
                section,
                int(options.get("consecutive", 3)),
                int(options.get("window_paragraphs", 6)),
                int(options.get("window_count", 4)),
            )
        )
    return [
        Finding(
            units[1].start,
            units[-1].end,
            f"{len(units)} paragraphs repeatedly open with '{key}'.",
            "Vary the paragraph entry or combine paragraphs that make the same move.",
        )
        for key, units in groups
    ]


TRANSITIONS = (
    "moreover",
    "furthermore",
    "additionally",
    "in addition",
    "ultimately",
    "in essence",
    "at its core",
    "that said",
    "on the other hand",
    "the key takeaway",
    "here's the thing",
    "here is the thing",
)


def transition_offsets(text: str, phrase: str) -> list[int]:
    offsets: list[int] = []
    for match in re.finditer(r"\b" + re.escape(phrase) + r"\b", text, re.IGNORECASE):
        start = match.start()
        while start > 0 and text[start - 1].isspace():
            start -= 1
        # Preserve the original start-of-line/sentence anchor and source offset.
        # Searching for phrases first avoids rescanning masked code at every line.
        if start == 0 or text[start - 1] in ".!?":
            offsets.append(start)
            continue
        newline = text.find("\n", start, match.start())
        if newline != -1:
            offsets.append(newline + 1)
    return offsets


def transition_repetition(
    document: Document, options: Mapping[str, Any]
) -> list[Finding]:
    max_count = int(options.get("max", 2))
    window = int(options.get("window_words", 500))
    findings: list[Finding] = []
    for phrase in TRANSITIONS:
        offsets = transition_offsets(document.visible, phrase)
        for cluster in cluster_offsets(document, offsets, max_count, window):
            findings.append(
                Finding(
                    cluster[max_count],
                    cluster[-1] + len(phrase),
                    f"The transition '{phrase}' appears {len(cluster)} times within {window} words.",
                    "Delete a transition where paragraph order already makes the relationship clear.",
                )
            )
    return findings


def loaded_word_repetition(
    document: Document, options: Mapping[str, Any]
) -> list[Finding]:
    stems = {
        "delve": r"\bdelv(?:e|es|ed|ing)\b",
        "pivotal": r"\bpivotal\b",
        "nuanced": r"\bnuanced?\b",
        "robust": r"\brobust\b",
        "seamless": r"\bseamless(?:ly)?\b",
        "transformative": r"\btransformative\b",
        "landscape": r"\blandscape\b",
        "tapestry": r"\btapestry\b",
        "underscore": r"\bunderscor(?:e|es|ed|ing)\b",
        "showcase": r"\bshowcas(?:e|es|ed|ing)\b",
        "foster": r"\bfoster(?:s|ed|ing)?\b",
        "elevate": r"\belevat(?:e|es|ed|ing)\b",
        "unlock": r"\bunlock(?:s|ed|ing)?\b",
    }
    max_count = int(options.get("max", 2))
    window = int(options.get("window_words", 500))
    findings: list[Finding] = []
    for label, pattern in stems.items():
        offsets = [
            m.start() for m in re.finditer(pattern, document.visible, re.IGNORECASE)
        ]
        for cluster in cluster_offsets(document, offsets, max_count, window):
            findings.append(
                Finding(
                    cluster[max_count],
                    cluster[-1] + len(label),
                    f"The loaded word '{label}' appears {len(cluster)} times within {window} words.",
                    "Replace at least one use with the concrete property you mean.",
                )
            )
    return findings


def short_runs(
    section: Sequence[TextUnit], max_words: int, minimum_run: int
) -> list[list[TextUnit]]:
    runs: list[list[TextUnit]] = []
    index = 0
    while index < len(section):
        if section[index].word_count > max_words:
            index += 1
            continue
        end = index + 1
        while end < len(section) and section[end].word_count <= max_words:
            end += 1
        if end - index >= minimum_run:
            runs.append(list(section[index:end]))
        index = end
    return runs


def short_sentence_run(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    max_words = int(options.get("max_words", 5))
    minimum_run = int(options.get("minimum_run", 3))
    runs = [
        units
        for section in document.units_by_section(document.sentences)
        for units in short_runs(section, max_words, minimum_run)
    ]
    return [
        Finding(
            units[1].start,
            units[-1].end,
            f"{len(units)} consecutive sentences contain at most {max_words} words each, creating a manufactured staccato rhythm.",
            "Combine related fragments and reserve the short sentence for emphasis.",
        )
        for units in runs
    ]


def uniform_sentence_length(
    document: Document, options: Mapping[str, Any]
) -> list[Finding]:
    minimum = int(options.get("minimum_sentences", 10))
    lengths = [
        sentence.word_count
        for sentence in document.sentences
        if sentence.word_count >= 3
    ]
    if len(lengths) < minimum:
        return []
    mean = statistics.mean(lengths)
    coefficient = statistics.pstdev(lengths) / mean if mean else 1.0
    maximum = float(options.get("maximum_cv", 0.18))
    if coefficient >= maximum:
        return []
    return [
        Finding(
            document.sentences[0].start,
            document.sentences[-1].end,
            f"Sentence lengths are unusually uniform (coefficient of variation {coefficient:.2f} across {len(lengths)} sentences).",
            "Mix short assertions with longer explanatory sentences where the content supports it.",
        )
    ]


def density_findings(
    document: Document,
    offsets: Sequence[int],
    options: Mapping[str, Any],
    noun: str,
    suggestion: str,
) -> list[Finding]:
    max_count = int(options.get("max", 4))
    window = int(options.get("window_words", 500))
    return [
        Finding(
            cluster[max_count],
            cluster[-1] + 1,
            f"{len(cluster)} {noun} appear within {window} words.",
            suggestion,
        )
        for cluster in cluster_offsets(document, offsets, max_count, window)
    ]


def em_dash_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    return density_findings(
        document,
        [m.start() for m in re.finditer("—", document.visible)],
        options,
        "em dashes",
        "Keep the strongest interruption and use commas, parentheses, or separate sentences elsewhere.",
    )


def bold_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    return density_findings(
        document,
        [span.start for span in document.bold_spans],
        options,
        "bold spans",
        "Use emphasis only where the reader genuinely needs a visual anchor.",
    )


def parenthetical_density(
    document: Document, options: Mapping[str, Any]
) -> list[Finding]:
    return density_findings(
        document,
        [span.start for span in document.parenthetical_spans],
        options,
        "parenthetical asides",
        "Move necessary context into the sentence and delete dispensable asides.",
    )


def heading_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_headings", 6))
    min_words = int(options.get("min_words_per_heading", 70))
    count = len(document.heading_spans)
    if count < minimum or not document.word_count:
        return []
    ratio = document.word_count / float(count)
    if ratio >= min_words:
        return []
    return [
        Finding(
            document.heading_spans[1].start
            if count > 1
            else document.heading_spans[0].start,
            document.heading_spans[-1].end,
            f"{count} headings divide {document.word_count} words, or only {ratio:.0f} words per heading.",
            "Merge sections whose headings promise more structure than the content delivers.",
        )
    ]
