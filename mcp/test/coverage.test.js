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
const EXPECTED_AWARDS = {
  2015: { count: 652, total: 73199837 },
  2016: { count: 335, total: 89917012 },
  2017: { count: 364, total: 89901487 },
  2018: { count: 480, total: 102716956 },
  2019: { count: 846, total: 181026931 },
  2020: { count: 2841, total: 258762385 },
  2021: { count: 1800, total: 201529188 },
  2022: { count: 1479, total: 221761943 },
  2023: { count: 1824, total: 260064374 },
  2024: { count: 5299, total: 398000074 },
  2025: { count: 5609, total: 410223110 },
  2026: { count: 5806, total: 483619905 },
  2027: { count: 6085, total: 600928032 },
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
    const agg = db
      .prepare(`SELECT COUNT(*) n, COALESCE(SUM(amount),0) total FROM awards WHERE fiscal_year = ?`)
      .get(fy);
    assert.equal(agg.n, exp.count, `FY${fy} award count`);
    assert.equal(agg.total, exp.total, `FY${fy} award dollar total`);
    assert.ok(agg.total > 1_000_000, `FY${fy} total should be a plausible (>$1M) figure`);

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
