/**
 * The index build fails loud and installs atomically (#95).
 *
 * On Node 20 CI (npm 10), `npm pack --ignore-scripts` still ran `prepare`, which rebuilt
 * data/budget.db by deleting it and inserting from scratch while other test files were reading it.
 * Those readers saw empty tables and answered "The Council capital list covers (none)". Three
 * guards, each with a falsifying outcome:
 *   1. verifyIndex() reports a dataset with 0 rows or a declared year that is missing.
 *   2. build-index.mjs never exposes a partly built or empty index at data/budget.db.
 *   3. `prepare` honors --ignore-scripts, so `npm pack --ignore-scripts` does not rebuild.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { copyFileSync, mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { verifyIndex, CAPITAL_REPORT_YEARS } from "../scripts/verify-index.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const DB_PATH = join(MCP, "data", "budget.db");

const csv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true, trim: true });

function expectations() {
  const capitalRowsByYear = new Map();
  for (const r of csv("data/capital/council_capital_awards.csv")) {
    const y = Number(r.report_year);
    capitalRowsByYear.set(y, (capitalRowsByYear.get(y) ?? 0) + 1);
  }
  return { disclosureYears: csv("data/disclosure_years.csv"), capitalRowsByYear };
}

/** A writable scratch copy of the built index, damaged by `sql`, then verified. */
function problemsAfter(sql) {
  const dir = mkdtempSync(join(tmpdir(), "nycb-guard-"));
  try {
    const p = join(dir, "budget.db");
    copyFileSync(DB_PATH, p);
    const db = new Database(p);
    db.pragma("journal_mode = DELETE");
    if (sql) db.exec(sql);
    const problems = verifyIndex(db, expectations());
    db.close();
    return problems;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("verifyIndex passes the index as built (positive control)", () => {
  assert.deepEqual(problemsAfter(null), []);
});

test("verifyIndex fails an empty capital table, naming every missing year", () => {
  // FAILS (passes wrongly) if an empty capital_council could ship: the Node 20 symptom.
  const problems = problemsAfter("DELETE FROM capital_council");
  assert.ok(problems.includes("capital_council: 0 rows"), problems.join("\n"));
  for (const y of CAPITAL_REPORT_YEARS) {
    assert.ok(problems.includes(`capital_council: FY${y} is missing (0 rows)`), `FY${y}\n${problems.join("\n")}`);
  }
});

test("verifyIndex fails a missing disclosure year, a short year, and an empty comparison table", () => {
  assert.ok(problemsAfter("DELETE FROM disclosure WHERE fiscal_year = 2009")
    .some((p) => p.startsWith("disclosure: FY2009 is missing (0 rows")));
  assert.ok(problemsAfter("DELETE FROM disclosure WHERE rowid IN (SELECT rowid FROM disclosure WHERE fiscal_year = 2027 LIMIT 1)")
    .some((p) => /^disclosure: FY2027 has \d+ rows; data\/disclosure_years\.csv says \d+$/.test(p)));
  assert.ok(problemsAfter("DELETE FROM disclosure_years WHERE fiscal_year = 2010")
    .includes("disclosure_years: FY2010 is in data/disclosure_years.csv but not in the index"));
  assert.ok(problemsAfter("DELETE FROM capital_vs_omb").includes("capital_vs_omb: 0 rows"));
  assert.ok(problemsAfter("DELETE FROM capital_sources WHERE report_year = 2026")
    .includes("capital_sources: FY2026 has no provenance row"));
  assert.ok(problemsAfter("DELETE FROM disclosure").includes("disclosure: 0 rows"));
});

test("verifyIndex fails a capital year the CSV lacks, even if the index agrees with the CSV", () => {
  // The expectation is the published year list, not the CSV, so a year dropped from both is caught.
  const e = expectations();
  e.capitalRowsByYear.delete(2027);
  const dir = mkdtempSync(join(tmpdir(), "nycb-guard-"));
  try {
    const p = join(dir, "budget.db");
    copyFileSync(DB_PATH, p);
    const db = new Database(p);
    db.pragma("journal_mode = DELETE");
    db.exec("DELETE FROM capital_council WHERE report_year = 2027");
    const problems = verifyIndex(db, e);
    db.close();
    assert.ok(problems.some((x) => x.startsWith("capital: FY2027 is a published report year")), problems.join("\n"));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a rebuild never exposes an empty or partial index to a reader opening data/budget.db", async () => {
  // FAILS on the pre-#95 build, which deleted data/budget.db and filled a new file in place: a
  // reader opening it mid-build saw 0 capital rows.
  const before = new Database(DB_PATH, { readonly: true });
  const expected = before.prepare("SELECT COUNT(*) AS n FROM capital_council").get().n;
  before.close();
  assert.ok(expected > 0, "premise: the index is built");
  const child = spawn(process.execPath, [join(MCP, "scripts", "build-index.mjs")], { stdio: ["ignore", "ignore", "pipe"] });
  let stderr = "";
  child.stderr.on("data", (d) => (stderr += d));
  let running = true;
  const exited = new Promise((resolve) => child.on("exit", (code) => { running = false; resolve(code); }));
  const seen = [];
  while (running) {
    try {
      const db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
      seen.push(db.prepare("SELECT COUNT(*) AS n FROM capital_council").get().n);
      db.close();
    } catch (err) {
      seen.push(`error: ${err.message}`);
    }
    await new Promise((r) => setTimeout(r, 20));
  }
  assert.equal(await exited, 0, stderr);
  assert.ok(seen.length >= 5, `premise: sampled during the build (${seen.length} samples)`);
  assert.deepEqual([...new Set(seen)], [expected], "every read during the rebuild saw the full index");
  assert.deepEqual(readdirSync(join(MCP, "data")).filter((f) => f.includes(".building-")), [], "no temp file left behind");
});

test("prepare honors --ignore-scripts: it does not rebuild", () => {
  // FAILS if prepare builds anyway, which is what npm 10 did inside `npm pack --ignore-scripts`.
  const r = spawnSync(process.execPath, [join(MCP, "scripts", "prepare.mjs")], {
    env: { ...process.env, npm_config_ignore_scripts: "true" },
    encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stderr, /"event":"skipped"/);
  assert.doesNotMatch(r.stderr + r.stdout, /build-index|tsc/);
});
