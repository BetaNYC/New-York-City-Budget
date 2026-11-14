/**
 * The third engine (#301): every query that carries a `json` form answers the same from the
 * Council JSON files (data/council/) as its SQL does from the Parquet in DuckDB, row for row and
 * in the same order. Needs `npm run data`.
 *
 *   node --test test/council-parity.test.mjs
 *
 * A text filter is compared here too once a view's json form takes one (the JS fold against
 * DuckDB's lower(); a character they disagree on fails here). Each test says what would make it FAIL.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import { DuckDBInstance } from "@duckdb/node-api";

import * as Q from "../src/query/sql.js";
import * as P from "../src/query/pdf.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(resolve(HERE, ".."), "public", "data");
if (!existsSync(join(DATA, "manifest.json"))) throw new Error("council-parity: public/data/manifest.json is missing. Run `npm run data` first.");
const MANIFEST = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));

let instance;
let conn;
before(async () => {
  instance = await DuckDBInstance.create(":memory:");
  conn = await instance.connect();
  for (const f of Object.keys(MANIFEST.files)) {
    const t = f.slice(0, -".parquet".length);
    await conn.run(`CREATE TABLE "${t}" AS SELECT * FROM read_parquet('${join(DATA, f).replaceAll("'", "''")}')`);
  }
});
after(() => {
  conn?.closeSync();
  instance?.closeSync();
});

/** A value as both engines should agree on it: BIGINT as Number, money to the cent. */
const norm = (v) => (typeof v === "bigint" ? Number(v) : typeof v === "number" && !Number.isInteger(v) ? Math.round(v * 100) / 100 : v);
const normRows = (rows) => rows.map((r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, norm(v)])));

async function both(q, label) {
  assert.ok(q.json, `${label}: no json form`);
  const sql = normRows((await conn.runAndReadAll(q.sql, q.params ?? [])).getRowObjectsJS());
  const files = q.json.files.map((p) => JSON.parse(readFileSync(join(DATA, p), "utf8")));
  const json = normRows(q.json.run(files));
  assert.deepEqual(json, sql, label);
  return sql.length;
}

describe("lookups and the Years view", () => {
  test("every lookup and both Years queries", async () => {
    // FAILS if years.json's lookups or totals differ from the tables.
    for (const [name, q] of Object.entries(Q.LOOKUP_QUERIES)) assert.ok((await both(q, name)) > 0, name);
    assert.ok((await both(P.pdfYearsQuery(), "pdfYearsQuery")) > 0);
    assert.ok((await both(Q.YEAR_DISCLOSURE_QUERY, "YEAR_DISCLOSURE_QUERY")) > 0);
    assert.ok((await both(Q.YEAR_CAPITAL_QUERY, "YEAR_CAPITAL_QUERY")) > 0);
  });
});

describe("Council vs OMB", () => {
  const years = MANIFEST.index_counts ? JSON.parse(readFileSync(join(DATA, "council", "years.json"), "utf8")).omb_years : [];
  const cases = [
    [{}, 0],
    [{}, 1],
    [{}, 40],
    ...Q.OMB_VERDICTS.map((verdict) => [{ verdict }, 0]),
    ...years.map((report_year) => [{ report_year }, 0]),
    [{ report_year: years.at(-1), verdict: "differ" }, 0],
    [{ budget_line: "HL DN164" }, 0],
    [{ budget_line: "hl-dn164" }, 0],
    [{ budget_line: "PD018" }, 0],
    [{ budget_line: "  " }, 0],
    [{ report_year: 1999 }, 0],
  ];
  test("rows and counts, for every filter case", async () => {
    // FAILS if the JS filter, order or paging differs from the SQL for any case.
    let rows = 0;
    for (const [f, page] of cases) {
      rows += await both(Q.ombRowsQuery(f, page), `ombRowsQuery ${JSON.stringify(f)} page ${page}`);
      await both(Q.ombCountsQuery(f), `ombCountsQuery ${JSON.stringify(f)}`);
    }
    assert.ok(rows > 500, `${rows} rows compared`);
  });
});

describe("Expense awards: one year's file, and the unfiltered list", () => {
  const yj = JSON.parse(readFileSync(join(DATA, "council", "years.json"), "utf8"));
  const loaded = yj.disclosure_years.filter((y) => y.loaded).map((y) => y.fiscal_year);
  const newest = Math.max(...loaded);
  // The parity test's section 3 filters, each within one year, plus the text cases the fold must
  // agree on: accents, an apostrophe, punctuation, upper case, a term that folds to nothing.
  const within = [
    {},
    { status: "pending" },
    { status: "other" },
    { legal_name: "jewish emigre" },
    { legal_name: "Émigré" },
    { legal_name: "Women's" },
    { legal_name: "WOMEN’S" },
    { legal_name: "y.m.c.a" },
    { legal_name: "---" },
    { council_member: "rivera" },
    { agency: "youth", min_amount: 10000, max_amount: 50000 },
    { ein: "13-2612524" },
    { program_name: "senior", source: "local" },
    { legal_name: "zzzz-no-such-grantee" },
  ];

  test("every loaded year, unfiltered: totals, flags and the first two pages", async () => {
    // FAILS if a year's file answers its list differently from DuckDB.
    for (const fiscal_year of loaded) {
      const f = { fiscal_year };
      await both(Q.disclosureTotalsQuery(f), `totals FY${fiscal_year}`);
      await both(Q.disclosureFlagsQuery(f), `flags FY${fiscal_year}`);
      for (const page of [0, 1]) await both(Q.disclosureRowsQuery(f, page), `rows FY${fiscal_year} page ${page}`);
    }
  });

  test("every filter, in the newest year and two older ones", async () => {
    // FAILS if a JS filter (the fold against DuckDB's lower(), an EIN, an amount range) differs.
    let rows = 0;
    for (const fiscal_year of [newest, 2024, 2012].filter((y) => loaded.includes(y))) {
      for (const g of within) {
        const f = { ...g, fiscal_year };
        await both(Q.disclosureTotalsQuery(f), `totals ${JSON.stringify(f)}`);
        await both(Q.disclosureFlagsQuery(f), `flags ${JSON.stringify(f)}`);
        rows += await both(Q.disclosureRowsQuery(f, 0), `rows ${JSON.stringify(f)}`);
      }
    }
    assert.ok(rows > 500, `${rows} rows compared`);
  });

  test("all years, no filter: awards/index.json's first page, totals and flags", async () => {
    // FAILS if the landing page over all years differs from DuckDB; or a later page or any filter
    // over all years claims a json form (they need the engine).
    await both(Q.disclosureRowsQuery({}, 0), "rows all years");
    await both(Q.disclosureTotalsQuery({}), "totals all years");
    await both(Q.disclosureFlagsQuery({}), "flags all years");
    assert.equal(Q.disclosureRowsQuery({}, 1).json, undefined);
    assert.equal(Q.disclosureTotalsQuery({ legal_name: "food" }).json, undefined);
    assert.equal(Q.disclosureRowsQuery({ fiscal_year: newest, sc_side: "matched" }, 0).json, undefined);
  });

  test("one award: the row and its year's source, for rows across every year", async () => {
    // FAILS if an award read from its year's file differs from DuckDB's join, in any column.
    let n = 0;
    for (const fiscal_year of loaded) {
      const file = JSON.parse(readFileSync(join(DATA, "council", "awards", `fy${fiscal_year}.json`), "utf8"));
      const j = file.columns.indexOf("source_row");
      const rows = file.rows.map((r) => r[j]);
      for (const row of [rows[0], rows[Math.floor(rows.length / 2)], rows.at(-1)]) n += await both(Q.awardQuery(fiscal_year, row), `award FY${fiscal_year} row ${row}`);
    }
    assert.equal(n, loaded.length * 3);
  });

  test("an award that does not exist: no row from either engine", async () => {
    // FAILS if a missing row or a year that is not loaded is an error, or finds something.
    const unloaded = yj.disclosure_years.find((y) => !y.loaded)?.fiscal_year ?? 2010;
    for (const [fy, row] of [[newest, 99_999_999], [unloaded, 2]]) {
      const q = Q.awardQuery(fy, row);
      const sql = (await conn.runAndReadAll(q.sql, q.params)).getRowObjectsJS();
      const files = q.json.files.map((p) => (existsSync(join(DATA, p)) ? JSON.parse(readFileSync(join(DATA, p), "utf8")) : null));
      assert.deepEqual(q.json.run(files), []);
      assert.deepEqual(sql, []);
    }
  });
});
