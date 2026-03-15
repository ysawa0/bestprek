.PHONY: release

release:
	@test -n "$(VERSION)" || (echo 'usage: make release VERSION=<version>' >&2; exit 1)
	git push origin main
	git tag -a "$(VERSION)" -m "$(VERSION)"
	git push origin "$(VERSION)"
