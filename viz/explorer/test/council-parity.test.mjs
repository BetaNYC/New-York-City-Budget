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
