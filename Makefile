.PHONY: release

PREK := uvx prek==0.4.12

release:
	@test -n "$(VERSION)" || (echo 'usage: make release VERSION=<version>' >&2; exit 1)
	@test -z "$$(git status --porcelain)" || (echo 'working tree must be clean' >&2; exit 1)
	@test -z "$$(git tag --list "$(VERSION)")" || (echo 'tag $(VERSION) already exists' >&2; exit 1)
	@grep -Fq 'rev = "$(VERSION)"' README.md || (echo 'update README.md to rev $(VERSION)' >&2; exit 1)
	$(PREK) validate-config prek.toml
	$(PREK) validate-manifest .pre-commit-hooks.yaml
	$(PREK) run --all-files
	$(PREK) try-repo . --all-files
	git tag -a "$(VERSION)" -m "$(VERSION)"
	git push --atomic origin main "$(VERSION)"
