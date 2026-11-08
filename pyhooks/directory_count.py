import argparse
import os
import subprocess
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Limit tracked files in each subdirectory"
    )
    parser.add_argument("--max-files", type=int, default=20)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    directories = {Path(filename).parent for filename in args.files} - {Path(".")}
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--stage", "-z"],
        capture_output=True,
        check=True,
    )
    counts: Counter[Path] = Counter()
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, _, filename = entry.partition(b"\t")
        directory = Path(os.fsdecode(filename)).parent
        if not metadata.startswith(b"160000 ") and directory in directories:
            counts[directory] += 1
    failed = False
    for directory, count in sorted(counts.items()):
        if count > args.max_files:
            print(
                f"{directory}: {count} tracked files exceeds the limit of {args.max_files}. Group related files into subdirectories."
            )
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
