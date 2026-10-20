#!/usr/bin/env node
/**
 * prepare.mjs — the `prepare` lifecycle script: compile, then build the index.
 *
 * Honors --ignore-scripts. npm 10 (bundled with Node 20 and 22) still runs `prepare` on
 * `npm pack --ignore-scripts`; npm 11 does not. Under npm 10 that rebuilt the index in the middle
 * of the test suite, while other test files were reading it (#95). npm passes the flag to the
 * script as npm_config_ignore_scripts=true, so this exits without building when it is set.
 */
import { execSync } from "node:child_process";

if (process.env.npm_config_ignore_scripts === "true") {
  console.error(JSON.stringify({ script: "prepare", event: "skipped", reason: "--ignore-scripts", ts: new Date().toISOString() }));
  process.exit(0);
}
execSync("npm run build && npm run build-index", { stdio: "inherit" });
