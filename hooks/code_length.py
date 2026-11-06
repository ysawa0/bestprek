import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Limit code file length")
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
                "Split or refactor the code file as needed."
            )
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
