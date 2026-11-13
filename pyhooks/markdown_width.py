import argparse
from pathlib import Path

from pyhooks.directives import suppressed


def main() -> int:
    parser = argparse.ArgumentParser(description="Limit Markdown line width")
    parser.add_argument("--max-chars", type=int, default=300)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failed = False
    for filename in args.files:
        lines = Path(filename).read_text(encoding="utf-8").splitlines()
        skipped = suppressed(lines, "markdown-width")
        for number, line in enumerate(lines, start=1):
            # Table rows cannot wrap, so only prose lines count.
            if (
                len(line) > args.max_chars
                and number not in skipped
                and not line.lstrip().startswith("|")
            ):
                print(
                    f"{filename}:{number}: {len(line)} characters exceeds the limit of "
                    f"{args.max_chars}. Create new lines or new sub-bullet points."
                )
                failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
