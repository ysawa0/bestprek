import argparse
from pathlib import Path


def check(description: str, advice: str) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--max-lines", type=int, default=1000)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failed = False
    for filename in args.files:
        with Path(filename).open("rb") as file:
            lines = sum(1 for _ in file)
        if lines > args.max_lines:
            print(
                f"{filename}: {lines} lines exceeds the limit of {args.max_lines}. "
                + advice
            )
            failed = True
    return int(failed)


def code() -> int:
    return check("Limit code file length", "Split or refactor the code file as needed.")


def markdown() -> int:
    return check(
        "Limit Markdown file length",
        'Move content into an "archive" subdirectory or delete content '
        "that is no longer needed.",
    )
