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


def too_big(filename: str, max_kb: int, why: str, fix: str) -> bool:
    size = Path(filename).stat().st_size
    if size <= max_kb * 1024:
        return False
    print(
        f"{filename}: {math.ceil(size / 1024)} KB, over the "
        f"{max_kb} KB limit (~{max_kb // 4}k tokens).\n  Why: {why}\n  Fix: {fix}"
    )
    return True


def markdown() -> int:
    args = parse("Limit Markdown file size", "--max-kb", 20)
    why = (
        "agents load whole Markdown files into context, so large files waste tokens "
        "and bury the parts that matter."
    )
    fix = (
        "split it into focused files, delete what is outdated or unneeded, or move "
        "history into an archive/ directory and add it to this hook's exclude in prek.toml."
    )
    failed = [too_big(f, args.max_kb, why, fix) for f in args.files]
    return int(any(failed))


def skill() -> int:
    parser = argparse.ArgumentParser(description="Limit agent skill file size")
    parser.add_argument("--max-kb", type=int, default=8)
    parser.add_argument("--max-ref-kb", type=int, default=12)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failed = [
        too_big(
            f,
            args.max_kb,
            "an agent loads the whole SKILL.md every time the skill triggers.",
            "keep SKILL.md to when and how to use the skill, move detail into "
            "reference files it links to, and delete what is outdated or unneeded.",
        )
        if Path(f).name == "SKILL.md"
        else too_big(
            f,
            args.max_ref_kb,
            "an agent loads a whole reference file each time it follows a link to it.",
            "split it into references that each cover one task, link each from SKILL.md, "
            "and delete what is outdated or unneeded.",
        )
        for f in args.files
    ]
    return int(any(failed))
