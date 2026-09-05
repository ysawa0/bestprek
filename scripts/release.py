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
    previous = (ROOT / "RELEASE").read_text().strip()
    replacements = {
        "README.md": (f'rev = "{previous}"', f'rev = "{version}"'),
        "hooks/unslop.py": (f'VERSION = "{previous}"', f'VERSION = "{version}"'),
    }
    for filename, (old, new) in replacements.items():
        path = ROOT / filename
        text = path.read_text()
        if text.count(old) != 1:
            raise SystemExit(f"Expected one {old!r} in {filename}")
        path.write_text(text.replace(old, new))
    (ROOT / "RELEASE").write_text(version + "\n")
    print(f"Prepared {version}. Commit and push to main; CI tests and publishes it.")


if __name__ == "__main__":
    main()
