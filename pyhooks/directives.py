"""Inline suppression directives shared by bestprek hooks, modeled on ESLint.

- `bestprek-disable-line` suppresses its own line.
- `bestprek-disable` suppresses lines until `bestprek-enable` or the end of the file.

A directive must open an HTML comment (`<!--`). It takes optional
comma-separated hook ids and applies to every hook without them. Free text must
follow ` -- `. Lines holding a directive are suppressed for the hooks it names.
"""

import re
from collections.abc import Sequence

DIRECTIVE = re.compile(
    r"<!--\s*bestprek-(disable-line|disable|enable)\b"
    r"((?:[ ,]+[a-z0-9]+(?:-[a-z0-9]+)*)*)\s*(?=--|$)"
)


def suppressed(lines: Sequence[str], hook: str) -> set[int]:
    """Return the 1-based line numbers whose diagnostics `hook` should drop."""
    result: set[int] = set()
    disabled = False
    for number, line in enumerate(lines, start=1):
        if disabled:
            result.add(number)
        for match in DIRECTIVE.finditer(line):
            hooks = re.split(r"[ ,]+", match[2].strip()) if match[2] else []
            if hooks and hook not in hooks:
                continue
            result.add(number)
            if match[1] == "disable":
                disabled = True
            elif match[1] == "enable":
                disabled = False
    return result
