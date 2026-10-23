/**
 * Lazy loading against the real build (after `npm run data`): each view's queries run in a
 * database holding only the files src/duckdb/needs.js says that view needs, so a view never asks
 * for a table it did not load. And the first visit's files: no PDF family's, and about 4 MB.
 *
 *   node --test test/lazy-load.test.mjs
 *
 * Fails if a view's query names a table its list leaves out (DuckDB: "Table ... does not exist"),
 * if the landing page's list grows a PDF family file, or if the first visit's data passes 4.5 MB.
 * test/unit/lazy-load.test.js checks that the store fetches exactly these lists.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import { DuckDBInstance } from "@duckdb/node-api";

import * as Q from "../src/query/sql.js";
import * as C from "../src/compare/queries.js";
import * as P from "../src/query/pdf.js";
import * as OD from "../src/query/opendata.js";
import { BASE, awardsExtras, bytesOf, tablesForView } from "../src/duckdb/needs.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(resolve(HERE, ".."), "public", "data");
if (!existsSync(join(DATA, "manifest.json"))) throw new Error("lazy-load: public/data/manifest.json is missing. Run `npm run data` first.");
const MANIFEST = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
const MAX_FIRST_VISIT = 4.5e6;

/** A database with only these tables, and a runner for { sql, params } queries. */
async function only(tables) {
  const instance = await DuckDBInstance.create(":memory:");
  const conn = await instance.connect();
  for (const t of tables) await conn.run(`CREATE TABLE "${t}" AS SELECT * FROM read_parquet('${join(DATA, `${t}.parquet`).replaceAll("'", "''")}')`);
  const run = async (q, label) => {
    if (!q) return [];
    try {
      return (await conn.runAndReadAll(q.sql, q.params ?? [])).getRowObjectsJS();
    } catch (err) {
      throw new Error(`${label}: ${err.message}`);
    }
  };
  return { run, close: () => (conn.closeSync(), instance.closeSync()) };
}

const fy = (fam) => {
  const y = (MANIFEST.pdf_families?.[fam] ? Object.keys(MANIFEST.pdf_families[fam].decisions ?? {}) : []).map(Number).sort((a, b) => b - a)[0];
  return y ?? 2027;
};

/** Each view's queries, as the view makes them (src/views/*.jsx, src/components/*.jsx). */
const VIEWS = {
  awards: async (run) => {
    const rows = await run(Q.disclosureRowsQuery({}, 0), "disclosureRowsQuery");
    await run(Q.disclosureTotalsQuery({}), "disclosureTotalsQuery");
    await run(Q.disclosureFlagsQuery({}), "disclosureFlagsQuery");
    await run(P.pdfYearsQuery(), "pdfYearsQuery");
    await run({ sql: "SELECT fiscal_year, loaded, early_snapshot, note FROM disclosure_years", params: [] }, "lookups");
    await run({ sql: "SELECT report_year FROM capital_sources", params: [] }, "lookups");
    await run({ sql: "SELECT DISTINCT report_year FROM capital_vs_omb", params: [] }, "lookups");
    return rows;
  },
  awardsWithExtras: async (run) => {
    const rows = await VIEWS.awards(run);
    await run(P.scSummaryQuery(null), "scSummaryQuery");
    await run(P.scForDisclosureRowsQuery(rows), "scForDisclosureRowsQuery");
    await run(OD.coverageQuery("expense"), "coverageQuery");
    await run(OD.odForRecordsQuery("expense", rows.map((r) => [r.fiscal_year, r.source_row])), "odForRecordsQuery");
  },
  awardsPdfOnly: async (run) => {
    await run(P.scOnlyQuery({}, 0), "scOnlyQuery");
    await run(P.scOnlyTotalsQuery({}), "scOnlyTotalsQuery");
    await run(Q.disclosureRowsQuery({ sc_side: "matched" }, 0), "disclosureRowsQuery sc_side");
  },
  award: async (run) => {
    const [a] = await run(Q.disclosureRowsQuery({ fiscal_year: fy("schedule_c") }, 0), "rows");
    await run(Q.awardQuery(a.fiscal_year, a.source_row), "awardQuery");
    await run(P.scForDisclosureRowsQuery([a]), "scForDisclosureRowsQuery");
    await run(OD.coverageQuery("expense"), "coverageQuery");
    await run(OD.odForRecordsQuery("expense", [[a.fiscal_year, a.source_row]]), "odForRecordsQuery");
  },
  years: async (run) => {
    await run(Q.YEAR_DISCLOSURE_QUERY, "YEAR_DISCLOSURE_QUERY");
    await run(Q.YEAR_CAPITAL_QUERY, "YEAR_CAPITAL_QUERY");
  },
  omb: async (run) => {
    await run(Q.ombRowsQuery({}, 0), "ombRowsQuery");
    await run(Q.ombCountsQuery({}), "ombCountsQuery");
  },
  capital: async (run) => {
    const rows = await run(Q.capitalRowsQuery({}, 0), "capitalRowsQuery");
    await run(Q.capitalTotalsQuery({}), "capitalTotalsQuery");
    await run(P.capitalPdfMatchesQuery([fy("capital_sd")]), "capitalPdfMatchesQuery");
    await run(P.capitalTotalsPdfQuery(fy("capital_sd")), "capitalTotalsPdfQuery");
    await run(OD.coverageQuery("capital_award"), "coverageQuery");
    await run(OD.odForRecordsQuery("capital_award", rows.map((r) => [r.report_year, r.source_row, r.amount_fy])), "odForRecordsQuery");
    await run(Q.capitalRowQuery(rows[0].seq), "capitalRowQuery");
    await run(OD.odForLinesQuery([[rows[0].report_year, rows[0].budget_line_norm ?? ""]]), "odForLinesQuery");
  },
  book: async (run) => {
    const f = { fiscal_year: fy("capital_sd") };
    const rows = await run(P.bookQuery(f, 0), "bookQuery");
    await run(P.bookTotalsQuery(f), "bookTotalsQuery");
    await run(P.bookPart2OnlyQuery(f), "bookPart2OnlyQuery");
    await run(P.odForBookRowsQuery(rows), "odForBookRowsQuery");
    await run(P.reviewNotesQuery(rows.map((r) => r.review_id).filter(Boolean).slice(0, 5), { full: false }), "reviewNotesQuery");
    await run(P.councilQuestionsQuery(), "councilQuestionsQuery");
    await run(P.part2SeriesQuery(), "part2SeriesQuery");
  },
  orgs: async (run) => {
    await run(P.orgsQuery({ fiscal_year: fy("capital_sd") }, 0), "orgsQuery");
    await run(P.orgsTotalsQuery({ fiscal_year: fy("capital_sd") }), "orgsTotalsQuery");
  },
  terms: async (run) => {
    const f = { fiscal_year: fy("terms") };
    const rows = await run(P.termsQuery(f, 0), "termsQuery");
    await run(P.termsCountQuery(f), "termsCountQuery");
    await run(P.termsFsrQuery(f.fiscal_year), "termsFsrQuery");
    await run(OD.coverageQuery("terms_unit"), "coverageQuery");
    await run(OD.odForRecordsQuery("terms_unit", rows.map((c) => [c.fiscal_year, c.item_number]), { pdf: 1 }), "odForRecordsQuery");
  },
  schedc: async (run) => {
    const f = { fiscal_year: fy("schedule_c") };
    const rows = await run(P.scSearchQuery(f, 0), "scSearchQuery");
    await run(P.scSearchTotalsQuery(f), "scSearchTotalsQuery");
    await run(P.scSubawardsQuery(rows), "scSubawardsQuery");
    await run(P.reviewNotesQuery(rows.map((r) => r.review_id).filter(Boolean).slice(0, 5), { full: false }), "reviewNotesQuery");
  },
  transparency: async (run) => {
    const f = { fiscal_year: fy("transparency") };
    await run(P.trQuery(f, 0), "trQuery");
    await run(P.trTotalsQuery(f), "trTotalsQuery");
    await run(P.trResolutionsQuery(), "trResolutionsQuery");
  },
  compareTotals: async (run) => {
    for (const [name, q] of Object.entries(C.totalsQueries(2026, 2027))) await run(q, `totalsQueries.${name}`);
  },
  compareTerms: async (run) => {
    await run(C.termsQuery(fy("terms")), "compare termsQuery");
  },
};

/** View -> the URL state that opens it, and the query set above. */
const CASES = [
  ["awards (the landing page)", { view: "awards" }, "awards"],
  ["awards, Schedule C only rows (deep link)", { view: "awards", scside: "pdf_only" }, "awardsPdfOnly"],
  ["award detail (deep link)", { view: "award" }, "award"],
  ["years", { view: "years" }, "years"],
  ["capital vs OMB", { view: "omb" }, "omb"],
  ["capital", { view: "capital" }, "capital"],
  ["capital book", { view: "book" }, "book"],
  ["organizations", { view: "orgs" }, "orgs"],
  ["terms", { view: "terms" }, "terms"],
  ["schedule C", { view: "schedc" }, "schedc"],
  ["transparency", { view: "transparency" }, "transparency"],
  ["compare, totals", { view: "compare" }, "compareTotals"],
  ["compare, terms", { view: "compare", csec: "terms" }, "compareTerms"],
];

describe("each view runs on its own files only", () => {
  for (const [label, state, set] of CASES) {
    test(label, async () => {
      const db = await only(tablesForView(state, MANIFEST));
      try {
        await VIEWS[set](db.run);
      } finally {
        db.close();
      }
    });
  }

  test("the expense list's optional columns run on the landing files plus awardsExtras", async () => {
    const db = await only(tablesForView({ view: "awards" }, MANIFEST, { extras: true }));
    try {
      await VIEWS.awardsWithExtras(db.run);
    } finally {
      db.close();
    }
  });

  for (const dim of Object.keys(C.DIM_SOURCES)) {
    test(`compare, by ${dim}, with its drill-downs`, async () => {
      const db = await only(tablesForView({ view: "compare", csec: dim }, MANIFEST));
      try {
        for (const src of C.DIM_SOURCES[dim]) {
          await db.run(C.groupQuery(src, dim, 2027), `groupQuery ${src}`);
          await db.run(C.drillQuery(src, dim, 2027, "*"), `drillQuery ${src}`);
        }
      } finally {
        db.close();
      }
    });
  }
});

describe("the first visit", () => {
  const first = tablesForView({ view: "awards" }, MANIFEST);

  test("loads no PDF family's file and no Open Data file", () => {
    assert.deepEqual(first.filter((t) => (t.startsWith("pdf_") && t !== "pdf_years") || t.startsWith("open_data_")), []);
    assert.deepEqual([...first].sort(), BASE.filter((t) => MANIFEST.files[`${t}.parquet`]).sort());
  });

  test(`downloads at most ${MAX_FIRST_VISIT / 1e6} MB of data, where the whole build is more`, () => {
    const bytes = bytesOf(MANIFEST, first);
    const all = Object.values(MANIFEST.files).reduce((t, f) => t + f.bytes, 0);
    console.log(`first visit: ${(bytes / 1e6).toFixed(2)} MB of data (${first.length} files); every file: ${(all / 1e6).toFixed(2)} MB`);
    assert.ok(bytes <= MAX_FIRST_VISIT, `${bytes} bytes`);
    assert.ok(awardsExtras(MANIFEST).length > 0, "the build has Schedule C or Open Data columns to add");
  });
});
