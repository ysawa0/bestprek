# bestprek

Pre-commit hooks

## Hooks

- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON
- `oxlint`: lint JavaScript, JSX, TypeScript, and TSX with the bundled anti-slop policy
- `ruff-check`: lint Python and Jupyter files
- `ruff-format`: format Python and Jupyter files
- `unbold`: strip Markdown bold markers in place while preserving code and escaped punctuation
- `unslop`: lint Markdown prose for canned, repetitive, bloated, or mechanically over-polished writing
- `gofumpt`: format Go
- `goimports`: format Go and fix imports
- `gopls-check`: run `gopls check` on Go files
- `go-vet`: run `go vet ./...` in the current Go module
- `gocyclo`: reject Go functions with cyclomatic complexity above 15
- `shellcheck`: lint shell scripts
- `shfmt`: format shell scripts

## Quickstart

Install Prek:

```sh
brew install prek
```

Add `prek.toml` to the consuming repository:

```toml
[[repos]]
repo = "https://github.com/ysawa0/bestprek"
rev = "1.27"

[[repos.hooks]]
id = "oxfmt"
exclude = "(^|/)(dist|build|coverage|vendor|\\.cache|cache|generated)/"

[[repos.hooks]]
id = "oxlint"

[[repos.hooks]]
id = "ruff-format"

[[repos.hooks]]
id = "ruff-check"

[[repos.hooks]]
id = "unbold"

[[repos.hooks]]
id = "unslop"

[[repos.hooks]]
id = "goimports"

[[repos.hooks]]
id = "gofumpt"

[[repos.hooks]]
id = "gopls-check"

[[repos.hooks]]
id = "go-vet"

[[repos.hooks]]
id = "gocyclo"

[[repos.hooks]]
id = "shfmt"

[[repos.hooks]]
id = "shellcheck"
```

Keep only the hooks relevant to the repository, then install and run them:

```sh
prek install -f
prek run --all-files
```

Run one hook with `prek run <hook-id> --all-files`.

## Full copyable setup

`example_conf/` is the complete configuration for consuming repositories. Copy its contents, including hidden files, into the destination repository root:

```sh
cp -R /path/to/prek/example_conf/. /path/to/your-repo/
cd /path/to/your-repo
prek install --prepare-hooks
prek run --all-files
```

The directory contains:

- `prek.toml`: all 13 bundled hooks plus whitespace and large-file checks;
- `ruff.toml`: Ruff's `ALL` rule set, with boilerplate requirements and formatter conflicts excluded;
- `.unslop.json`: recommended prose rules, failing on warnings and errors;
- `.oxfmtrc.jsonc`: JavaScript, TypeScript, and JSON formatting settings;
- `.shellcheckrc`: optional ShellCheck checks except SC2250 (variable-brace style);
- `.github/workflows/lint.yml`: the same hooks on pushes and pull requests.

The Oxlint hook loads its bundled policy automatically, including all 15 custom rules. The hook's existing rule exclusions remain in force, as do ShellCheck's SC1091 and SC2250 exclusions. Ruff retains the hook's explicit preview-rule policy and nesting limit. See [Ruff's formatter compatibility guidance](https://docs.astral.sh/ruff/formatter/#conflicting-lint-rules) for the formatting exclusions.

Install Prek before running these commands. Because this hook repository is public, local and CI runs do not need GitHub credentials or repository secrets to fetch it.

Merge files where the destination already has configuration you want to retain. Hooks skip languages without matching files; repositories with Go files need a root `go.mod` or `go.work` appropriate for `go vet ./...`.

Keep `example_conf/` current whenever the hooks or their configuration change. The release command updates its revision, and CI tests the copied setup.

## Unslop

The `unslop` hook is a deterministic prose linter written in Rust. It evaluates the text in front of it rather than guessing whether a person or model wrote it. Prek builds the native executable with Cargo during hook installation and runs independent file batches in parallel.

The catalogue contains 25 rules across the recommended and strict presets for:

- removable filler and redundant phrases;
- vague attribution and promotional wording;
- repeated contrast scaffolding and staged questions;
- repeated sentence, paragraph, and transition openings;
- loaded-word repetition;
- short-sentence runs and optional rhythm checks;
- em-dash, bold, parenthetical, and heading density;
- pasted chatbot citation or UI residue.

The recommended preset disables em-dash density, three-item-list density, question density, question-answer turns, short-sentence runs, parenthetical density, heading density, and uniform sentence lengths. These checks often flag legitimate reference documents and interview question banks. Strict enables them as informational review suggestions, not required edits. Do not mechanically replace punctuation, remove useful headings, or paraphrase source quotations to satisfy them.

The linter preserves source positions while ignoring code fences, inline code, LaTeX math (`\(...\)`, `\[...\]`, `$...$`, and `$$...$$`), URLs, front matter, comments, blockquotes, tables, link destinations, and MDX tags. Equation references such as `(CW5)` do not count as parenthetical asides. Repetition rules reset at headings so API reference sections can use a consistent template without being mistaken for monotonous prose. By default, warnings and errors fail the hook; informational findings do not. `--fail-level info` explicitly makes advisory findings blocking. Use `--fail-level none` for an editorial review that never fails on findings.

Use `.unslop.json` for repository-specific tuning. An example lives at `.unslop.example.json`.

```json
{
  "preset": "recommended",
  "fail_level": "warning",
  "rules": {
    "density.em-dash": {
      "severity": "info",
      "max": 5,
      "window_words": 500
    },
    "phrase.marketing-language": "off"
  }
}
```

Local suppressions are available when repetition or phrasing is deliberate:

```markdown
<!-- unslop-disable-next-line rhetoric.negative-parallelism -->
The quoted line stays exactly as written.

<!-- unslop-disable repetition.* -->
This section deliberately uses anaphora.
<!-- unslop-enable repetition.* -->
```

Direct CLI usage after the Python hook environment is installed:

```sh
unslop README.md docs/*.md
unslop --preset strict README.md
unslop --format json README.md
unslop --list-rules
```

The calibration under `.ci/fixtures/unslop/` includes a deliberately bloated coffee article and a revised version. Tests require the noisy article to exercise structural rules and the revised article to produce no findings.

## Tool versions and configuration

The release tag pins each hook implementation and its tool version. Prek creates isolated Python, Node, and Go environments and prepares the required tools on first use.

The shared Ruff policy disables docstring rules (`D`, `DOC`), copyright headers (`CPY001`), print bans (`T201`), exception-message formatting (`EM`, `TRY003`), forced absolute imports (`TID252`), required `__init__.py` files (`INP001`), and unittest-to-pytest conversion (`PT009`, `PT027`). These exclusions apply even when a consumer selects `ALL`; the hook preserves the consumer’s other ignored rules. Type annotations, correctness, security, and complexity checks remain available. The copied `ruff.toml` enables them and includes the same exclusions for direct Ruff runs.

Project-local files such as `.oxfmtrc.jsonc` and `ruff.toml` control their respective tools. `ruff-check` always enables `SIM102` and preview rule `PLR1702`, allowing at most two nested blocks. The `oxlint` hook always uses this repository's fixed `.oxlintrc.json`, which enables the vendored [anti-slop](https://github.com/dmmulroy/anti-slop) code rules alongside the built-in policy; consuming repositories' Oxlint configuration and command-line options are ignored. The Markdown `unslop` hook is separate from that JavaScript policy. `go-vet` runs once from the repository root, so enable it only where that root is the intended Go module or workspace.

## Development

CI checks, test suites, and fixtures live in `.ci/`. Run the same checks as GitHub Actions with:

```sh
.ci/check.sh
```

The GitHub workflow in `.github/workflows/ci.yml` prepares the tools and calls this script. The repository's `prek.toml` checks the current worktree with local hooks. To run only the end-to-end hook suite:

```sh
uv run --no-sync python3 .ci/hook_checks.py
```

The Go executables and Rust Unslop implementation live under `tools/`. Build Unslop with `cargo +stable build --release --locked` before running the repository's local hooks. File-backed test inputs and expected output live under `.ci/fixtures/<hook>/`; each group has a `cases.json` manifest. Inputs use `.txt` so repository formatters do not rewrite deliberately invalid examples.

The end-to-end suite installs hooks from the committed HEAD in a temporary consuming repository. It checks lint failures, formatter output, ignored files, code preservation, and clean second runs. Commit implementation changes before running it.

## Release

1. Write `.github/release-notes/<version>.md`.
2. Run `make release VERSION=<version>` to update `RELEASE`, the README example, `example_conf/prek.toml`, and the Unslop CLI version.
3. Commit and push the changes to `main`.
4. CI builds and lints Rust, validates the manifest, and runs local hooks, CLI reference fixtures, published-hook smoke checks, and end-to-end hook checks. After they pass, CI creates the GitHub release and matching tag.

The local release command only prepares metadata. CI is the sole publisher.
