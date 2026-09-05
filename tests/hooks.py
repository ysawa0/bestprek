"""Exercise installed hooks in a disposable consuming repository."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def check(
    work: Path,
    hook: str,
    filename: str,
    before: str,
    *,
    after: str | None = None,
    diagnostic: str | None = None,
) -> None:
    path = work / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(before)
    subprocess.run(["git", "add", filename], cwd=work, check=True)
    result = run("prek", "run", hook, "--files", filename, cwd=work)
    output = result.stdout + result.stderr
    expected = 1 if after is not None or diagnostic is not None else 0
    if result.returncode != expected:
        raise AssertionError(
            f"{hook}: expected exit {expected}, got {result.returncode}\n{output}"
        )
    if diagnostic is not None and diagnostic not in output:
        raise AssertionError(f"{hook}: missing {diagnostic}\n{output}")
    if after is not None:
        if path.read_text() != after:
            raise AssertionError(f"{hook}: unexpected rewrite {path.read_text()!r}")
        second = run("prek", "run", hook, "--files", filename, cwd=work)
        if second.returncode:
            raise AssertionError(
                f"{hook}: second run failed\n{second.stdout}{second.stderr}"
            )
    print(f"PASS {hook}: {filename}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--rev")
    args = parser.parse_args()
    revision = (
        args.rev
        or subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    )
    with tempfile.TemporaryDirectory(prefix="hooks-", dir=ROOT / "tmp") as directory:
        work = Path(directory)
        subprocess.run(["git", "init", "-q", str(work)], check=True)
        hooks = [
            "unbold",
            "unslop",
            "oxfmt",
            "oxlint",
            "ruff-check",
            "ruff-format",
            "shellcheck",
            "shfmt",
        ]
        config = (
            f"[[repos]]\nrepo = {json.dumps(args.repo)}\nrev = {json.dumps(revision)}\n"
        )
        config += "".join(f'\n[[repos.hooks]]\nid = "{hook}"\n' for hook in hooks)
        (work / "prek.toml").write_text(config)

        code = (
            "`__init__` and `a ** b` and `` `**literal**` ``\n\n"
            "```python\ndef __init__():\n    return 2 ** 3\n```\n\n"
            "~~~~text\n**literal** __literal__\n~~~~\n\n"
            "    __indented__ **code**\n\n"
            "> ```python\n> __init__\n> ```\n\n"
            "`multiline\n__code__`\n\n"
            "\\*\\*escaped\\*\\*\n"
        )
        check(
            work,
            "unbold",
            "prose.md",
            "**bold** and __strong__\n\n" + code,
            after="bold and strong\n\n" + code,
        )
        check(
            work,
            "unbold",
            "unmatched.md",
            "A ` marker and **bold**.\n",
            after="A ` marker and bold.\n",
        )
        check(
            work,
            "unslop",
            "draft.md",
            "The transition is seamless.\n",
            diagnostic="phrase.marketing-language",
        )
        check(work, "unslop", "clean.md", "Weigh the beans before brewing.\n")
        check(
            work,
            "oxfmt",
            "format.ts",
            "export const answer=42\n",
            after="export const answer = 42;\n",
        )
        check(
            work,
            "oxlint",
            "bad.ts",
            "export function echo(value: unknown): string { return String(value); }\n",
            diagnostic="leaves input unparsed",
        )
        check(work, "oxlint", "clean.ts", "export const answer = 42;\n")
        check(
            work,
            "oxlint",
            "dist/ignored.ts",
            "export function echo(value: unknown): string { return String(value); }\n",
        )
        check(
            work,
            "ruff-check",
            "bad.py",
            "print(undefined_name)\n",
            diagnostic="Undefined name",
        )
        check(work, "ruff-format", "format.py", "answer=42\n", after="answer = 42\n")
        check(
            work,
            "shellcheck",
            "bad.sh",
            "#!/bin/sh\nprintf '%s\\n' $value\n",
            diagnostic="SC2086",
        )
        check(
            work,
            "shfmt",
            "format.sh",
            "#!/bin/sh\nif true;then\necho ok\nfi\n",
            after="#!/bin/sh\nif true; then\n\techo ok\nfi\n",
        )


if __name__ == "__main__":
    main()
