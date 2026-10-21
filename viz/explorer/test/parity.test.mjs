/**
 * Parity: the explorer's Parquet files hold exactly what the MCP's budget.db holds, and the
 * explorer's queries answer exactly what the MCP's tools answer.
 *
 *   node --test test/parity.test.mjs        (after `npm run data`)
 *
 * Three layers, each of which would catch a different break:
 *   1. Per fiscal year: row counts and dollar totals by status (disclosure), by report year and
 *      amount kind (capital), verdict counts and dollar sums (Council vs OMB) — the figures the
 *      site shows. A year dropped, duplicated or mis-summed fails here with the year named.
 *   2. Every row, every column, in order: a value changed in the copy (a type coerced, a NULL
 *      turned into "" or 0, text re-encoded) fails here with the table, row and column named.
 *   3. The same filters through the MCP (mcp/dist/db.js) and through src/query/sql.js on the
 *      Parquet: matched count, totals by status/kind and the first page of rows must agree.
 *
 * 6. Whether each record is on NYC Open Data (open_data_*): per family, dataset, year and status,
 *    and the coverage strip's numbers. Layer 2 covers every row.
 *
 * 4. The reviewed PDF tables (pdf_*), per family, fiscal year and status: rows, and the dollar
 *    sums where the table has amounts. Layer 2 also covers them row by row. The index compared is
 *    the one manifest.json names: mcp/data/budget.db, or .cache/budget-reviewed.db for a build
 *    made with --include-reviewed, whose manifest must then say include_reviewed.
 *
 * Reads budget.db with better-sqlite3 (read-only) and the Parquet with @duckdb/node-api.
 * Amounts are compared to within half a cent: the two engines may add the same doubles in a
 * different order. Integers and text are compared exactly.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import Database from "better-sqlite3";
import { DuckDBInstance } from "@duckdb/node-api";

import * as Q from "../src/query/sql.js";
import * as C from "../src/compare/queries.js";
import { PDF_FAMILIES, PDF_TABLES } from "../../../mcp/scripts/pdf-families.mjs";
import { OPEN_DATA_TABLES } from "../../../mcp/scripts/open-data.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..");
const REPO = resolve(APP, "..", "..");
const DATA = join(APP, "public", "data");
if (!existsSync(join(DATA, "manifest.json"))) throw new Error("parity: public/data/manifest.json is missing. Run `npm run data` first.");
const MANIFEST = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
const DB_PATH = join(REPO, MANIFEST.index ?? "mcp/data/budget.db");
const TABLES = ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta",
  ...PDF_TABLES, ...OPEN_DATA_TABLES];
const CENT = 0.005;

for (const f of [DB_PATH, ...TABLES.map((t) => join(DATA, `${t}.parquet`)), join(DATA, "manifest.json")]) {
  if (!existsSync(f)) throw new Error(`parity: ${f} is missing. Run \`npm run data\` first.`);
}

let sqlite;
let instance;
let conn;
let mcp;

/** Plain JS rows from DuckDB, with BIGINT returned as Number (all values here are safe integers). */
async function duck(sql, params = []) {
  const reader = await conn.runAndReadAll(sql, params);
  return reader.getRowObjectsJS().map((r) =>
    Object.fromEntries(
      Object.entries(r).map(([k, v]) => {
        if (typeof v === "bigint") {
          assert.ok(v <= BigInt(Number.MAX_SAFE_INTEGER) && v >= BigInt(Number.MIN_SAFE_INTEGER), `${k}: ${v} unsafe`);
          return [k, Number(v)];
        }
        return [k, v];
      })
    )
  );
}

const near = (a, b, msg) => assert.ok(Math.abs(Number(a) - Number(b)) < CENT, `${msg}: ${a} vs ${b}`);

before(async () => {
  sqlite = new Database(DB_PATH, { readonly: true, fileMustExist: true });
  instance = await DuckDBInstance.create(":memory:");
  conn = await instance.connect();
  for (const t of TABLES) {
    const p = join(DATA, `${t}.parquet`).replace(/'/g, "''");
    await conn.run(`CREATE TABLE "${t}" AS SELECT * FROM read_parquet('${p}')`);
  }
  mcp = await import("../../../mcp/dist/db.js");
});

after(() => {
  conn?.closeSync();
  instance?.closeSync();
  sqlite?.close();
});

describe("1. per-year counts and dollar totals", () => {
  test("disclosure: rows and amount per fiscal year and status_norm", async () => {
    const q = "SELECT fiscal_year, status_norm, COUNT(*) AS n, SUM(amount) AS amount FROM disclosure GROUP BY 1, 2 ORDER BY 1, 2";
    const a = sqlite.prepare(q).all();
    const b = await duck(q);
    assert.equal(b.length, a.length, "same (year, status) groups");
    a.forEach((r, i) => {
      const at = `FY${r.fiscal_year} ${r.status_norm}`;
      assert.equal(b[i].fiscal_year, r.fiscal_year, at);
      assert.equal(b[i].status_norm, r.status_norm, at);
      assert.equal(b[i].n, r.n, `${at} rows`);
      near(b[i].amount, r.amount, `${at} amount`);
    });
  });

  test("disclosure: every loaded year of disclosure_years has exactly award_rows rows", async () => {
    const years = await duck("SELECT fiscal_year, loaded, award_rows FROM disclosure_years ORDER BY 1");
    const counts = new Map((await duck("SELECT fiscal_year, COUNT(*) AS n FROM disclosure GROUP BY 1")).map((r) => [r.fiscal_year, r.n]));
    for (const y of years) {
      if (y.loaded) assert.equal(counts.get(y.fiscal_year), y.award_rows, `FY${y.fiscal_year}`);
      else assert.equal(counts.get(y.fiscal_year), undefined, `FY${y.fiscal_year} is not loaded and must have no rows`);
    }
  });

  test("capital: rows and amount per report year and amount kind", async () => {
    const q = `SELECT report_year,
                 CASE WHEN amount IS NULL THEN 'unknown' WHEN amount_fy = report_year THEN 'report' ELSE 'out' END AS kind,
                 COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount
               FROM capital_council GROUP BY 1, 2 ORDER BY 1, 2`;
    const a = sqlite.prepare(q).all();
    const b = await duck(q);
    assert.equal(b.length, a.length);
    a.forEach((r, i) => {
      const at = `FY${r.report_year} ${r.kind}`;
      assert.deepEqual([b[i].report_year, b[i].kind, b[i].n], [r.report_year, r.kind, r.n], at);
      near(b[i].amount, r.amount, `${at} amount`);
    });
  });

  test("Council vs OMB: verdict counts and dollar sums per report year", async () => {
    const q = `SELECT report_year, verdict, COUNT(*) AS n, SUM(council_y1) AS c1, SUM(omb_y1) AS o1,
                 SUM(council_y2) AS c2, SUM(omb_y2) AS o2 FROM capital_vs_omb GROUP BY 1, 2 ORDER BY 1, 2`;
    assert.deepEqual(await duck(q), sqlite.prepare(q).all());
  });

  test("the manifest's counts are the index's", () => {
    const m = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
    const counts = JSON.parse(sqlite.prepare("SELECT value FROM meta WHERE key = 'counts'").get().value);
    assert.deepEqual(m.index_counts, counts);
    for (const t of TABLES) {
      const n = sqlite.prepare(`SELECT COUNT(*) AS n FROM ${t}`).get().n;
      assert.equal(m.files[`${t}.parquet`].rows, n, t);
    }
  });
});

describe("4. reviewed PDF tables, per family, year and status", () => {
  test("the manifest's gate is the index's", () => {
    const flag = sqlite.prepare("SELECT value FROM meta WHERE key = 'include_reviewed'").get().value;
    assert.equal(MANIFEST.include_reviewed, flag === "yes");
    if (!MANIFEST.include_reviewed) {
      for (const t of PDF_TABLES) assert.equal(sqlite.prepare(`SELECT COUNT(*) AS n FROM ${t} WHERE status <> 'closed'`).get().n, 0, t);
    }
  });
  for (const t of PDF_TABLES) {
    test(t, async () => {
      const cols = sqlite.prepare(`PRAGMA table_info(${t})`).all().map((c) => c.name);
      const sums = cols.filter((c) => /^(amount|org_printed|printed|sum)_y\d$/.test(c) || ["dollars", "amount", "disclosure_amount", "rows_sum", "designated", "reserve"].includes(c));
      const keys = ["status", ...(cols.includes("family") ? ["family"] : []), ...(cols.includes("fiscal_year") ? ["fiscal_year"] : [])];
      const q = `SELECT ${keys.join(", ")}, COUNT(*) AS n${sums.map((c) => `, COALESCE(SUM(${c}), 0) AS ${c}`).join("")}
                 FROM ${t} GROUP BY ${keys.join(", ")} ORDER BY ${keys.join(", ")}`;
      assert.deepEqual(await duck(q), sqlite.prepare(q).all());
    });
  }
  test("Schedule C beside the disclosure: rows and dollars per side, from both engines", async () => {
    const q = `SELECT fiscal_year, status, side, reason, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount,
                 COALESCE(SUM(disclosure_amount), 0) AS d FROM pdf_sc_disclosure GROUP BY ALL ORDER BY ALL`;
    const a = sqlite.prepare(q.replace("GROUP BY ALL ORDER BY ALL", "GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4")).all();
    const b = await duck(q);
    assert.equal(b.length, a.length);
    a.forEach((r, i) => {
      assert.deepEqual([b[i].fiscal_year, b[i].status, b[i].side, b[i].reason, b[i].n, b[i].amount], [r.fiscal_year, r.status, r.side, r.reason, r.n, r.amount]);
      near(b[i].d, r.d, `${r.side} ${r.reason} disclosure amount`);
    });
    // Every matched pair points at a real disclosure row with the same EIN.
    if (a.length) {
      const [{ n }] = await duck(`SELECT COUNT(*) AS n FROM pdf_sc_disclosure m LEFT JOIN disclosure d ON d.fiscal_year = m.fiscal_year AND d.source_row = m.disclosure_row
                                  WHERE m.side <> 'pdf_only' AND (d.source_row IS NULL OR d.ein <> m.ein)`);
      assert.equal(n, 0);
    }
  });
  test("each loaded family's main table has pdf_years.rows rows", async () => {
    for (const y of await duck("SELECT fiscal_year, family, status, rows FROM pdf_years")) {
      const main = PDF_FAMILIES[y.family].main;
      const [{ n }] = await duck(`SELECT COUNT(*) AS n FROM ${main} WHERE fiscal_year = ? AND family = ? AND status = ?`, [y.fiscal_year, y.family, y.status]);
      assert.equal(n, y.rows, `FY${y.fiscal_year} ${y.family}`);
    }
  });
});

describe("6. NYC Open Data: crosswalk and coverage", () => {
  test("crosswalk rows per family, dataset, year and status, from both engines", async () => {
    const q = `SELECT family, dataset_id, fiscal_year, match_status, record_pdf, COUNT(*) AS n
               FROM open_data_crosswalk GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2, 3, 4, 5`;
    assert.deepEqual(await duck(q), sqlite.prepare(q).all());
  });
  test("the coverage strip's numbers, from both engines", async () => {
    const q = `SELECT family, dataset_id, fiscal_year, covered, records, same, differs, ambiguous, absent, context,
                 not_covered, portal_rows, portal_only FROM open_data_coverage ORDER BY 1, 2, 3`;
    assert.deepEqual(await duck(q), sqlite.prepare(q).all());
  });
  test("the explorer's badge query joins every expense crosswalk row to its award", async () => {
    const [{ n }] = await duck(`SELECT COUNT(*) AS n FROM open_data_crosswalk x LEFT JOIN disclosure d
      ON d.fiscal_year = x.fiscal_year AND d.source_row = CAST(x.record_row AS BIGINT)
      WHERE x.family = 'expense' AND d.source_row IS NULL`);
    assert.equal(n, 0);
  });
});

describe("5. compare two years: every grouping keeps every row", () => {
  // For each source the Compare view reads, each dimension and each year in the index: the
  // view's groups (DuckDB, on the Parquet) add up to the year's rows and dollars in budget.db.
  // A key expression that dropped blanks or split a row would fail here, with the source named.
  for (const [src, s] of Object.entries(C.SOURCES)) {
    for (const dim of Object.keys(s.dims)) {
      test(`${src} by ${dim}`, async () => {
        const where = s.where ? ` AND ${s.where}` : "";
        const years = sqlite.prepare(`SELECT DISTINCT ${s.fy} AS y FROM ${s.table} WHERE 1 = 1${where} ORDER BY 1`).all().map((r) => r.y);
        for (const y of years) {
          const want = sqlite.prepare(`SELECT COUNT(*) AS n, COALESCE(SUM(${s.amount}), 0) AS amount FROM ${s.table} WHERE ${s.fy} = ?${where}`).get(y);
          const g = C.groupQuery(src, dim, y);
          const rows = await duck(g.sql, g.params);
          assert.equal(rows.reduce((t, r) => t + r.n, 0), want.n, `FY${y} rows`);
          near(rows.reduce((t, r) => t + Number(r.amount), 0), want.amount, `FY${y} amount`);
          assert.equal(new Set(rows.map((r) => r.key)).size, rows.length, `FY${y} keys unique`);
        }
      });
    }
  }
});

describe("2. every row, every column", () => {
  for (const table of TABLES) {
    test(table, async () => {
      const cols = sqlite.prepare(`PRAGMA table_info(${table})`).all();
      const pcols = (await duck(`DESCRIBE "${table}"`)).map((r) => r.column_name);
      assert.deepEqual(pcols, cols.map((c) => c.name), "same columns, same order");
      const a = sqlite.prepare(`SELECT * FROM ${table} ORDER BY rowid`).all();
      const b = await duck(`SELECT * FROM "${table}"`);
      assert.equal(b.length, a.length, "row count");
      for (let i = 0; i < a.length; i++) {
        for (const { name } of cols) {
          if (a[i][name] !== b[i][name]) assert.fail(`${table} row ${i + 1} ${name}: ${JSON.stringify(a[i][name])} vs ${JSON.stringify(b[i][name])}`);
        }
      }
    });
  }
});

describe("3. the explorer's queries answer what the MCP answers", () => {
  const rowKey = (r) => `${r.fiscal_year}:${r.source_row}`;
  // The MCP's tool layer (src/server.ts budgetLineArg) normalizes budget_line before db.ts sees it.
  const asTool = (f) => (f.budget_line == null ? f : { ...f, budget_line: mcp.normBudgetLine(f.budget_line) });

  const disclosureCases = [
    {},
    { fiscal_year: 2027 },
    { fiscal_year: 2027, status: "pending" },
    { legal_name: "jewish emigre" },
    { legal_name: "Women's" },
    { council_member: "rivera" },
    { agency: "youth", fiscal_year: 2024, min_amount: 10000, max_amount: 50000 },
    { ein: "13-2612524" },
    { program_name: "senior", source: "local" },
    { fiscal_year: 2012, status: "other" },
    { legal_name: "zzzz-no-such-grantee" },
  ];
  for (const f of disclosureCases) {
    test(`disclosure ${JSON.stringify(f)}`, async () => {
      const m = mcp.searchDisclosure({ ...f, limit: Q.PAGE_SIZE });
      const t = Q.disclosureTotalsQuery(f);
      const mine = Q.rollupDisclosure(await duck(t.sql, t.params));
      assert.equal(mine.matched, m.matched, "matched");
      for (const s of Q.DISCLOSURE_STATUSES) {
        assert.equal(mine.totals[s].rows, m.totals[s].rows, `${s} rows`);
        near(mine.totals[s].amount, m.totals[s].amount, `${s} amount`);
      }
      assert.deepEqual(mine.by_year.map((y) => y.fiscal_year), m.by_year.map((y) => y.fiscal_year), "years");
      const r = Q.disclosureRowsQuery(f, 0);
      assert.deepEqual((await duck(r.sql, r.params)).map(rowKey), m.rows.map(rowKey), "first page, in order");
    });
  }

  const capitalCases = [
    {},
    { fiscal_year: 2027 },
    { fiscal_year: 2020 },
    { sponsor: "avilés" },
    { council_district: 8 },
    { budget_line: "p-d018" },
    { borough: "X", min_amount: 1000000 },
    { title: "library", description: "renovat" },
    { amount_fy: 2028 },
  ];
  for (const f of capitalCases) {
    test(`capital ${JSON.stringify(f)}`, async () => {
      const m = mcp.searchCapital({ ...asTool(f), limit: Q.PAGE_SIZE });
      const t = Q.capitalTotalsQuery(f);
      const mine = Q.rollupCapital(await duck(t.sql, t.params));
      assert.equal(mine.matched, m.matched, "matched");
      assert.equal(mine.amount_unknown, m.amount_unknown, "amount unknown");
      assert.equal(mine.report_year_amounts.rows, m.report_year_amounts.rows, "report-year rows");
      near(mine.report_year_amounts.amount, m.report_year_amounts.amount, "report-year amount");
      const r = Q.capitalRowsQuery(f, 0);
      const key = (x) => `${x.report_year}:${x.source_file}:${x.source_row}:${x.amount_fy}:${x.amount}`;
      assert.deepEqual((await duck(r.sql, r.params)).map(key), m.rows.map(key), "first page, in order");
    });
  }

  const ombCases = [{}, { report_year: 2024 }, { verdict: "differ" }, { budget_line: "hl-dn164" }];
  for (const f of ombCases) {
    test(`Council vs OMB ${JSON.stringify(f)}`, async () => {
      const m = mcp.compareCapitalToOmb({ ...asTool(f), limit: Q.PAGE_SIZE });
      const c = Q.ombCountsQuery(f);
      const counts = await duck(c.sql, c.params);
      assert.equal(counts.reduce((s, r) => s + r.n, 0), m.matched, "matched");
      const r = Q.ombRowsQuery(f, 0);
      const key = (x) => `${x.report_year}:${x.budget_line_norm}:${x.verdict}`;
      assert.deepEqual((await duck(r.sql, r.params)).map(key), m.rows.map(key), "first page, in order");
    });
  }

  test("normBudgetLine is the MCP's rule", () => {
    for (const v of ["P D018", "p-d018", "  pw   dn846 ", "PD018", "", "HL DN164", "AG-D001", "X"]) {
      assert.equal(Q.normBudgetLine(v), mcp.normBudgetLine(v), JSON.stringify(v));
    }
  });
});
