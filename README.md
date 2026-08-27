# Prek Hooks

A small, version-pinned hook bundle for ysawa0 repositories, designed for Prek.

## Hooks

- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON
- `oxlint`: lint JavaScript, JSX, TypeScript, and TSX with the bundled anti-slop policy
- `ruff-check`: lint Python and Jupyter files
- `ruff-format`: format Python and Jupyter files
- `unbold`: strip Markdown bold markers in place
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
repo = "https://github.com/ysawa0/precommit"
rev = "1.11"

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

## Tool versions and configuration

The release tag pins each hook implementation and its tool version. Prek creates isolated Python, Node, and Go environments and prepares the required tools on first use.

Project-local files such as `.oxfmtrc.jsonc` and `ruff.toml` control their respective tools. The `oxlint` hook always uses this repository's fixed `.oxlintrc.json`, which enables the vendored [anti-slop](https://github.com/dmmulroy/anti-slop) rules alongside the built-in policy; consuming repositories' Oxlint configuration and command-line options are ignored. `go-vet` runs once from the repository root, so enable it only where that root is the intended Go module or workspace.

## Development

The repository's `prek.toml` uses local hooks so it checks the current worktree instead of a previous release. Run:

```sh
prek run --all-files
prek try-repo . --all-files
```

The second command tests the published manifest and its pinned environments against the smoke fixtures.

## Release

1. Update the README example `rev` to the new version.
2. Commit the release changes on `main`.
3. Run `make release VERSION=<version>`.

The release target validates the current configuration and manifest, runs the maintenance and published hooks, creates an annotated tag, and atomically pushes `main` and the tag.
