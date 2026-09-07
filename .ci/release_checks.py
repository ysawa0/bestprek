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
        "Cargo.toml",
        "Cargo.lock",
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
        manifest_path = work / "Cargo.toml"
        original_manifest = manifest_path.read_text()
        previous = (work / "RELEASE").read_text().splitlines()[0]
        manifest_path.write_text(
            original_manifest.replace(f'version = "{previous}.0"', 'version = "1.23.0"')
        )
        inputs = {path: path.read_bytes() for path in work.rglob("*") if path.is_file()}
        result = subprocess.run(
            [sys.executable, str(work / "scripts/release.py"), "99.99"],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 or "in Cargo.toml" not in result.stderr:
            raise AssertionError("Release preparation must reject a mismatched version")
        changed = [
            path.name
            for path, original in inputs.items()
            if path.read_bytes() != original
        ]
        if changed:
            raise AssertionError(f"Failed release preparation changed {changed}")
        manifest_path.write_text(original_manifest)
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
        manifest = tomllib.loads((work / "Cargo.toml").read_text())
        packages = tomllib.loads((work / "Cargo.lock").read_text())["package"]
        binary = next(package for package in packages if package["name"] == "unslop")
        if (
            manifest["package"]["version"] != "99.99.0"
            or binary["version"] != "99.99.0"
        ):
            raise AssertionError("Release preparation must update the CLI version")
    print(
        "PASS release preparation: failed validation preserves inputs; "
        "versions updated and upkeep note preserved"
    )


if __name__ == "__main__":
    main()
