.PHONY: release

release:
	@test -n "$(VERSION)" || (echo 'usage: make release VERSION=<version>' >&2; exit 1)
	uv run --no-sync python3 scripts/release.py "$(VERSION)"
