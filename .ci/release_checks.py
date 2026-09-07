"""Exercise release preparation against a disposable copy of its input files."""

import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    files = [
        "RELEASE",
        "README.md",
        "scripts/release.py",
        "hooks/unslop.py",
        "example_conf/prek.toml",
    ]
    with tempfile.TemporaryDirectory(prefix="release-", dir=ROOT / "tmp") as directory:
        work = Path(directory)
        for filename in files:
            target = work / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / filename, target)
        notes = work / ".github" / "release-notes"
        notes.mkdir(parents=True)
        (notes / "99.99.md").write_text("Release preparation fixture.\n")
        subprocess.run(
            [sys.executable, str(work / "scripts/release.py"), "99.99"],
            cwd=work,
            check=True,
        )
        lines = (work / "RELEASE").read_text().splitlines()
        if (
            lines[0] != "99.99"
            or lines[1:] != (ROOT / "RELEASE").read_text().splitlines()[1:]
        ):
            raise AssertionError(
                "Release preparation must preserve the upkeep instructions"
            )
        config = tomllib.loads((work / "example_conf/prek.toml").read_text())
        bundle = next(repo for repo in config["repos"] if repo["repo"] != "builtin")
        if bundle["rev"] != "99.99":
            raise AssertionError("Release preparation must update the copyable example")
        if 'rev = "99.99"' not in (work / "README.md").read_text():
            raise AssertionError("Release preparation must update the README")
        if 'VERSION = "99.99"' not in (work / "hooks/unslop.py").read_text():
            raise AssertionError("Release preparation must update the CLI version")
    print("PASS release preparation: versions updated and upkeep note preserved")


if __name__ == "__main__":
    main()
