#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const configPath = resolve(root, ".oxlintrc.json");
const { ignorePatterns } = JSON.parse(readFileSync(configPath, "utf8"));
const result = spawnSync(
  "oxlint",
  [
    "--config",
    configPath,
    "--deny-warnings",
    "--no-error-on-unmatched-pattern",
    ...ignorePatterns.flatMap((pattern) => ["--ignore-pattern", pattern]),
    "--",
    ...process.argv.slice(2),
  ],
  { stdio: "inherit" },
);

process.exit(result.status ?? 1);
