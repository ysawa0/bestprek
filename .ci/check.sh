#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p tmp

cargo +stable build --release --locked
cargo +stable fmt --all -- --check
cargo +stable clippy --locked -- -D warnings
uv run --no-sync python3 .ci/unslop_checks.py
prek validate-config prek.toml
prek validate-manifest .pre-commit-hooks.yaml
prek run --all-files
uvx ty check hooks scripts .ci
uv run --no-sync python3 .ci/hook_checks.py
uv run --no-sync python3 .ci/example_checks.py
uv run --no-sync python3 .ci/release_checks.py
uv run --no-sync python3 .ci/repo_checks.py
