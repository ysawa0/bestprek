"""Exercise installed hooks using the file-backed cases in .ci/fixtures."""

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import NotRequired, TypedDict

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / ".ci" / "fixtures"


class Case(TypedDict):
    name: str
    path: str
    input: str
    expected: NotRequired[str]
    diagnostics: NotRequired[list[str]]
    rules: NotRequired[list[str]]
    args: NotRequired[list[str]]
    setup: NotRequired[dict[str, str]]
    exit: NotRequired[int]


def run(work: Path, hook: str, path: str) -> subprocess.CompletedProcess[str]:
    # Keep fixture diagnostics stable instead of emitting GitHub annotations.
    environment = {
        key: value for key, value in os.environ.items() if key != "GITHUB_ACTIONS"
    }
    environment["NO_COLOR"] = "1"
    return subprocess.run(
        ["prek", "run", hook, "--files", path],
        cwd=work,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def write_config(work: Path, repo: str, revision: str, hook: str, case: Case) -> None:
    config = (
        f"[[repos]]\nrepo = {json.dumps(repo)}\nrev = {json.dumps(revision)}\n"
        f"\n[[repos.hooks]]\nid = {json.dumps(hook)}\n"
    )
    if "args" in case:
        config += f"args = {json.dumps(case['args'])}\n"
    (work / "prek.toml").write_text(config)


def assert_result(
    case: Case, hook: str, result: subprocess.CompletedProcess[str]
) -> None:
    output = result.stdout + result.stderr
    expected_exit = case.get("exit", int("expected" in case or "diagnostics" in case))
    if result.returncode != expected_exit:
        raise AssertionError(
            f"expected exit {expected_exit}, got {result.returncode}\n{output}"
        )
    for diagnostic in case.get("diagnostics", []):
        if diagnostic not in output:
            raise AssertionError(f"missing diagnostic {diagnostic!r}\n{output}")
    if hook == "oxlint":
        actual = re.findall(r"anti-slop\(([^)]+)\):", output)
        if sorted(actual) != sorted(case.get("rules", [])):
            raise AssertionError(
                f"unexpected custom-rule diagnostics: {actual}\n{output}"
            )


def check(work: Path, folder: Path, case: Case) -> None:
    hook = folder.name
    path = work / case["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    before = (folder / case["input"]).read_bytes()
    expected = (
        (folder / case["expected"]).read_bytes() if "expected" in case else before
    )
    path.write_bytes(before)
    subprocess.run(["git", "add", "--", case["path"]], cwd=work, check=True)
    result = run(work, hook, case["path"])
    assert_result(case, hook, result)
    if path.read_bytes() != expected:
        raise AssertionError(f"unexpected file contents: {path.read_bytes()!r}")
    if "expected" in case:
        second = run(work, hook, case["path"])
        if second.returncode or path.read_bytes() != expected:
            raise AssertionError(
                f"formatter is not idempotent\n{second.stdout}{second.stderr}"
            )
    print(f"PASS {hook}: {case['name']}", flush=True)


def run_case(work: Path, folder: Path, case: Case, repo: str, revision: str) -> None:
    write_config(work, repo, revision, folder.name, case)
    setup = case.get("setup", {})
    for filename, content in setup.items():
        path = work / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    try:
        check(work, folder, case)
    except AssertionError as exc:
        raise AssertionError(f"{folder.name}/{case['name']}: {exc}") from exc
    finally:
        for filename in [case["path"], *setup]:
            (work / filename).unlink()


def verify_coverage(manifests: list[Path]) -> None:
    hooks = set(
        re.findall(
            r"^- id: (.+)$", (ROOT / ".pre-commit-hooks.yaml").read_text(), re.MULTILINE
        )
    )
    if hooks != {manifest.parent.name for manifest in manifests}:
        raise SystemExit("Every published hook must have a fixture group")
    policy = json.loads((ROOT / ".oxlintrc.json").read_text())
    enabled = {
        name.removeprefix("anti-slop/")
        for name, level in policy["rules"].items()
        if name.startswith("anti-slop/") and level != "off"
    }
    cases: list[Case] = json.loads((FIXTURES / "oxlint" / "cases.json").read_text())
    covered = {rule for case in cases for rule in case.get("rules", [])}
    if missing := enabled - covered:
        raise SystemExit(
            "Missing Oxlint rejection fixtures: " + ", ".join(sorted(missing))
        )


def run_group(work: Path, manifest: Path, repo: str, revision: str) -> int:
    cases: list[Case] = json.loads(manifest.read_text())
    for case in cases:
        run_case(work, manifest.parent, case, repo, revision)
    return len(cases)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--rev")
    parser.add_argument("--hook", help="Run one hook's fixture group")
    args = parser.parse_args()
    revision = (
        args.rev
        or subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    )
    manifests = sorted(FIXTURES.glob("*/cases.json"))
    verify_coverage(manifests)
    if args.hook:
        manifests = [FIXTURES / args.hook / "cases.json"]
    count = 0
    (ROOT / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hooks-", dir=ROOT / "tmp") as directory:
        work = Path(directory)
        subprocess.run(["git", "init", "-q", str(work)], check=True)
        for manifest in manifests:
            count += run_group(work, manifest, args.repo, revision)
    print(f"Passed {count} fixture cases across {len(manifests)} hooks.")


if __name__ == "__main__":
    main()
