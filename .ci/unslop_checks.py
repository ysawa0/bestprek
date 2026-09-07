"""Exercise the Rust CLI against saved diagnostics, options, and a large document."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / ".ci" / "fixtures" / "unslop"
BIN = ROOT / "target" / "release" / "unslop"


def lint(path: Path, config: Path) -> list[dict[str, object]]:
    result = subprocess.run(
        [
            str(BIN),
            "--config",
            str(config),
            "--format",
            "json",
            str(path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if result.returncode != 1:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
        work = Path(directory)
        config = work / ".unslop.json"
        config.write_text(
            '{"rules":{"repetition.transition":{"max":0,"window_words":1}}}\n'
        )
        source = FIXTURES / "transitions.input.txt"
        expected = json.loads((FIXTURES / "transitions.expected.json").read_text())
        actual = lint(source, config)
        for diagnostic in actual:
            diagnostic.pop("path")
        if actual != expected:
            raise AssertionError(actual)
        print("PASS unslop CLI: transition diagnostics and source locations")

        path = work / "large.md"
        block = "```text\n" + "sample = 123\n" * 20_000 + "```\n\n"
        path.write_text(block + source.read_text())
        shifted = lint(path, config)
        for diagnostic in shifted:
            diagnostic.pop("path")
        expected = [
            {
                **diagnostic,
                "line": diagnostic["line"] + block.count("\n"),
                "end_line": diagnostic["end_line"] + block.count("\n"),
            }
            for diagnostic in expected
        ]
        if shifted != expected:
            raise AssertionError(shifted)
        print("PASS unslop CLI: 20,000 masked code lines finish within 10 seconds")

        check_parity(work)
        check_options(work)


def check_parity(work: Path) -> None:
    folder = FIXTURES / "parity"
    cases = json.loads((folder / "cases.json").read_text())
    for case in cases:
        check_case(work, folder, case)
    print(f"PASS unslop CLI: {len(cases)} reference cases match Python diagnostics")


def check_case(work: Path, folder: Path, case: dict) -> None:
    name = case["name"]
    source = folder / case.get("input", f"{name}.input.txt")
    path = work / "draft.md"
    path.write_bytes(source.read_bytes())
    config = work / ".unslop.json"
    config.write_text(json.dumps(case["config"]))
    result = subprocess.run(
        [
            str(BIN),
            "--config",
            str(config),
            "--preset",
            case["preset"],
            "--format",
            "json",
            str(path),
        ],
        cwd=work,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if "error" in case:
        if result.returncode != 2 or case["error"] not in result.stderr:
            raise AssertionError(f"{name}: {result.stdout}{result.stderr}")
        return
    expected = json.loads((folder / f"{name}.expected.txt").read_text())
    if result.returncode != int(bool(expected)):
        raise AssertionError(f"{name}: {result.stdout}{result.stderr}")
    actual = json.loads(result.stdout)
    for diagnostic in actual:
        diagnostic.pop("path")
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def invoke(
    work: Path, *arguments: str, expected: int
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(BIN), *arguments],
        cwd=work,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if result.returncode != expected:
        raise AssertionError(result.stdout + result.stderr)
    return result


def check_options(work: Path) -> None:
    config = work / ".unslop.json"
    config.write_text("{}\n")
    name = "draft %é,:.md"
    (work / name).write_text("🎯 In order to brew coffee, heat the water.\n")
    for mode, arguments in [
        ("text", []),
        ("no-excerpts", ["--no-excerpts"]),
        ("github", ["--format", "github"]),
    ]:
        actual = invoke(work, *arguments, name, expected=1).stdout
        expected = (FIXTURES / "parity" / f"format-{mode}.expected.txt").read_text()
        if actual != expected:
            raise AssertionError(f"{mode}: {actual}")
    invoke(work, "--fail-level", "none", name, expected=0)
    invoke(work, "--fail-level", "error", name, expected=0)
    invoke(work, "--format", "invalid", name, expected=2)
    invoke(work, "--unknown", name, expected=2)
    invoke(work, "--preset", "invalid", name, expected=2)
    invoke(work, expected=2)
    invoke(work, "missing.md", expected=2)
    (work / "invalid.md").write_bytes(b"\xff")
    invoke(work, "invalid.md", expected=2)
    invoke(work, "--help", expected=0)
    version = (ROOT / "RELEASE").read_text().splitlines()[0]
    if invoke(work, "--version", expected=0).stdout != f"unslop {version}\n":
        raise AssertionError("CLI version must match RELEASE")
    rules = invoke(work, "--list-rules", expected=0).stdout.splitlines()
    covered = {
        diagnostic["rule"]
        for path in (FIXTURES / "parity").glob("*.expected.txt")
        if not path.name.startswith("format-")
        for diagnostic in json.loads(path.read_text())
    }
    if len(rules) != 25 or {line.split()[0] for line in rules} != covered:
        raise AssertionError("Every published prose rule needs a positive fixture")
    invalid_configs = [
        ([], "Config root must be a JSON object"),
        ({"unknown": True}, "Unknown config keys"),
        ({"preset": "invalid"}, "'preset' must be"),
        ({"fail_level": "invalid"}, "'fail_level' must be"),
        ({"rules": []}, "'rules' must be a JSON object"),
        ({"rules": {"made.up": "off"}}, "Unknown rules"),
        ({"rules": {"density.em-dash": "fatal"}}, "invalid severity"),
        ({"rules": {"density.em-dash": 3}}, "must be a severity string or JSON object"),
        ({"rules": {"density.em-dash": {"max": True}}}, "must be an integer"),
        ({"rules": {"density.em-dash": {"max": -1}}}, "invalid range"),
        (
            {"rules": {"rhythm.uniform-sentence-length": {"maximum_cv": 0}}},
            "positive number",
        ),
        (
            {"rules": {"rhetoric.echoed-clauses": {"minimum_clauses": 6}}},
            "minimum_clauses <= maximum_clauses",
        ),
    ]
    for value, diagnostic in invalid_configs:
        config.write_text(json.dumps(value))
        result = invoke(work, name, expected=2)
        if diagnostic not in result.stderr:
            raise AssertionError(result.stderr)
    config.write_text("{broken")
    if "Cannot read config" not in invoke(work, name, expected=2).stderr:
        raise AssertionError("Malformed configuration must report a config error")
    print("PASS unslop CLI: output formats, rule coverage, versions, and config errors")


if __name__ == "__main__":
    main()
