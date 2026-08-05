import os
import sys
from typing import NoReturn


def main() -> NoReturn:
    os.execvp("shellcheck", ["shellcheck", *sys.argv[1:]])
