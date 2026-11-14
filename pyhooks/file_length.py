import argparse
import math
from pathlib import Path


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
                f"{filename}: {math.ceil(size / 1024)} KB, over the "
                f"{args.max_kb} KB limit (~{args.max_kb // 4}k tokens).\n"
                "  Why: agents load whole Markdown files into context, so large "
                "files waste tokens and bury the parts that matter.\n"
                "  Fix: split it into focused files linked from a short index, "
                "delete what is outdated, or move history into an archive/ "
                "directory and add it to this hook's exclude in prek.toml."
            )
            failed = True
    return int(failed)
