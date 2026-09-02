"""Markdown projection and source-location model for Unslop."""

from __future__ import annotations

import bisect
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

SEVERITY_ORDER = {"off": -1, "info": 0, "warning": 1, "error": 2}
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[’'][A-Za-z0-9]+)*(?:-[A-Za-z0-9]+)*")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
DIRECTIVE_RE = re.compile(
    r"<!--\s*unslop-(disable-next-line|disable|enable|ignore)(?:\s+([^>]*?))?\s*-->",
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
    checker: Callable[[Document, Mapping[str, Any]], list[Finding]]
    defaults: dict[str, Any] = field(default_factory=dict)
    strict_severity: str | None = None
    strict_defaults: dict[str, Any] = field(default_factory=dict)


class ConfigError(ValueError):
    """Raised for invalid unslop configuration."""


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
        Word(
            match.group(0),
            match.group(0).lower().replace("’", "'"),
            match.start(),
            match.end(),
        )
        for match in WORD_RE.finditer(text)
    ]


ABBREVIATIONS = {
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "st.",
    "fig.",
    "no.",
}


def looks_like_abbreviation(text: str, punctuation_index: int) -> bool:
    prefix = text[max(0, punctuation_index - 12) : punctuation_index + 1].lower()
    if any(prefix.endswith(item) for item in ABBREVIATIONS):
        return True
    return bool(re.search(r"\b[A-Za-z]\.$", prefix))


def split_sentences(text: str, base_offset: int) -> list[TextUnit]:
    units: list[TextUnit] = []
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        boundary = char in "!?" or (
            char == "." and not looks_like_abbreviation(text, index)
        )
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
                units.append(
                    TextUnit(
                        base_offset + start + leading,
                        base_offset + start + trailing,
                        clean,
                        count,
                    )
                )
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

    def mask(
        self, start: int, end: int, visible: bool = True, structural: bool = True
    ) -> None:
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
            for match in re.finditer(
                r"(?<!\\)(\*\*|__)(?=\S)(.+?)(?<=\S)\1", visible_text, re.DOTALL
            )
            if "\n\n" not in match.group(0)
        ]
        self.parenthetical_spans = [
            Span(m.start(), m.end())
            for m in re.finditer(r"\([^()\n]{2,120}\)", visible_text)
        ]
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
            elif re.match(
                r"^ {0,3}" + re.escape(open_char) + "{" + str(open_len) + r",}\s*$",
                line,
            ):
                self.mask(block_start, end)
                open_char = None
                open_len = 0
        if open_char is not None:
            self.mask(block_start, len(self.source))

    def mask_comments_and_raw_code(self) -> None:
        for match in re.finditer(r"<!--[\s\S]*?-->", self.source):
            self.mask(match.start(), match.end())
        for match in re.finditer(
            r"<(pre|script|style|code)\b[^>]*>[\s\S]*?</\1\s*>",
            self.source,
            re.IGNORECASE,
        ):
            self.mask(match.start(), match.end())

    def mask_line_constructs(self) -> None:
        table_lines: set[int] = set()
        list_lines: set[int] = set()
        for index, (start, end) in enumerate(self.lines):
            line = self.source[start:end]
            if TABLE_SEPARATOR_RE.match(line):
                table_lines.add(index)
                if (
                    index > 0
                    and "|"
                    in self.source[self.lines[index - 1][0] : self.lines[index - 1][1]]
                ):
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
            if re.match(r"^\s*(?:import|export)\s+", line) or re.match(
                r"^ {0,3}\[[^\]]+\]:\s*\S+", line
            ):
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
                    self.mask(
                        start, start + marker.end(), visible=True, structural=False
                    )

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
        for match in re.finditer(r"(?<!!)\[[^\]\n]+\](\([^\n)]*\))", self.source):
            self.mask(match.start(1), match.end(1))
        for match in re.finditer(
            r"<(?:(?:https?|mailto):[^>]+)>", self.source, re.IGNORECASE
        ):
            self.mask(match.start(), match.end())
        for match in re.finditer(
            r"\b(?:https?://|www\.)[^\s<>()]+", self.source, re.IGNORECASE
        ):
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
        self.heading_spans = sorted(
            projection.heading_spans, key=lambda item: item.start
        )
        self.heading_starts = [span.start for span in self.heading_spans]
        self.bold_spans = [
            span for span in projection.bold_spans if self.span_visible(span)
        ]
        self.parenthetical_spans = [
            span for span in projection.parenthetical_spans if self.span_visible(span)
        ]
        self.words = extract_words(self.visible)
        self.word_starts = [word.start for word in self.words]
        self.paragraphs = extract_paragraphs(self.structural)
        self.sentences: list[TextUnit] = []
        for paragraph in self.paragraphs:
            self.sentences.extend(split_sentences(paragraph.text, paragraph.start))

    def span_visible(self, span: Span) -> bool:
        return any(not char.isspace() for char in self.visible[span.start : span.end])

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
        line_index = min(
            max(0, bisect.bisect_right(self.line_starts, offset) - 1),
            len(self.suppressed_all) - 1,
        )
        return self.suppressed_all[line_index] or any(
            selector_matches(selector, rule_id)
            for selector in self.suppressed_rules[line_index]
        )

    def excerpt(self, line: int) -> str:
        lines = self.source.splitlines()
        return lines[line - 1] if 1 <= line <= len(lines) else ""
