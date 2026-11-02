import sys
from pathlib import Path


def main() -> int:
    failed = False
    for filename in sys.argv[1:]:
        with Path(filename).open("rb") as file:
            lines = sum(1 for _ in file)
        if lines > 1000:
            print(
                f"{filename}: {lines} lines exceeds the 1,000-line limit. "
                'Move content into an "archive" subdirectory or delete content '
                "that is no longer needed."
            )
            failed = True
    return int(failed)
