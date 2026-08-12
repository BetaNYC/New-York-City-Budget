/**
 * Schedule C appendix ingest — Phase 0.5 (v1.4.0).
 *
 * Before this release `scripts/build-index.mjs` read only `*_schedule_c_awards.csv`. The 28,575
 * rows parsed into the per-year `schedule_c` appendix CSVs reached NO consumer: they were on
 * disk, committed, QA'd, and invisible to every tool.
 *
 * THE CANONICAL CASE (the first test below). Bard College, EIN 14-1713034, had three FY2023
 * designations sitting in `data/fy23/schedule_c/fy23_appendix_b_local.csv` — Abreu $5,000,
 * Brooks-Powers $10,000, Powers $5,000, $20,000 across three members — and ZERO FY2023 rows in
 * the index. All three are independently confirmed in the Council's own published disclosure
 * spreadsheet (`source/expense-funding-disclosure/funded_disclosure_FY2023.xlsx`, `Source`
 * column = "Local"), so they are real designations the MCP was failing to report, not an
 * extraction artifact.
 *
 * "Absent → present" is encoded here as a pair, because a test can only observe the after state:
 * the rows are now returned, AND `source_table='schedule_c'` (the exact pre-1.4.0 result set)
 * still returns zero for FY2023. The second half is what proves the first half is new data
 * rather than a number that quietly moved.
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
const BARD = "141713034";

let client;
let db;

before(async () => {
  const [c, s] = InMemoryTransport.createLinkedPair();
  await server.connect(s);
  client = new Client({ name: "appendix-ingest-test", version: "0" }, { capabilities: {} });
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

test("CANONICAL CASE — Bard College FY2023: absent before v1.4.0, present now", async () => {
  // Present now, through the real tool.
  const out = await callText("get_awards_by_ein", { ein: "14-1713034", fiscal_year: 2023 });
  assert.doesNotMatch(out, /No Schedule C awards for EIN/, "FY2023 Bard designations must be reachable");
  assert.match(out, /Bard College/);
  assert.match(out, /FY2023: 3 award\(s\), \$20,000/, "three FY2023 designations totalling $20,000");
  for (const member of ["Abreu", "Brooks-Powers", "Powers"]) {
    assert.match(out, new RegExp(member), `sponsoring member ${member} must appear`);
  }
  // Tagged as appendix, so nobody mistakes them for main-body Schedule C rows.
  assert.match(out, /\[appendix: local\]/, "appendix provenance must be visible in the output");

  // The other half: the pre-1.4.0 result set is unchanged — it still has nothing for FY2023.
  const before = await callText("get_awards_by_ein", {
    ein: "14-1713034",
    fiscal_year: 2023,
    source_table: "schedule_c",
  });
  assert.match(
    before,
    /No Schedule C awards for EIN/,
    "these rows are NEW to the index, not a main-body figure that shifted"
  );

  // And at the data layer, matching the three CSV lines exactly.
  const rows = db
    .prepare(
      `SELECT member, amount, source_table, appendix_stream FROM awards
       WHERE ein = ? AND fiscal_year = 2023 ORDER BY member`
    )
    .all(BARD);
  assert.equal(rows.length, 3);
  assert.deepEqual(
    rows.map((r) => [r.member, r.amount]),
    [["Abreu", 5000], ["Brooks-Powers", 10000], ["Powers", 5000]]
  );
  assert.ok(rows.every((r) => r.source_table === "appendix" && r.appendix_stream === "local"));
});

test("Bard's gap was never FY2023-only — every appendix year now resolves", () => {
  // The FY2023 total was zero, which made it the clean test case; FY2024–FY2027 were merely
  // INCOMPLETE (main-body rows present, appendix designations missing). Both are fixed.
  const byYear = db
    .prepare(
      `SELECT fiscal_year fy, COUNT(*) n FROM awards
       WHERE ein = ? AND source_table = 'appendix' GROUP BY fiscal_year ORDER BY fiscal_year`
    )
    .all(BARD);
  assert.ok(byYear.length >= 6, `expected Bard appendix rows in several years, got ${JSON.stringify(byYear)}`);
  assert.ok(
    byYear.some((r) => r.fy === 2023 && r.n === 3),
    "FY2023 remains the three-row canonical case"
  );
});

test("the whole appendix corpus landed — 28,575 rows, and no main-body row moved", () => {
  const n = db.prepare(`SELECT COUNT(*) n FROM awards WHERE source_table = 'appendix'`).get().n;
  assert.equal(n, 28575, "all parsed appendix rows must be indexed");
  const main = db.prepare(`SELECT COUNT(*) n FROM awards WHERE source_table = 'schedule_c'`).get().n;
  assert.equal(main, 33638, "the main-body corpus must be byte-for-byte the pre-1.4.0 33,638 rows");
  const total = db.prepare(`SELECT COUNT(*) n, SUM(amount) s FROM awards`).get();
  assert.equal(total.n, 62213);
  assert.equal(total.s, 3741615569, "3,388,618,294 main body + 352,997,275 appendix");
});

test("source_table='schedule_c' reproduces the pre-1.4.0 result set exactly (the cheap reversal)", async () => {
  // If the mixed default turns out to be the wrong call, this is the escape hatch, so it has to
  // be exact rather than approximately right.
  const agg = db
    .prepare(
      `SELECT COUNT(*) n, SUM(amount) s FROM awards WHERE fiscal_year = 2023 AND source_table = 'schedule_c'`
    )
    .get();
  assert.equal(agg.n, 1848, "FY2023 main-body count as published from v1.3.x");
  assert.equal(agg.s, 262419214, "FY2023 main-body total as published from v1.3.x");

  const out = await callText("search_awards", { fiscal_year: 2023, source_table: "schedule_c", limit: 500 });
  assert.doesNotMatch(out, /\[appendix/, "the schedule_c slice must contain no appendix rows at all");
  assert.doesNotMatch(out, /By source:/, "a single-source result needs no split");
});

test("a mixed result set says so, instead of quietly returning a bigger number", async () => {
  const out = await callText("search_awards", { fiscal_year: 2023, limit: 500 });
  assert.match(out, /By source: main-body Schedule C/, "the split must be stated");
  assert.match(out, /appendix \(aging\/local\/youth\)/);
  assert.match(out, /NOT returned by @betanyc\/nyc-budget-mcp before v1\.4\.0/, "must warn about published totals");
  assert.match(out, /source_table:"schedule_c"/, "must name the escape hatch");
});

test("appendix rows carry no invented category, initiative, award_type — or agency where the column is absent", () => {
  // The four gap fields are stored EMPTY. Guessing DFTA-for-aging / DYCD-for-youth would have
  // been plausible and wrong: appendix B records MOCJ on Bard's FY2023 local rows, so agency is
  // demonstrably not a constant per stream.
  const invented = db
    .prepare(
      `SELECT COUNT(*) n FROM awards WHERE source_table = 'appendix'
       AND (category <> '' OR initiative <> '' OR award_type <> '')`
    )
    .get().n;
  assert.equal(invented, 0, "category/initiative/award_type do not exist in the appendix and must stay empty");

  const agencyOnAgingYouth = db
    .prepare(
      `SELECT COUNT(*) n FROM awards WHERE source_table = 'appendix'
       AND appendix_stream IN ('aging','youth') AND agency <> ''`
    )
    .get().n;
  assert.equal(agencyOnAgingYouth, 0, "the aging/youth appendix CSVs have no agency column — none may be fabricated");

  // Appendix B does have one, and it must survive the load rather than being dropped.
  const localWithAgency = db
    .prepare(
      `SELECT COUNT(*) n FROM awards WHERE source_table = 'appendix' AND appendix_stream = 'local' AND agency <> ''`
    )
    .get().n;
  assert.ok(localWithAgency > 0, "appendix B carries an agency column and it must be loaded");
});

test("filtering on a main-body-only field excludes appendix rows (they have no such value to match)", async () => {
  const out = await callText("search_awards", { initiative: "Digital Inclusion and Literacy", limit: 500 });
  assert.doesNotMatch(out, /\[appendix/, "an initiative filter cannot match a row with no initiative");
});

test("list_available_fiscal_years reports appendix coverage as a subset, and warns about totals", async () => {
  const out = await callText("list_available_fiscal_years");
  assert.match(out, /appendix rows:\s+FY2018, FY2021, FY2022, FY2023, FY2024, FY2025, FY2026, FY2027/);
  assert.match(out, /EXCEED those published from v1\.3\.x/, "the coverage report must own the behavior change");
});
