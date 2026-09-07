"""Run every published hook on this checkout using the fixture suite's cache."""

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    hooks = re.findall(
        r"^- id: (.+)$", (ROOT / ".pre-commit-hooks.yaml").read_text(), re.MULTILINE
    )
    with tempfile.TemporaryDirectory(prefix="repo-", dir=ROOT / "tmp") as directory:
        config = Path(directory) / "prek.toml"
        config.write_text(
            f"[[repos]]\nrepo = {json.dumps(str(ROOT))}\nrev = {json.dumps(revision)}\n"
            + "hooks = [\n"
            + "".join(f"  {{ id = {json.dumps(hook)} }},\n" for hook in hooks)
            + "]\n"
        )
        subprocess.run(
            ["prek", "run", "--config", str(config), "--all-files"],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
