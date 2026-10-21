/**
 * Whether each record is on NYC Open Data (scripts/open-data.mjs, data/open_data/, PLAN
 * research/2026-10-21-open-data-tracking/PLAN.md §5). Each test names the outcome that fails it.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { cpSync, mkdirSync, readFileSync, rmSync } from "node:fs";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";

import { OPEN_DATA_FAMILIES, OPEN_DATA_TABLES } from "../scripts/open-data.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const DEFAULT_DB = join(MCP, "data", "budget.db");
const TMP = join(MCP, ".open-data-test");
const REVIEWED_DB = join(TMP, "data", "budget.db");
const csv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true });

before(() => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "data"), { recursive: true });
  cpSync(join(MCP, "dist"), join(TMP, "dist"), { recursive: true });
  cpSync(join(MCP, "package.json"), join(TMP, "package.json"));
  const r = spawnSync(process.execPath, [join(MCP, "scripts", "build-index.mjs"), "--include-reviewed", "--out", REVIEWED_DB],
    { cwd: MCP, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
});
after(() => rmSync(TMP, { recursive: true, force: true }));

const withDb = (path, fn) => {
  const db = new Database(path, { readonly: true });
  try {
    return fn(db);
  } finally {
    db.close();
  }
};
const n = (db, sql, ...a) => db.prepare(sql).get(...a).n;

test("the default index carries the structured families' crosswalk, row for row", () => {
  // FAILS if an expense, capital award or capital line row of data/open_data/ is dropped or added.
  withDb(DEFAULT_DB, (db) => {
    for (const fam of ["expense", "capital_line"]) {
      assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE family = ?", fam), csv(`data/open_data/crosswalk_${fam}.csv`).length, fam);
    }
    const cap = csv("data/open_data/crosswalk_capital_award.csv").filter((r) => !r.record_key.startsWith("pdf|"));
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE family = 'capital_award'"), cap.length);
  });
});

test("the default index carries no crosswalk row about a PDF-derived record", () => {
  // FAILS if T&C units or PDF capital rows reach the MCP's own index (status = closed only).
  withDb(DEFAULT_DB, (db) => {
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE record_pdf = 1 OR family = 'terms_unit'"), 0);
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_coverage WHERE family = 'terms_unit'"), 0);
  });
});

test("a reviewed index adds them, and every one names a loaded record", () => {
  // FAILS if the reviewed build drops the PDF-derived crosswalk rows, or one names no record.
  withDb(REVIEWED_DB, (db) => {
    assert.ok(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE family = 'terms_unit'") > 400);
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE record_pdf = 1 AND family = 'capital_award' AND match_status = 'same'"), 1252);
    assert.equal(n(db, `SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'terms_unit' AND NOT EXISTS
      (SELECT 1 FROM pdf_terms p WHERE p.fiscal_year = x.fiscal_year AND p.item_number = CAST(x.record_row AS INTEGER))`), 0);
  });
});

test("every expense and capital crosswalk row joins its record", () => {
  // FAILS if a record key stops naming a disclosure or capital_council row.
  withDb(DEFAULT_DB, (db) => {
    assert.equal(n(db, `SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'expense' AND NOT EXISTS
      (SELECT 1 FROM disclosure d WHERE d.fiscal_year = x.fiscal_year AND d.source_row = CAST(x.record_row AS INTEGER))`), 0);
    assert.equal(n(db, `SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'capital_award' AND NOT EXISTS
      (SELECT 1 FROM capital_council c WHERE c.report_year = x.fiscal_year AND c.source_row = x.record_row
         AND (c.amount_fy = x.record_amount_fy OR (c.amount_fy IS NULL AND x.record_amount_fy IS NULL)))`), 0);
  });
});

test("the vocabularies hold, and a same row names exactly one portal row", () => {
  // FAILS if a status outside the plan, a not_covered row, or a multi-row same/differs is loaded.
  withDb(DEFAULT_DB, (db) => {
    const st = db.prepare("SELECT DISTINCT match_status s FROM open_data_crosswalk").all().map((r) => r.s).sort();
    assert.deepEqual(st, ["absent", "ambiguous", "context", "differs", "same"]);
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk WHERE match_status IN ('same','differs') AND (portal_row_id = '' OR portal_row_id LIKE '%;%')"), 0);
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_crosswalk x WHERE NOT EXISTS (SELECT 1 FROM open_data_rules r WHERE r.rule_id = x.rule_id)"), 0);
    assert.deepEqual(db.prepare("SELECT DISTINCT family f FROM open_data_crosswalk ORDER BY f").all().map((r) => r.f),
      OPEN_DATA_FAMILIES.filter((f) => f !== "terms_unit").sort());
  });
});

test("coverage adds up and names the datasets the index lists", () => {
  // FAILS if a coverage year's statuses do not sum to its records, or a dataset has no metadata row.
  withDb(DEFAULT_DB, (db) => {
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_coverage WHERE same+differs+ambiguous+absent+context+not_covered <> records"), 0);
    assert.equal(n(db, "SELECT COUNT(*) n FROM open_data_coverage c WHERE NOT EXISTS (SELECT 1 FROM open_data_datasets d WHERE d.dataset_id = c.dataset_id)"), 0);
    const fy09 = db.prepare("SELECT covered, records FROM open_data_coverage WHERE dataset_id = '4d7f-74pe' AND fiscal_year = 2009").get();
    assert.deepEqual(fy09, { covered: 1, records: 5745 });
    assert.equal(db.prepare("SELECT covered FROM open_data_coverage WHERE dataset_id = '4d7f-74pe' AND fiscal_year = 2027").get().covered, 0);
  });
});

test("no tool reads an open_data table", () => {
  // FAILS if src/*.ts starts serving these tables without its own tests (the MCP's answers are
  // unchanged in 2.0.1).
  for (const f of ["db.ts", "server.ts", "index.ts", "fold.ts"]) {
    const src = readFileSync(join(MCP, "src", f), "utf8");
    for (const t of OPEN_DATA_TABLES) assert.ok(!src.includes(t), `${f} names ${t}`);
  }
});
