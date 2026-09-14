# Install or update bestprek

Follow these steps when installing bestprek in a consuming repository, upgrading its pinned release, or refreshing its example configs. Run commands from the consuming repository root and follow that repository's agent instructions.

1. Inspect the existing hook configuration, tool configs, and lint workflow. Record the current bestprek revision and any repository-specific exclusions, hook arguments, and settings. Preserve existing work. If required tools or dependencies are missing, ask the user to install them according to the repository's dependency policy.

2. Resolve the latest published release and fetch its example configs together. Use a fresh directory under `./tmp` for the source checkout:

   ```sh
   bestprek_version=$(gh release view --repo ysawa0/bestprek --json tagName --jq .tagName)
   mkdir -p ./tmp
   bestprek_source=$(mktemp -d ./tmp/bestprek-install.XXXXXX)
   git clone --depth 1 --branch "$bestprek_version" https://github.com/ysawa0/bestprek.git "$bestprek_source"
   ```

   Read the release notes for the selected version and, during upgrades, the intervening releases. Use the selected tag's `example_conf/` as the source of truth for configuration files, including hidden files and workflows. Keep the hook revision and example configs on the same published version; `main` may contain an unpublished release.

3. Apply every applicable file from `example_conf/` to the consuming repository. For a new installation, copy missing files to the same relative paths. For an upgrade, compare and merge each file with its existing destination. Updating only `rev` leaves old settings in place and does not complete an upgrade.

   Adopt the release's current shared settings while retaining intentional repository-specific settings. Review conflicting local overrides so they do not silently retain superseded defaults. Record any deliberate differences from the examples. Merge existing workflows and hook configurations so each check runs once.

   Keep the hooks relevant to the repository's languages. Oxlint loads the policy bundled with the hook; a separate copy of bestprek's root Oxlint config is unnecessary. Go hooks require an appropriate root `go.mod` or `go.work`.

4. Set the consuming repository's bestprek `rev` to the resolved `bestprek_version`. Update any other bestprek version references in its setup instructions or CI configuration. Confirm that the example files and the pinned hook revision come from that same tag.

5. Validate and prepare the updated setup. For a repository using the example's `prek.toml`, run:

   ```sh
   prek validate-config prek.toml
   prek install --prepare-hooks
   prek run --all-files
   ```

   Use the repository's actual config path if it differs. Follow its dependency policy when preparing hook environments. Review formatter edits, fix failures within the requested scope, and rerun until the checks pass without further changes. Report any unresolved failure explicitly.

6. Remove the temporary source checkout created in step 2, review the final diff, and commit according to the consuming repository's instructions. Report the installed release, configs updated, deliberate local differences, and validation result. Installation is complete when the revision and configs agree and the configured hooks pass.
