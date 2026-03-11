# Pre-Commit Hooks

Hooks in this repo:
- `oxfmt`: format JavaScript, JSX, TypeScript, TSX, and JSON files with oxfmt
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `rumdl-fmt`: format Markdown files with rumdl
- `shellcheck`: lint shell scripts with shellcheck
- `shfmt`: format shell scripts with shfmt

Requirements:
- `pre-commit`
- Go toolchain
- `oxfmt` on your `PATH` (for the `oxfmt` hook)
- `rumdl` (for the `rumdl-fmt` hook)
- `shellcheck` (for the `shellcheck` hook)
- `shfmt` v3+ (for the `shfmt` hook)

Install rumdl:
```sh
brew install rumdl
```

Install:
```yaml
repos:
- repo: https://github.com/ysawa0/precommit
  rev: v1.1
hooks:
  - id: oxfmt
  - id: unbold
  - id: rumdl-fmt
  - id: shellcheck
  - id: shfmt
```

Run:
```sh
pre-commit run unbold -a
pre-commit run oxfmt -a
pre-commit run rumdl-fmt -a
pre-commit run shellcheck -a
pre-commit run shfmt -a
```

Local run:
```sh
go run ./unbold --write README.md
oxfmt --no-error-on-unmatched-pattern path/to/file.ts
rumdl check --fix README.md
```

Local `oxfmt` example:
```yaml
repos:
  - repo: local
    hooks:
      - id: oxfmt
        name: oxfmt
        entry: oxfmt --no-error-on-unmatched-pattern
        language: system
        types_or: [javascript, jsx, ts, tsx, json]
        pass_filenames: true
```

If `oxfmt` is installed via npm, pnpm, or bun and is not already on your `PATH`, prefer calling it through your package manager:

```yaml
repos:
  - repo: local
    hooks:
      - id: oxfmt
        name: oxfmt
        entry: npx oxfmt --no-error-on-unmatched-pattern
        language: system
        types_or: [javascript, jsx, ts, tsx, json]
        pass_filenames: true
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

Only add `yaml` if your installed `oxfmt` version supports it in your repo:

```yaml
types_or: [javascript, jsx, ts, tsx, json, yaml]
```

Most minimal version:

```yaml
repos:
  - repo: local
    hooks:
      - id: oxfmt
        name: oxfmt
        entry: oxfmt --no-error-on-unmatched-pattern
        language: system
        files: \.(js|jsx|ts|tsx|json)$
```
