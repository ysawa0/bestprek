# Pre-Commit Hooks

Small pre-commit hook bundle for ysawa0 repos.

Published hooks:
- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON files with `oxfmt --no-error-on-unmatched-pattern`
- `ruff-check`: lint Python files with `ruff check --force-exclude`
- `ruff-format`: format Python files with `ruff format --force-exclude`
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `rumdl-fmt`: format Markdown files with `rumdl check --fix`
- `shellcheck`: lint shell scripts with `shellcheck`
- `shfmt`: format shell scripts with `shfmt -w`

Quickstart:

1. Install the required tools:
```sh
brew install pre-commit ruff rumdl shellcheck shfmt
```

2. Add this to `.pre-commit-config.yaml`:
```yaml
repos:
- repo: https://github.com/ysawa0/precommit
  rev: "1.2"
  hooks:
  - id: oxfmt
  - id: ruff-check
  - id: ruff-format
  - id: unbold
  - id: rumdl-fmt
  - id: shellcheck
  - id: shfmt
```

3. Install and run:
```sh
pre-commit install
pre-commit run -a
```

Notes:
- The published hooks expect `ruff`, `rumdl`, `shellcheck`, and `shfmt` to already be on your `PATH`.
- `unbold` is built by pre-commit using Go, so you need a Go toolchain installed.
- The published `oxfmt` hook also expects `oxfmt` on your `PATH`.

If you want `oxfmt` installed per-repo instead of globally, install it with `pnpm` and use a local hook:

```sh
pnpm add -D oxfmt
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
```

Run individual hooks:
```sh
pre-commit run oxfmt -a
pre-commit run ruff-check -a
pre-commit run ruff-format -a
pre-commit run unbold -a
pre-commit run rumdl-fmt -a
pre-commit run shellcheck -a
pre-commit run shfmt -a
```

Direct CLI equivalents:
```sh
oxfmt --no-error-on-unmatched-pattern path/to/file.ts
ruff check --force-exclude .
ruff format --force-exclude .
go run ./unbold --write README.md
rumdl check --fix README.md
shellcheck script.sh
shfmt -w script.sh
```
