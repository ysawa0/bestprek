#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const ignorePatterns = [
  ".agent/**",
  ".agents/**",
  ".claude/**",
  ".codex/**",
  ".continue/**",
  ".cursor/**",
  ".gemini/**",
  ".opencode/**",
  ".pi/**",
  ".roo/**",
  ".windsurf/**",
  "coverage/**",
  "dist/**",
  "node_modules/**",
  "oxlint/anti-slop/**",
  "vendor/**",
];
const result = spawnSync(
  "oxlint",
  [
    "--config",
    resolve(root, ".oxlintrc.json"),
    "--deny-warnings",
    "--no-error-on-unmatched-pattern",
    ...ignorePatterns.flatMap((pattern) => ["--ignore-pattern", pattern]),
    "--",
    ...process.argv.slice(2),
  ],
  { stdio: "inherit" },
);

process.exit(result.status ?? 1);
