#!/usr/bin/env node
/** Cross-platform npm/npx launcher for gh-unfollow. */
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const main = path.resolve(__dirname, "..", "src", "main.py");
const candidates = process.platform === "win32"
  ? [["py", ["-3"]], ["python", []]]
  : [["python3", []], ["python", []], ["py", ["-3"]]];

let result;
for (const [command, prefix] of candidates) {
  const version = spawnSync(command, [...prefix, "-c", "import sys; raise SystemExit(sys.version_info < (3, 10))"], {
    stdio: "ignore",
    windowsVerbatimArguments: false,
  });
  if (version.error && version.error.code === "ENOENT") {
    continue;
  }
  if (version.status !== 0) {
    continue;
  }
  result = spawnSync(command, [...prefix, main, ...process.argv.slice(2)], {
    stdio: "inherit",
    windowsVerbatimArguments: false,
  });
  if (!result.error) {
    process.exit(result.status === null ? 1 : result.status);
  }
  if (result.error.code !== "ENOENT") {
    console.error(`Failed to start ${command}: ${result.error.message}`);
    process.exit(1);
  }
}

console.error("Error: Python 3.10+ is required but was not found in PATH.");
console.error("Install Python from https://www.python.org/downloads/");
process.exit(1);
