/**
 * search_disclosure_awards in 2.0.0: FY2009, FY2011 and FY2012 from the Council's archived
 * workbooks, the early-snapshot years, FY2010's exclusion, the NYC Open Data cross-reference
 * (od_mocs_id) and the recorded row flags.
 *
 * Expected values are computed from data/disclosure_years.csv and the per-year CSVs, never from
 * the index under test. Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const DB_PATH = join(HERE, "..", "data", "budget.db");
const TOOL = "search_disclosure_awards";

const readCsv = (p) => parse(readFileSync(p, "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const YEARS_CSV = readCsv(join(REPO, "data", "disclosure_years.csv"));
const yearRow = (fy) => YEARS_CSV.find((r) => Number(r.fiscal_year) === fy);
const yy = (fy) => String(fy % 100).padStart(2, "0");
const disclosureCsv = (fy) =>
  readCsv(join(REPO, "data", `fy${yy(fy)}`, "expense_disclosure", `fy${yy(fy)}_expense_awards.csv`));
const usd = (n) => {
  const c = Math.round(n * 100) / 100;
  const s = Math.abs(c).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return c < 0 ? `-$${s}` : `$${s}`;
};
const sum = (rows) => rows.reduce((s, r) => s + Number(r.amount), 0);
const fmt = (n) => n.toLocaleString("en-US");
const noLabel = (note) => note.replace(/^(not loaded|early snapshot):\s*/i, "");

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "disclosure-v2", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

async function call(args) {
  const res = await client.callTool({ name: TOOL, arguments: args });
  return { isError: res.isError === true, text: res.content.map((c) => c.text).join("\n") };
}

test("FY2009, FY2011 and FY2012 are indexed with od_mocs_id, od_match and row_flag exactly as the CSV has them", () => {
  // FAILS if one of the three archived years is skipped, or a cross-reference or flag is dropped,
  // rewritten or attached to the wrong row.
  const db = new Database(DB_PATH, { readonly: true });
  try {
    for (const fy of [2009, 2011, 2012]) {
      const csv = disclosureCsv(fy);
      assert.equal(yearRow(fy).source_kind, "internet_archive", `FY${fy} premise`);
      const got = db
        .prepare("SELECT source_row, od_mocs_id, od_match, row_flag FROM disclosure WHERE fiscal_year = ? ORDER BY source_row")
        .all(fy);
      assert.equal(got.length, csv.length, `FY${fy} rows`);
      const want = csv
        .map((r) => ({ source_row: Number(r.source_row), od_mocs_id: r.od_mocs_id, od_match: r.od_match, row_flag: r.row_flag }))
        .sort((a, b) => a.source_row - b.source_row);
      assert.deepEqual(got, want, `FY${fy}`);
    }
  } finally {
    db.close();
  }
});

test("an early-snapshot year's Cleared total is labeled as not a headline, with the reason and its Internet Archive source", async () => {
  // FAILS if FY2009 is presented under "Cleared (headline)", if the EARLY SNAPSHOT note is not
  // the one data/disclosure_years.csv records, or if the capture timestamp and original URL are missing.
  const y = yearRow(2009);
  assert.equal(y.early_snapshot, "yes", "fixture premise");
  const rows = disclosureCsv(2009);
  const cleared = rows.filter((r) => r.status_norm === "cleared");
  const { isError, text } = await call({ fiscal_year: 2009, limit: 1 });
  assert.ok(!isError, text);
  assert.ok(text.includes(`Cleared (early snapshot, not a headline): ${fmt(cleared.length)} row(s), ${usd(sum(cleared))}`), text.slice(0, 400));
  assert.doesNotMatch(text, /Cleared \(headline\)/);
  assert.ok(text.includes(`EARLY SNAPSHOT: ${noLabel(y.note)}`));
  assert.ok(text.includes(`Internet Archive capture ${y.wayback_timestamp} of ${y.url}`));
  assert.ok(text.includes(`retrieved ${y.retrieved} (sha256 ${y.sha256.slice(0, 12)})`));
});

test("every answer states the coverage: FY2010 not included, FY2009 and FY2013 early", async () => {
  // FAILS if an answer for an ordinary year omits that FY2010 is excluded or which years are
  // early snapshots, or wrongly marks that ordinary year as early.
  const { text } = await call({ fiscal_year: 2026, limit: 1 });
  assert.match(text, /Cleared \(headline\):/);
  assert.doesNotMatch(text, /EARLY SNAPSHOT/);
  assert.ok(text.includes("Coverage: FY2009, FY2011–FY2027. FY2010 is NOT included"));
  assert.ok(text.includes("Early snapshots, whose Cleared totals are not headline figures: FY2009, FY2013."));
  const none = await call({ legal_name: "zz-no-such-grantee-zz" });
  assert.ok(none.text.includes("FY2010 is NOT included"), "no-match answers state it too");
});

test("a multi-year answer that mixes early and ordinary years says so and marks the early years", async () => {
  // FAILS if a total spanning FY2009 and later years reads as a clean headline with no warning,
  // or the per-year split does not mark FY2009.
  const ein = "132744557"; // 7 Loaves, Inc.: FY2009 row 2 and later years
  const years = [...new Set(YEARS_CSV.filter((r) => r.loaded === "yes").map((r) => Number(r.fiscal_year))
    .filter((fy) => disclosureCsv(fy).some((r) => r.ein === ein)))];
  assert.ok(years.includes(2009) && years.some((fy) => fy > 2013), `fixture premise: ${years}`);
  const { text } = await call({ ein, limit: 1 });
  assert.match(text, /Includes early-snapshot year\(s\) FY2009/);
  assert.match(text, /^  FY2009 \(early snapshot\): cleared /m);
  assert.doesNotMatch(text, /^  FY2026 \(early snapshot\)/m);
});

test("FY2010 returns the reason it is excluded, not an empty search", async () => {
  // FAILS if FY2010 reads as "no matching designations" (as if the Council funded nothing), is
  // an error, or loses the recorded reason.
  const y = yearRow(2010);
  assert.equal(y.loaded, "no", "fixture premise");
  const { isError, text } = await call({ fiscal_year: 2010, legal_name: "a" });
  assert.equal(isError, false);
  assert.match(text, /^FY2010 is not in the disclosure dataset: /);
  assert.ok(text.includes(noLabel(y.note)));
  assert.doesNotMatch(text, /matching designation/);
});

test("od_mocs_id and mocs_id are exact filters, case and spacing ignored", async () => {
  // FAILS if either is a substring match ('FY09 28' must not match 'FY09 2838'), is case-sensitive,
  // or the row stops showing the Open Data cross-reference and how its amounts agree.
  const csv09 = disclosureCsv(2009);
  const target = csv09.find((r) => r.od_mocs_id === "FY09 2838");
  assert.ok(target, "fixture premise");
  const want = csv09.filter((r) => r.od_mocs_id === "FY09 2838");
  const res = await call({ od_mocs_id: "  fy09 2838 " });
  assert.match(res.text, new RegExp(`^${want.length} matching designation`, "m"));
  assert.ok(res.text.includes(`NYC Open Data 4d7f-74pe MOCS ID FY09 2838 (cross-reference; amounts agree: ${target.od_match})`));
  const part = await call({ od_mocs_id: "FY09 28" });
  assert.match(part.text, /^No matching designations/);

  const csv26 = disclosureCsv(2026);
  const m = csv26.find((r) => r.mocs_id !== "").mocs_id;
  const wantM = csv26.filter((r) => r.mocs_id === m);
  const r2 = await call({ mocs_id: m.toLowerCase() });
  assert.match(r2.text, new RegExp(`^${wantM.length} matching designation`, "m"));
  const empty = await call({ od_mocs_id: " " });
  assert.equal(empty.isError, true);
});

test("row_flag not_an_award rows stay in the totals and are counted in a note", async () => {
  // FAILS if a flagged row is dropped from the totals, or if the answer does not say how many
  // matched rows carry the flag and what they sum to.
  const rows = disclosureCsv(2009);
  const flagged = rows.filter((r) => r.row_flag === "not_an_award");
  assert.equal(flagged.length, 2, "fixture premise");
  const { text } = await call({ fiscal_year: 2009, limit: 1 });
  assert.ok(text.includes(`Note: ${flagged.length} matched row(s), ${usd(sum(flagged))}, carry row_flag not_an_award`));
  assert.ok(text.includes(`All statuses (not a headline figure): ${fmt(rows.length)} row(s), ${usd(sum(rows))}`));
  const one = await call({ fiscal_year: 2009, legal_name: "Provider's Choice" });
  assert.match(one.text, /row_flag not_an_award: printed as a designation but not a grant/);
  const clean = await call({ fiscal_year: 2026, limit: 1 });
  assert.doesNotMatch(clean.text, /carry row_flag/);
});
