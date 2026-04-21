# Pre-Commit Hooks

Small pre-commit hook bundle for ysawa0 repos.

Published hooks:
- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON files with `oxfmt --no-error-on-unmatched-pattern`
- `oxlint`: lint JavaScript, JSX, TypeScript, and TSX files with `oxlint`
- `ruff-check`: lint Python files with `ruff check --force-exclude`
- `ruff-format`: format Python files with `ruff format --force-exclude`
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `gofumpt`: format Go files with `gofumpt -w`
- `goimports`: format Go files and fix imports with `goimports -w`
- `gopls-check`: run `gopls check` diagnostics on staged Go files
- `go-vet`: run `go vet ./...` in the current Go module
- `shellcheck`: lint shell scripts with `shellcheck`
- `shfmt`: format shell scripts with `shfmt -w`

Quickstart:

1. Install the required tools:
```sh
brew install pre-commit ruff shellcheck shfmt gofumpt goimports
go install golang.org/x/tools/gopls@latest
pnpm add -g oxfmt oxlint
```

2. Add this to `.pre-commit-config.yaml`:
```yaml
repos:
- repo: https://github.com/ysawa0/precommit
  rev: "1.9"
  hooks:
  - id: oxfmt
  - id: oxlint
  - id: ruff-format
  - id: ruff-check
  - id: unbold
  - id: goimports
  - id: gofumpt
  - id: gopls-check
  - id: go-vet
  - id: shfmt
  - id: shellcheck
```

3. Install and run:
```sh
pre-commit install
pre-commit run -a
```

Notes:
- The default example hooks expect `ruff`, `shellcheck`, and `shfmt` to already be on your `PATH`.
- `unbold` is built by pre-commit using Go, so you need a Go toolchain installed.
- `gofumpt`, `goimports`, and `gopls` also need to already be on your `PATH`.
- `go-vet` runs `go vet ./...` from the repo root, so use it only in repos where the hook runs inside the intended Go module.
- Install `oxfmt` globally with `pnpm add -g oxfmt` so the published `oxfmt` hook can find it on your `PATH`.
- Install `oxlint` globally with `pnpm add -g oxlint` so the published `oxlint` hook can find it on your `PATH`.

If you want Oxc tools installed per-repo instead of globally, use local hooks instead:

`pnpm add -D oxfmt oxlint` by itself does not make the published hooks work. The published hooks expect those binaries on your `PATH`; the local hooks below use `pnpm exec` instead.

```sh
pnpm add -D oxfmt oxlint
```

```yaml
repos:
- repo: local
  hooks:
  - id: oxfmt
    name: oxfmt
    entry: pnpm exec oxfmt --no-error-on-unmatched-pattern
    language: system
    types_or: [javascript, jsx, ts, tsx, json]
    pass_filenames: true
  - id: oxlint
    name: oxlint
    entry: pnpm exec oxlint
    language: system
    types_or: [javascript, jsx, ts, tsx]
    pass_filenames: true
```

Run individual hooks:
```sh
pre-commit run oxfmt -a
pre-commit run oxlint -a
pre-commit run ruff-check -a
pre-commit run ruff-format -a
pre-commit run unbold -a
pre-commit run gofumpt -a
pre-commit run goimports -a
pre-commit run gopls-check -a
pre-commit run go-vet -a
pre-commit run shellcheck -a
pre-commit run shfmt -a
```

Direct CLI equivalents:
```sh
oxfmt --no-error-on-unmatched-pattern path/to/file.ts
oxlint path/to/file.ts
ruff check --force-exclude .
ruff format --force-exclude .
go run ./unbold --write README.md
gofumpt -w path/to/file.go
goimports -w path/to/file.go
gopls check path/to/file.go
go vet ./...
shellcheck script.sh
shfmt -w script.sh
```

Cut a release:

1. Commit the changes you want to release on `main`.
2. Run:
```sh
make release VERSION=<version>
```
3. Update `.pre-commit-config.yaml` and README example `rev:` pins to the new tag.
4. Commit and push that follow-up version bump.

This will:
- push `main` to `origin`
- create an annotated numeric tag matching `VERSION`
- push that tag to GitHub
