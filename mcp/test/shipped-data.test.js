/**
 * What the npm package ships (GitHub #215). Replaces, on purpose, 2.0.0's no-pdf-data.test.js:
 * the checked PDF tables are served now (#212), but never from the package. The package carries
 * the spreadsheet index only; the PDF tables are an optional download (src/pdfdata.ts), and the
 * old parser's output is never read by any build (test/pdf-families.test.js).
 *
 *   1. data/budget.db (pretest: build-index --spreadsheet-only) has the expected tables, every
 *      pdf_* table empty, and records the gate, the PDF years it does not carry, and the commit.
 *   2. Every file that build read is a structured source: no PDF and no PDF-derived CSV.
 *   3. `npm pack` ships exactly the code and that index.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { readFileSync } from "node:fs";
import { parse } from "csv-parse/sync";
import { PDF_TABLES } from "../scripts/pdf-families.mjs";
import { OPEN_DATA_TABLES } from "../scripts/open-data.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const DB_PATH = join(MCP, "data", "budget.db");

const ALLOWED_TABLES = ["capital_council", "capital_sources", "capital_vs_omb", "disclosure", "disclosure_years", "meta",
  ...PDF_TABLES, ...OPEN_DATA_TABLES].sort();
/** Every input must match one of these: the structured datasets and their manifests. */
const ALLOWED_INPUTS = [
  /^data\/disclosure_years\.csv$/,
  /^data\/fy\d{2}\/expense_disclosure\/fy\d{2}_expense_awards\.csv$/,
  /^data\/capital\/(council_capital_awards|council_vs_omb_by_budget_line)\.csv$/,
  /^source\/(wayback-council|expense-funding-disclosure|open-data-t474-a92g)\/MANIFEST\.csv$/,
  /^source\/wayback-council\/files\/\d{14}\/Capital-Database(-FY\d{2})?\.xlsx$/,
  /^source\/expense-funding-disclosure\/Capital-Database\.xlsx$/,
  /^source\/open-data-t474-a92g\/t474-a92g\.csv\.gz$/,
  // Read for its list of family-years and statuses only (meta.pdf_years_listed); no family loads.
  /^data\/pdf_years\.csv$/,
  /^data\/open_data\/(crosswalk_(expense|capital_award|capital_line|terms_unit)|coverage)\.csv$/,
  /^source\/open-data-watch\.csv$/,
];
/** PDF-derived trees and file shapes, retired or checked: none may be read for, or shipped in, the package. */
const PDF_DERIVED = [
  /(^|\/)schedule_c(\/|_)/, /appendix_/, /(^|\/)terms(\/|_)/, /transparency/, /(^|\/)data\/fy\d{2}\/capital\//,
  /(^|\/)data\/fy\d{2}\/pdf\//, /(^|\/)data\/combined\//, /(^|\/)data\/recovered\//, /(^|\/)data\/retired\//,
  /legistar_crosswalk/, /\.pdf$/i, /recovered/, /pdf_review_suggestions/,
];

test("the package's index holds the spreadsheet tables, and every PDF table is empty", () => {
  // FAILS if a build adds a table, or loads any PDF family (closed or reviewed) into the index
  // the package ships.
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").all().map((r) => r.name);
    assert.deepEqual(tables, ALLOWED_TABLES);
    for (const t of PDF_TABLES) assert.equal(db.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get().n, 0, t);
    const meta = Object.fromEntries(db.prepare("SELECT key, value FROM meta").all().map((r) => [r.key, r.value]));
    assert.equal(meta.pdf_gate, "none");
    assert.equal(meta.include_reviewed, "no");
    assert.match(meta.source_commit, /^[0-9a-f]{40}$/, "the commit the index was built from");
    assert.equal(meta.source_commit_check, "no_pdfs_cited");
    // What exists, so list_available_fiscal_years can say so without the download.
    const listed = JSON.parse(meta.pdf_years_listed);
    const csv = parse(readFileSync(join(MCP, "..", "data", "pdf_years.csv"), "utf8"), { columns: true, skip_empty_lines: true });
    assert.deepEqual(listed, csv.map((y) => ({ fiscal_year: Number(y.fiscal_year), family: y.family, status: y.status, rows: Number(y.rows) })));
  } finally {
    db.close();
  }
});

test("every file the package's index build read is a structured source", () => {
  // FAILS if build-index --spreadsheet-only reads a PDF, a checked PDF table, or an old-parser CSV.
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

test("--spreadsheet-only and --include-reviewed cannot be combined", () => {
  const r = spawnSync(process.execPath, [join(MCP, "scripts", "build-index.mjs"), "--spreadsheet-only", "--include-reviewed", "--out", join(MCP, ".pdf-test", "never.db")], { cwd: MCP, encoding: "utf8" });
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /contradict/);
});

test("the npm tarball ships the code and the spreadsheet index only", () => {
  // FAILS if `npm pack` would ship a CSV, a script, a test, a PDF, the PDF tables, or anything
  // beyond the expected files. --ignore-scripts: the index was already built by pretest, and a
  // rebuild here would race the other test files reading it (#95: npm 10 runs `prepare` on
  // `pack --ignore-scripts`; scripts/prepare.mjs now honors the flag).
  const r = spawnSync("npm", ["pack", "--dry-run", "--json", "--ignore-scripts"], { cwd: MCP, encoding: "utf8", shell: process.platform === "win32" });
  assert.equal(r.status, 0, r.stderr);
  assert.doesNotMatch(r.stderr, /"script":"build-index"|> tsc/, "npm pack --ignore-scripts must not rebuild");
  const files = JSON.parse(r.stdout)[0].files.map((f) => f.path).sort();
  assert.deepEqual(files, ["LICENSE", "README.md", "data/budget.db", "dist/checkwords.js", "dist/db.js", "dist/fold.js", "dist/index.js", "dist/pdfdata.js",
    "dist/pdfquery.js", "dist/publisher-copies.js", "dist/questions.js", "dist/rowlinks.js", "dist/server.js", "package.json"]);
  for (const f of files) assert.ok(!PDF_DERIVED.some((re) => re.test(f)), f);
});
