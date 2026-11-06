#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const bundledConfig = resolve(root, ".oxlintrc.json");

const localConfig = [".oxlintrc.json", ".oxlintrc.jsonc"].map((name) => resolve(process.cwd(), name)).find((path) => existsSync(path) && readFileSync(path, "utf8") !== readFileSync(bundledConfig, "utf8"));

const temporaryDirectory = localConfig ? mkdtempSync(resolve(tmpdir(), "bestprek-oxlint-")) : null;

const configPath = temporaryDirectory ? resolve(temporaryDirectory, "config.json") : bundledConfig;

if (localConfig) {
  writeFileSync(configPath, JSON.stringify({ extends: [bundledConfig, localConfig] }));
}

const { ignorePatterns } = JSON.parse(readFileSync(bundledConfig, "utf8"));

const result = spawnSync("oxlint", ["--config", configPath, "--no-error-on-unmatched-pattern", ...ignorePatterns.flatMap((pattern) => ["--ignore-pattern", pattern]), ...process.argv.slice(2)], { stdio: "inherit" });

if (temporaryDirectory) rmSync(temporaryDirectory, { recursive: true });

process.exit(result.status ?? 1);
