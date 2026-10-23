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
 * 7. The PDF family searches (#213: Schedule C every row, Transparency, the capital book): for a
 *    set of filters, the explorer's query on the Parquet and a plain-JavaScript filter over
 *    budget.db's rows agree on the count, the totals and the first page, in order. The MCP's own
 *    tools for these families (W3, #212) are not on main yet; when they land, these cases are the
 *    ones to ask them too.
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
import * as P from "../src/query/pdf.js";
import { PDF_FAMILIES, PDF_TABLES } from "../../../mcp/scripts/pdf-families.mjs";
import { OPEN_DATA_TABLES } from "../../../mcp/scripts/open-data.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..");
const REPO = resolve(APP, "..", "..");
const DATA = join(APP, "public", "data");
if (!existsSync(join(DATA, "manifest.json"))) throw new Error("parity: public/data/manifest.json is missing. Run `npm run data` first.");
const MANIFEST = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
const DB_PATH = join(REPO, MANIFEST.index ?? "mcp/data/budget.db");
// A public build withholds the review screen's tables (manifest.withheld); every other table is compared.
const WITHHELD = MANIFEST.withheld ?? [];
const TABLES = ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta",
  ...PDF_TABLES, ...OPEN_DATA_TABLES].filter((t) => !WITHHELD.includes(t));
const COMPARED_PDF_TABLES = PDF_TABLES.filter((t) => !WITHHELD.includes(t));
// ...and leaves internal columns out of some it ships (manifest.dropped_columns): compare the rest.
const DROPPED = MANIFEST.dropped_columns ?? {};
const shipped = (table, cols) => cols.filter((c) => !(DROPPED[table] ?? []).includes(c.name ?? c));
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
    // public (reviewed + closed, no review screen), review (the same, with it), closed (closed only).
    assert.ok(["public", "review", "closed"].includes(MANIFEST.build), `build ${MANIFEST.build}`);
    assert.equal(MANIFEST.review_screen, MANIFEST.build === "review", "the review screen is only in a review build");
    assert.equal(MANIFEST.include_reviewed, MANIFEST.build !== "closed");
    // The suggested decisions are the review screen's: never in a public build's files.
    assert.deepEqual(WITHHELD, MANIFEST.build === "public" ? ["pdf_review_suggestions"] : []);
    for (const t of WITHHELD) {
      assert.equal(MANIFEST.files[`${t}.parquet`], undefined, `${t} is listed in a public manifest`);
      assert.equal(existsSync(join(DATA, `${t}.parquet`)), false, `${t}.parquet is in a public build's data`);
    }
    // A public pdf_review carries no check id, severity or other internal review field.
    const internal = ["check_id", "severity", "dollars", "expected", "observed", "detail"];
    assert.deepEqual(DROPPED, MANIFEST.build === "public" ? { pdf_review: internal } : {});
  });
  test("a public build's pdf_review file has no check_id or severity column; a review build's has both", async () => {
    const p = join(DATA, "pdf_review.parquet").replace(/'/g, "''");
    const cols = (await duck(`DESCRIBE SELECT * FROM read_parquet('${p}')`)).map((r) => r.column_name);
    for (const c of ["check_id", "severity", "dollars", "expected", "observed", "detail"]) {
      assert.equal(cols.includes(c), MANIFEST.build !== "public", `pdf_review.${c} in a ${MANIFEST.build} build`);
    }
    for (const c of ["review_id", "note", "decision", "decision_note"]) assert.ok(cols.includes(c), `pdf_review.${c}`);
    if (!MANIFEST.include_reviewed) {
      // Every table but pdf_council_questions, which has no family-year status (not gated).
      for (const t of PDF_TABLES.filter((t) => t !== "pdf_council_questions")) assert.equal(sqlite.prepare(`SELECT COUNT(*) AS n FROM ${t} WHERE status <> 'closed'`).get().n, 0, t);
    }
  });
  for (const t of COMPARED_PDF_TABLES) {
    test(t, async () => {
      const cols = shipped(t, sqlite.prepare(`PRAGMA table_info(${t})`).all().map((c) => c.name));
      const sums = cols.filter((c) => /^(amount|org_printed|printed|sum)_y\d$/.test(c) || ["dollars", "amount", "disclosure_amount", "rows_sum", "designated", "reserve"].includes(c));
      const keys = [cols.includes("status") ? "status" : "question_status", ...(cols.includes("family") ? ["family"] : []), ...(cols.includes("fiscal_year") ? ["fiscal_year"] : [])];
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
    const q = `SELECT family, dataset_id, fiscal_year, covered, records, same, differs, ambiguous, ambiguous_present, absent, context,
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

describe("7. the PDF family searches answer what budget.db answers", () => {
  // The oracle: every row of the table from budget.db, filtered and sorted in JavaScript with the
  // same rules (P.textKey for text, digits for an EIN), independent of the SQL under test.
  const has = (cols, v) => (r) => v == null || String(v).trim() === "" || cols.some((c) => P.textKey(r[c] ?? "").includes(P.textKey(v)));
  const ein = (cols, v) => (r) => !P.einDigits(v) || cols.some((c) => r[c] === P.einDigits(v));
  const eq = (c, v, f = (x) => x) => (r) => v == null || v === "" || r[c] === f(v);
  const range = (c, lo, hi) => (r) => (lo == null || (r[c] != null && r[c] >= Number(lo))) && (hi == null || (r[c] != null && r[c] <= Number(hi)));
  const all = (...ps) => (r) => ps.every((p) => p(r));
  const cmp = (...keys) => (a, b) => {
    for (const [k, dir] of keys) {
      const x = a[k];
      const y = b[k];
      if (x === y) continue;
      if (x == null) return 1; // NULLS LAST, as DuckDB orders by default
      if (y == null) return -1;
      return (x < y ? -1 : 1) * (dir === "desc" ? -1 : 1);
    }
    return 0;
  };
  const cache = {};
  const rowsOf = (t) => (cache[t] ??= sqlite.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all());
  const sum = (rows, c) => rows.reduce((t, r) => t + (r[c] ?? 0), 0);

  const scCases = [
    {},
    { fiscal_year: 2027 },
    { org: "jewish" },
    { org: "Women's" },
    { ein: "13-2612524" },
    { sponsor: "speaker", fiscal_year: 2025 },
    { sponsor: "delegation" },
    { category: "local", agency: "dycd", min_amount: 10000, max_amount: 50000 },
    { initiative: "senior" },
    { disclosure: "unmatched" },
    { fiscal_year: 2019, org: "jobs to build on" },
    { org: "zzzz-no-such-grantee" },
  ];
  for (const f of scCases) {
    test(`Schedule C ${JSON.stringify(f)}`, async () => {
      const want = rowsOf("pdf_schedule_c").filter(
        all(
          eq("fiscal_year", f.fiscal_year),
          has(["org"], f.org),
          ein(["ein", "fiscal_conduit_ein"], f.ein),
          has(["member", "sponsor", "delegation"], f.sponsor),
          has(["category"], f.category),
          has(["initiative"], f.initiative),
          has(["agency"], f.agency),
          range("amount", f.min_amount, f.max_amount),
          eq("disclosure_status", f.disclosure)
        )
      );
      const t = P.scSearchTotalsQuery(f);
      const [got] = await duck(t.sql, t.params);
      assert.equal(got.n, want.length, "matched");
      assert.equal(got.amount, sum(want, "amount"), "amount");
      assert.equal(got.no_amount, want.filter((r) => r.amount == null).length, "no dollar amount");
      const page = [...want].sort(cmp(["amount", "desc"], ["fiscal_year", "desc"], ["award_id", "asc"])).slice(0, Q.PAGE_SIZE);
      const r = P.scSearchQuery(f, 0);
      const mine = await duck(r.sql, r.params);
      assert.deepEqual(mine.map((x) => `${x.fiscal_year}:${x.award_id}`), page.map((x) => `${x.fiscal_year}:${x.award_id}`), "first page, in order");
      // Each row's disclosure partner and sub-award count, from budget.db.
      const pair = sqlite.prepare("SELECT disclosure_row FROM pdf_sc_disclosure WHERE fiscal_year = ? AND award_id = ? AND side = 'matched'");
      const subs = sqlite.prepare("SELECT COUNT(*) AS n FROM pdf_schedule_c_subawards WHERE fiscal_year = ? AND parent_award_id = ?");
      for (const x of mine) {
        assert.equal(x.disclosure_row, pair.get(x.fiscal_year, x.award_id)?.disclosure_row ?? null, `${x.award_id} disclosure row`);
        assert.equal(x.subawards, subs.get(x.fiscal_year, x.award_id).n, `${x.award_id} sub-awards`);
      }
    });
  }

  test("Schedule C: every sub-award's parent is a Schedule C award, and none is in an award total", async () => {
    const [{ n }] = await duck(`SELECT COUNT(*) AS n FROM pdf_schedule_c_subawards s LEFT JOIN pdf_schedule_c a
      ON a.fiscal_year = s.fiscal_year AND a.award_id = s.parent_award_id WHERE a.award_id IS NULL`);
    assert.equal(n, 0);
    const t = P.scSearchTotalsQuery({});
    const [got] = await duck(t.sql, t.params);
    assert.equal(got.amount, sqlite.prepare("SELECT COALESCE(SUM(amount), 0) AS s FROM pdf_schedule_c").get().s);
  });

  const trCases = [
    {},
    { fiscal_year: 2025 },
    { org: "south asian youth" },
    { ein: "13-3943630" },
    { member: "lee", fiscal_year: 2025 },
    { member: "speaker" },
    { resolution: "1013" },
    { date_from: "2025-08-01", date_to: "2025-08-31" },
    { budget_fiscal_year: 2017 },
    { action: "listed" },
    { action: "rescind", fiscal_year: 2018 },
  ];
  for (const f of trCases) {
    test(`Transparency ${JSON.stringify(f)}`, async () => {
      const want = rowsOf("pdf_transparency").filter(
        all(
          eq("fiscal_year", f.fiscal_year),
          eq("budget_fiscal_year", f.budget_fiscal_year),
          has(["org"], f.org),
          ein(["ein", "fiscal_conduit_ein"], f.ein),
          has(["member"], f.member),
          has(["resolution_number"], f.resolution),
          (r) => !f.date_from || r.resolution_date >= f.date_from,
          (r) => !f.date_to || r.resolution_date <= f.date_to,
          eq("action", f.action)
        )
      );
      const t = P.trTotalsQuery(f);
      const got = P.rollupTr(await duck(t.sql, t.params));
      assert.equal(got.matched, want.length, "matched");
      // Organization lines and the agency side's lines, kept apart (code/transreso/structure.py).
      for (const [side, by] of [[0, got.byAction], [1, got.agencyByAction]]) {
        for (const a of P.TR_ACTIONS) {
          const w = want.filter((r) => r.action === a && Number(r.agency_side ?? 0) === side);
          assert.equal(by[a]?.n ?? 0, w.length, `side ${side} ${a} rows`);
          assert.equal(by[a]?.amount ?? 0, sum(w, "amount"), `side ${side} ${a} amount`);
          assert.equal(by[a]?.no_amount ?? 0, w.filter((r) => r.amount == null).length, `side ${side} ${a} no dollar amount`);
        }
      }
      const page = [...want]
        .sort(cmp(["resolution_date", "desc"], ["fiscal_year", "desc"], ["resolution_seq", "desc"], ["pdf_page", "asc"], ["table_index", "asc"], ["row_index", "asc"], ["row_id", "asc"]))
        .slice(0, Q.PAGE_SIZE);
      const r = P.trQuery(f, 0);
      assert.deepEqual((await duck(r.sql, r.params)).map((x) => `${x.fiscal_year}:${x.row_id}`), page.map((x) => `${x.fiscal_year}:${x.row_id}`), "first page, in order");
    });
  }

  test("Transparency: organization lines equal the resolutions' own totals (designations, rescissions), agency side apart", async () => {
    // pdf_transparency_resolutions carries the pipeline's sums: org_designations_sum, org_rescissions_sum, agency_side_net.
    // agency_side_net covers the designation charts' agency lines (money added and taken back), not purpose changes.
    const res = sqlite.prepare(`SELECT fiscal_year, resolution_seq, org_designations_sum AS d, org_rescissions_sum AS r, agency_side_net AS a,
      agency_side_rows AS an FROM pdf_transparency_resolutions`).all();
    for (const x of res) {
      const t = P.trTotalsQuery({ fiscal_year: x.fiscal_year });
      const rows = await duck(t.sql.replace("FROM pdf_transparency WHERE", "FROM pdf_transparency WHERE resolution_seq = ? AND"), [x.resolution_seq, ...t.params]);
      const got = P.rollupTr(rows);
      const ag = ["designate", "rescind"].map((a) => got.agencyByAction[a] ?? { n: 0, amount: 0 });
      const agencyNet = ag[0].amount + ag[1].amount;
      assert.equal(ag[0].n + ag[1].n, x.an ?? 0, `FY${x.fiscal_year} resolution ${x.resolution_seq} agency-side rows`);
      assert.equal(got.byAction.designate?.amount ?? 0, x.d ?? 0, `FY${x.fiscal_year} resolution ${x.resolution_seq} designations`);
      assert.equal(got.byAction.rescind?.amount ?? 0, x.r ?? 0, `FY${x.fiscal_year} resolution ${x.resolution_seq} rescissions`);
      assert.equal(agencyNet, x.a ?? 0, `FY${x.fiscal_year} resolution ${x.resolution_seq} agency side`);
    }
  });

  test("Transparency: rows that print no dollar amount have no amount, so every total skips them", async () => {
    const [{ n }] = await duck("SELECT COUNT(*) AS n FROM pdf_transparency WHERE amount_kind = 'no_dollar_amount' AND amount IS NOT NULL");
    assert.equal(n, 0);
  });

  const bookCases = [
    {},
    { fiscal_year: 2027 },
    { sub_id: "cn001" },
    { sponsor: "sanchez" },
    { sponsor: "avilés" },
    { sponsor: "CD 22" },
    { boro: "k", fiscal_year: 2025 },
    { agency: "library" },
    { title: "library" },
    { title: "heating", fiscal_year: 2019 },
    { budget_line: "lb-d104" },
    { part: "II" },
    { max_amount: -1 },
    { min_amount: 1000000, fiscal_year: 2026 },
  ];
  for (const f of bookCases) {
    test(`capital book ${JSON.stringify(f)}`, async () => {
      const line = f.budget_line ? Q.normBudgetLine(f.budget_line) : null;
      const want = rowsOf("pdf_capital_sd").filter(
        all(
          eq("fiscal_year", f.fiscal_year),
          has(["sub_id"], f.sub_id),
          has(["sponsor", "sponsor_raw"], f.sponsor),
          (r) => !f.boro || String(r.boro ?? "").toUpperCase() === f.boro.toUpperCase(),
          has(["agency"], f.agency),
          has(["title", "description"], f.title),
          (r) => !line || r.budget_line === line,
          eq("part", f.part),
          range("amount_y1", f.min_amount, f.max_amount)
        )
      );
      const t = P.bookTotalsQuery(f);
      const [got] = await duck(t.sql, t.params);
      assert.equal(got.n, want.length, "matched");
      // The book's total is Part I; Part II apart, split into rows also in Part I and rows only in Part II.
      const same = (a, b) => a.fiscal_year === b.fiscal_year && a.sub_id === b.sub_id && a.budget_line === b.budget_line;
      const book = rowsOf("pdf_capital_sd");
      const p1 = want.filter((r) => r.part === "I");
      const p2 = want.filter((r) => r.part === "II");
      const noncity = p1.filter((r) => book.some((o) => o.part === "II" && same(o, r)));
      const only = p2.filter((r) => !book.some((o) => o.part === "I" && same(o, r)));
      assert.equal(got.part1_n, p1.length, "Part I rows");
      for (const k of [1, 2, 3, 4]) assert.equal(got[`y${k}`], sum(p1, `amount_y${k}`), `Part I amount_y${k}`);
      assert.deepEqual([got.noncity_n, got.noncity_y1], [noncity.length, sum(noncity, "amount_y1")], "Part I rows listed again in Part II");
      assert.deepEqual([got.part2_n, got.part2_y1], [p2.length, sum(p2, "amount_y1")], "Part II");
      assert.deepEqual([got.part2_only_n, got.part2_only_y1], [only.length, sum(only, "amount_y1")], "printed only in Part II");
      const o = P.bookPart2OnlyQuery(f);
      const key0 = (x) => `${x.fiscal_year}:${x.pdf_page}:${x.row_in_page}`;
      assert.deepEqual((await duck(o.sql, o.params)).map(key0), [...only].sort(cmp(["fiscal_year", "desc"], ["pdf_page", "asc"], ["row_in_page", "asc"])).slice(0, Q.PAGE_SIZE).map(key0), "Part-II-only list");
      assert.equal(got.negative_rows, want.filter((r) => [1, 2, 3, 4].some((k) => r[`amount_y${k}`] < 0)).length, "negative rows");
      assert.equal(got.negative_y1, sum(want.filter((r) => r.amount_y1 < 0), "amount_y1"), "negative amount");
      assert.equal(got.vacant_rows, want.filter((r) => P.isVacantDistrict(r.sponsor)).length, "vacant-district sponsors");
      const page = [...want].sort(cmp(["fiscal_year", "desc"], ["part", "asc"], ["pdf_page", "asc"], ["row_in_page", "asc"])).slice(0, Q.PAGE_SIZE);
      const r = P.bookQuery(f, 0);
      const key = (x) => `${x.fiscal_year}:${x.part}:${x.pdf_page}:${x.row_in_page}`;
      assert.deepEqual((await duck(r.sql, r.params)).map(key), page.map(key), "first page, in order");
    });
  }

  test("capital book FY2027: Part I $853,688,000, Part II $210,677,000, 148 Part I rows again in Part II, 30 only in Part II", async () => {
    const t = P.bookTotalsQuery({ fiscal_year: 2027 });
    const [got] = await duck(t.sql, t.params);
    assert.equal(got.part1_n, 1213);
    assert.equal(got.y1, 853688000);
    assert.equal(got.part2_n, 178);
    assert.equal(got.part2_y1, 210677000);
    assert.equal(got.noncity_n, 148);
    assert.equal(got.part2_only_n, 30);
    assert.equal(got.noncity_y1 + got.part2_only_y1, got.part2_y1, "Part II = rows also in Part I + rows only in Part II");
    // Both equal the book's own printed "TOTALS FOR ALL" lines.
    const printed = Object.fromEntries(sqlite.prepare("SELECT part, printed_y1 FROM pdf_capital_sd_totals WHERE fiscal_year = 2027 AND kind = 'totals_for' AND name = 'ALL'").all().map((r) => [r.part, r.printed_y1]));
    assert.deepEqual(printed, { I: 853688000, II: 210677000 });
    const o = P.bookPart2OnlyQuery({ fiscal_year: 2027 });
    const only = await duck(o.sql, o.params);
    assert.equal(only.length, 30);
    assert.ok(only.every((r) => P.isMaSeries(r.sub_id)), "FY2027's Part-II-only rows are the MA series");
    const b = P.bookQuery({ fiscal_year: 2027, part: "II" }, 0);
    assert.ok((await duck(b.sql, b.params)).length > 0, "Part II rows stay searchable");
  });

  test("capital book: a row's place (year, part, page, row) is unique, so the page order is total", () => {
    const n = sqlite.prepare("SELECT COUNT(*) AS n FROM (SELECT 1 FROM pdf_capital_sd GROUP BY fiscal_year, part, pdf_page, row_in_page HAVING COUNT(*) > 1)").get().n;
    assert.equal(n, 0);
  });

  test("#205: every crosswalk row keyed on a place points at exactly one book row with that SUB ID", async () => {
    const xs = await duck(`SELECT fiscal_year, record_row, record_part FROM open_data_crosswalk
      WHERE family = 'capital_award' AND record_pdf = 1 AND record_part IS NOT NULL AND record_part <> ''`);
    const book = new Map();
    for (const r of rowsOf("pdf_capital_sd")) {
      const k = `${r.fiscal_year}|${r.sub_id}|${P.bookPlace(r)}`;
      book.set(k, (book.get(k) ?? 0) + 1);
    }
    for (const x of xs) assert.equal(book.get(`${x.fiscal_year}|${x.record_row}|${x.record_part}`), 1, `FY${x.fiscal_year} ${x.record_row} ${x.record_part}`);
    // And through the explorer's own lookup: each such row gets only its own matches.
    const byId = new Map();
    for (const x of xs) byId.set(`${x.fiscal_year}|${x.record_row}`, [x.fiscal_year, x.record_row]);
    // A crosswalk row with no place, for a SUB ID the book prints on several rows, is never shown as that row's own match.
    const idRows = new Map();
    for (const r of rowsOf("pdf_capital_sd")) idRows.set(`${r.fiscal_year}|${r.sub_id}`, (idRows.get(`${r.fiscal_year}|${r.sub_id}`) ?? 0) + 1);
    const loose = await duck(`SELECT fiscal_year, record_row FROM open_data_crosswalk WHERE family = 'capital_award' AND record_pdf = 1 AND (record_part IS NULL OR record_part = '')`);
    let shared = 0;
    for (const x of loose) {
      const n = idRows.get(`${x.fiscal_year}|${x.record_row}`) ?? 0;
      const r = rowsOf("pdf_capital_sd").find((b) => b.fiscal_year === x.fiscal_year && b.sub_id === x.record_row);
      if (!r) continue;
      const [m] = P.odForBookRow([x], { ...r, id_rows: n });
      assert.equal(m.exact, n === 1, `FY${x.fiscal_year} ${x.record_row}: ${n} book rows`);
      if (n > 1) shared++;
    }
    assert.ok(shared > 0, "some crosswalk rows are on a SUB ID printed more than once");
    const b = P.bookQuery({}, 0);
    for (const r of await duck(b.sql, b.params)) assert.equal(r.id_rows, idRows.get(`${r.fiscal_year}|${r.sub_id}`), `${r.sub_id} id_rows`);
    for (const [fy, id] of byId.values()) {
      const rows = rowsOf("pdf_capital_sd").filter((r) => r.fiscal_year === fy && r.sub_id === id);
      const q = P.odForBookRowsQuery(rows);
      const found = await duck(q.sql, q.params);
      for (const r of rows) {
        for (const x of P.odForBookRow(found, r)) assert.ok(x.record_part == null || x.record_part === P.bookPlace(r), `FY${fy} ${id} ${P.bookPlace(r)}`);
      }
    }
  });
});

describe("2. every row, every column", () => {
  for (const table of TABLES) {
    test(table, async () => {
      const cols = shipped(table, sqlite.prepare(`PRAGMA table_info(${table})`).all());
      const pcols = (await duck(`DESCRIBE "${table}"`)).map((r) => r.column_name);
      assert.deepEqual(pcols, cols.map((c) => c.name), "same columns, same order (less any a public build drops)");
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
