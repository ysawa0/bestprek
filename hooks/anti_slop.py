"""Deterministic anti-slop linter for Markdown prose.

The linter intentionally judges writing patterns, not authorship. It preserves
source offsets while masking Markdown constructs that should not participate in
prose analysis, then applies explainable phrase, repetition, rhetoric, rhythm,
and density rules.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence

VERSION = "1.15"
SEVERITY_ORDER = {"off": -1, "info": 0, "warning": 1, "error": 2}
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[’'][A-Za-z0-9]+)*(?:-[A-Za-z0-9]+)*")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
DIRECTIVE_RE = re.compile(
    r"<!--\s*anti-slop-(disable-next-line|disable|enable|ignore)(?:\s+([^>]*?))?\s*-->",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Span:
    start: int
    end: int


@dataclass(frozen=True)
class Word:
    text: str
    normalized: str
    start: int
    end: int


@dataclass(frozen=True)
class TextUnit:
    start: int
    end: int
    text: str
    word_count: int


@dataclass(frozen=True)
class Finding:
    start: int
    end: int
    message: str
    suggestion: str | None = None


@dataclass(frozen=True)
class Diagnostic:
    path: str
    rule_id: str
    severity: str
    message: str
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int
    suggestion: str | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    summary: str
    recommended_severity: str
    checker: Callable[["Document", Mapping[str, Any]], list[Finding]]
    defaults: dict[str, Any] = field(default_factory=dict)
    strict_severity: str | None = None
    strict_defaults: dict[str, Any] = field(default_factory=dict)


class ConfigError(ValueError):
    """Raised for invalid anti-slop configuration."""


def line_spans(source: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"\r?\n", source):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(source)))
    return spans


def compute_line_starts(source: str) -> list[int]:
    return [0, *(match.end() for match in re.finditer(r"\n", source))]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_words(text: str) -> list[Word]:
    return [
        Word(match.group(0), match.group(0).lower().replace("’", "'"), match.start(), match.end())
        for match in WORD_RE.finditer(text)
    ]


ABBREVIATIONS = {
    "e.g.", "i.e.", "etc.", "vs.", "mr.", "mrs.", "ms.", "dr.", "prof.",
    "sr.", "jr.", "st.", "fig.", "no.",
}


def looks_like_abbreviation(text: str, punctuation_index: int) -> bool:
    prefix = text[max(0, punctuation_index - 12): punctuation_index + 1].lower()
    if any(prefix.endswith(item) for item in ABBREVIATIONS):
        return True
    return bool(re.search(r"\b[A-Za-z]\.$", prefix))


def split_sentences(text: str, base_offset: int) -> list[TextUnit]:
    units: list[TextUnit] = []
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        boundary = char in "!?" or (char == "." and not looks_like_abbreviation(text, index))
        if not boundary:
            index += 1
            continue
        end = index + 1
        while end < len(text) and text[end] in ".!?\"'”’)]":
            end += 1
        if end < len(text) and not text[end].isspace():
            index += 1
            continue
        chunk = text[start:end]
        leading = len(chunk) - len(chunk.lstrip())
        trailing = len(chunk.rstrip())
        if trailing > leading:
            clean = normalize_space(chunk[leading:trailing])
            count = len(WORD_RE.findall(clean))
            if count:
                units.append(TextUnit(base_offset + start + leading, base_offset + start + trailing, clean, count))
        start = end
        index = end
    return units


def extract_paragraphs(structural: str) -> list[TextUnit]:
    paragraphs: list[TextUnit] = []
    current_start: int | None = None
    current_end = 0
    for start, end in line_spans(structural):
        line = structural[start:end]
        if line.strip():
            if current_start is None:
                current_start = start
            current_end = end
        elif current_start is not None:
            text = structural[current_start:current_end]
            count = len(WORD_RE.findall(text))
            if count >= 4:
                paragraphs.append(TextUnit(current_start, current_end, text, count))
            current_start = None
    if current_start is not None:
        text = structural[current_start:current_end]
        count = len(WORD_RE.findall(text))
        if count >= 4:
            paragraphs.append(TextUnit(current_start, current_end, text, count))
    return paragraphs


def selectors(value: str | None) -> set[str]:
    if not value or not value.strip():
        return {"*"}
    return {token for token in re.split(r"[\s,]+", value.strip()) if token}


def selector_matches(selector: str, rule_id: str) -> bool:
    if selector in {"*", "all"}:
        return True
    if selector.endswith(".*"):
        return rule_id.startswith(selector[:-1])
    return selector == rule_id


def parse_suppressions(source: str) -> tuple[list[bool], list[set[str]]]:
    all_flags: list[bool] = []
    rule_flags: list[set[str]] = []
    disabled_all = False
    disabled_rules: set[str] = set()
    pending_all = False
    pending_rules: set[str] = set()
    for start, end in line_spans(source):
        line = source[start:end]
        line_all = disabled_all or pending_all
        line_rules = set(disabled_rules) | set(pending_rules)
        pending_all = False
        pending_rules.clear()
        for match in DIRECTIVE_RE.finditer(line):
            action = match.group(1).lower()
            selected = selectors(match.group(2))
            selects_all = bool(selected & {"*", "all"})
            if action == "ignore":
                if selects_all:
                    line_all = True
                else:
                    line_rules.update(selected)
            elif action == "disable-next-line":
                if selects_all:
                    pending_all = True
                else:
                    pending_rules.update(selected)
            elif action == "disable":
                if selects_all:
                    disabled_all = True
                else:
                    disabled_rules.update(selected)
            elif action == "enable":
                if selects_all:
                    disabled_all = False
                    disabled_rules.clear()
                else:
                    disabled_rules.difference_update(selected)
        all_flags.append(line_all)
        rule_flags.append(line_rules)
    return all_flags, rule_flags


class Projection:
    """Create visible and structural offset-preserving views of Markdown."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.visible = list(source)
        self.structural = list(source)
        self.lines = line_spans(source)
        self.heading_spans: list[Span] = []
        self.bold_spans: list[Span] = []
        self.parenthetical_spans: list[Span] = []
        self.project()

    def mask(self, start: int, end: int, visible: bool = True, structural: bool = True) -> None:
        targets: list[list[str]] = []
        if visible:
            targets.append(self.visible)
        if structural:
            targets.append(self.structural)
        for target in targets:
            for index in range(max(0, start), min(len(target), end)):
                if target[index] not in "\r\n":
                    target[index] = " "

    def line_masked(self, start: int, end: int) -> bool:
        return bool(self.source[start:end].strip()) and not any(
            not char.isspace() for char in self.visible[start:end]
        )

    def project(self) -> None:
        self.mask_front_matter()
        self.mask_fenced_code()
        self.mask_comments_and_raw_code()
        self.mask_line_constructs()
        self.mask_inline_constructs()
        visible_text = "".join(self.visible)
        self.bold_spans = [
            Span(match.start(), match.end())
            for match in re.finditer(r"(?<!\\)(\*\*|__)(?=\S)(.+?)(?<=\S)\1", visible_text, re.DOTALL)
            if "\n\n" not in match.group(0)
        ]
        self.parenthetical_spans = [Span(m.start(), m.end()) for m in re.finditer(r"\([^()\n]{2,120}\)", visible_text)]
        for target in (self.visible, self.structural):
            for index, char in enumerate(target):
                if char in "*_`":
                    target[index] = " "

    def mask_front_matter(self) -> None:
        if not self.lines:
            return
        first_start, first_end = self.lines[0]
        if self.source[first_start:first_end].strip() != "---":
            return
        for index in range(1, min(200, len(self.lines))):
            start, end = self.lines[index]
            if self.source[start:end].strip() in {"---", "..."}:
                self.mask(first_start, end)
                return

    def mask_fenced_code(self) -> None:
        open_char: str | None = None
        open_len = 0
        block_start = 0
        for start, end in self.lines:
            line = self.source[start:end]
            marker_match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if open_char is None:
                if marker_match:
                    marker = marker_match.group(1)
                    open_char = marker[0]
                    open_len = len(marker)
                    block_start = start
            elif re.match(r"^ {0,3}" + re.escape(open_char) + "{" + str(open_len) + r",}\s*$", line):
                self.mask(block_start, end)
                open_char = None
                open_len = 0
        if open_char is not None:
            self.mask(block_start, len(self.source))

    def mask_comments_and_raw_code(self) -> None:
        for match in re.finditer(r"<!--[\s\S]*?-->", self.source):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"<(pre|script|style|code)\b[^>]*>[\s\S]*?</\1\s*>", self.source, re.IGNORECASE):
            self.mask(match.start(), match.end())

    def mask_line_constructs(self) -> None:
        table_lines: set[int] = set()
        list_lines: set[int] = set()
        for index, (start, end) in enumerate(self.lines):
            line = self.source[start:end]
            if TABLE_SEPARATOR_RE.match(line):
                table_lines.add(index)
                if index > 0 and "|" in self.source[self.lines[index - 1][0]:self.lines[index - 1][1]]:
                    table_lines.add(index - 1)
                cursor = index + 1
                while cursor < len(self.lines):
                    cstart, cend = self.lines[cursor]
                    candidate = self.source[cstart:cend]
                    if not candidate.strip() or "|" not in candidate:
                        break
                    table_lines.add(cursor)
                    cursor += 1
            if LIST_RE.match(line):
                list_lines.add(index)

        setext_titles: set[int] = set()
        setext_underlines: set[int] = set()
        for index in range(1, len(self.lines)):
            start, end = self.lines[index]
            if re.match(r"^ {0,3}(?:=+|-+)\s*$", self.source[start:end]):
                previous_start, previous_end = self.lines[index - 1]
                if self.source[previous_start:previous_end].strip():
                    setext_titles.add(index - 1)
                    setext_underlines.add(index)
                    self.heading_spans.append(Span(previous_start, previous_end))

        for index, (start, end) in enumerate(self.lines):
            line = self.source[start:end]
            if self.line_masked(start, end):
                continue
            if index in table_lines or index in setext_underlines:
                self.mask(start, end)
                continue
            if index in setext_titles:
                self.mask(start, end, visible=False, structural=True)
                continue
            if re.match(r"^ {0,3}>", line) or re.match(r"^(?: {4}|\t)", line):
                self.mask(start, end)
                continue
            if re.match(r"^\s*(?:import|export)\s+", line) or re.match(r"^ {0,3}\[[^\]]+\]:\s*\S+", line):
                self.mask(start, end)
                continue
            if re.match(r"^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$", line):
                self.mask(start, end)
                continue
            heading = HEADING_RE.match(line)
            if heading:
                self.heading_spans.append(Span(start, end))
                self.mask(start, end, visible=False, structural=True)
                self.mask(start, start + heading.end(), visible=True, structural=False)
                continue
            if index in list_lines:
                self.mask(start, end, visible=False, structural=True)
                marker = LIST_RE.match(line)
                if marker:
                    self.mask(start, start + marker.end(), visible=True, structural=False)

    def mask_inline_constructs(self) -> None:
        index = 0
        while index < len(self.source):
            if self.source[index] != "`" or self.visible[index] == " ":
                index += 1
                continue
            run_end = index + 1
            while run_end < len(self.source) and self.source[run_end] == "`":
                run_end += 1
            marker = self.source[index:run_end]
            close = self.source.find(marker, run_end)
            if close == -1:
                index = run_end
                continue
            self.mask(index, close + len(marker))
            index = close + len(marker)
        for match in re.finditer(r"!\[[^\]]*\]\([^\n)]*\)", self.source):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"(?<!!)\[[^\]\n]+\]\(([^\n)]*)\)", self.source):
            self.mask(match.start(1), match.end(1))
        for match in re.finditer(r"<(?:(?:https?|mailto):[^>]+)>", self.source, re.IGNORECASE):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"\b(?:https?://|www\.)[^\s<>()]+", self.source, re.IGNORECASE):
            self.mask(match.start(), match.end())
        for match in re.finditer(r"</?[A-Za-z][^>\n]*>", self.source):
            self.mask(match.start(), match.end())


class Document:
    def __init__(self, path: str, source: str) -> None:
        self.path = path
        self.source = source
        self.line_starts = compute_line_starts(source)
        self.suppressed_all, self.suppressed_rules = parse_suppressions(source)
        projection = Projection(source)
        self.visible = "".join(projection.visible)
        self.structural = "".join(projection.structural)
        self.heading_spans = sorted(projection.heading_spans, key=lambda item: item.start)
        self.heading_starts = [span.start for span in self.heading_spans]
        self.bold_spans = [span for span in projection.bold_spans if self.span_visible(span)]
        self.parenthetical_spans = [span for span in projection.parenthetical_spans if self.span_visible(span)]
        self.words = extract_words(self.visible)
        self.word_starts = [word.start for word in self.words]
        self.paragraphs = extract_paragraphs(self.structural)
        self.sentences: list[TextUnit] = []
        for paragraph in self.paragraphs:
            self.sentences.extend(split_sentences(paragraph.text, paragraph.start))

    def span_visible(self, span: Span) -> bool:
        return any(not char.isspace() for char in self.visible[span.start:span.end])

    @property
    def word_count(self) -> int:
        return len(self.words)

    def word_index_at(self, offset: int) -> int:
        if not self.words:
            return 0
        return max(0, bisect.bisect_right(self.word_starts, offset) - 1)

    def location(self, offset: int) -> tuple[int, int]:
        line_index = max(0, bisect.bisect_right(self.line_starts, offset) - 1)
        return line_index + 1, offset - self.line_starts[line_index] + 1

    def section_at(self, offset: int) -> int:
        return bisect.bisect_right(self.heading_starts, offset)

    def units_by_section(self, units: Sequence[TextUnit]) -> list[list[TextUnit]]:
        result: list[list[TextUnit]] = []
        current: int | None = None
        for unit in units:
            section = self.section_at(unit.start)
            if section != current:
                result.append([])
                current = section
            result[-1].append(unit)
        return result

    def is_suppressed(self, offset: int, rule_id: str) -> bool:
        line_index = min(max(0, bisect.bisect_right(self.line_starts, offset) - 1), len(self.suppressed_all) - 1)
        return self.suppressed_all[line_index] or any(
            selector_matches(selector, rule_id) for selector in self.suppressed_rules[line_index]
        )

    def excerpt(self, line: int) -> str:
        lines = self.source.splitlines()
        return lines[line - 1] if 1 <= line <= len(lines) else ""


def cluster_offsets(document: Document, offsets: Sequence[int], max_occurrences: int, window_words: int) -> list[list[int]]:
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
            cluster = ordered[left:right + 1]
            cursor = right + 1
            while cursor < len(ordered) and indices[cursor] - indices[left] <= window_words:
                cluster.append(ordered[cursor])
                cursor += 1
            clusters.append(cluster)
            right = cursor
            left = right
        else:
            right += 1
    return clusters


def phrase_checker(entries: Sequence[tuple[str, str, str | None]]) -> Callable[[Document, Mapping[str, Any]], list[Finding]]:
    compiled = [(re.compile(pattern, re.IGNORECASE), message, suggestion) for pattern, message, suggestion in entries]

    def check(document: Document, _: Mapping[str, Any]) -> list[Finding]:
        candidates: list[Finding] = []
        for pattern, message, suggestion in compiled:
            for match in pattern.finditer(document.visible):
                candidates.append(Finding(match.start(), match.end(), message, suggestion))
        findings: list[Finding] = []
        for finding in sorted(candidates, key=lambda item: (item.start, -(item.end - item.start))):
            if any(finding.start < existing.end and existing.start < finding.end for existing in findings):
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
    return [Finding(m.start(), m.end(), "Chatbot or generated-citation residue remains in the prose.", "Remove the artifact and verify the surrounding claim.") for m in pattern.finditer(document.visible)]


def negative_parallelism(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    patterns = [
        re.compile(r"\b(?:this|that|it|[A-Z][A-Za-z0-9' -]{0,35})\s+(?:isn't|is not|wasn't|was not)\s+(?:just\s+)?[^.!?\n]{2,100}[.!?]\s+(?:it(?:'s| is| was)|this is|that(?:'s| is))\s+[^.!?\n]{2,120}", re.IGNORECASE),
        re.compile(r"\bnot\s+(?:just\s+)?[^,.;!?\n]{2,80},?\s+(?:but|rather)\s+[^.;!?\n]{2,110}", re.IGNORECASE),
    ]
    spans: list[Span] = []
    for pattern in patterns:
        spans.extend(Span(match.start(), match.end()) for match in pattern.finditer(document.visible))
    spans.sort(key=lambda item: (item.start, -(item.end - item.start)))
    deduped: list[Span] = []
    for span in spans:
        if not any(span.start < existing.end and existing.start < span.end for existing in deduped):
            deduped.append(span)
    max_count = int(options.get("max", 1))
    window = int(options.get("window_words", 500))
    return [
        Finding(cluster[max_count], next((span.end for span in deduped if span.start == cluster[-1]), cluster[-1] + 1), f"{len(cluster)} contrast reframes appear within {window} words; repeated 'not X, but Y' structure starts to sound manufactured.", "State at least one positive claim directly, or keep only the strongest contrast.")
        for cluster in cluster_offsets(document, [span.start for span in deduped], max_count, window)
    ]


def no_chain(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_items", 3))
    pattern = re.compile(r"\bno\s+[^,.;:!?\n]{1,45}(?:\s*,\s*no\s+[^,.;:!?\n]{1,45})+", re.IGNORECASE)
    findings: list[Finding] = []
    for match in pattern.finditer(document.visible):
        count = len(re.findall(r"\bno\s+", match.group(0), re.IGNORECASE))
        if count >= minimum:
            findings.append(Finding(match.start(), match.end(), f"A {count}-item 'no X, no Y' chain performs emphasis without adding evidence.", "Replace the chain with the specific positive claim."))
    return findings


def question_answer(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    offsets: list[int] = []
    ends: dict[int, int] = {}
    max_answer = int(options.get("answer_max_words", 5))
    for first, second in zip(document.sentences, document.sentences[1:]):
        if document.section_at(first.start) != document.section_at(second.start):
            continue
        if first.text.rstrip().endswith("?") and second.word_count <= max_answer and not second.text.rstrip().endswith("?"):
            offsets.append(first.start)
            ends[first.start] = second.end
    max_count = int(options.get("max", 1))
    window = int(options.get("window_words", 400))
    return [Finding(cluster[max_count], ends.get(cluster[-1], cluster[-1] + 1), f"{len(cluster)} staged question-and-short-answer turns appear within {window} words.", "Turn at least one question into a direct statement.") for cluster in cluster_offsets(document, offsets, max_count, window)]


def question_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    offsets = [sentence.start for sentence in document.sentences if sentence.text.rstrip().endswith("?")]
    max_count = int(options.get("max", 3))
    window = int(options.get("window_words", 500))
    return [Finding(cluster[max_count], cluster[-1] + 1, f"{len(cluster)} questions appear within {window} words; the passage is interrogating the reader instead of explaining.", "Keep the question that creates useful tension and state the others directly.") for cluster in cluster_offsets(document, offsets, max_count, window)]


def echoed_clauses(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_clauses", 3))
    maximum = int(options.get("maximum_clauses", 5))
    findings: list[Finding] = []
    for sentence in document.sentences:
        raw = document.structural[sentence.start:sentence.end]
        pieces = [normalize_space(piece) for piece in re.split(r"\s*(?:,|;)\s*(?:(?:and|or)\s+)?", raw)]
        pieces = [piece for piece in pieces if len(WORD_RE.findall(piece)) >= 3]
        if not minimum <= len(pieces) <= maximum:
            continue
        prefixes: dict[str, int] = {}
        suffixes: dict[str, int] = {}
        for piece in pieces:
            words = [match.group(0).lower() for match in WORD_RE.finditer(piece)]
            if len(words) < 3:
                continue
            prefixes[" ".join(words[:2])] = prefixes.get(" ".join(words[:2]), 0) + 1
            suffixes[" ".join(words[-2:])] = suffixes.get(" ".join(words[-2:]), 0) + 1
        repeated_prefix = next((key for key, count in prefixes.items() if count >= minimum), None)
        repeated_suffix = next((key for key, count in suffixes.items() if count >= minimum), None)
        repeated = repeated_prefix or repeated_suffix
        if repeated and not re.search(r"\d", repeated):
            position = "opening" if repeated_prefix else "ending"
            findings.append(Finding(sentence.start, sentence.end, f"{len(pieces)} parallel clauses repeat the {position} '{repeated}'.", "Keep the parallelism only if the rhythm earns its space; otherwise combine the clauses or vary the syntax."))
    return findings


def tricolon_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    spans: list[Span] = []
    pattern = re.compile(r":\s*[^,.;!?\n]{1,36},\s*[^,.;!?\n]{1,36},\s*(?:and|or)\s+[^.;!?\n]{1,48}", re.IGNORECASE)
    spans.extend(Span(m.start(), m.end()) for m in pattern.finditer(document.structural))
    for sentence in document.sentences:
        raw = document.structural[sentence.start:sentence.end]
        if raw.count(",") == 2 and re.search(r",\s*(?:and|or)\s+", raw, re.IGNORECASE):
            parts = [part for part in re.split(r",\s*(?:and|or\s+)?|\s+(?:and|or)\s+", raw) if normalize_space(part)]
            if len(parts) == 3 and all(1 <= len(WORD_RE.findall(part)) <= 8 for part in parts):
                spans.append(Span(sentence.start, sentence.end))
    spans.sort(key=lambda item: item.start)
    max_count = int(options.get("max", 3))
    window = int(options.get("window_words", 750))
    return [Finding(cluster[max_count], cluster[-1] + 1, f"{len(cluster)} three-part rhetorical lists appear within {window} words.", "Vary the list length or convert one list into a concrete example.") for cluster in cluster_offsets(document, [span.start for span in spans], max_count, window)]


def opener_key(text: str) -> str | None:
    words = [match.group(0).lower().replace("’", "'") for match in WORD_RE.finditer(text)]
    return " ".join(words[:2]) if len(words) >= 2 else None


def repeated_openers(units: Sequence[TextUnit], consecutive: int, window_units: int, window_count: int) -> list[tuple[str, list[TextUnit]]]:
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
        grouped: dict[str, list[tuple[int, TextUnit]]] = {}
        for index in range(start, end):
            key = keys[index]
            if key is not None and index not in consumed:
                grouped.setdefault(key, []).append((index, units[index]))
        for key, pairs in grouped.items():
            if len(pairs) >= window_count and min(index for index, _ in pairs) == start:
                results.append((key, [unit for _, unit in pairs]))
                consumed.update(index for index, _ in pairs)
    return results


def sentence_openers(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    groups: list[tuple[str, list[TextUnit]]] = []
    for section in document.units_by_section(document.sentences):
        groups.extend(repeated_openers(section, int(options.get("consecutive", 3)), int(options.get("window_sentences", 8)), int(options.get("window_count", 5))))
    return [Finding(units[1].start, units[-1].end, f"{len(units)} sentences repeatedly open with '{key}'.", "Merge a sentence or vary the grammatical opening unless the repetition is deliberate anaphora.") for key, units in groups]


def paragraph_openers(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    groups: list[tuple[str, list[TextUnit]]] = []
    for section in document.units_by_section(document.paragraphs):
        groups.extend(repeated_openers(section, int(options.get("consecutive", 3)), int(options.get("window_paragraphs", 6)), int(options.get("window_count", 4))))
    return [Finding(units[1].start, units[-1].end, f"{len(units)} paragraphs repeatedly open with '{key}'.", "Vary the paragraph entry or combine paragraphs that make the same move.") for key, units in groups]


def transition_repetition(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    phrases = ["moreover", "furthermore", "additionally", "in addition", "ultimately", "in essence", "at its core", "that said", "on the other hand", "the key takeaway", "here's the thing", "here is the thing"]
    max_count = int(options.get("max", 2))
    window = int(options.get("window_words", 500))
    findings: list[Finding] = []
    for phrase in phrases:
        offsets = [m.start() for m in re.finditer(r"(?:(?<=^)|(?<=[.!?]))\s*" + re.escape(phrase) + r"\b", document.visible, re.IGNORECASE | re.MULTILINE)]
        for cluster in cluster_offsets(document, offsets, max_count, window):
            findings.append(Finding(cluster[max_count], cluster[-1] + len(phrase), f"The transition '{phrase}' appears {len(cluster)} times within {window} words.", "Delete a transition where paragraph order already makes the relationship clear."))
    return findings


def loaded_word_repetition(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    stems = {
        "delve": r"\bdelv(?:e|es|ed|ing)\b", "pivotal": r"\bpivotal\b", "nuanced": r"\bnuanced?\b",
        "robust": r"\brobust\b", "seamless": r"\bseamless(?:ly)?\b", "transformative": r"\btransformative\b",
        "landscape": r"\blandscape\b", "tapestry": r"\btapestry\b", "underscore": r"\bunderscor(?:e|es|ed|ing)\b",
        "showcase": r"\bshowcas(?:e|es|ed|ing)\b", "foster": r"\bfoster(?:s|ed|ing)?\b", "elevate": r"\belevat(?:e|es|ed|ing)\b",
        "unlock": r"\bunlock(?:s|ed|ing)?\b",
    }
    max_count = int(options.get("max", 2))
    window = int(options.get("window_words", 500))
    findings: list[Finding] = []
    for label, pattern in stems.items():
        offsets = [m.start() for m in re.finditer(pattern, document.visible, re.IGNORECASE)]
        for cluster in cluster_offsets(document, offsets, max_count, window):
            findings.append(Finding(cluster[max_count], cluster[-1] + len(label), f"The loaded word '{label}' appears {len(cluster)} times within {window} words.", "Replace at least one use with the concrete property you mean."))
    return findings


def short_sentence_run(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    max_words = int(options.get("max_words", 5))
    minimum_run = int(options.get("minimum_run", 3))
    findings: list[Finding] = []
    for section in document.units_by_section(document.sentences):
        index = 0
        while index < len(section):
            if section[index].word_count > max_words:
                index += 1
                continue
            end = index + 1
            while end < len(section) and section[end].word_count <= max_words:
                end += 1
            if end - index >= minimum_run:
                units = section[index:end]
                findings.append(Finding(units[1].start, units[-1].end, f"{len(units)} consecutive sentences contain at most {max_words} words each, creating a manufactured staccato rhythm.", "Combine related fragments and reserve the short sentence for emphasis."))
            index = end
    return findings


def uniform_sentence_length(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_sentences", 10))
    lengths = [sentence.word_count for sentence in document.sentences if sentence.word_count >= 3]
    if len(lengths) < minimum:
        return []
    mean = statistics.mean(lengths)
    coefficient = statistics.pstdev(lengths) / mean if mean else 1.0
    maximum = float(options.get("maximum_cv", 0.18))
    if coefficient >= maximum:
        return []
    return [Finding(document.sentences[0].start, document.sentences[-1].end, f"Sentence lengths are unusually uniform (coefficient of variation {coefficient:.2f} across {len(lengths)} sentences).", "Mix short assertions with longer explanatory sentences where the content supports it.")]


def density_findings(document: Document, offsets: Sequence[int], options: Mapping[str, Any], noun: str, suggestion: str) -> list[Finding]:
    max_count = int(options.get("max", 4))
    window = int(options.get("window_words", 500))
    return [Finding(cluster[max_count], cluster[-1] + 1, f"{len(cluster)} {noun} appear within {window} words.", suggestion) for cluster in cluster_offsets(document, offsets, max_count, window)]


def em_dash_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    return density_findings(document, [m.start() for m in re.finditer("—", document.visible)], options, "em dashes", "Keep the strongest interruption and use commas, parentheses, or separate sentences elsewhere.")


def bold_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    return density_findings(document, [span.start for span in document.bold_spans], options, "bold spans", "Use emphasis only where the reader genuinely needs a visual anchor.")


def parenthetical_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    return density_findings(document, [span.start for span in document.parenthetical_spans], options, "parenthetical asides", "Move necessary context into the sentence and delete dispensable asides.")


def heading_density(document: Document, options: Mapping[str, Any]) -> list[Finding]:
    minimum = int(options.get("minimum_headings", 6))
    min_words = int(options.get("min_words_per_heading", 70))
    count = len(document.heading_spans)
    if count < minimum or not document.word_count:
        return []
    ratio = document.word_count / float(count)
    if ratio >= min_words:
        return []
    return [Finding(document.heading_spans[1].start if count > 1 else document.heading_spans[0].start, document.heading_spans[-1].end, f"{count} headings divide {document.word_count} words, or only {ratio:.0f} words per heading.", "Merge sections whose headings promise more structure than the content delivers.")]


RULES = [
    Rule("artifact.chatbot-residue", "Generated-chat or citation artifacts left in prose", "error", chatbot_residue),
    Rule("verbosity.throat-clearing", "Generic opening clauses that delay the actual claim", "warning", phrase_checker([
        (r"\bwhen it comes to\b", "'When it comes to' delays the subject.", "Start with the subject and verb."),
        (r"\bin (?:today's|the modern|an? ever-changing|an? ever-evolving) (?:world|era|landscape)\b", "A generic era or landscape opener adds atmosphere instead of information.", "Name the specific change, market, or constraint."),
        (r"\bin the (?:realm|world) of\b", "This realm/world framing is vague throat-clearing.", "Name the field directly."),
        (r"\bat its core\b", "'At its core' often announces a simplification instead of making it.", "State the simplified claim directly."),
        (r"\bthe fact of the matter is\b", "This lead-in delays the claim.", "Delete the lead-in."),
    ])),
    Rule("verbosity.filler", "Wordy phrases with shorter direct equivalents", "warning", phrase_checker([
        (r"\bin order to\b", "'In order to' is usually just 'to'.", "Replace it with 'to'."),
        (r"\bdue to the fact that\b", "This phrase is wordier than 'because'.", "Replace it with 'because'."),
        (r"\bat this point in time\b", "This phrase is usually just 'now'.", "Replace it with 'now'."),
        (r"\bhas the ability to\b|\bis able to\b", "This ability phrase usually hides a direct verb.", "Use 'can' or the direct verb."),
        (r"\ba wide variety of\b", "This quantity phrase is vague unless the variety matters.", "Use 'many', list examples, or quantify."),
    ])),
    Rule("verbosity.redundant-pair", "Redundant or doubled expressions", "warning", phrase_checker([
        (r"\beach and every\b", "'Each and every' repeats the same idea.", "Choose 'each' or 'every'."),
        (r"\bvarious different\b", "'Various different' is redundant.", "Choose 'various' or 'different'."),
        (r"\bpast history\b", "History is already in the past.", "Use 'history'."),
        (r"\bfuture plans\b", "Plans normally concern the future.", "Use 'plans' unless contrasting with past plans."),
        (r"\bcompletely eliminate\b", "'Eliminate' already means remove completely.", "Use 'eliminate'."),
    ])),
    Rule("phrase.note-to-reader", "Meta-language that tells the reader what to notice", "info", phrase_checker([
        (r"\bit (?:is|'s) important to note that\b", "The sentence tells the reader what to note instead of proving its importance.", "Delete the lead-in and strengthen the claim."),
        (r"\bit (?:is|'s) worth noting that\b|\bit should be noted that\b", "The note-to-reader phrase adds editorial scaffolding.", "State the point directly."),
        (r"\bthe key takeaway is\b", "This phrase often repeats a point the paragraph should already establish.", "State the takeaway once, in the strongest location."),
    ]), strict_severity="warning"),
    Rule("phrase.marketing-language", "Generic promotional wording without a concrete property", "info", phrase_checker([
        (r"\bunlock(?:s|ed|ing)? (?:the )?(?:power|potential|possibilities)\b", "'Unlocking potential' is promotional unless the mechanism is named.", "Describe the capability or measured result."),
        (r"\bseamless(?:ly)?\b", "'Seamless' makes a quality claim without naming the seam.", "Name the transition, integration, or failure mode."),
        (r"\bgame[- ]changer\b", "'Game-changer' substitutes enthusiasm for evidence.", "Describe what changed and by how much."),
        (r"\belevat(?:e|es|ed|ing) (?:your|the)\b", "'Elevate' is generic promotional language here.", "Use the concrete improvement."),
        (r"\btransformative\b", "'Transformative' needs a specific before-and-after claim.", "Describe the transformation."),
        (r"\bultimate guide\b", "'Ultimate guide' makes a completeness claim the article is unlikely to prove.", "Use a descriptive title that states the scope."),
    ]), strict_severity="warning"),
    Rule("phrase.abstract-role", "Abstract role language that can usually be replaced by a direct verb", "info", phrase_checker([
        (r"\bserves as (?:a|an|the)\b", "'Serves as' often hides a simpler verb.", "Use 'is', 'provides', or the specific action."),
        (r"\bplays? (?:a )?(?:pivotal|crucial|vital|important) role\b", "The sentence announces importance without demonstrating it.", "Name the consequence or dependency."),
        (r"\bstands as (?:a|an|the)\b", "'Stands as' adds ceremony to a direct claim.", "Use 'is' or a more specific verb."),
    ]), strict_severity="warning"),
    Rule("phrase.landscape", "Vague landscape or tapestry metaphors", "warning", phrase_checker([
        (r"\bever[- ]evolving(?:\s+[A-Za-z-]+){0,2}\s+landscape\b", "'Ever-evolving landscape' is vague and overworked.", "Name what changed and when."),
        (r"\bin today['’]s(?:\s+[A-Za-z-]+){0,2}\s+landscape\b", "This landscape frame is generic.", "Name the current condition and its consequence."),
        (r"\b(?:rich|complex|intricate) tapestry\b", "The tapestry metaphor decorates the claim without clarifying it.", "Describe the actual components or relationship."),
    ])),
    Rule("phrase.vague-attribution", "Claims attributed to unnamed authorities", "warning", phrase_checker([
        (r"\bexperts (?:say|argue|believe|agree)\b", "'Experts' is too vague to support the claim.", "Name the expert, institution, or source."),
        (r"\bstudies (?:show|suggest|indicate|have shown)\b", "'Studies' needs a citation or identifying detail.", "Cite the study or state what evidence you reviewed."),
        (r"\bit is widely (?:believed|known|accepted)\b", "A claim of broad agreement needs evidence.", "Name the source of the consensus or remove the appeal to consensus."),
    ])),
    Rule("rhetoric.negative-parallelism", "Repeated contrast reframes", "warning", negative_parallelism, {"max": 1, "window_words": 500}, strict_defaults={"max": 0}),
    Rule("rhetoric.no-chain", "Three or more 'no X, no Y' items", "warning", no_chain, {"minimum_items": 3}, strict_defaults={"minimum_items": 2}),
    Rule("rhetoric.question-answer", "Repeated staged questions followed by short answers", "warning", question_answer, {"max": 1, "window_words": 400, "answer_max_words": 5}, strict_defaults={"max": 0}),
    Rule("rhetoric.question-density", "Too many questions in a short passage", "warning", question_density, {"max": 3, "window_words": 500}, strict_defaults={"max": 2}),
    Rule("rhetoric.echoed-clauses", "Parallel clauses repeat the same opening or ending", "warning", echoed_clauses, {"minimum_clauses": 3, "maximum_clauses": 5}),
    Rule("rhetoric.tricolon-density", "Repeated three-part rhetorical lists", "info", tricolon_density, {"max": 3, "window_words": 750}, strict_severity="warning", strict_defaults={"max": 2}),
    Rule("repetition.sentence-opener", "Repeated sentence openings", "warning", sentence_openers, {"consecutive": 3, "window_sentences": 8, "window_count": 5}, strict_defaults={"window_count": 4}),
    Rule("repetition.paragraph-opener", "Repeated paragraph openings", "warning", paragraph_openers, {"consecutive": 3, "window_paragraphs": 6, "window_count": 4}, strict_defaults={"window_count": 3}),
    Rule("repetition.transition", "Repeated stock transitions", "warning", transition_repetition, {"max": 2, "window_words": 500}, strict_defaults={"max": 1}),
    Rule("repetition.loaded-word", "Repeated abstract or promotional vocabulary", "warning", loaded_word_repetition, {"max": 2, "window_words": 500}, strict_defaults={"max": 1}),
    Rule("rhythm.short-sentence-run", "Run of very short sentences", "warning", short_sentence_run, {"max_words": 5, "minimum_run": 3}, strict_defaults={"max_words": 6}),
    Rule("rhythm.uniform-sentence-length", "Unusually uniform sentence lengths", "off", uniform_sentence_length, {"minimum_sentences": 10, "maximum_cv": 0.18}, strict_severity="info"),
    Rule("density.em-dash", "High em-dash density", "warning", em_dash_density, {"max": 4, "window_words": 500}, strict_defaults={"max": 3}),
    Rule("density.bold", "High bold-emphasis density", "warning", bold_density, {"max": 10, "window_words": 500}, strict_defaults={"max": 6}),
    Rule("density.parenthetical", "High parenthetical-aside density", "off", parenthetical_density, {"max": 6, "window_words": 500}, strict_severity="info", strict_defaults={"max": 5}),
    Rule("structure.heading-density", "Many headings relative to prose", "off", heading_density, {"minimum_headings": 6, "min_words_per_heading": 70}, strict_severity="info"),
]
RULES_BY_ID = {rule.id: rule for rule in RULES}


INTEGER_OPTIONS = {
    "max", "window_words", "minimum_items", "answer_max_words", "minimum_clauses", "maximum_clauses",
    "consecutive", "window_sentences", "window_count", "window_paragraphs", "max_words", "minimum_run",
    "minimum_sentences", "minimum_headings", "min_words_per_heading",
}


def load_config(path: str | None) -> dict[str, Any]:
    candidate = path
    if candidate is None:
        default_path = os.path.join(os.getcwd(), ".anti-slop.json")
        candidate = default_path if os.path.isfile(default_path) else None
    if candidate is None:
        return {}
    try:
        with open(candidate, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"Cannot read config {candidate}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a JSON object")
    unknown = set(data) - {"preset", "fail_level", "rules"}
    if unknown:
        raise ConfigError("Unknown config keys: " + ", ".join(sorted(unknown)))
    if data.get("preset") not in {None, "recommended", "strict"}:
        raise ConfigError("'preset' must be 'recommended' or 'strict'")
    if data.get("fail_level") not in {None, "info", "warning", "error", "none"}:
        raise ConfigError("'fail_level' must be info, warning, error, or none")
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        raise ConfigError("'rules' must be a JSON object")
    unknown_rules = set(rules) - set(RULES_BY_ID)
    if unknown_rules:
        raise ConfigError("Unknown rules: " + ", ".join(sorted(unknown_rules)))
    return data


def resolve_rule(rule: Rule, preset: str, config: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    severity = rule.recommended_severity
    options = dict(rule.defaults)
    if preset == "strict":
        severity = rule.strict_severity if rule.strict_severity is not None else severity
        options.update(rule.strict_defaults)
    override = config.get("rules", {}).get(rule.id)
    if isinstance(override, str):
        severity = override
    elif isinstance(override, dict):
        override = dict(override)
        if "severity" in override:
            severity = override.pop("severity")
        unknown = set(override) - (set(rule.defaults) | set(rule.strict_defaults))
        if unknown:
            raise ConfigError(f"Rule '{rule.id}' has unknown options: {', '.join(sorted(unknown))}")
        options.update(override)
    elif override is not None:
        raise ConfigError(f"Rule '{rule.id}' must be a severity string or JSON object")
    if severity not in SEVERITY_ORDER:
        raise ConfigError(f"Rule '{rule.id}' has invalid severity '{severity}'")
    for name, value in options.items():
        if name == "maximum_cv":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ConfigError(f"Rule '{rule.id}' option '{name}' must be a positive number")
        elif name in INTEGER_OPTIONS:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfigError(f"Rule '{rule.id}' option '{name}' must be an integer")
            if value < (0 if name == "max" else 1):
                raise ConfigError(f"Rule '{rule.id}' option '{name}' has an invalid range")
    if options.get("minimum_clauses", 1) > options.get("maximum_clauses", sys.maxsize):
        raise ConfigError(f"Rule '{rule.id}' requires minimum_clauses <= maximum_clauses")
    return severity, options


def lint_document(document: Document, preset: str = "recommended", config: Mapping[str, Any] | None = None) -> list[Diagnostic]:
    if preset not in {"recommended", "strict"}:
        raise ConfigError(f"Unknown preset '{preset}'")
    config = config or {}
    diagnostics: list[Diagnostic] = []
    for rule in RULES:
        severity, options = resolve_rule(rule, preset, config)
        if severity == "off":
            continue
        for finding in rule.checker(document, options):
            if document.is_suppressed(finding.start, rule.id):
                continue
            line, column = document.location(finding.start)
            end_line, end_column = document.location(max(finding.start, finding.end - 1))
            diagnostics.append(Diagnostic(document.path, rule.id, severity, finding.message, finding.start, finding.end, line, column, end_line, end_column + 1, finding.suggestion))
    return sorted(diagnostics, key=lambda item: (item.path, item.start, -SEVERITY_ORDER[item.severity], item.rule_id))


def diagnostic_dict(item: Diagnostic) -> dict[str, Any]:
    return {
        "path": item.path, "line": item.line, "column": item.column, "end_line": item.end_line,
        "end_column": item.end_column, "severity": item.severity, "rule": item.rule_id,
        "message": item.message, "suggestion": item.suggestion,
    }


def github_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A").replace(":", "%3A").replace(",", "%2C")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="anti-slop", description="Deterministically lint Markdown for canned, repetitive, or bloated prose.")
    parser.add_argument("files", metavar="FILE", nargs="*")
    parser.add_argument("--config")
    parser.add_argument("--preset", choices=["recommended", "strict"])
    parser.add_argument("--format", choices=["text", "json", "github"], default="text")
    parser.add_argument("--fail-level", choices=["info", "warning", "error", "none"])
    parser.add_argument("--no-excerpts", action="store_true")
    parser.add_argument("--list-rules", action="store_true")
    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_rules:
        for rule in RULES:
            strict = rule.strict_severity if rule.strict_severity is not None else rule.recommended_severity
            print(f"{rule.id:<38} recommended={rule.recommended_severity:<7} strict={strict:<7} {rule.summary}")
        return 0
    if not args.files:
        print("anti-slop: no files provided", file=sys.stderr)
        return 2
    try:
        config = load_config(args.config)
        preset = args.preset or config.get("preset", "recommended")
        fail_level = args.fail_level or config.get("fail_level", "warning")
        documents: dict[str, Document] = {}
        diagnostics: list[Diagnostic] = []
        for path in args.files:
            try:
                with open(path, encoding="utf-8") as handle:
                    source = handle.read()
            except (OSError, UnicodeError) as exc:
                print(f"anti-slop: cannot read {path}: {exc}", file=sys.stderr)
                return 2
            document = Document(path, source)
            documents[path] = document
            diagnostics.extend(lint_document(document, preset, config))
        diagnostics.sort(key=lambda item: (item.path, item.start, -SEVERITY_ORDER[item.severity], item.rule_id))
    except ConfigError as exc:
        print(f"anti-slop: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([diagnostic_dict(item) for item in diagnostics], indent=2, sort_keys=True))
    elif args.format == "github":
        for item in diagnostics:
            level = "error" if item.severity == "error" else "warning" if item.severity == "warning" else "notice"
            message = item.message + ((" Suggestion: " + item.suggestion) if item.suggestion else "")
            print(f"::{level} file={github_escape(item.path)},line={item.line},col={item.column},endLine={item.end_line},endColumn={item.end_column},title={github_escape('anti-slop/' + item.rule_id)}::{github_escape(message)}")
    else:
        for item in diagnostics:
            print(f"{item.path}:{item.line}:{item.column}: {item.severity} [{item.rule_id}] {item.message}")
            if item.suggestion:
                print(f"  suggestion: {item.suggestion}")
            if not args.no_excerpts:
                excerpt = documents[item.path].excerpt(item.line)
                if excerpt:
                    print("  " + excerpt.rstrip())
        if diagnostics:
            counts = {severity: sum(item.severity == severity for item in diagnostics) for severity in ("error", "warning", "info")}
            print(f"\nanti-slop: {len(diagnostics)} diagnostics ({counts['error']} error, {counts['warning']} warning, {counts['info']} info)")
    if fail_level == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_level]
    return 1 if any(SEVERITY_ORDER[item.severity] >= threshold for item in diagnostics) else 0


if __name__ == "__main__":
    raise SystemExit(main())
