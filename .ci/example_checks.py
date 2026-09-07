"""Copy the complete example into a consumer repo and exercise its settings."""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "example_conf"
FIXTURES = ROOT / ".ci" / "fixtures"
REPOSITORY = "https://github.com/ysawa0/prek"


def run(work: Path, *arguments: str, expected: int = 0, diagnostic: str = "") -> None:
    environment = {
        key: value for key, value in os.environ.items() if key != "GITHUB_ACTIONS"
    }
    result = subprocess.run(
        ["prek", *arguments],
        cwd=work,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode != expected or diagnostic not in output:
        raise AssertionError(output)


def verify_config() -> str:
    config = tomllib.loads((EXAMPLE / "prek.toml").read_text())
    bundle = next(repo for repo in config["repos"] if repo["repo"] == REPOSITORY)
    published = set(
        re.findall(
            r"^- id: (.+)$", (ROOT / ".pre-commit-hooks.yaml").read_text(), re.MULTILINE
        )
    )
    enabled = [hook["id"] for hook in bundle["hooks"]]
    if set(enabled) != published or len(enabled) != len(published):
        raise AssertionError("Example must enable every published hook exactly once")
    version = (ROOT / "RELEASE").read_text().splitlines()[0]
    if bundle["rev"] != version:
        raise AssertionError("Example revision must match RELEASE")
    return version


def seed(work: Path) -> None:
    sources = {
        "sample.py": "example/sample.py.txt",
        "sample.ts": "oxlint/clean.input.txt",
        "sample.go": "gofumpt/format.expected.txt",
        "sample.sh": "shfmt/format.expected.txt",
        "README.md": "unslop/clean.input.txt",
    }
    for target, source in sources.items():
        shutil.copyfile(FIXTURES / source, work / target)
    (work / "__init__.py").write_text(
        '# Copyright (c) 2026 Example Authors\n"""Example package."""\n'
    )
    (work / "go.mod").write_text("module hooktest\n\ngo 1.25\n")
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)


def check_rejections(work: Path) -> None:
    cases = [
        (
            "ruff-check",
            "sample.py",
            "example/annotations.py.txt",
            "Missing type annotation",
        ),
        ("oxlint", "sample.ts", "oxlint/bad.input.txt", "leaves input unparsed"),
        ("unslop", "README.md", "example/strict.md.txt", "density.parenthetical"),
        ("shellcheck", "sample.sh", "example/optional.sh.txt", "SC2230"),
    ]
    for hook, target, source, diagnostic in cases:
        path = work / target
        clean = path.read_bytes()
        shutil.copyfile(FIXTURES / source, path)
        run(work, "run", hook, "--files", target, expected=1, diagnostic=diagnostic)
        path.write_bytes(clean)
        print(
            f"PASS copied example: {hook} rejects its configured violation", flush=True
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--published", action="store_true", help="Use the example's public release pin"
    )
    args = parser.parse_args()
    version = verify_config()
    (ROOT / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="example_", dir=ROOT / "tmp") as directory:
        work = Path(directory)
        shutil.copytree(EXAMPLE, work, dirs_exist_ok=True)
        if not args.published:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
            path = work / "prek.toml"
            path.write_text(
                path.read_text()
                .replace(REPOSITORY, str(ROOT))
                .replace(f'rev = "{version}"', f'rev = "{revision}"')
            )
        subprocess.run(["git", "init", "-q", str(work)], check=True)
        seed(work)
        run(work, "validate-config", "prek.toml")
        run(work, "install", "--prepare-hooks")
        run(work, "run", "--all-files")
        check_rejections(work)
        run(work, "run", "--all-files")
        print("PASS copied example: all hooks pass on clean files", flush=True)


if __name__ == "__main__":
    main()
