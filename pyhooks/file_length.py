import argparse
import math
from pathlib import Path

ARCHIVE_ADVICE = (
    'Move content into an "archive" subdirectory or delete content '
    "that is no longer needed."
)


def parse(description: str, flag: str, default: int) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(flag, type=int, default=default)
    parser.add_argument("files", nargs="+")
    return parser.parse_args()


def code() -> int:
    args = parse("Limit code file length", "--max-lines", 1000)
    failed = False
    for filename in args.files:
        with Path(filename).open("rb") as file:
            lines = sum(1 for _ in file)
        if lines > args.max_lines:
            print(
                f"{filename}: {lines} lines exceeds the limit of {args.max_lines}. "
                "Split or refactor the code file as needed."
            )
            failed = True
    return int(failed)


def markdown() -> int:
    args = parse("Limit Markdown file size", "--max-kb", 20)
    failed = False
    for filename in args.files:
        size = Path(filename).stat().st_size
        if size > args.max_kb * 1024:
            print(
                f"{filename}: {math.ceil(size / 1024)} KB exceeds the limit of "
                f"{args.max_kb} KB. {ARCHIVE_ADVICE}"
            )
            failed = True
    return int(failed)
