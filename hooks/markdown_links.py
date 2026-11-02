import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import (  # ty: ignore[unresolved-import]  # Installed in prek's hook environment.
    MarkdownIt,
)


def check_file(source: Path, parser: MarkdownIt) -> bool:
    failed = False
    for block in parser.parse(source.read_text(encoding="utf-8")):
        for token in block.children or []:
            attribute = {"link_open": "href", "image": "src"}.get(token.type)
            if attribute is None or not isinstance(
                destination := token.attrGet(attribute), str
            ):
                continue
            url = urlsplit(destination)
            if url.scheme or url.netloc or not url.path:
                continue
            path = unquote(url.path)
            target = (
                Path.cwd() / path.lstrip("/")
                if path.startswith("/")
                else source.parent / path
            )
            if not target.exists():
                print(f"{source}: local link target not found: {destination}")
                failed = True
    return failed


def main() -> int:
    parser = MarkdownIt("commonmark")
    results = [check_file(Path(filename), parser) for filename in sys.argv[1:]]
    return int(any(results))
