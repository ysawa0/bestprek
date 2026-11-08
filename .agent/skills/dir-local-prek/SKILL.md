---
name: dir-local-prek
description: Move directory-specific prek hooks out of the root prek.toml into a nested project. Use when a root hook's `files` or `entry` targets one subdirectory, or when adding hooks for one project in a monorepo.
---

# Dir-local prek

Any subdirectory with its own `prek.toml` is a separate prek project. The root config keeps the repo-wide hooks; each project's own checks live in `<dir>/prek.toml`.

## How a nested project behaves

- Its hooks see only files under its directory, run from that directory, and get paths relative to it. Drop `-C <dir>` and `<dir>/` prefixes from `entry` and `files`.
- Root hooks still run on its files. Set top-level `orphan = true` in the nested config only when the project should own all of its checks.
- The root top-level `exclude` does not reach nested hooks. A hook that used `always_run` to see files the root excludes can drop it.
- A `local` repo needs at least one hook, so remove or comment out its `[[repos]]` header when the last hook moves out.
- prek caches the project list. Run `prek list --refresh` after adding a nested config, or the new project is invisible.
- prek skips configs in gitignored directories, so a nested project under `tmp/` or `build/` never loads.

## Steps

1. List root hooks whose `files` or `entry` names one directory. Repo-wide hooks with a path-specific `exclude` stay at the root.
2. For each directory, write `<dir>/prek.toml` with its hooks, rebased to directory-relative paths, and delete them from the root.
3. Run `prek validate-config` on every changed config, then `prek list --refresh`. Each moved hook should be listed as `<dir>:<id>` and none as `.:<id>`.
4. Run `prek run --refresh --files` on one file each hook should check and one it should skip. Done when every moved hook runs on the first, skips the second, and the result matches the hook before the move.
