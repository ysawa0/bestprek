"""Deterministic Markdown prose linter."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from .unslop_core import (
    SEVERITY_ORDER,
    ConfigError,
    Diagnostic,
    Document,
    Finding,
    Rule,
)
from .unslop_rules import RULES, RULES_BY_ID

VERSION = "1.18"

INTEGER_OPTIONS = {
    "max",
    "window_words",
    "minimum_items",
    "answer_max_words",
    "minimum_clauses",
    "maximum_clauses",
    "consecutive",
    "window_sentences",
    "window_count",
    "window_paragraphs",
    "max_words",
    "minimum_run",
    "minimum_sentences",
    "minimum_headings",
    "min_words_per_heading",
}


def load_config(path: str | None) -> dict[str, Any]:
    candidate = path
    if candidate is None:
        default_path = os.path.join(os.getcwd(), ".unslop.json")
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


def validate_option(rule: Rule, name: str, value: Any) -> None:
    if name == "maximum_cv":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ConfigError(
                f"Rule '{rule.id}' option '{name}' must be a positive number"
            )
        return
    if name not in INTEGER_OPTIONS:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Rule '{rule.id}' option '{name}' must be an integer")
    if value < (0 if name == "max" else 1):
        raise ConfigError(f"Rule '{rule.id}' option '{name}' has an invalid range")


def resolve_rule(
    rule: Rule, preset: str, config: Mapping[str, Any]
) -> tuple[str, dict[str, Any]]:
    severity = rule.recommended_severity
    options = dict(rule.defaults)
    if preset == "strict":
        severity = (
            rule.strict_severity if rule.strict_severity is not None else severity
        )
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
            raise ConfigError(
                f"Rule '{rule.id}' has unknown options: {', '.join(sorted(unknown))}"
            )
        options.update(override)
    elif override is not None:
        raise ConfigError(f"Rule '{rule.id}' must be a severity string or JSON object")
    if severity not in SEVERITY_ORDER:
        raise ConfigError(f"Rule '{rule.id}' has invalid severity '{severity}'")
    for name, value in options.items():
        validate_option(rule, name, value)
    if options.get("minimum_clauses", 1) > options.get("maximum_clauses", sys.maxsize):
        raise ConfigError(
            f"Rule '{rule.id}' requires minimum_clauses <= maximum_clauses"
        )
    return severity, options


def make_diagnostic(
    document: Document, rule: Rule, severity: str, finding: Finding
) -> Diagnostic:
    line, column = document.location(finding.start)
    end_line, end_column = document.location(max(finding.start, finding.end - 1))
    return Diagnostic(
        document.path,
        rule.id,
        severity,
        finding.message,
        finding.start,
        finding.end,
        line,
        column,
        end_line,
        end_column + 1,
        finding.suggestion,
    )


def apply_rule(
    document: Document, rule: Rule, preset: str, config: Mapping[str, Any]
) -> list[Diagnostic]:
    severity, options = resolve_rule(rule, preset, config)
    if severity == "off":
        return []
    return [
        make_diagnostic(document, rule, severity, finding)
        for finding in rule.checker(document, options)
        if not document.is_suppressed(finding.start, rule.id)
    ]


def lint_document(
    document: Document,
    preset: str = "recommended",
    config: Mapping[str, Any] | None = None,
) -> list[Diagnostic]:
    if preset not in {"recommended", "strict"}:
        raise ConfigError(f"Unknown preset '{preset}'")
    config = config or {}
    diagnostics: list[Diagnostic] = []
    for rule in RULES:
        diagnostics.extend(apply_rule(document, rule, preset, config))
    return sorted(
        diagnostics,
        key=lambda item: (
            item.path,
            item.start,
            -SEVERITY_ORDER[item.severity],
            item.rule_id,
        ),
    )


def diagnostic_dict(item: Diagnostic) -> dict[str, Any]:
    return {
        "path": item.path,
        "line": item.line,
        "column": item.column,
        "end_line": item.end_line,
        "end_column": item.end_column,
        "severity": item.severity,
        "rule": item.rule_id,
        "message": item.message,
        "suggestion": item.suggestion,
    }


def github_escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="unslop",
        description="Deterministically lint Markdown for canned, repetitive, or bloated prose.",
    )
    parser.add_argument("files", metavar="FILE", nargs="*")
    parser.add_argument("--config")
    parser.add_argument("--preset", choices=["recommended", "strict"])
    parser.add_argument("--format", choices=["text", "json", "github"], default="text")
    parser.add_argument("--fail-level", choices=["info", "warning", "error", "none"])
    parser.add_argument("--no-excerpts", action="store_true")
    parser.add_argument("--list-rules", action="store_true")
    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    return parser.parse_args(argv)


def read_document(path: str) -> Document:
    try:
        with open(path, encoding="utf-8") as handle:
            return Document(path, handle.read())
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc


def lint_paths(
    paths: Sequence[str], preset: str, config: Mapping[str, Any]
) -> tuple[dict[str, Document], list[Diagnostic]]:
    documents: dict[str, Document] = {}
    diagnostics: list[Diagnostic] = []
    for path in paths:
        document = read_document(path)
        documents[path] = document
        diagnostics.extend(lint_document(document, preset, config))
    diagnostics.sort(
        key=lambda item: (
            item.path,
            item.start,
            -SEVERITY_ORDER[item.severity],
            item.rule_id,
        )
    )
    return documents, diagnostics


def print_json(diagnostics: Sequence[Diagnostic]) -> None:
    print(
        json.dumps(
            [diagnostic_dict(item) for item in diagnostics],
            indent=2,
            sort_keys=True,
        )
    )


def github_level(severity: str) -> str:
    if severity == "error":
        return "error"
    if severity == "warning":
        return "warning"
    return "notice"


def print_github(diagnostics: Sequence[Diagnostic]) -> None:
    for item in diagnostics:
        message = item.message + (
            (" Suggestion: " + item.suggestion) if item.suggestion else ""
        )
        print(
            f"::{github_level(item.severity)} file={github_escape(item.path)},line={item.line},col={item.column},endLine={item.end_line},endColumn={item.end_column},title={github_escape('unslop/' + item.rule_id)}::{github_escape(message)}"
        )


def print_excerpt(document: Document, line: int) -> None:
    excerpt = document.excerpt(line)
    if excerpt:
        print("  " + excerpt.rstrip())


def print_text(
    diagnostics: Sequence[Diagnostic],
    documents: Mapping[str, Document],
    no_excerpts: bool,
) -> None:
    for item in diagnostics:
        print(
            f"{item.path}:{item.line}:{item.column}: {item.severity} [{item.rule_id}] {item.message}"
        )
        if item.suggestion:
            print(f"  suggestion: {item.suggestion}")
        if not no_excerpts:
            print_excerpt(documents[item.path], item.line)
    if not diagnostics:
        return
    counts = {
        severity: sum(item.severity == severity for item in diagnostics)
        for severity in ("error", "warning", "info")
    }
    print(
        f"\nunslop: {len(diagnostics)} diagnostics ({counts['error']} error, {counts['warning']} warning, {counts['info']} info)"
    )


def print_diagnostics(
    output_format: str,
    diagnostics: Sequence[Diagnostic],
    documents: Mapping[str, Document],
    no_excerpts: bool,
) -> None:
    if output_format == "json":
        print_json(diagnostics)
        return
    if output_format == "github":
        print_github(diagnostics)
        return
    print_text(diagnostics, documents, no_excerpts)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_rules:
        for rule in RULES:
            strict = (
                rule.strict_severity
                if rule.strict_severity is not None
                else rule.recommended_severity
            )
            print(
                f"{rule.id:<38} recommended={rule.recommended_severity:<7} strict={strict:<7} {rule.summary}"
            )
        return 0
    if not args.files:
        print("unslop: no files provided", file=sys.stderr)
        return 2
    try:
        config = load_config(args.config)
        preset = args.preset or config.get("preset", "recommended")
        fail_level = args.fail_level or config.get("fail_level", "info")
        documents, diagnostics = lint_paths(args.files, preset, config)
    except ConfigError as exc:
        print(f"unslop: {exc}", file=sys.stderr)
        return 2

    print_diagnostics(args.format, diagnostics, documents, args.no_excerpts)
    if fail_level == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_level]
    return (
        1
        if any(SEVERITY_ORDER[item.severity] >= threshold for item in diagnostics)
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
