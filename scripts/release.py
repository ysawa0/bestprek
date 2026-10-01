"""Prepare release metadata; CI publishes the committed release."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    version = sys.argv[1]
    if not re.fullmatch(r"[0-9]+\.[0-9]+", version):
        raise SystemExit("Version must have the form 1.18")
    notes = ROOT / ".github" / "release-notes" / f"{version}.md"
    if not notes.is_file():
        raise SystemExit(f"Write release notes in {notes} first")
    release = ROOT / "RELEASE"
    lines = release.read_text().splitlines()
    example = ROOT / "example_conf" / "prek.toml"
    old, new = f'rev = "{lines[0]}"', f'rev = "{version}"'
    text = example.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Expected one {old!r} in {example}")
    example.write_text(text.replace(old, new))
    lines[0] = version
    release.write_text("\n".join(lines) + "\n")
    print(f"Prepared {version}. Commit and push to main; CI tests and publishes it.")


if __name__ == "__main__":
    main()
