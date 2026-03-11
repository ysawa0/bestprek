# Pre-Commit Hooks

Custom pre-commit hooks for Python, JavaScript/TypeScript, Markdown, and shell files.

Available hooks:
- `ruff-check`: lint Python files with `ruff check --force-exclude`
- `ruff-format`: format Python files with `ruff format --force-exclude`
- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON files with `oxfmt`
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `rumdl-fmt`: format Markdown files with `rumdl check --fix`
- `shellcheck`: lint shell scripts with `shellcheck`
- `shfmt`: format shell scripts with `shfmt -w`

Requirements:
- `pre-commit`
- Go toolchain for the `unbold` hook
- `ruff` on your `PATH`
- `oxfmt` on your `PATH`
- `rumdl` on your `PATH`
- `shellcheck` on your `PATH`
- `shfmt` v3+ on your `PATH`

Install required CLI tools:
```sh
brew install pre-commit ruff rumdl shellcheck shfmt
```

If `oxfmt` is not globally installed, install it in your repo with `pnpm`:
```sh
pnpm add -D oxfmt
```

Published config:
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

Run:
```sh
pre-commit run -a
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

If you want to run `oxfmt` through `pnpm` instead of relying on `PATH`, use a local hook:
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
