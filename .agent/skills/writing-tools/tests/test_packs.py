"""Package correctness tests, not live-agent or prose-quality evaluations."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_packs", ROOT / "scripts/build_packs.py")
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackTests(unittest.TestCase):
    def fixture(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        target = Path(temp.name) / "writing-tools"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return target

    def test_all_55_canonical_rules(self):
        self.assertEqual(set(builder.load_rules(ROOT)), set(range(1, 56)))

    def test_exact_description(self):
        front = (ROOT / "SKILL.md").read_text().split("---", 2)[1]
        self.assertEqual(front.strip(), 'name: writing-tools\ndescription: "Writing Tools for prose writing.  Use when drafting prose, revising a draft."')

    def test_cumulative_counts_and_emphasis(self):
        packs = builder.load_packs(ROOT, builder.load_rules(ROOT))
        self.assertEqual([len(ids) for _, _, ids in packs], [12, 25, 55])
        self.assertTrue(packs[0][2] < packs[1][2] < packs[2][2])
        for _, _, ids in packs:
            self.assertIn(2, ids)

    def test_generated_blocks_are_exact(self):
        rules = builder.load_rules(ROOT)
        for filename, text in builder.build(ROOT, check=True).items():
            matches = list(builder.HEADING.finditer(text))
            for i, match in enumerate(matches):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                self.assertEqual(text[match.start():end].strip(), rules[int(match.group(1))])
            self.assertEqual(text, (ROOT / "packs" / filename).read_text())

    def test_core_output_excludes_unselected_rules(self):
        text = builder.expected_packs(ROOT)["01-core.md"]
        ids = {int(n) for n in re.findall(r"^## (\d+)\.", text, re.MULTILINE)}
        self.assertEqual(ids, set(json.loads((ROOT / "packs.json").read_text())["core"]["rules"]))
        self.assertNotIn(50, ids)
        self.assertNotIn(52, ids)

    def test_stale_generated_text_rejected_without_writing(self):
        root = self.fixture()
        path = root / "packs/01-core.md"
        path.write_text("stale\n")
        with self.assertRaisesRegex(ValueError, "Regenerate packs"):
            builder.build(root, check=True)
        self.assertEqual(path.read_text(), "stale\n")
        builder.build(root)
        builder.build(root, check=True)

    def test_missing_pass_rejected(self):
        root = self.fixture()
        path = root / "references/01-nuts-and-bolts.md"
        path.write_text(path.read_text().replace("**Pass:**", "**Check:**", 1))
        with self.assertRaisesRegex(ValueError, "Requirement and one Pass"):
            builder.build(root)

    def test_wrong_filename_prefix_rejected(self):
        root = self.fixture()
        (root / "references/01-nuts-and-bolts.md").rename(root / "references/02-nuts-and-bolts.md")
        with self.assertRaisesRegex(ValueError, "prefix"):
            builder.build(root)

    def test_duplicate_pack_id_rejected(self):
        root = self.fixture()
        path = root / "packs.json"
        config = json.loads(path.read_text())
        config["core"]["rules"].append(2)
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "Duplicate or unknown"):
            builder.build(root)

    def test_missing_cross_rule_dependency_rejected(self):
        root = self.fixture()
        path = root / "packs.json"
        config = json.loads(path.read_text())
        config["polish"]["rules"].remove(33)
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "missing dependencies"):
            builder.build(root)

    def test_inheritance_cycle_rejected(self):
        root = self.fixture()
        path = root / "packs.json"
        config = json.loads(path.read_text())
        config["core"]["extends"] = "polish"
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "inheritance"):
            builder.build(root)

    def test_extra_generated_file_rejected(self):
        root = self.fixture()
        (root / "packs/old.md").write_text("stale\n")
        with self.assertRaisesRegex(ValueError, "Stale pack"):
            builder.build(root)

    def test_cli_works_outside_skill_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_packs.py"), "--check"], cwd="/", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Checked 3 packs", result.stdout)

    def test_local_markdown_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts:
                continue
            text = re.sub(r"```.*?```", "", path.read_text(), flags=re.DOTALL)
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue((path.parent / target.split("#", 1)[0]).exists(), (path, target))


if __name__ == "__main__":
    unittest.main()
