/**
 * Agency budgets parity (#270): the explorer's new view equals the old /agencies/ app on every
 * row and every year, and its data equals the MCP's index.
 *
 *   node --test test/agency-parity.test.mjs        (after `npm run data`)
 *
 * PENDING #284 (sections 1-2) and #286 (section 3): each section is skipped, with that reason,
 * until what it reads exists: public/data/agency_budget.parquet, then src/query/agency.js. They
 * run unchanged once it does. #288 retires the old app only when all three pass with no skips.
 *
 *   1. The Parquet equals budget.db's agency_budget, every row and column, in order.
 *   2. The Parquet equals viz/agencies/data/nyc_budget.csv (what /agencies/ loads), on every unit
 *      x fiscal year x adopted/modified: 764 units x FY2017-FY2027 x 2 = 16,808 cells today.
 *      Two differences are by design and are COUNTED here, never hidden:
 *        - "absent": the old CSV writes 0 where a unit is not in that year's release; the new
 *          data has NULL there ("not in this year's budget"). 936 adopted cells as of 2026-11-09.
 *        - agency 866 appears under two names in the old app (DEPARTMENT OF CONSUMER AFFAIRS and
 *          DEPT OF CONSUMER & WORKER PROTECTION), because it names each unit by the newest release
 *          that unit is in. The new view groups by agency number.
 *   3. The explorer's own queries (src/query/agency.js) on the Parquet answer what the old app
 *      shows: citywide total per year, every agency's total per year, and an agency's units.
 *
 * Read with @duckdb/node-api (the Parquet, and the CSV with every column as text) and
 * better-sqlite3 (budget.db). Dollars are compared in whole cents.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import Database from "better-sqlite3";
import { DuckDBInstance } from "@duckdb/node-api";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..");
const REPO = resolve(APP, "..", "..");
const DATA = join(APP, "public", "data");
const PARQUET = join(DATA, "agency_budget.parquet");
const CSV = join(REPO, "viz", "agencies", "data", "nyc_budget.csv");
const QUERY_MODULE = join(APP, "src", "query", "agency.js");

const MANIFEST = existsSync(join(DATA, "manifest.json")) ? JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8")) : null;
const DB_PATH = join(REPO, MANIFEST?.index ?? "mcp/data/budget.db");

const DATA_PENDING = !MANIFEST
  ? "PENDING #284: public/data/manifest.json is missing (run `npm run data`)"
  : !existsSync(PARQUET)
    ? "PENDING #284: build-data.mjs does not export agency_budget.parquet yet"
    : false;
const QUERY_PENDING = DATA_PENDING || (existsSync(QUERY_MODULE) ? false : "PENDING #286: src/query/agency.js does not exist yet");

const COLUMNS = ["fiscal_year", "agency_number", "agency_name", "unit_number", "unit_name", "adopted", "modified", "adopted_release", "modified_release"];
const cents = (v) => (v === null || v === undefined || v === "" ? null : Math.round(Number(v) * 100));

let instance;
let conn;
/** Plain JS rows; BIGINT as Number (every value here is a safe integer). */
async function duck(sql, params = []) {
  const reader = await conn.runAndReadAll(sql, params);
  return reader.getRowObjectsJS().map((r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, typeof v === "bigint" ? Number(v) : v])));
}

before(async () => {
  if (DATA_PENDING) return;
  instance = await DuckDBInstance.create(":memory:");
  conn = await instance.connect();
  await conn.run(`CREATE TABLE agency_budget AS SELECT * FROM read_parquet('${PARQUET.replace(/'/g, "''")}')`);
  await conn.run(`CREATE TABLE old_csv AS SELECT * FROM read_csv('${CSV.replace(/'/g, "''")}', header = true, all_varchar = true)`);
});
after(() => {
  conn?.closeSync();
  instance?.closeSync();
});

/** The old CSV, with each row's agency number found from the names in the new data. */
async function oldRows() {
  const csv = await duck("SELECT * FROM old_csv");
  const names = await duck("SELECT DISTINCT agency_name, agency_number FROM agency_budget");
  const byName = new Map();
  for (const n of names) byName.set(n.agency_name, [...new Set([...(byName.get(n.agency_name) ?? []), n.agency_number])]);
  return csv.map((r) => {
    const nums = byName.get(r.Fund) ?? [];
    assert.equal(nums.length, 1, `old agency name ${JSON.stringify(r.Fund)} maps to ${nums.length} agency numbers`);
    return { ...r, agency_number: nums[0] };
  });
}
const yearsOf = (csvRow) => Object.keys(csvRow).filter((k) => /^Adopted \d{4}$/.test(k)).map((k) => Number(k.slice(8)));

describe("1. agency_budget.parquet equals budget.db, every row and column", { skip: DATA_PENDING }, () => {
  test("same columns, same rows, same values, same order", async () => {
    // FAILS if the export coerces a type (a NULL to 0, "040" to 40), drops or reorders a row.
    const sqlite = new Database(DB_PATH, { readonly: true, fileMustExist: true });
    try {
      const want = sqlite.prepare("SELECT * FROM agency_budget ORDER BY rowid").all();
      const got = await duck("SELECT * FROM agency_budget");
      assert.deepEqual(Object.keys(got[0] ?? {}), COLUMNS);
      assert.equal(got.length, want.length, "row count");
      for (let i = 0; i < want.length; i++) {
        for (const c of COLUMNS) {
          const a = want[i][c];
          const b = got[i][c];
          if (c === "adopted" || c === "modified") assert.equal(cents(b), cents(a), `row ${i + 1} ${c}`);
          else assert.equal(b, a, `row ${i + 1} ${c}`);
        }
      }
    } finally {
      sqlite.close();
    }
  });

  test("the manifest lists agency_budget.parquet with its row count", () => {
    // FAILS if the file ships without a manifest entry (no cache-busting hash, no lazy-load size).
    assert.ok(MANIFEST.files["agency_budget.parquet"], "manifest.files has agency_budget.parquet");
    assert.ok(MANIFEST.files["agency_budget.parquet"].rows > 0);
  });
});

describe("2. the new data equals /agencies/ (viz/agencies/data/nyc_budget.csv), every cell", { skip: DATA_PENDING }, () => {
  test("every unit, year, adopted and modified: equal, or a counted, by-design difference", async () => {
    // (DuckDB reads a blank CSV cell as NULL.)
    // FAILS on any cell that differs by a cent, any CSV unit the new data lacks, or any unit the new
    // data has that the old app doesn't show.
    const old = await oldRows();
    const rows = await duck("SELECT * FROM agency_budget");
    const by = new Map(rows.map((r) => [`${r.fiscal_year}|${r.agency_number}|${r.unit_number}`, r]));
    const newest = Math.max(...rows.map((r) => r.fiscal_year));
    const problems = [];
    let compared = 0;
    let absentAdopted = 0;
    let absentModified = 0;
    for (const r of old) {
      for (const y of yearsOf(r)) {
        const n = by.get(`${y}|${r.agency_number}|${r["Department ID"]}`);
        for (const [col, field] of [[`Adopted ${y}`, "adopted"], [`Modified ${y}`, "modified"]]) {
          compared++;
          const was = r[col];
          const now = n ? n[field] : null;
          if (field === "modified" && y === newest) {
            if ((was !== "" && was !== null) || now !== null) problems.push(`${r.Fund} ${r["Department ID"]} ${col}: old ${JSON.stringify(was)}, new ${now} (want blank / NULL)`);
          } else if (now === null) {
            // By design: absent in the release. The old app wrote 0 there.
            if (cents(was) !== 0) problems.push(`${r.Fund} ${r["Department ID"]} ${col}: old ${was}, new NULL`);
            else if (field === "adopted") absentAdopted++;
            else absentModified++;
          } else if (cents(was) !== cents(now)) {
            problems.push(`${r.Fund} ${r["Department ID"]} ${col}: old ${was}, new ${now}`);
          }
        }
      }
    }
    const oldKeys = new Set(old.map((r) => `${r.agency_number}|${r["Department ID"]}`));
    for (const r of rows) if (!oldKeys.has(`${r.agency_number}|${r.unit_number}`)) problems.push(`new unit ${r.agency_number}/${r.unit_number} is not on /agencies/`);
    assert.deepEqual(problems.slice(0, 25), [], `${problems.length} problem(s)`);
    assert.equal(old.length, 764, "units on /agencies/ (2026-11-09 data)");
    assert.equal(compared, 764 * yearsOf(old[0]).length * 2);
    // The by-design difference, counted so a change in it is seen. Update with the data, in a PR
    // that says why (DATA-ANOMALIES §57).
    assert.equal(absentAdopted, 936, "adopted cells the old app shows as $0 that are not in that year's budget");
    console.log(`agency parity: ${compared} cells compared; ${absentAdopted} adopted and ${absentModified} modified cells are "not in this year's budget" (old app: $0)`);
  });

  test("each unit's agency and unit names equal the old app's (the newest release it is in)", async () => {
    // FAILS if the new view names a unit differently from /agencies/ without a reason.
    const old = await oldRows();
    const latest = await duck(`SELECT agency_number, unit_number, agency_name, unit_name FROM agency_budget a
      WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM agency_budget b WHERE b.agency_number = a.agency_number AND b.unit_number = a.unit_number)`);
    const by = new Map(latest.map((r) => [`${r.agency_number}|${r.unit_number}`, r]));
    for (const r of old) {
      const n = by.get(`${r.agency_number}|${r["Department ID"]}`);
      assert.ok(n, `${r.Fund} ${r["Department ID"]}`);
      assert.equal(n.agency_name, r.Fund, `${r.agency_number}/${r["Department ID"]} agency name`);
      assert.equal(n.unit_name, r.Department, `${r.agency_number}/${r["Department ID"]} unit name`);
    }
  });

  test("agency 866 is the one agency the old app splits under two names, and the split adds up", async () => {
    // FAILS if another agency starts to split (a rename the new view must explain), or the two old
    // totals don't add up to the new one.
    const old = await oldRows();
    const namesPer = new Map();
    for (const r of old) namesPer.set(r.agency_number, new Set([...(namesPer.get(r.agency_number) ?? []), r.Fund]));
    const split = [...namesPer].filter(([, s]) => s.size > 1).map(([a]) => a);
    assert.deepEqual(split, ["866"]);
    for (const y of yearsOf(old[0])) {
      const oldSum = old.filter((r) => r.agency_number === "866").reduce((s, r) => s + (cents(r[`Adopted ${y}`]) ?? 0), 0);
      const [{ v }] = await duck("SELECT COALESCE(SUM(adopted), 0) AS v FROM agency_budget WHERE agency_number = '866' AND fiscal_year = ?", [y]);
      assert.equal(cents(v), oldSum, `866 FY${y}`);
    }
  });
});

describe("3. the explorer's queries answer what /agencies/ shows", { skip: QUERY_PENDING }, () => {
  let Q;
  before(async () => {
    if (!QUERY_PENDING) Q = await import(QUERY_MODULE);
  });
  const run = (q) => duck(q.sql, q.params ?? []);

  test("citywide adopted and modified, every year, equal the old app's top line", async () => {
    // FAILS if a year is mis-summed, or the newest year's modified shows as 0 instead of NULL.
    const old = await oldRows();
    const got = await run(Q.agencyYearsQuery({ abag: "", abunit: "" }));
    const years = yearsOf(old[0]);
    assert.deepEqual(got.map((r) => r.fiscal_year), years);
    const newest = years.at(-1);
    for (const g of got) {
      const a = old.reduce((s, r) => s + (cents(r[`Adopted ${g.fiscal_year}`]) ?? 0), 0);
      assert.equal(cents(g.adopted), a, `FY${g.fiscal_year} adopted`);
      if (g.fiscal_year === newest) assert.equal(g.modified, null, `FY${newest} modified is not published`);
      else assert.equal(cents(g.modified), old.reduce((s, r) => s + (cents(r[`Modified ${g.fiscal_year}`]) ?? 0), 0), `FY${g.fiscal_year} modified`);
    }
  });

  test("every agency's total, every year, equals the old app's (866: both old names together)", async () => {
    // FAILS if an agency is missing from a year's list, or its total differs from /agencies/.
    const old = await oldRows();
    for (const y of yearsOf(old[0])) {
      const want = new Map();
      for (const r of old) {
        const w = want.get(r.agency_number) ?? { adopted: 0, modified: 0 };
        w.adopted += cents(r[`Adopted ${y}`]) ?? 0;
        w.modified += cents(r[`Modified ${y}`]) ?? 0;
        want.set(r.agency_number, w);
      }
      const got = new Map((await run(Q.agencyListQuery({ abfy: y }))).map((g) => [g.agency_number, g]));
      for (const [a, w] of want) {
        const g = got.get(a);
        if (!g) {
          // An agency with no unit in the year's releases: the old app lists it at $0.
          assert.equal(w.adopted + w.modified, 0, `FY${y} agency ${a} missing from the new list but nonzero on /agencies/`);
          continue;
        }
        assert.equal(cents(g.adopted) ?? 0, w.adopted, `FY${y} ${a} adopted`);
        assert.equal(cents(g.modified) ?? 0, w.modified, `FY${y} ${a} modified`);
      }
    }
  });

  test("an agency's units (NYPD 056 and Manhattan CB 1, 341), every year, equal the old app's rows", async () => {
    // FAILS if a unit is dropped, merged with another, or shows another year's figure.
    const old = await oldRows();
    for (const abag of ["056", "341"]) {
      for (const y of yearsOf(old[0])) {
        const want = old.filter((r) => r.agency_number === abag);
        const got = new Map((await run(Q.agencyUnitsQuery({ abfy: y, abag }))).map((g) => [g.unit_number, g]));
        for (const r of want) {
          const g = got.get(r["Department ID"]);
          const wa = cents(r[`Adopted ${y}`]);
          if (!g) {
            assert.equal(wa, 0, `FY${y} ${abag}/${r["Department ID"]} missing but nonzero`);
            continue;
          }
          assert.equal(cents(g.adopted) ?? 0, wa, `FY${y} ${abag}/${r["Department ID"]} adopted`);
        }
      }
    }
  });
});
