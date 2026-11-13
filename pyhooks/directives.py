"""Inline suppression directives shared by bestprek hooks, modeled on ESLint.

- `bestprek-disable-line` skips its own line.
- `bestprek-disable-next-line` skips the following line.
- `bestprek-disable` skips lines until `bestprek-enable`, or to the end of the file.

Each directive takes optional comma-separated hook ids and applies to every hook
without them. Text after ` -- ` is a free-form reason. Directives work inside any
comment syntax, such as `<!-- bestprek-disable-line markdown-width -- long URL -->`.
"""

import re
from collections.abc import Iterable, Iterator

DIRECTIVE = re.compile(
    r"\bbestprek-(disable-next-line|disable-line|disable|enable)"
    r"((?:[ ,]+[a-z][a-z0-9-]*)*)"
)


def checked_lines(lines: Iterable[str], hook: str) -> Iterator[tuple[int, str]]:
    """Yield the numbered lines that `hook` should check."""
    disabled = False
    skip_next = False
    for number, line in enumerate(lines, start=1):
        skip, skip_next = skip_next, False
        for match in DIRECTIVE.finditer(line):
            hooks = re.split(r"[ ,]+", match[2].strip()) if match[2] else []
            if hooks and hook not in hooks:
                continue
            # A directive line never counts against the hooks it names.
            skip = True
            if match[1] == "disable":
                disabled = True
            elif match[1] == "enable":
                disabled = False
            elif match[1] == "disable-next-line":
                skip_next = True
        if not (skip or disabled):
            yield number, line
