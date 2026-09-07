#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p tmp

uv run --no-sync python3 -m unittest discover -s .ci -p test_unslop.py -v
prek validate-config prek.toml
prek validate-manifest .pre-commit-hooks.yaml
prek run --all-files
uvx ty check
uv run --no-sync python3 .ci/hook_checks.py
prek try-repo "$PWD" --all-files
