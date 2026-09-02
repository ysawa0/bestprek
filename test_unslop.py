import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hooks import unslop

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples" / "unslop"


class UnslopTest(unittest.TestCase):
    def lint(self, text, preset="recommended", config=None):
        return unslop.lint_document(
            unslop.Document("test.md", text), preset, config or {}
        )

    def test_rule_count(self):
        self.assertEqual(len(unslop.RULES), 25)

    def test_bad_coffee_exercises_structural_rules(self):
        text = (EXAMPLES / "coffee-before.md").read_text(encoding="utf-8")
        diagnostics = self.lint(text)
        rules = {item.rule_id for item in diagnostics}
        self.assertGreaterEqual(len(diagnostics), 25)
        self.assertTrue(
            {
                "rhetoric.negative-parallelism",
                "rhetoric.no-chain",
                "rhetoric.question-answer",
                "rhetoric.question-density",
                "repetition.sentence-opener",
                "repetition.loaded-word",
                "rhythm.short-sentence-run",
                "density.em-dash",
                "verbosity.filler",
            }.issubset(rules)
        )

    def test_revised_coffee_is_clean(self):
        text = (EXAMPLES / "coffee-after.md").read_text(encoding="utf-8")
        self.assertEqual(self.lint(text), [])

    def test_markdown_projection_ignores_non_prose(self):
        text = """---
title: In today's ever-evolving landscape
---

> In order to unlock the power of coffee.

`In order to unlock the power of coffee.`

[clean link](https://example.com/?utm_source=chatgpt)

```text
In order to unlock the power of coffee.
turn1search2
```

<!-- In order to unlock the power of coffee. -->

A plain, direct sentence remains.
"""
        self.assertEqual(self.lint(text), [])

    def test_markdown_links_do_not_count_as_parenthetical_asides(self):
        links = " ".join(
            f"[Source {index}](https://example.com/{index})" for index in range(6)
        )
        rules = {item.rule_id for item in self.lint(links, preset="strict")}
        self.assertNotIn("density.parenthetical", rules)

        asides = " ".join(f"(aside {index})" for index in range(6))
        rules = {item.rule_id for item in self.lint(asides, preset="strict")}
        self.assertIn("density.parenthetical", rules)

    def test_mdx_tags_are_masked_but_text_is_linted(self):
        diagnostics = self.lint(
            "<Callout>In order to make coffee, weigh it.</Callout>\n"
        )
        self.assertEqual([item.rule_id for item in diagnostics], ["verbosity.filler"])

    def test_chatbot_residue_is_error(self):
        diagnostics = self.lint(
            "The draft still contains turn4search12 in the paragraph.\n"
        )
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].severity, "error")

    def test_single_contrast_is_allowed_but_repetition_warns(self):
        one = "This is not a speed problem. It is a coordination problem.\n"
        self.assertNotIn(
            "rhetoric.negative-parallelism", {d.rule_id for d in self.lint(one)}
        )
        two = one + "The failure is not about throughput, but predictability.\n"
        self.assertIn(
            "rhetoric.negative-parallelism", {d.rule_id for d in self.lint(two)}
        )

    def test_single_em_dash_is_allowed(self):
        self.assertEqual(
            self.lint("A grinder matters—but it need not be expensive.\n"), []
        )

    def test_headings_reset_repetition(self):
        text = """# API

## Open
The event fires when the socket opens. Ready. Connected.

## Close
The event fires when the socket closes. Done. Disconnected.

## Error
The event fires when the socket fails. Failed. Closed.
"""
        rules = {item.rule_id for item in self.lint(text)}
        self.assertNotIn("repetition.sentence-opener", rules)
        self.assertNotIn("rhythm.short-sentence-run", rules)

    def test_disable_next_line(self):
        text = """<!-- unslop-disable-next-line verbosity.filler -->
In order to weigh the coffee, use a scale.

In order to heat the water, use a kettle.
"""
        fillers = [
            item for item in self.lint(text) if item.rule_id == "verbosity.filler"
        ]
        self.assertEqual(len(fillers), 1)
        self.assertEqual(fillers[0].line, 4)

    def test_category_suppression(self):
        text = """<!-- unslop-disable verbosity.* -->
In order to brew, use water.
<!-- unslop-enable verbosity.* -->
In order to brew, use water.
"""
        fillers = [
            item for item in self.lint(text) if item.rule_id == "verbosity.filler"
        ]
        self.assertEqual(len(fillers), 1)

    def test_inline_ignore(self):
        text = "In order to brew, weigh the coffee. <!-- unslop-ignore verbosity.filler -->\n"
        self.assertEqual(self.lint(text), [])

    def test_strict_promotes_subjective_rules(self):
        diagnostics = self.lint(
            "It is important to note that water matters.\n", preset="strict"
        )
        self.assertEqual(diagnostics[0].severity, "warning")

    def test_unknown_rule_is_config_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"rules": {"made.up": "off"}}), encoding="utf-8")
            with self.assertRaises(unslop.ConfigError):
                unslop.load_config(str(path))

    def test_unknown_option_is_config_error(self):
        with self.assertRaises(unslop.ConfigError):
            self.lint(
                "Direct prose.\n", config={"rules": {"density.em-dash": {"maximum": 3}}}
            )

    def test_json_cli_and_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("The transition is seamless.\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "hooks.unslop", "--format", "json", str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                json.loads(result.stdout)[0]["rule"], "phrase.marketing-language"
            )


if __name__ == "__main__":
    unittest.main()
