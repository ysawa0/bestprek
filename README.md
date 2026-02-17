# Pre-Commit Hooks

Hooks in this repo:
- `unbold`: strip markdown bold markers (`**` and `__`) in place
- `mdformat`: format markdown files (commonly used in Google-hosted docs workflows)

Requirements:
- `pre-commit`
- Go toolchain

Install:
```yaml
repos:
- repo: https://github.com/ysawa0/precommit
  rev: v0.1.0
hooks:
  - id: unbold
  - id: mdformat
```

Run:
```sh
pre-commit run unbold -a
pre-commit run mdformat -a
```

Local run:
```sh
go run ./unbold --write README.md
```
