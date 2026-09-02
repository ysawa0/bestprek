# Prose-linter calibration

`coffee-before.md` is intentionally padded with canned phrases, repeated rhetorical shapes, promotional wording, and mechanical rhythm. `coffee-after.md` answers the same practical questions directly.

The calibration exists for two reasons: a release should prove that the linter catches broad structural slop, and the revised version should remain clean. Tests enforce both properties so rule changes cannot quietly turn the tool into a word blacklist with delusions of grandeur.

Run the comparison with:

```sh
unslop --format json --fail-level none examples/unslop/coffee-before.md
unslop --format json --fail-level none examples/unslop/coffee-after.md
```

The test suite also checks Markdown masking, heading-scoped repetition, local suppressions, configuration validation, density behavior, and CLI exit codes.
