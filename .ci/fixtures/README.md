# Hook fixtures

Each hook has a directory with a `cases.json` manifest, input files, and expected output files. The runner copies inputs into a temporary Git repository using the real file extension, then runs the installed hook through Prek.

Run all cases or one group:

```sh
uv run --no-sync python3 .ci/hook_checks.py
uv run --no-sync python3 .ci/hook_checks.py --hook oxlint
uv run --no-sync python3 .ci/unslop_checks.py
```

Fixture fields:

| Field | Purpose |
| --- | --- |
| `name` | Label printed in test results |
| `path` | Filename presented to the hook, including its real extension |
| `input` | Input file relative to this manifest |
| `expected` | Exact file contents after formatting; also requires a clean second run |
| `diagnostics` | Required diagnostic text for a rejected input |
| `rules` | Exact list of custom Oxlint rule IDs, including duplicates |
| `setup` | Consumer configuration or module files needed by this case |
| `args` | Consumer hook arguments |
| `exit` | Expected Prek exit status when the default does not apply |

Without `expected`, file contents must remain byte-for-byte unchanged. The default exit status is 1 for formatter changes or required diagnostics, and 0 for accepted input. The runner removes each case's files and configuration before the next case.

Payloads use `.txt` to keep repository hooks from formatting deliberate errors. Coffee calibration documents remain Markdown under `unslop/`; the noisy article is excluded from routine prose linting and exercised by the tests.

The suite checks all 12 published hooks and has accepted and rejected examples for all 15 vendored Oxlint rules. Coverage checks require a fixture group for each published hook and a rejection fixture for each enabled custom Oxlint rule.

The Unslop CLI check verifies transition diagnostics and source locations against the saved JSON fixture. It repeats the check after a 20,000-line code block, with a 10-second timeout to catch repeated whitespace scans.
