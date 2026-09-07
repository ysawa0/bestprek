"""Exercise Unslop's CLI on sentence boundaries and a large masked code block."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / ".ci" / "fixtures" / "unslop"


def lint(path: Path, config: Path) -> list[dict[str, object]]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hooks.unslop",
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


if __name__ == "__main__":
    main()
