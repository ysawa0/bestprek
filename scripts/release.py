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
    previous = lines[0]
    replacements = {
        "README.md": (f'rev = "{previous}"', f'rev = "{version}"'),
        "example_conf/prek.toml": (f'rev = "{previous}"', f'rev = "{version}"'),
        "Cargo.toml": (f'version = "{previous}.0"', f'version = "{version}.0"'),
        "Cargo.lock": (f'version = "{previous}.0"', f'version = "{version}.0"'),
    }
    for filename, (old, new) in replacements.items():
        path = ROOT / filename
        text = path.read_text()
        if text.count(old) != 1:
            raise SystemExit(f"Expected one {old!r} in {filename}")
        path.write_text(text.replace(old, new))
    lines[0] = version
    release.write_text("\n".join(lines) + "\n")
    print(f"Prepared {version}. Commit and push to main; CI tests and publishes it.")


if __name__ == "__main__":
    main()
