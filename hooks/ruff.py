import os
import sys
from typing import NoReturn


def main() -> NoReturn:
    os.execvp("ruff", ["ruff", *sys.argv[1:]])
