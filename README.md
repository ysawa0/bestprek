# Pre-Commit Hooks

Hooks in this repo:
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `mdformat`: format markdown files (commonly used in Google-hosted docs workflows)
- `shellcheck`: lint shell scripts with shellcheck
- `shfmt`: format shell scripts with shfmt

Requirements:
- `pre-commit`
- Go toolchain
- `shellcheck` (for the `shellcheck` hook)
- `shfmt` v3+ (for the `shfmt` hook)

Install:
```yaml
repos:
- repo: https://github.com/ysawa0/precommit
  rev: v0.1.0
hooks:
  - id: unbold
  - id: mdformat
  - id: shellcheck
  - id: shfmt
```

Run:
```sh
pre-commit run unbold -a
pre-commit run mdformat -a
pre-commit run shellcheck -a
pre-commit run shfmt -a
```

Local run:
```sh
go run ./unbold --write README.md
```
