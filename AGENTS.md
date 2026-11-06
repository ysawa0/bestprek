# Cut new release

Keep `example_conf/` complete and current when hooks or configuration change. Dog food new changes: enable all new lints or new configurations in this repo. Run `make release VERSION=<version>` to update the release and example pin; CI verifies the copied setup.

# Testing

Testing means getting `prek run --all-files` green locally. Ignore GitHub Actions results.
