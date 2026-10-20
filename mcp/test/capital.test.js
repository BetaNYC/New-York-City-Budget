/**
 * search_council_capital and compare_capital_to_omb (2.0.0) — the Council capital dataset built
 * from structured sources (data/capital/), and the repo's by-budget-line comparison with OMB.
 *
 * Expected values are computed here from data/capital/*.csv, the source manifests and the
 * committed source files (hashed here), never from the index under test. Each test says what
 * result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
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

const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const CAP = readCsv("data/capital/council_capital_awards.csv");
const CMP = readCsv("data/capital/council_vs_omb_by_budget_line.csv");
const fmt = (n) => n.toLocaleString("en-US");
const usd = (n) => {
  const c = Math.round(n * 100) / 100;
  const s = Math.abs(c).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return c < 0 ? `-$${s}` : `$${s}`;
};
const own = (rows) => rows.filter((r) => r.amount !== "" && r.amount_fy === r.report_year);
const sum = (rows) => rows.reduce((s, r) => s + Number(r.amount), 0);
const ownLine = (rows) =>
  `For the list's own year (amount_fy = report year): ${fmt(own(rows).length)} row(s), ${usd(sum(own(rows)))}`;
const YEARS = [...new Set(CAP.map((r) => Number(r.report_year)))].sort((a, b) => a - b);

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "capital-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

async function call(name, args) {
  const res = await client.callTool({ name, arguments: args });
  return { isError: res.isError === true, text: res.content.map((c) => c.text).join("\n") };
}
const cap = (args) => call("search_council_capital", args);
const omb = (args) => call("compare_capital_to_omb", args);
const matchedOf = (text) => Number((/^([\d,]+) matching row/m.exec(text) ?? [, "-1"])[1].replace(/,/g, ""));
const shownAmounts = (text) =>
  [...text.matchAll(/^FY\d{4} list · (-?)\$([\d,.]+) for FY/gm)].map((m) => Number(m[1] + m[2].replace(/,/g, "")));

// ---------------------------------------------------------------- the index

test("the index holds every capital row, per report year, with amounts and flags as the CSV has them", () => {
  // FAILS if a row or a year is dropped or doubled, an amount is mis-parsed, a split record gets
  // an invented amount (0 instead of NULL), or FY2018 appears from nowhere.
  assert.deepEqual(YEARS, [2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027], "fixture premise");
  const db = new Database(DB_PATH, { readonly: true });
  try {
    for (const fy of YEARS) {
      const rows = CAP.filter((r) => Number(r.report_year) === fy);
      const got = db
        .prepare(
          `SELECT COUNT(*) AS n, SUM(CASE WHEN amount_fy = report_year THEN amount END) AS own,
             SUM(amount IS NULL) AS unknown FROM capital_council WHERE report_year = ?`
        )
        .get(fy);
      assert.equal(got.n, rows.length, `FY${fy} rows`);
      assert.equal(got.own ?? 0, sum(own(rows)), `FY${fy} own-year amount`);
      assert.equal(got.unknown, rows.filter((r) => r.row_flag === "split_record_amount_unknown").length, `FY${fy} split`);
    }
    assert.equal(db.prepare("SELECT COUNT(*) AS n FROM capital_council WHERE report_year = 2018").get().n, 0);
  } finally {
    db.close();
  }
});

test("each report year cites its one source file, hashed at build and equal to its manifest", () => {
  // FAILS if a year's provenance names the wrong file, a sha256 that is not the committed file's,
  // or a retrieval date its manifest does not record.
  const manifests = {
    "source/wayback-council/": readCsv("source/wayback-council/MANIFEST.csv"),
    "source/expense-funding-disclosure/": readCsv("source/expense-funding-disclosure/MANIFEST.csv"),
    "source/open-data-t474-a92g/": readCsv("source/open-data-t474-a92g/MANIFEST.csv"),
  };
  const db = new Database(DB_PATH, { readonly: true });
  try {
    for (const fy of YEARS) {
      const files = [...new Set(CAP.filter((r) => Number(r.report_year) === fy).map((r) => r.source_file))];
      assert.equal(files.length, 1, `FY${fy} premise: one file`);
      const src = db.prepare("SELECT * FROM capital_sources WHERE report_year = ?").get(fy);
      assert.equal(src.source_file, files[0]);
      const sha = createHash("sha256").update(readFileSync(join(REPO, files[0]))).digest("hex");
      assert.equal(src.sha256, sha, `FY${fy} sha256`);
      const [prefix, man] = Object.entries(manifests).find(([p]) => files[0].startsWith(p));
      const m = man.find((r) => r.file === files[0].slice(prefix.length));
      assert.equal(m.sha256, sha, `FY${fy} manifest sha256`);
      assert.equal(src.retrieved, (m.retrieved_at ?? m.retrieved).slice(0, 10), `FY${fy} retrieved`);
    }
  } finally {
    db.close();
  }
});

// ---------------------------------------------------------------- totals and ordering

test("the true match count and totals cover every match, however small the page", async () => {
  // FAILS if the count or a total is computed from the shown page, or out-year amounts are folded
  // into the list-year total.
  const rows = CAP.filter((r) => r.report_year === "2022");
  const outs = rows.filter((r) => r.amount !== "" && r.amount_fy !== r.report_year);
  assert.ok(outs.length > 0, "fixture premise: FY2022 lists out-year amounts");
  for (const limit of [1, 500]) {
    const { text } = await cap({ fiscal_year: 2022, limit });
    assert.equal(matchedOf(text), rows.length, `limit ${limit}`);
    assert.ok(text.includes(ownLine(rows)), `limit ${limit}: own-year total`);
    const byFy = {};
    for (const r of outs) (byFy[r.amount_fy] ??= []).push(r);
    for (const [fy, rs] of Object.entries(byFy)) assert.ok(text.includes(`FY${fy} ${fmt(rs.length)} row(s) ${usd(sum(rs))}`), `out-year FY${fy}`);
  }
  const { text } = await cap({ fiscal_year: 2022, limit: 1 });
  assert.match(text, new RegExp(`Showing 1 of ${fmt(rows.length)}`));
});

test("rows are the highest amounts of all years, ordered before the limit", async () => {
  // FAILS if the limit is applied before the sort (a year-first sort shows only FY2015) or the
  // page is not in descending order.
  const top = CAP.filter((r) => r.amount !== "").map((r) => Number(r.amount)).sort((a, b) => b - a).slice(0, 50);
  const { text } = await cap({});
  assert.deepEqual(shownAmounts(text), top);
  assert.ok(new Set([...text.matchAll(/^FY(\d{4}) list/gm)].map((m) => m[1])).size > 1);
});

test("a split record shows no amount and stays out of every total", async () => {
  // FAILS if a split_record_amount_unknown row is given an amount, summed as 0 silently, or hidden.
  const flagged = CAP.filter((r) => r.report_year === "2020" && r.row_flag === "split_record_amount_unknown");
  assert.equal(flagged.length, 2, "fixture premise");
  const { text } = await cap({ fiscal_year: 2020, limit: 500 });
  assert.ok(text.includes(`Amount unknown (split records; in no total): ${flagged.length} row(s)`));
  // FY2020 has 1,662 rows: rows without an amount sort after every amount, so none is on this page.
  assert.equal((text.match(/amount unknown \(split_record_amount_unknown/g) ?? []).length, 0, "no-amount rows sort last");
  const all = await cap({ fiscal_year: 2020, title: flagged[0].title, limit: 500 });
  assert.match(all.text, /amount unknown \(split_record_amount_unknown/);
});

// ---------------------------------------------------------------- filters

test("budget_line is exact on the normal form; a separator-less line is refused", async () => {
  // FAILS if 'p  d018' or 'P-D018' does not equal 'P D018', if budget_line matches by substring
  // ('P D01' matching P D018), or if 'PD018' is guessed at instead of refused.
  const want = CAP.filter((r) => r.budget_line_norm === "P D018");
  assert.ok(want.length > 0);
  for (const v of ["P D018", "p  d018", "P-D018"]) {
    const { text } = await cap({ budget_line: v, limit: 1 });
    assert.equal(matchedOf(text), want.length, v);
  }
  const part = await cap({ budget_line: "P D01" });
  assert.match(part.text, /^No matching rows/);
  const bad = await cap({ budget_line: "PD018" });
  assert.equal(bad.isError, true);
  assert.match(bad.text, /where the agency code ends cannot be told/);
});

test("project_id is exact, ignoring case and runs of spaces", async () => {
  // FAILS if project_id is a substring match or is case- or spacing-sensitive.
  const norm = (v) => v.trim().replace(/\s+/g, " ").toUpperCase();
  const want = CAP.filter((r) => norm(r.project_id) === "E CN005");
  assert.ok(want.length > 1, "fixture premise: the same ID in more than one year");
  const { text } = await cap({ project_id: "e   cn005", limit: 1 });
  assert.equal(matchedOf(text), want.length);
  const part = await cap({ project_id: "E CN00" });
  assert.match(part.text, /^No matching rows/);
});

test("sponsor is a literal substring that lists every value it blended; sponsor_exact is one value", async () => {
  // FAILS if co-sponsored rows are summed with sole-sponsor rows silently, if sponsor_exact is a
  // substring match, or if '_' acts as a LIKE wildcard.
  const sub = CAP.filter((r) => r.sponsor.toLowerCase().includes("rivera"));
  const exact = CAP.filter((r) => r.sponsor.trim().toLowerCase() === "rivera");
  assert.ok(sub.length > exact.length && exact.length > 0, "fixture premise");
  const s = await cap({ sponsor: "Rivera", limit: 1 });
  assert.equal(matchedOf(s.text), sub.length);
  assert.match(s.text, /the sponsor filter is a substring match and matched \d+ different values/);
  assert.ok(s.text.includes(ownLine(sub)));
  const e = await cap({ sponsor_exact: " rivera ", limit: 1 });
  assert.equal(matchedOf(e.text), exact.length);
  assert.doesNotMatch(e.text, /substring match/);
  assert.equal(CAP.filter((r) => r.sponsor.includes("_")).length, 0, "premise: no '_' in any sponsor");
  const w = await cap({ sponsor: "_" });
  assert.match(w.text, /^No matching rows/);
});

test("council_district matches a district inside the workbook's list, never a t474 row", async () => {
  // FAILS if district 3 matches '33' or '13' (substring), if the zero-padded '03' is missed, or if
  // a t474 row (district lists collapsed by Open Data) is matched.
  const tokens = (r) => r.council_district.split(",").map((t) => t.trim()).filter(Boolean).map((t) => (/^\d{1,2}$/.test(t) ? String(Number(t)) : t));
  const want = CAP.filter((r) => r.source_kind === "council_workbook" && tokens(r).includes("3"));
  assert.ok(want.length > 0);
  const { text } = await cap({ council_district: 3, limit: 1 });
  assert.equal(matchedOf(text), want.length);
  assert.ok(text.includes(ownLine(want)));
  assert.match(text, /Rows from FY2019–FY2025 \(NYC Open Data t474-a92g\) never match it/);
  const t474 = await cap({ council_district: 3, fiscal_year: 2022 });
  assert.match(t474.text, /^No matching rows/);
  const bad = await cap({ council_district: 100 });
  assert.equal(bad.isError, true);
});

test("borough is exact and case-sensitive: the printed lower-case codes are not folded into upper case", async () => {
  // FAILS if 'K' also matches FY2016's lower-case 'k' (an unconfirmed reading), or vice versa.
  const K = CAP.filter((r) => r.borough === "K");
  const k = CAP.filter((r) => r.borough === "k");
  assert.ok(k.length > 0, "fixture premise");
  assert.equal(matchedOf((await cap({ borough: "K", limit: 1 })).text), K.length);
  assert.equal(matchedOf((await cap({ borough: "k", limit: 1 })).text), k.length);
  assert.equal((await cap({ borough: "Brooklyn" })).isError, true);
});

test("title is a literal, case-insensitive substring; min/max bound inclusively", async () => {
  // FAILS if '%' or '_' acts as a wildcard, if a bound is exclusive, or if min > max quietly
  // returns nothing.
  const lib = CAP.filter((r) => r.title.toLowerCase().includes("library"));
  assert.equal(matchedOf((await cap({ title: "LiBrArY", limit: 1 })).text), lib.length);
  assert.match((await cap({ title: "%" })).text, /^No matching rows/);
  const band = CAP.filter((r) => r.amount !== "" && Number(r.amount) >= 1000000 && Number(r.amount) <= 2000000);
  assert.equal(matchedOf((await cap({ min_amount: 1000000, max_amount: 2000000, limit: 1 })).text), band.length);
  assert.equal((await cap({ min_amount: 5, max_amount: 1 })).isError, true);
  assert.equal((await cap({ limit: 0 })).isError, true);
});

// ---------------------------------------------------------------- honesty

test("FY2018 answers with why it is missing; every answer carries the caveat and names its sources", async () => {
  // FAILS if FY2018 reads as an empty year, or an answer drops the caveat (missing FY2018,
  // unconfirmed codes, no contract-level link) or the per-year source line.
  const f18 = await cap({ fiscal_year: 2018 });
  assert.equal(f18.isError, false);
  assert.match(f18.text, /^FY2018 is in no source found/);
  const { text } = await cap({ sponsor_exact: "Restler", limit: 1 });
  assert.match(text, /FY2018 is missing/);
  assert.match(text, /borough A, council district 80, ID prefix CC and ID type PN .* unconfirmed/);
  assert.match(text, /there is no contract-level data here/);
  const years = [...new Set(CAP.filter((r) => r.sponsor.trim() === "Restler").map((r) => r.report_year))];
  assert.ok(years.length > 1, "fixture premise: Restler spans several years");
  for (const fy of years)
    assert.match(text, new RegExp(`^  FY${fy}: (Council capital workbook|NYC Open Data t474-a92g)`, "m"), `source line FY${fy}`);
  assert.match(text, /NYC Open Data t474-a92g \(published by the Council\), source\/open-data-t474-a92g\/t474-a92g\.csv\.gz/);
  assert.match(text, /Open Data says its rows were last updated 2025-12-17/);
});

// ---------------------------------------------------------------- compare_capital_to_omb

test("compare_capital_to_omb: verdict counts per report year equal the CSV's", async () => {
  // FAILS if a verdict is miscounted, a year dropped, or the counts come from the shown page.
  const years = [...new Set(CMP.map((r) => Number(r.report_year)))];
  assert.deepEqual(years, [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027], "fixture premise");
  for (const fy of years) {
    const rows = CMP.filter((r) => Number(r.report_year) === fy);
    const { text } = await omb({ report_year: fy, limit: 1 });
    const c = (v) => rows.filter((r) => r.verdict === v).length;
    assert.ok(
      text.includes(`match (both years equal) ${c("match")} · differ ${c("differ")} · Council only (no OMB line) ${c("council_only")} · OMB only (no Council row) ${c("omb_only")}`),
      `FY${fy}`
    );
    const lines = new Set(rows.map((r) => r.budget_line_norm)).size;
    assert.match(text, new RegExp(`^${rows.length} line-year comparison\\(s\\) \\(report year, budget line\\) over ${lines} distinct budget line\\(s\\)`, "m"));
  }
});

test("compare_capital_to_omb: all years say 1,425 line-year comparisons over 515 budget lines", async () => {
  // Red team S5. FAILS if the tool calls 1,425 (report year, line) pairs "budget lines".
  const { text } = await omb({ limit: 1 });
  assert.equal(CMP.length, 1425, "fixture premise");
  assert.match(text, /^1,425 line-year comparison\(s\) \(report year, budget line\) over 515 distinct budget line\(s\)/m);
});

test("compare_capital_to_omb: a Council row off the Council series is reported, never silently dropped", async () => {
  // Red team S2. FAILS if FY2021 PW MN02A ($304,000, Constantinides) is not named as not compared
  // on an FY2021 answer and on a direct query for its line, or appears on a verdict-filtered one.
  const off = CAP.filter((r) => Number(r.report_year) >= 2019 && r.budget_line_norm && !r.budget_line_norm.split(" ")[1].startsWith("D"));
  assert.deepEqual(off.map((r) => [r.report_year, r.budget_line_norm, r.amount]), [["2021", "PW MN02A", "304000"]], "fixture premise");
  const y = await omb({ report_year: 2021, limit: 1 });
  assert.match(y.text, /Not compared: 1 Council capital row\(s\).*FY2021 PW MN02A, Constantinides, "BIOBUS, INC\.-NEW BIOBUS MOBILE SCIENCE LAB", \$304,000 for FY2021/);
  const line = await omb({ budget_line: "PW MN02A" });
  assert.match(line.text, /No budget lines matched/);
  assert.match(line.text, /Not compared: 1 Council capital row\(s\)/);
  const v = await omb({ report_year: 2021, verdict: "match", limit: 1 });
  assert.doesNotMatch(v.text, /Not compared/);
  const y24 = await omb({ report_year: 2024, limit: 1 });
  assert.doesNotMatch(y24.text, /Not compared/);
});

test("compare_capital_to_omb: one line's figures, a missing side shown as absent, disagreements first", async () => {
  // FAILS if a line's figures differ from the CSV, if an absent Council side prints as $0, or if
  // matches crowd out the lines that disagree.
  const r = CMP.find((x) => x.report_year === "2027" && x.budget_line_norm === "HD D022");
  const { text } = await omb({ report_year: 2027, budget_line: "hd-d022" });
  assert.ok(text.includes(`FY2027: Council ${usd(Number(r.council_y1))} / OMB ${usd(Number(r.omb_y1))}`));
  const o = CMP.find((x) => x.verdict === "omb_only");
  const ot = (await omb({ report_year: Number(o.report_year), budget_line: o.budget_line_norm })).text;
  assert.ok(ot.includes(`Council — / OMB ${usd(Number(o.omb_y1))}`), ot.slice(0, 400));
  const page = (await omb({ report_year: 2027, limit: 15 })).text;
  const shown = [...page.matchAll(/^FY2027 · \S+ \S+ · (\S+)/gm)].map((m) => m[1]);
  const nonMatch = CMP.filter((x) => x.report_year === "2027" && x.verdict !== "match").length;
  assert.ok(shown.slice(0, nonMatch).every((v) => v !== "match"), shown.join(","));
  assert.match(page, /this is BetaNYC's arithmetic, not a Council or OMB reconciliation/);
  const out = await omb({ report_year: 2016 });
  assert.match(out.text, /^FY2016 is not in the comparison/);
});
