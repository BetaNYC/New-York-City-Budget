/**
 * Agency budgets JSON parity (#299): the files the agency view reads (public/data/agency_budget/,
 * written by scripts/agency-json.mjs) give the same answer as the explorer's SQL
 * (src/query/agency.js) over agency_budget.parquet, on every cell.
 *
 *   node --test test/agency-json.test.mjs        (after `npm run data`)
 *
 * Every fiscal year x every agency (the list), every agency's units in every year, every
 * agency's and every unit's years, and the citywide totals. Dollars in whole cents; NULL must
 * stay null on both sides ("Not in this year's budget", "Not yet published"), never 0.
 * The build checks the same files against budget.db with its own SQL (verifyAgencyJson); this is
 * the second, independent check, through the queries the old view ran.
 */
import assert from "node:assert/strict";
import { cpSync, existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import Database from "better-sqlite3";
import { DuckDBInstance } from "@duckdb/node-api";

import { verifyAgencyJson } from "../scripts/agency-json.mjs";

import * as J from "../src/agency/data.js";
import * as Q from "../src/query/agency.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(resolve(HERE, ".."), "public", "data");
const PARQUET = join(DATA, "agency_budget.parquet");
const PENDING = !existsSync(join(DATA, J.citywidePath())) ? "run `npm run data` first: public/data/agency_budget/ is missing" : false;

const read = (p) => JSON.parse(readFileSync(join(DATA, p), "utf8"));
const cents = (v) => (v === null || v === undefined ? null : Math.round(Number(v) * 100));

let instance;
let conn;
async function run({ sql, params }) {
  const reader = await conn.runAndReadAll(sql, params);
  return reader.getRowObjectsJS().map((r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, typeof v === "bigint" ? Number(v) : v])));
}

before(async () => {
  if (PENDING) return;
  instance = await DuckDBInstance.create(":memory:");
  conn = await instance.connect();
  await conn.run(`CREATE TABLE agency_budget AS SELECT * FROM read_parquet('${PARQUET.replace(/'/g, "''")}')`);
});
after(() => {
  conn?.closeSync();
  instance?.closeSync();
});

/** Compare two row lists field by field; returns the differences and the cell count. */
function compare(label, got, want, fields, money) {
  const diffs = [];
  let cells = 0;
  if (got.length !== want.length) diffs.push(`${label}: ${got.length} rows in JSON, ${want.length} in SQL`);
  want.forEach((w, i) => {
    const g = got[i] ?? {};
    for (const f of fields) {
      cells++;
      const a = money.includes(f) ? cents(g[f]) : g[f] ?? null;
      const b = money.includes(f) ? cents(w[f]) : w[f] ?? null;
      if (a !== b) diffs.push(`${label} row ${i} ${f}: JSON ${JSON.stringify(g[f])}, SQL ${JSON.stringify(w[f])}`);
    }
  });
  return { diffs, cells };
}

const TOTALS = ["adopted", "modified", "units", "units_no_adopted", "units_no_modified"];
const MONEY = ["adopted", "modified"];

describe("agency JSON equals agency_budget through the explorer's SQL (#299)", { skip: PENDING }, () => {
  test("every cell: citywide, every agency list, every agency's units and years, every unit's years", async () => {
    const city = read(J.citywidePath());
    const agencies = read(J.agenciesPath());
    const all = { diffs: [], cells: 0 };
    const add = (r) => {
      all.diffs.push(...r.diffs);
      all.cells += r.cells;
    };

    const years = await run(Q.agencyFiscalYearsQuery());
    add(compare("fiscal years", J.fiscalYears(city), years.map((y) => ({ ...y, has_modified: Boolean(y.has_modified) })), ["fiscal_year", "has_modified"], []));
    add(compare("citywide", J.cityByYear(city), await run(Q.agencyYearsQuery({ abag: "", abunit: "" })), ["fiscal_year", ...TOTALS, "adopted_release", "modified_release"], MONEY));

    for (const { fiscal_year: fy } of years) {
      add(compare(`list FY${fy}`, J.agencyList(agencies, fy), await run(Q.agencyListQuery({ abfy: fy })), ["agency_number", "agency_name", ...TOTALS], MONEY));
    }
    for (const a of agencies.agencies) {
      const file = read(J.agencyPath(a.agency_number));
      add(compare(`agency ${a.agency_number} by year`, J.agencyByYear(file), await run(Q.agencyYearsQuery({ abag: a.agency_number, abunit: "" })), ["fiscal_year", "agency_name", ...TOTALS, "adopted_release", "modified_release"], MONEY));
      for (const { fiscal_year: fy } of years) {
        add(compare(`agency ${a.agency_number} FY${fy} units`, J.agencyUnits(file, fy), await run(Q.agencyUnitsQuery({ abfy: fy, abag: a.agency_number })), ["unit_number", "unit_name", "agency_name", "adopted", "modified", "adopted_release", "modified_release"], MONEY));
      }
      for (const u of file.units) {
        add(compare(`unit ${a.agency_number}/${u.unit_number}`, J.unitByYear(file, u.unit_number), await run(Q.agencyYearsQuery({ abag: a.agency_number, abunit: u.unit_number })), ["fiscal_year", "agency_name", "unit_name", "adopted", "modified", "adopted_release", "modified_release"], MONEY));
      }
    }
    assert.deepEqual(all.diffs.slice(0, 20), [], `${all.diffs.length} differences in ${all.cells} cells`);
    assert.ok(all.cells > 100_000, `only ${all.cells} cells compared`);
    console.log(`agency JSON parity: ${all.cells} cells, 0 differences`);
  });

  test("a missing figure stays null in the JSON, never 0", async () => {
    // FAILS if the writer turns NULL into 0 (the old CSV's habit; the view says words instead).
    const [{ n }] = await run({ sql: "SELECT COUNT(*) AS n FROM agency_budget WHERE adopted IS NULL", params: [] });
    let nulls = 0;
    for (const a of read(J.agenciesPath()).agencies) {
      for (const u of read(J.agencyPath(a.agency_number)).units) nulls += u.years.filter((y) => y.adopted === null).length;
    }
    assert.equal(nulls, n);
    const city = read(J.citywidePath());
    assert.equal(city.years.at(-1).modified, null, "the newest year's modified budget is not published yet");
  });

  test("the build's own check catches a changed figure (so the build fails)", () => {
    // FAILS if verifyAgencyJson (build-data.mjs stops on any difference) misses a one-cent change.
    const m = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
    const db = new Database(join(resolve(HERE, "..", "..", ".."), m.index), { readonly: true, fileMustExist: true });
    try {
      assert.deepEqual(verifyAgencyJson(db, DATA).diffs, []);
      const copy = mkdtempSync(join(tmpdir(), "agency-json-"));
      cpSync(join(DATA, J.AGENCY_JSON_DIR), join(copy, J.AGENCY_JSON_DIR), { recursive: true });
      const p = join(copy, J.agencyPath("056"));
      const f = JSON.parse(readFileSync(p, "utf8"));
      f.units[0].years[0].adopted += 0.01;
      writeFileSync(p, JSON.stringify(f));
      const { diffs } = verifyAgencyJson(db, copy);
      assert.ok(diffs.length >= 1 && diffs.some((d) => d.includes("agency 056")), diffs.join("\n"));
    } finally {
      db.close();
    }
  });

  test("citywide totals equal the old /agencies/ app's top line, every year (#300)", () => {
    // The old app summed viz/agencies/data/nyc_budget.csv's columns (0 where a unit is absent, so
    // the sums agree); its newest Modified column is blank, which the view says is not published.
    const csv = readFileSync(join(resolve(HERE, "..", "..", ".."), "viz", "agencies", "data", "nyc_budget.csv"), "utf8").trim().split(/\r?\n/);
    const split = (line) => [...line.matchAll(/("(?:[^"]|"")*"|[^,]*)(,|$)/g)].map((m) => m[1].replace(/^"|"$/g, "").replace(/""/g, '"')).slice(0, -1);
    const head = split(csv[0]);
    const sums = new Map();
    for (const line of csv.slice(1)) {
      split(line).forEach((v, i) => {
        if (!/^(Adopted|Modified) \d{4}$/.test(head[i])) return;
        const cur = sums.get(head[i]) ?? null;
        sums.set(head[i], v === "" ? cur : (cur ?? 0) + Math.round(Number(v) * 100));
      });
    }
    const diffs = [];
    let cells = 0;
    for (const y of read(J.citywidePath()).years) {
      for (const [kind, col] of [["adopted", `Adopted ${y.fiscal_year}`], ["modified", `Modified ${y.fiscal_year}`]]) {
        cells++;
        if (cents(y[kind]) !== (sums.get(col) ?? null)) diffs.push(`FY${y.fiscal_year} ${kind}: JSON ${y[kind]}, old app ${sums.get(col)}`);
      }
    }
    assert.deepEqual(diffs, []);
    assert.equal(cells, 22);
    // The figures Noel's QA quoted from the old app (FY2026).
    const fy26 = read(J.citywidePath()).years.find((y) => y.fiscal_year === 2026);
    assert.equal(fy26.adopted, 117791473676);
    assert.equal(fy26.modified, 129228819136);
  });

  test("the manifest records the JSON build", () => {
    const m = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
    assert.equal(m.agency_json.files, read(J.agenciesPath()).agencies.length + 2);
    assert.equal(read(J.citywidePath()).generated_at, m.generated_at);
  });
});
