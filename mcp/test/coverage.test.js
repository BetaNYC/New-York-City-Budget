/**
 * Per-fiscal-year coverage spot-checks — the "is each year good enough for others to use" gate.
 *
 * For every award year FY2015–FY2027 this asserts, as a real per-year check (not merely "it
 * loads"):
 *   1. the year is QUERYABLE through the MCP tools (search_awards returns it; get_awards_by_ein
 *      resolves an EIN that exists that year),
 *   2. the award count and dollar total match the QA-cleared committed data exactly (a regression
 *      guard — if a reparse shifts a year, this flags it for review), and
 *   3. every award row that year carries a valid 9-digit EIN (the 100% coverage the QA report
 *      records — this is the property that makes the award tools trustworthy).
 *
 * It also asserts the honesty boundary: FY2009–FY2014 (initiatives-only, no EIN) are NOT present
 * in the award tools, and the parsed-but-non-award datasets (terms/capital/transparency) cover
 * exactly the expected years.
 *
 * Tools are driven through the real MCP protocol (InMemoryTransport); per-year count/total/EIN
 * facts are checked against the built index (mcp/data/budget.db) the server itself serves.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import Database from "better-sqlite3";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { server } from "../dist/server.js";

const DB_PATH = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "budget.db");

// Expected per-year award facts, from the QA-cleared committed data (data/QA-REPORT.md EIN table
// + reconciled Schedule C). count = award rows; total = sum(amount). If a legitimate reparse
// changes a year, update this table (and confirm it against a fresh data/QA-REPORT.md).
//
// SCOPE (v1.4.0): these are the MAIN-BODY (source_table='schedule_c') figures, and they are
// deliberately unchanged from v1.3.x. They are the numbers already published from this MCP, so
// the regression guard on them has to survive the appendix ingest — every assertion below filters
// on source_table='schedule_c'. Appendix expectations are a separate table (EXPECTED_APPENDIX),
// which is what makes the delta auditable instead of absorbed.
const EXPECTED_AWARDS = {
  2015: { count: 652, total: 73199837 },
  2016: { count: 335, total: 89917012 },
  2017: { count: 364, total: 89901487 },
  2018: { count: 480, total: 102716956 },
  2019: { count: 846, total: 181026931 },
  2020: { count: 2841, total: 258762385 },
  2021: { count: 1810, total: 202070188 },
  2022: { count: 1492, total: 222556943 },
  2023: { count: 1848, total: 262419214 },
  2024: { count: 5368, total: 400663574 },
  2025: { count: 5646, total: 412985110 },
  2026: { count: 5838, total: 487287245 },
  2027: { count: 6118, total: 605111412 },
};

// Appendix A/B/C rows, loaded into `awards` under source_table='appendix' in v1.4.0.
// Counts/totals are the committed CSVs' own; the per-year totals also match the table recorded
// independently in DATA-ANOMALIES.md #19 (the fixed aging/local/youth pots). Years absent from
// this table have header-only appendix CSVs (FY2015–FY2017, FY2019–FY2020) — a known upstream
// parse gap, NOT something this release addresses.
// `streams` is asserted per year rather than assumed uniform: FY2018 has an aging appendix ONLY
// (its local and youth CSVs are header-only upstream), so a blanket "all three streams" check
// would be a false expectation dressed as a guard.
const ALL_STREAMS = ["aging", "local", "youth"];
const EXPECTED_APPENDIX = {
  2018: { count: 422, total: 4419275, streams: ["aging"] },
  2021: { count: 4310, total: 49799000, streams: ALL_STREAMS },
  2022: { count: 4182, total: 49799000, streams: ALL_STREAMS },
  2023: { count: 4056, total: 49789000, streams: ALL_STREAMS },
  2024: { count: 3911, total: 49799000, streams: ALL_STREAMS },
  2025: { count: 3920, total: 49799000, streams: ALL_STREAMS },
  2026: { count: 3914, total: 49794000, streams: ALL_STREAMS },
  2027: { count: 3860, total: 49799000, streams: ALL_STREAMS },
};

let client;
let db;

before(async () => {
  const [c, s] = InMemoryTransport.createLinkedPair();
  await server.connect(s);
  client = new Client({ name: "coverage-test", version: "0" }, { capabilities: {} });
  await client.connect(c);
  db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
});

after(async () => {
  await client.close();
  db.close();
});

async function callText(name, args = {}) {
  const res = await client.callTool({ name, arguments: args });
  assert.ok(!res.isError, `${name} errored: ${JSON.stringify(res.content)}`);
  return res.content.map((c) => c.text).join("\n");
}

// One real per-year assertion for every award year.
for (const [fyStr, exp] of Object.entries(EXPECTED_AWARDS)) {
  const fy = Number(fyStr);
  test(`FY${fy} awards — queryable, ${exp.count} rows, sane total, 100% valid EIN`, async () => {
    // --- data facts, checked against the index the server serves ---
    // Scoped to the main body: this is the published-figure regression guard and must NOT move
    // when appendix rows land. The appendix delta is asserted separately, below.
    const agg = db
      .prepare(
        `SELECT COUNT(*) n, COALESCE(SUM(amount),0) total FROM awards
         WHERE fiscal_year = ? AND source_table = 'schedule_c'`
      )
      .get(fy);
    assert.equal(agg.n, exp.count, `FY${fy} main-body award count`);
    assert.equal(agg.total, exp.total, `FY${fy} main-body award dollar total`);
    assert.ok(agg.total > 1_000_000, `FY${fy} total should be a plausible (>$1M) figure`);

    // Deliberately NOT scoped by source: 100% valid-EIN coverage is asserted over the whole
    // expanded corpus, appendix rows included. That property is what makes EIN the safe join key.
    const badEin = db
      .prepare(`SELECT COUNT(*) n FROM awards WHERE fiscal_year = ? AND ein NOT GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'`)
      .get(fy).n;
    assert.equal(badEin, 0, `FY${fy} must have a valid 9-digit EIN on every award row`);

    // --- queryable through the tools ---
    const search = await callText("search_awards", { fiscal_year: fy, limit: 500 });
    assert.doesNotMatch(search, /No matching Schedule C awards/, `FY${fy} search_awards returned nothing`);
    assert.match(search, new RegExp(`FY${fy}: `), `FY${fy} not in the by-year summary`);

    // EIN-keyed retrieval works for a real EIN that exists this year.
    const topEin = db
      .prepare(`SELECT ein FROM awards WHERE fiscal_year = ? AND ein GLOB '[0-9]*' ORDER BY amount DESC LIMIT 1`)
      .get(fy).ein;
    const byEin = await callText("get_awards_by_ein", { ein: topEin, fiscal_year: fy });
    assert.match(byEin, new RegExp(`FY${fy}: `), `get_awards_by_ein failed to return FY${fy} for EIN ${topEin}`);
  });
}

// Per-year appendix facts — the other half of every award year, loaded in v1.4.0.
for (const [fyStr, exp] of Object.entries(EXPECTED_APPENDIX)) {
  const fy = Number(fyStr);
  test(`FY${fy} appendix — ${exp.count} rows, ${exp.total} total, reachable via source_table`, async () => {
    const agg = db
      .prepare(
        `SELECT COUNT(*) n, COALESCE(SUM(amount),0) total FROM awards
         WHERE fiscal_year = ? AND source_table = 'appendix'`
      )
      .get(fy);
    assert.equal(agg.n, exp.count, `FY${fy} appendix row count`);
    assert.equal(agg.total, exp.total, `FY${fy} appendix dollar total`);

    // Every appendix row carries a stream read off its filename — never blank, never anything else.
    const streams = db
      .prepare(
        `SELECT DISTINCT appendix_stream s FROM awards
         WHERE fiscal_year = ? AND source_table = 'appendix' ORDER BY s`
      )
      .all(fy)
      .map((r) => r.s);
    assert.deepEqual(streams, exp.streams, `FY${fy} appendix streams`);

    // And the rows reach a caller through the real tool.
    const out = await callText("search_awards", { fiscal_year: fy, source_table: "appendix", limit: 5 });
    assert.match(out, /\[appendix: (aging|local|youth)\]/, `FY${fy} appendix rows must be tagged in output`);
  });
}

test("years with header-only appendix CSVs contribute no appendix rows (a known upstream gap, stated not hidden)", () => {
  for (const fy of [2015, 2016, 2017, 2019, 2020]) {
    const n = db
      .prepare(`SELECT COUNT(*) n FROM awards WHERE fiscal_year = ? AND source_table = 'appendix'`)
      .get(fy).n;
    assert.equal(n, 0, `FY${fy} appendix CSVs are header-only upstream; the loader must not invent rows`);
  }
});

test("every awards row carries exactly one of the two known source_table values", () => {
  const bad = db
    .prepare(`SELECT COUNT(*) n FROM awards WHERE source_table NOT IN ('schedule_c','appendix')`)
    .get().n;
  assert.equal(bad, 0, "no award row may carry an unknown or NULL source_table");
  // Main-body rows must never carry a stream — that column belongs to the appendix alone.
  const leaked = db
    .prepare(`SELECT COUNT(*) n FROM awards WHERE source_table = 'schedule_c' AND appendix_stream <> ''`)
    .get().n;
  assert.equal(leaked, 0, "appendix_stream must be empty on main-body rows");
});

test("honesty boundary — FY2009–FY2014 have NO award data in the award tools", () => {
  for (const fy of [2009, 2010, 2011, 2012, 2013, 2014]) {
    const n = db.prepare(`SELECT COUNT(*) n FROM awards WHERE fiscal_year = ?`).get(fy).n;
    assert.equal(n, 0, `FY${fy} must not appear in the awards table (initiatives-only, no EIN)`);
  }
});

test("non-award datasets cover exactly the expected parsed years", () => {
  const yrs = (t, col = "fiscal_year") =>
    db.prepare(`SELECT DISTINCT ${col} y FROM ${t} WHERE ${col} IS NOT NULL ORDER BY y`).all().map((r) => r.y);
  assert.deepEqual(yrs("awards"), [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]);
  assert.deepEqual(yrs("terms"), [2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024, 2025, 2026, 2027]);
  assert.deepEqual(yrs("capital"), [2020, 2022, 2023, 2024, 2025, 2026, 2027]);
  assert.deepEqual(
    yrs("transparency", "source_fy"),
    [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026]
  );
});

test("FY2025 capital is the reconciled Supporting-Detail-Book detail (full schema), not the old Appropriation Changes file", async () => {
  // Regression guard for the loader picking the right FY2025 capital CSV. The old
  // fy25_capital_changes_appropriation.csv has no borough/sub-id/sponsor (and an `action`
  // column); the canonical fy25_capital_projects.csv is the reconciled Council-additions
  // Capital Project Detail in the shared 13-column schema. If the loader ever indexed the
  // wrong file, boro/sponsor would be empty and these assertions would fail.
  const agg = db
    .prepare(
      `SELECT
         COUNT(*) n,
         SUM(CASE WHEN part = 'I' THEN 1 ELSE 0 END) part1,
         SUM(CASE WHEN part = 'II' THEN 1 ELSE 0 END) part2,
         SUM(CASE WHEN TRIM(COALESCE(boro,'')) <> '' THEN 1 ELSE 0 END) boro_pop,
         SUM(CASE WHEN part = 'I' AND TRIM(COALESCE(sponsor,'')) <> '' THEN 1 ELSE 0 END) part1_sponsor_pop,
         COALESCE(SUM(CASE WHEN part = 'I' THEN fy1 ELSE 0 END), 0) part1_fy1,
         COALESCE(SUM(CASE WHEN part = 'II' THEN fy1 ELSE 0 END), 0) part2_fy1
       FROM capital WHERE fiscal_year = 2025`
    )
    .get();
  assert.equal(agg.n, 1508, "FY2025 capital row count (1327 Part I + 181 Part II)");
  assert.equal(agg.part1, 1327, "FY2025 Part I project count");
  assert.equal(agg.part2, 181, "FY2025 Part II non-city project count");
  assert.equal(agg.boro_pop, 1508, "every FY2025 capital row must carry a borough (proves the full schema)");
  assert.equal(agg.part1_sponsor_pop, 1327, "every FY2025 Part I row must carry a sponsor");
  assert.equal(agg.part1_fy1, 775000000, "FY2025 Part I fy1 grand total reconciles to $775,000,000");
  assert.equal(agg.part2_fy1, 158992000, "FY2025 Part II non-city fy1 total reconciles to $158,992,000");

  // No FY2025 row should carry the legacy `action` value — that column belongs to the retired
  // Appropriation Changes file, which is no longer indexed.
  const withAction = db
    .prepare(`SELECT COUNT(*) n FROM capital WHERE fiscal_year = 2025 AND TRIM(COALESCE(action,'')) <> ''`)
    .get().n;
  assert.equal(withAction, 0, "FY2025 capital must not carry the legacy `action` column");

  // And the full schema reaches the caller through the tool: rows show boro + sponsor.
  const out = await callText("search_capital_projects", { fiscal_year: 2025, limit: 50 });
  assert.doesNotMatch(out, /No matching capital projects/, "FY2025 search_capital_projects returned nothing");
  assert.match(out, /FY2025 · /, "FY2025 rows not present in output");
  assert.match(out, /boro:/, "FY2025 output must surface a borough (proves reconciled detail, not old schema)");
  assert.match(out, /sponsor:/, "FY2025 output must surface a sponsor");
});

test("FY2010–FY2013 transparency is flagged low-confidence and surfaces the caveat", async () => {
  // The four low-confidence years are marked in the index.
  const flagged = db
    .prepare(`SELECT DISTINCT source_fy y FROM transparency WHERE low_text_confidence = 1 ORDER BY y`)
    .all()
    .map((r) => r.y);
  assert.deepEqual(flagged, [2010, 2011, 2012, 2013]);
  // A modern year must NOT be flagged.
  const modern = db.prepare(`SELECT COUNT(*) n FROM transparency WHERE source_fy = 2026 AND low_text_confidence = 1`).get().n;
  assert.equal(modern, 0);

  // And the caveat reaches the caller in results for a low-confidence year.
  const out = await callText("search_transparency_resolutions", { fiscal_year: 2012, limit: 50 });
  assert.match(out, /FY2012 Reso/);
  assert.match(out, /LOW-confidence text/);
  assert.match(out, /join on EIN/);
});

test("list_available_fiscal_years reports the true expanded coverage + honesty guard", async () => {
  const out = await callText("list_available_fiscal_years");
  assert.match(out, /Schedule C awards:\s+FY2015, FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025, FY2026, FY2027/);
  assert.match(out, /Capital \(§254\):\s+FY2020, FY2022/);
  assert.match(out, /Transparency Resolutions:\s+FY2010,/);
  assert.match(out, /Award tools .* serve FY2015–FY2027 only/);
  assert.match(out, /FY2009–FY2014 Schedule C is INITIATIVES-ONLY/);
  // Must never claim FY2014 (or earlier) award data exists.
  assert.doesNotMatch(out, /Schedule C awards:[^\n]*FY2014/);
});
