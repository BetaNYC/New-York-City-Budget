/**
 * City agency budgets in the MCP's index: the `agency_budget` table (#270, built in #284).
 *
 * PENDING #284. Until build-index.mjs writes the table, every test here is skipped with that
 * reason, so `npm test` stays green. When the table exists they run, with no change to this file.
 *
 * The table's contract (docs/plans/2026-11-12-270-agency-budgets.md, "The agency_budget table"):
 *
 *   fiscal_year INTEGER, agency_number TEXT, agency_name TEXT, unit_number TEXT, unit_name TEXT,
 *   adopted REAL, modified REAL, adopted_release TEXT, modified_release TEXT
 *
 * One row per agency x unit of appropriation x fiscal year (FY2017 on) where the unit is in that
 * year's adopted release or the next year's. Agency and unit numbers are 3-character text.
 *
 * Every expected figure is recomputed HERE from the committed NYC Open Data snapshot
 * (source/agency-budget-qa/, the one code/qa_agency_budget.py checks), with code that shares
 * nothing with the loader. The year rule (DATA-DICTIONARY.md, DATA-ANOMALIES.md §57, #268, #274):
 *
 *   June release of tag Y = the tag's latest publication_date, dated June of Y-1.
 *   Adopted FY Y  = sum(financial_plan_amount)          in the June release tagged Y
 *   Modified FY Y = sum(current_modified_budget_amount) in the June release tagged Y+1
 *   The newest year's Modified is NULL ("not yet published"), never 0.
 *
 * Each test says what result would make it FAIL.
 */
import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const DB_PATH = join(MCP, "data", "budget.db");
const SNAP = "source/agency-budget-qa";
const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });

const COLUMNS = ["fiscal_year", "agency_number", "agency_name", "unit_number", "unit_name", "adopted", "modified", "adopted_release", "modified_release"];
const FIRST_YEAR = 2017;

/** Skip reason, or false when the table is there. */
function pending() {
  if (!existsSync(DB_PATH)) return "PENDING #284: mcp/data/budget.db is not built";
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const t = db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'agency_budget'").get();
    return t ? false : "PENDING #284: build-index.mjs does not write the agency_budget table yet";
  } finally {
    db.close();
  }
}
const SKIP = pending();

const pad = (s) => (/^\d+$/.test(String(s ?? "").trim()) ? String(s).trim().padStart(3, "0") : String(s ?? "").trim());
/** Whole cents, as integers, so sums are exact. The snapshot's amounts are whole dollars today. */
const cents = (s) => (s === "" || s == null ? 0 : Math.round(Number(s) * 100));

/** The year rule, recomputed from the snapshot. Map key: `${year}|${agency}|${unit}`. */
function expected() {
  const latest = new Map();
  for (const r of readCsv(`${SNAP}/releases.csv`)) {
    const t = Number(r.fiscal_year);
    if ((latest.get(t) ?? "") < r.publication_date) latest.set(t, r.publication_date);
  }
  const june = new Map([...latest].filter(([t, d]) => d.slice(0, 6) === `${t - 1}06`));
  const fp = new Map(); // tag|agency|unit -> cents of financial_plan_amount
  const cm = new Map(); // tag|agency|unit -> cents of current_modified_budget_amount
  const names = new Map(); // tag|agency|unit -> [agency_name, unit_name]
  for (const r of readCsv(`${SNAP}/by_unit.csv`)) {
    const t = Number(r.fiscal_year);
    if (june.get(t) !== r.publication_date) continue;
    const k = `${t}|${pad(r.agency_number)}|${pad(r.unit_appropriation_number)}`;
    fp.set(k, (fp.get(k) ?? 0) + cents(r.financial_plan_amount));
    cm.set(k, (cm.get(k) ?? 0) + cents(r.current_modified_budget_amount));
    names.set(k, [r.agency_name.trim(), r.unit_appropriation_name.trim()]);
  }
  const years = [...june.keys()].filter((y) => y >= FIRST_YEAR).sort((a, b) => a - b);
  const cells = new Map();
  const units = new Set([...fp.keys()].map((k) => k.slice(5)));
  for (const y of years) {
    for (const au of units) {
      const a = `${y}|${au}`;
      const m = `${y + 1}|${au}`;
      const inAdopted = fp.has(a);
      const inModified = june.has(y + 1) && fp.has(m);
      if (!inAdopted && !inModified) continue;
      cells.set(a, {
        adopted: inAdopted ? fp.get(a) : null,
        modified: inModified ? cm.get(m) : null,
        adopted_release: inAdopted ? june.get(y) : null,
        modified_release: inModified ? june.get(y + 1) : null,
        names: names.get(a) ?? names.get(m),
      });
    }
  }
  return { june, years, cells };
}

function rows() {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    return db.prepare("SELECT * FROM agency_budget ORDER BY fiscal_year, agency_number, unit_number").all();
  } finally {
    db.close();
  }
}

describe("agency_budget: the table and its columns", { skip: SKIP }, () => {
  test("has exactly the contract's columns, with the declared types", () => {
    // FAILS if a column is missing, renamed or extra, or a number column is stored as text (or the
    // reverse): agency and unit numbers must stay text so "040" keeps its zero.
    const db = new Database(DB_PATH, { readonly: true });
    try {
      const cols = db.prepare("PRAGMA table_info(agency_budget)").all();
      assert.deepEqual(cols.map((c) => c.name), COLUMNS);
      const type = Object.fromEntries(cols.map((c) => [c.name, c.type]));
      assert.equal(type.fiscal_year, "INTEGER");
      for (const c of ["agency_number", "agency_name", "unit_number", "unit_name", "adopted_release", "modified_release"]) assert.equal(type[c], "TEXT", c);
      for (const c of ["adopted", "modified"]) assert.equal(type[c], "REAL", c);
    } finally {
      db.close();
    }
  });

  test("agency and unit numbers are 3-character text, never a bare number", () => {
    // FAILS if a pre-2023 release's "40" or "1" slips in unpadded, which splits one unit into two.
    for (const r of rows()) {
      assert.match(r.agency_number, /^\d{3}$/, JSON.stringify(r));
      assert.match(r.unit_number, /^\d{3}$/, JSON.stringify(r));
    }
  });

  test("one row per fiscal year, agency and unit", () => {
    // FAILS if a unit is counted twice in a year (two releases summed, or padded and unpadded keys).
    const seen = new Set();
    for (const r of rows()) {
      const k = `${r.fiscal_year}|${r.agency_number}|${r.unit_number}`;
      assert.ok(!seen.has(k), `duplicate ${k}`);
      seen.add(k);
    }
  });

  test("the build records the snapshot it read in meta.inputs", () => {
    // FAILS if the index can't say which Open Data snapshot its agency figures came from.
    const db = new Database(DB_PATH, { readonly: true });
    try {
      const inputs = JSON.parse(db.prepare("SELECT value FROM meta WHERE key = 'inputs'").get().value);
      for (const f of [`${SNAP}/releases.csv`, `${SNAP}/by_unit.csv`]) assert.ok(inputs.includes(f), `meta.inputs lacks ${f}`);
    } finally {
      db.close();
    }
  });
});

describe("agency_budget: the year rule, cell by cell", { skip: SKIP }, () => {
  test("every adopted and modified figure equals the snapshot under the year rule", () => {
    // FAILS on any cell that differs by a cent, a row the snapshot doesn't have, or a row it has
    // that the table lacks. A one-year-late table (#274's bug) fails here on thousands of cells.
    const exp = expected();
    const got = new Map(rows().map((r) => [`${r.fiscal_year}|${r.agency_number}|${r.unit_number}`, r]));
    const problems = [];
    for (const [k, e] of exp.cells) {
      const r = got.get(k);
      if (!r) {
        problems.push(`${k}: missing from agency_budget`);
        continue;
      }
      const a = r.adopted == null ? null : Math.round(r.adopted * 100);
      const m = r.modified == null ? null : Math.round(r.modified * 100);
      if (a !== e.adopted) problems.push(`${k} adopted: ${r.adopted}, snapshot ${e.adopted == null ? null : e.adopted / 100}`);
      if (m !== e.modified) problems.push(`${k} modified: ${r.modified}, snapshot ${e.modified == null ? null : e.modified / 100}`);
      if (r.adopted_release !== e.adopted_release) problems.push(`${k} adopted_release: ${r.adopted_release}, want ${e.adopted_release}`);
      if (r.modified_release !== e.modified_release) problems.push(`${k} modified_release: ${r.modified_release}, want ${e.modified_release}`);
    }
    for (const k of got.keys()) if (!exp.cells.has(k)) problems.push(`${k}: in agency_budget, not in the snapshot`);
    assert.deepEqual(problems.slice(0, 25), [], `${problems.length} problem(s)`);
  });

  test("covers every year with a June release, FY2017 through the newest", () => {
    // FAILS if a year is dropped, or FY2016 (in the 2017 release's adopted_budget_amount) leaks in.
    const exp = expected();
    const years = [...new Set(rows().map((r) => r.fiscal_year))].sort((a, b) => a - b);
    assert.deepEqual(years, exp.years);
    assert.equal(years[0], FIRST_YEAR);
  });

  test("the newest year's modified is NULL, never 0, and so is its modified_release", () => {
    // FAILS if "not yet published" is stored as 0, which every sum would then count as a real $0.
    const newest = Math.max(...rows().map((r) => r.fiscal_year));
    for (const r of rows().filter((x) => x.fiscal_year === newest)) {
      assert.equal(r.modified, null, `${r.agency_number}/${r.unit_number}`);
      assert.equal(r.modified_release, null, `${r.agency_number}/${r.unit_number}`);
    }
  });

  test("a unit missing from a year's adopted release has NULL adopted, not 0", () => {
    // FAILS if absence is stored as $0. The old app shows those 936 cells as $0; the new view and
    // the MCP say "not in that year's budget" (#288 lists the difference).
    for (const r of rows()) if (r.adopted_release == null) assert.equal(r.adopted, null, JSON.stringify(r));
  });

  test("each release is the June release of its tag", () => {
    // FAILS if a Preliminary (January) or Executive (April/May) release is used: each one restates
    // the whole budget, so mixing them double-counts.
    for (const r of rows()) {
      if (r.adopted_release) assert.match(r.adopted_release, new RegExp(`^${r.fiscal_year - 1}06\\d\\d$`), JSON.stringify(r));
      if (r.modified_release) assert.match(r.modified_release, new RegExp(`^${r.fiscal_year}06\\d\\d$`), JSON.stringify(r));
    }
  });
});

describe("agency_budget: OMB's printed figures (viz/agencies/data/SCHEMA.md, validation gate)", { skip: SKIP }, () => {
  const sum = (year, col, where = () => true) => rows().filter((r) => r.fiscal_year === year && where(r)).reduce((s, r) => s + Math.round((r[col] ?? 0) * 100), 0) / 100;

  test("citywide FY2026 adopted, gross, is $117,791,473,676 (OMB adopt25/erc6-25.pdf p. 1E)", () => {
    // FAILS if the year rule is off by one (the FY2025 figure, $114,384,991,832, would show), or
    // a release is summed twice.
    assert.equal(sum(2026, "adopted"), 115_907_309_727 + 1_884_163_949);
  });

  test("citywide FY2025 adopted is $114,384,991,832 and FY2025 modified is $123,844,584,236", () => {
    // FAILS if modified comes from the release tagged Y instead of Y+1.
    assert.equal(sum(2025, "adopted"), 114_384_991_832);
    assert.equal(sum(2025, "modified"), 123_844_584_236);
  });

  test("Manhattan CB 1 (agency 341): OMB p. 182E, to the dollar", () => {
    // FAILS if a small agency's units are merged, unpadded or shifted a year.
    const cell = (y, u, col) => sum(y, col, (r) => r.agency_number === "341" && r.unit_number === u);
    assert.equal(cell(2025, "001", "adopted"), 267_484);
    assert.equal(cell(2025, "001", "modified"), 249_484);
    assert.equal(cell(2025, "002", "modified"), 190_939);
    assert.equal(cell(2026, "001", "adopted"), 275_060);
    assert.equal(cell(2026, "002", "adopted"), 27_245);
  });

  test("DOE (040) unit 401 FY2017 adopted is $6,164,926,031, not the FY2016 figure (#274)", () => {
    // FAILS with $5,844,620,680 if adopted_budget_amount of the release tagged Y is used for FY Y.
    const r = rows().find((x) => x.fiscal_year === 2017 && x.agency_number === "040" && x.unit_number === "401");
    assert.ok(r, "DOE 040/401 FY2017 row");
    assert.equal(r.adopted, 6_164_926_031);
  });

  test("all 59 community boards are agencies in every year", () => {
    // FAILS if a board's agency number is dropped or unpadded.
    const boards = [...Array.from({ length: 12 }, (_, i) => 341 + i), ...Array.from({ length: 12 }, (_, i) => 381 + i),
      ...Array.from({ length: 18 }, (_, i) => 471 + i), ...Array.from({ length: 14 }, (_, i) => 431 + i), 491, 492, 493].map(String);
    assert.equal(boards.length, 59);
    const have = new Set(rows().map((r) => r.agency_number));
    for (const b of boards) assert.ok(have.has(b), `board ${b}`);
  });
});

describe("agency_budget: one year rule across the index", { skip: SKIP }, () => {
  test("every T&C unit amount in data/open_data/crosswalk_terms_unit.csv equals agency_budget's adopted figure", () => {
    // FAILS if the T&C crosswalk (#274's fix, code/build_open_data_crosswalk.py) and the agency
    // table read the same Open Data field for different years. Read from the committed CSV: the
    // npm index loads T&C crosswalk rows only with the T&C PDF family. Two snapshots of mwzb-yiwb
    // feed them (2026-10-21 and 2026-11-09); a real restatement by the City between the two would
    // show here and must be disclosed, not smoothed.
    const xw = readCsv("data/open_data/crosswalk_terms_unit.csv").filter((x) => x.family === "terms_unit" && x.portal_value !== "");
    assert.ok(xw.length > 0, "the T&C crosswalk has amounts");
    const db = new Database(DB_PATH, { readonly: true });
    try {
      const ab = db.prepare("SELECT adopted FROM agency_budget WHERE fiscal_year = ? AND agency_number = ? AND unit_number = ?");
      const problems = [];
      for (const x of xw) {
        const [, , agency, unit] = x.record_key.split("|");
        const r = ab.get(Number(x.fiscal_year), agency, unit);
        if (!r) problems.push(`${x.record_key}: no agency_budget row`);
        else if (Math.round(Number(x.portal_value) * 100) !== Math.round((r.adopted ?? NaN) * 100)) problems.push(`${x.record_key}: crosswalk ${x.portal_value}, agency_budget ${r.adopted}`);
      }
      assert.deepEqual(problems.slice(0, 25), [], `${problems.length} problem(s)`);
    } finally {
      db.close();
    }
  });
});
