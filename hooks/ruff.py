import os
import sys
from typing import NoReturn

# Keep these off even when a consuming repository selects ALL.
IGNORED_RULES = (
    "D",
    "DOC",
    "CPY001",
    "T201",
    "EM",
    "TRY003",
    "TID252",
    "INP001",
    "PT009",
    "PT027",
)


def main() -> NoReturn:
    arguments = sys.argv[1:]
    if arguments[0] == "check":
        # Extend per-file ignores so the consumer's ignore list stays intact.
        arguments.insert(
            1,
            "--extend-per-file-ignores="
            + ",".join(f"*:{rule}" for rule in IGNORED_RULES),
        )
    os.execvp("ruff", ["ruff", *arguments])
