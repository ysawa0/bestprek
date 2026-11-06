import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Limit Markdown line width")
    parser.add_argument("--max-chars", type=int, default=300)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failed = False
    for filename in args.files:
        lines = Path(filename).read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            if len(line) > args.max_chars:
                print(
                    f"{filename}:{number}: {len(line)} characters exceeds the limit of "
                    f"{args.max_chars}. Create new lines or new sub-bullet points."
                )
                failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
