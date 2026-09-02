# Prek Hooks

A small, version-pinned hook bundle for ysawa0 repositories, designed for Prek.

## Hooks

- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON
- `oxlint`: lint JavaScript, JSX, TypeScript, and TSX with the bundled anti-slop policy
- `ruff-check`: lint Python and Jupyter files
- `ruff-format`: format Python and Jupyter files
- `unbold`: strip Markdown bold markers in place
- `anti-slop`: lint Markdown prose for canned, repetitive, bloated, or mechanically over-polished writing
- `gofumpt`: format Go
- `goimports`: format Go and fix imports
- `gopls-check`: run `gopls check` on Go files
- `go-vet`: run `go vet ./...` in the current Go module
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
repo = "https://github.com/ysawa0/prek"
rev = "1.15"

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
id = "anti-slop"

[[repos.hooks]]
id = "goimports"

[[repos.hooks]]
id = "gofumpt"

[[repos.hooks]]
id = "gopls-check"

[[repos.hooks]]
id = "go-vet"

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

## Markdown anti-slop

The `anti-slop` hook is a deterministic prose linter. It evaluates the text in front of it rather than guessing whether a person or model wrote it.

The recommended preset contains 25 explainable rules for:

- removable filler and redundant phrases;
- vague attribution and promotional wording;
- repeated contrast scaffolding and staged questions;
- repeated sentence, paragraph, and transition openings;
- loaded-word repetition;
- short-sentence runs and optional rhythm checks;
- em-dash, bold, parenthetical, and heading density;
- pasted chatbot citation or UI residue.

Most subjective devices are density-based. One em dash or one `not X, but Y` contrast is normal; a cluster of the same move is what gets flagged.

The linter preserves source positions while ignoring code fences, inline code, URLs, front matter, comments, blockquotes, tables, link destinations, and MDX tags. Repetition rules reset at headings so API reference sections can use a consistent template without being mistaken for monotonous prose.

Use `.anti-slop.json` for repository-specific tuning. An example lives at `.anti-slop.example.json`.

```json
{
  "preset": "recommended",
  "fail_level": "warning",
  "rules": {
    "density.em-dash": {
      "severity": "warning",
      "max": 5,
      "window_words": 500
    },
    "phrase.marketing-language": "off"
  }
}
```

Local suppressions are available when repetition or phrasing is deliberate:

```markdown
<!-- anti-slop-disable-next-line rhetoric.negative-parallelism -->
The quoted line stays exactly as written.

<!-- anti-slop-disable repetition.* -->
This section deliberately uses anaphora.
<!-- anti-slop-enable repetition.* -->
```

Direct CLI usage after the Python hook environment is installed:

```sh
ys-anti-slop README.md docs/*.md
ys-anti-slop --preset strict README.md
ys-anti-slop --format json README.md
ys-anti-slop --list-rules
```

The calibration under `examples/anti-slop/` includes a deliberately bloated coffee article and a revised version. Tests require the noisy article to exercise structural rules and the revised article to produce no findings.

## Tool versions and configuration

The release tag pins each hook implementation and its tool version. Prek creates isolated Python, Node, and Go environments and prepares the required tools on first use.

Project-local files such as `.oxfmtrc.jsonc` and `ruff.toml` control their respective tools. `ruff-check` always enables `SIM102` and preview rule `PLR1702`, allowing at most two nested blocks. The `oxlint` hook always uses this repository's fixed `.oxlintrc.json`, which enables the vendored [anti-slop](https://github.com/dmmulroy/anti-slop) code rules alongside the built-in policy; consuming repositories' Oxlint configuration and command-line options are ignored. The Markdown `anti-slop` hook is separate from that JavaScript policy. `go-vet` runs once from the repository root, so enable it only where that root is the intended Go module or workspace.

## Development

The repository's `prek.toml` uses local hooks so it checks the current worktree instead of a previous release. Run:

```sh
python3 -m unittest -v test_anti_slop.py
prek run --all-files
prek try-repo . --all-files
```

The final command tests the published manifest and its pinned environments against the repository fixtures.

## Release

1. Update the README example `rev` and `RELEASE` to the new version.
2. Commit the release changes on `main`.
3. CI validates the manifest, runs the unit tests and all local hooks, then tests the published hook environments.
4. After those checks pass on `main`, CI creates the GitHub release and matching tag if they do not already exist.

`make release VERSION=<version>` remains available for a manual local release when needed.
