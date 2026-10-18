"""Reject staged files estimated above a token limit, at four bytes per token."""

import argparse
import re
import subprocess
import sys

BYTES_PER_TOKEN = 4
# Files that tools write, which agents should regenerate rather than split.
GENERATED_PATHS = re.compile(
    r"(^|/)("
    r"[^/]*\.lock|package-lock\.json|npm-shrinkwrap\.json|pnpm-lock\.yaml"
    r"|go\.sum|go\.work\.sum|bun\.lockb?|deno\.lock"
    r"|(vendor|node_modules|third_party|dist|build|generated|__generated__"
    r"|__snapshots__)/.*"
    r"|[^/]*\.(min\.(js|css)|map|snap|svg|ipynb|csv|tsv)"
    r"|[^/]*[._-](generated|gen)\.[^/]+|[^/]*\.pb(\.gw)?\.go|[^/]*_pb2(_grpc)?\.pyi?"
    r")$"
)
GENERATED_MARKER = re.compile(rb"@generated|DO NOT EDIT|auto-?generated", re.IGNORECASE)
HEADER_BYTES = 1024

SPLIT_INSTRUCTIONS = """\
Split each file listed above into smaller files, each at most {limit:,} tokens \
({max_bytes:,} bytes):

1. Read the whole file and list its distinct responsibilities, such as types, \
helpers, separate features, entry points, and test subjects.
2. Move each responsibility into its own new file beside the original, named for what \
it does. Move code verbatim; do not rewrite logic while moving it.
3. Keep the original path as the entry point. Import from the new files, or \
update every caller's imports, so behavior and public names stay the same.
4. Split tests by the behavior they cover, and Markdown by top-level heading, \
linking the new pages from the original.
5. Delete dead code first, but do not reach the limit by removing needed \
content, minifying, shortening names, or joining lines.
6. Stage the new and changed files, then run the tests and commit again.

If a tool generates this file and no one edits it by hand, mark it instead: \
add "<path> linguist-generated" to .gitattributes."""


def staged_sizes() -> dict[str, int]:
    names = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")[:-1]
    if not names:
        return {}
    # Measure the index blob, which is exactly what the commit will contain.
    output = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectsize)"],
        input=b"".join(b":" + name + b"\n" for name in names),
        capture_output=True,
        check=True,
    ).stdout.split()
    return {name.decode(): int(size) for name, size in zip(names, output, strict=True)}


def marked_generated(paths: list[str]) -> set[str]:
    if not paths:
        return set()
    fields = subprocess.run(
        ["git", "check-attr", "-z", "linguist-generated", "linguist-vendored", "--"]
        + paths,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")[:-1]
    return {
        fields[index].decode()
        for index in range(0, len(fields), 3)
        if fields[index + 2] in {b"set", b"true"}
    }


def has_generated_header(path: str) -> bool:
    header = subprocess.run(
        ["git", "cat-file", "blob", f":{path}"], capture_output=True, check=True
    ).stdout[:HEADER_BYTES]
    return GENERATED_MARKER.search(header) is not None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    max_bytes = args.max_tokens * BYTES_PER_TOKEN
    sizes = staged_sizes()
    oversized = [
        path
        for path in args.files
        if sizes.get(path, 0) > max_bytes and not GENERATED_PATHS.search(path)
    ]
    exempt = marked_generated(oversized)
    failures = [
        path
        for path in oversized
        if path not in exempt and not has_generated_header(path)
    ]
    if not failures:
        return
    for path in failures:
        size = sizes[path]
        print(
            f"{path}: ~{size // BYTES_PER_TOKEN:,} tokens ({size:,} bytes / "
            f"{BYTES_PER_TOKEN}), limit {args.max_tokens:,}"
        )
    print()
    print(SPLIT_INSTRUCTIONS.format(limit=args.max_tokens, max_bytes=max_bytes))
    sys.exit(1)
