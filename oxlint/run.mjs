#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const result = spawnSync(
  "oxlint",
  [
    "--config",
    resolve(root, ".oxlintrc.json"),
    "--deny-warnings",
    "--",
    ...process.argv.slice(2),
  ],
  { stdio: "inherit" },
);

process.exit(result.status ?? 1);
