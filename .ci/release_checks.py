"""Exercise release preparation against a disposable copy of its input files."""

import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    files = ["RELEASE", "scripts/release.py", "example_conf/prek.toml"]
    with tempfile.TemporaryDirectory(prefix="release-", dir=ROOT / "tmp") as directory:
        work = Path(directory)
        for filename in files:
            target = work / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / filename, target)
        example = work / "example_conf/prek.toml"
        original = example.read_text()
        previous = (work / "RELEASE").read_text().splitlines()[0]
        example.write_text(original.replace(f'rev = "{previous}"', 'rev = "1.23"'))
        notes = work / ".github" / "release-notes"
        notes.mkdir(parents=True)
        (notes / "99.99.md").write_text("Release preparation fixture.\n")
        inputs = {path: path.read_bytes() for path in work.rglob("*") if path.is_file()}
        result = subprocess.run(
            [sys.executable, str(work / "scripts/release.py"), "99.99"],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 or "prek.toml" not in result.stderr:
            raise AssertionError("Release preparation must reject a mismatched example")
        changed = [
            path.name
            for path, original in inputs.items()
            if path.read_bytes() != original
        ]
        if changed:
            raise AssertionError(f"Failed release preparation changed {changed}")
        example.write_text(original)
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
        config = tomllib.loads(example.read_text())
        bundle = next(repo for repo in config["repos"] if repo["repo"] != "builtin")
        if bundle["rev"] != "99.99":
            raise AssertionError("Release preparation must update the copyable example")
    print(
        "PASS release preparation: failed validation preserves inputs; "
        "example updated and upkeep note preserved"
    )


if __name__ == "__main__":
    main()
