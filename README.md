# Pre-Commit Hooks

Hooks in this repo:
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `rumdl`: lint Markdown files with rumdl
- `rumdl-fmt`: format Markdown files with rumdl
- `shellcheck`: lint shell scripts with shellcheck
- `shfmt`: format shell scripts with shfmt

Requirements:
- `pre-commit`
- Go toolchain
- `rumdl` (for `rumdl` and `rumdl-fmt` hooks)
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
  - id: unbold
  - id: rumdl
  - id: rumdl-fmt
  - id: shellcheck
  - id: shfmt
```

Run:
```sh
pre-commit run unbold -a
pre-commit run rumdl -a
pre-commit run rumdl-fmt -a
pre-commit run shellcheck -a
pre-commit run shfmt -a
```

Local run:
```sh
go run ./unbold --write README.md
rumdl check README.md
rumdl check --fix README.md
```
