/**
 * 2.0.0 ships NO PDF-derived data. This file fails if any of it comes back: a table in the built
 * index, an input file the index build read, or a file in the npm tarball.
 *
 * PDF-derived, retired (kept in the repo for history, never shipped): data/fyNN/schedule_c/
 * (awards, initiatives, appendices), data/fyNN/terms/, data/fyNN/capital/ (§254),
 * data/fyNN/transparency-resolutions/, data/combined/ (roll-ups and the Legistar crosswalk of the
 * PDF documents) and data/recovered/.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const DB_PATH = join(MCP, "data", "budget.db");

const ALLOWED_TABLES = ["capital_council", "capital_sources", "capital_vs_omb", "disclosure", "disclosure_years", "meta"];
/** Every input must match one of these: the structured datasets and their manifests. */
const ALLOWED_INPUTS = [
  /^data\/disclosure_years\.csv$/,
  /^data\/fy\d{2}\/expense_disclosure\/fy\d{2}_expense_awards\.csv$/,
  /^data\/capital\/(council_capital_awards|council_vs_omb_by_budget_line)\.csv$/,
  /^source\/(wayback-council|expense-funding-disclosure|open-data-t474-a92g)\/MANIFEST\.csv$/,
  /^source\/wayback-council\/files\/\d{14}\/Capital-Database(-FY\d{2})?\.xlsx$/,
  /^source\/expense-funding-disclosure\/Capital-Database\.xlsx$/,
  /^source\/open-data-t474-a92g\/t474-a92g\.csv\.gz$/,
];
/** The retired PDF-derived trees and file shapes. None may be read or shipped. */
const PDF_DERIVED = [
  /(^|\/)schedule_c(\/|_)/, /appendix_/, /(^|\/)terms(\/|_)/, /transparency/, /(^|\/)data\/fy\d{2}\/capital\//,
  /(^|\/)data\/combined\//, /(^|\/)data\/recovered\//, /legistar_crosswalk/, /\.pdf$/i, /recovered/,
];

test("the built index holds only the structured tables", () => {
  // FAILS if any 1.x table (awards, terms, capital, transparency, crosswalk) or any other table
  // is created by the build.
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").all().map((r) => r.name);
    assert.deepEqual(tables, ALLOWED_TABLES);
  } finally {
    db.close();
  }
});

test("every file the index build read is a structured source, and none is PDF-derived", () => {
  // FAILS if build-index.mjs reads a Schedule C, appendix, recovered, terms, §254 capital,
  // transparency or data/combined file, or any input not on the allowlist.
  const db = new Database(DB_PATH, { readonly: true });
  let inputs;
  try {
    inputs = JSON.parse(db.prepare("SELECT value FROM meta WHERE key = 'inputs'").get().value);
  } finally {
    db.close();
  }
  assert.ok(inputs.length >= 20, `premise: inputs recorded (${inputs.length})`);
  for (const f of inputs) {
    assert.ok(ALLOWED_INPUTS.some((re) => re.test(f)), `not on the structured allowlist: ${f}`);
    assert.ok(!PDF_DERIVED.some((re) => re.test(f)), `PDF-derived input: ${f}`);
  }
});

test("the npm tarball ships the code and the structured index only", () => {
  // FAILS if `npm pack` would ship a CSV, a retired script or test, a PDF, or anything beyond
  // the eight expected files. --ignore-scripts: the index was already built by pretest, and a
  // rebuild here would race the other test files reading it (#95: npm 10 runs `prepare` on
  // `pack --ignore-scripts`; scripts/prepare.mjs now honors the flag).
  const r = spawnSync("npm", ["pack", "--dry-run", "--json", "--ignore-scripts"], { cwd: MCP, encoding: "utf8", shell: process.platform === "win32" });
  assert.equal(r.status, 0, r.stderr);
  assert.doesNotMatch(r.stderr, /"script":"build-index"|> tsc/, "npm pack --ignore-scripts must not rebuild");
  const out = r.stdout;
  const files = JSON.parse(out)[0].files.map((f) => f.path).sort();
  assert.deepEqual(files, ["LICENSE", "README.md", "data/budget.db", "dist/db.js", "dist/fold.js", "dist/index.js", "dist/server.js", "package.json"]);
  for (const f of files) assert.ok(!PDF_DERIVED.some((re) => re.test(f)), f);
});
