import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Limit Markdown line width")
    parser.add_argument("--max-chars", type=int, default=300)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failed = False
    for filename in args.files:
        with Path(filename).open(encoding="utf-8") as file:
            for number, line in enumerate(file, start=1):
                width = len(line.rstrip("\r\n"))
                if width > args.max_chars:
                    print(
                        f"{filename}:{number}: {width} characters exceeds the limit of "
                        f"{args.max_chars}. Create new lines or new sub-bullet points."
                    )
                    failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
