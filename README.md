# Unbold Pre-Commit Hook

Strip markdown bold markers (`**` and `__`) in place.

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
```

Run:
```sh
pre-commit run unbold -a
```

Local run:
```sh
go run ./unbold --write README.md
```
