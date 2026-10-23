/**
 * The four tools over the checked PDF tables (#212) and the rules they must keep (W5, #214):
 *
 *   - only reviewed and closed family-years are served, never a row whose family-year is not in
 *     pdf_years at that status (a synthetic file with planted rows proves the query gate, not
 *     just the build's);
 *   - every served row carries its status label;
 *   - hidden text is always labeled;
 *   - links are built from a commit id only, never from a branch;
 *   - "no dollar amount" rows are never in a sum;
 *   - the MCP's answers equal the explorer's queries (viz/explorer/src/query/pdf.js) for the same
 *     filters, and the committed CSVs;
 *   - without the download, each tool says how to add it.
 *
 * The tables come from pretest (.pdf-test/release/pdf-tables.db). Each test says what result
 * would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdirSync, readFileSync, rmSync, symlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { closePdfTables } from "../dist/pdfdata.js";
import { searchScheduleC, searchTransparency, searchCapitalBook, searchTerms, needsInfoLabel, STATUS_LABEL, HIDDEN_TEXT_LABEL } from "../dist/pdfquery.js";
import { fold } from "../dist/fold.js";
import * as explorer from "../../viz/explorer/src/query/pdf.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const TABLES_DB = join(MCP, ".pdf-test", "release", "pdf-tables.db");
const TMP = join(MCP, ".pdf-test", "tools");
const WITH = join(TMP, "with");
const WITHOUT = join(TMP, "without");
const SYNTH = join(TMP, "synthetic");
const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });

const PDF_TOOLS = ["search_schedule_c_awards", "search_transparency_changes", "search_capital_book", "search_terms_conditions"];

let client;
let db;
before(async () => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(WITH, "pdf-tables"), { recursive: true });
  mkdirSync(WITHOUT, { recursive: true });
  symlinkSync(TABLES_DB, join(WITH, "pdf-tables", "pdf-tables.db"));
  process.env.NYC_BUDGET_DATA_DIR = WITH;
  delete process.env.NYC_BUDGET_PDF_DATA;
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "pdf-tools-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
  db = new Database(TABLES_DB, { readonly: true });
  db.function("fold", { deterministic: true }, (v) => fold(v == null ? "" : String(v)));
});
after(async () => {
  await client.close();
  db.close();
  closePdfTables();
  rmSync(TMP, { recursive: true, force: true });
});

/** Point the server at a data folder (the tools read NYC_BUDGET_DATA_DIR on every call). */
function useDir(dir) {
  closePdfTables();
  process.env.NYC_BUDGET_DATA_DIR = dir;
}

async function call(name, args = {}) {
  const res = await client.callTool({ name, arguments: args });
  return { text: res.content.map((c) => c.text).join("\n"), isError: !!res.isError };
}

/** The row blocks of an answer: from each line starting "FY" after "Rows:"/"Items", to the next. */
function rowBlocks(text) {
  const start = text.search(/^(Rows:|Items \()/m);
  if (start < 0) return [];
  const body = text.slice(start).split(/\n(?=FY\d{4} )/).slice(1);
  return body.map((b) => b.split("\n\nCaveat:")[0]);
}

const COMMIT = () => db.prepare("SELECT value FROM meta WHERE key = 'source_commit'").get().value;

// ---------------------------------------------------------------- the tool surface

test("the four PDF tools are listed, with the four spreadsheet tools", async () => {
  // FAILS if a PDF tool is missing, or search_disclosure_awards was merged into Schedule C.
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name).sort(), [...PDF_TOOLS, "search_disclosure_awards", "search_council_capital", "compare_capital_to_omb", "list_available_fiscal_years"].sort());
});

test("without the download, each PDF tool says how to add it (not an error, no rows)", async () => {
  // FAILS if a tool errors, returns rows, or omits either way to add the tables.
  useDir(WITHOUT);
  try {
    for (const name of PDF_TOOLS) {
      const r = await call(name, { fiscal_year: 2026 });
      assert.equal(r.isError, false, name);
      assert.match(r.text, /optional download that is not part of the npm package/, name);
      assert.match(r.text, /npx @betanyc\/nyc-budget-mcp download --pdf-tables/, name);
      assert.match(r.text, /NYC_BUDGET_PDF_DATA=on/, name);
      assert.ok(r.text.includes(WITHOUT), `${name}: names the folder`);
      assert.doesNotMatch(r.text, /^Rows:/m, name);
    }
    const list = await call("list_available_fiscal_years");
    assert.match(list.text, /Checked PDF tables .*NOT INSTALLED on this machine/);
    assert.match(list.text, /FY2027: Schedule C checked, review in progress \(9,979 rows\)/, "statuses from the package's own record");
    // A bad parameter is still an error first, with or without the tables.
    assert.equal((await call("search_schedule_c_awards", { ein: "123" })).isError, true);
  } finally {
    useDir(WITH);
  }
});

test("list_available_fiscal_years reports every family-year's PDF status", async () => {
  // FAILS if a family-year of data/pdf_years.csv is missing or shows the wrong status, or the old
  // parser's years are offered.
  const { text } = await call("list_available_fiscal_years");
  assert.match(text, /Checked PDF tables .*: installed, built /);
  const LABEL = { schedule_c: "Schedule C", transparency: "Transparency resolutions", capital_sd: "Capital §254 supporting detail", terms: "Terms and Conditions" };
  for (const y of readCsv("data/pdf_years.csv")) {
    const line = new RegExp(`^  FY${y.fiscal_year}: (.*)$`, "m").exec(text)?.[1] ?? "";
    assert.ok(line.includes(`${LABEL[y.family]} ${STATUS_LABEL[y.status]} (${Number(y.rows).toLocaleString("en-US")} rows)`), `FY${y.fiscal_year} ${y.family}: ${line}`);
  }
  assert.match(text, /FY2008–FY2017: not available yet\. Only the old parser read those years/);
});

test("the retired 1.x tools point at the new tools", async () => {
  const want = {
    search_awards: "search_schedule_c_awards",
    search_transparency_resolutions: "search_transparency_changes",
    search_capital_projects: "search_capital_book",
    get_terms_conditions: "search_terms_conditions",
  };
  for (const [name, next] of Object.entries(want)) {
    const r = await call(name, {});
    assert.equal(r.isError, true);
    assert.ok(r.text.includes(next), `${name} -> ${next}`);
  }
});

test("an old-parser year, or a year not checked, answers that it is not available", async () => {
  // FAILS if FY2008–FY2017 (old parser only) or an unchecked year returns rows.
  for (const [name, fy] of [["search_schedule_c_awards", 2015], ["search_transparency_changes", 2012], ["search_capital_book", 2017], ["search_terms_conditions", 2010]]) {
    const r = await call(name, { fiscal_year: fy });
    assert.match(r.text, new RegExp(`FY${fy} is not available yet: only the old parser read`), name);
    assert.doesNotMatch(r.text, /^Rows:/m);
  }
  assert.match((await call("search_capital_book", { fiscal_year: 2021 })).text, /FY2021 Capital §254 .* is not in the checked tables\. Checked years: FY2018–FY2020, FY2022–FY2027/);
  assert.match((await call("search_terms_conditions", { fiscal_year: 2019 })).text, /is not in the checked tables/);
});

// ---------------------------------------------------------------- every served row

const SAMPLES = [
  ["search_schedule_c_awards", { fiscal_year: 2027, organization: "medicare rights" }],
  ["search_schedule_c_awards", { fiscal_year: 2019, organization: "Center for Employment Opportunities" }],
  ["search_schedule_c_awards", { member: "brewer", limit: 200 }],
  ["search_schedule_c_awards", { disclosure_status: "unmatched", limit: 300 }],
  ["search_transparency_changes", { fiscal_year: 2026, limit: 500 }],
  ["search_transparency_changes", { fiscal_year: 2018, action: "listed", limit: 200 }],
  ["search_capital_book", { fiscal_year: 2027, sponsor: "speaker", limit: 300 }],
  ["search_capital_book", { borough: "X", limit: 200 }],
  ["search_terms_conditions", { limit: 100 }],
  ["search_terms_conditions", { fiscal_year: 2024, text: "report", limit: 100 }],
];

test("every served row carries its status label, page and links built from the build's commit", async () => {
  // FAILS if a row is shown without "status: checked, …", without its page, or with a GitHub
  // link at a branch (or at any commit but the one the tables were built from).
  const commit = COMMIT();
  let rows = 0;
  for (const [name, args] of SAMPLES) {
    const { text, isError } = await call(name, args);
    assert.equal(isError, false, `${name} ${JSON.stringify(args)}: ${text.slice(0, 200)}`);
    const blocks = rowBlocks(text);
    assert.ok(blocks.length > 0, `${name} ${JSON.stringify(args)}: premise, rows shown`);
    for (const b of blocks) {
      assert.match(b, /\n    status: (checked, review in progress|checked and reviewed)\n/, b.slice(0, 200));
      assert.match(b, /\n    page: PDF page \d+ of source\/.+\.pdf\n/, b.slice(0, 200));
      assert.match(b, /\n    see the row on its page: https:\/\/betanyc\.github\.io\/New-York-City-Budget\/explorer\/#view=source&spdf=source%2F/, b.slice(0, 200));
      const gh = /the PDF on GitHub at the build's commit: (\S+)/.exec(b)?.[1];
      assert.ok(gh, b.slice(0, 200));
      assert.ok(gh.startsWith(`https://github.com/BetaNYC/New-York-City-Budget/blob/${commit}/source/`), gh);
      rows++;
    }
    assert.doesNotMatch(text, /\/blob\/(main|master|HEAD)\//);
  }
  assert.ok(rows > 1000, `premise: many rows checked (${rows})`);
});

test("every link resolves to a file: each cited PDF is in the repo and in the commit, at its sha256", () => {
  // FAILS if a source-view link names a PDF the explorer cannot open, or a GitHub link points at
  // a path the build's commit does not have (checked locally, without the network).
  const commit = COMMIT();
  const pdfs = db.prepare(`SELECT source_pdf, pdf_sha256 FROM pdf_schedule_c UNION SELECT source_pdf, pdf_sha256 FROM pdf_transparency
    UNION SELECT source_pdf, pdf_sha256 FROM pdf_capital_sd UNION SELECT source_pdf, pdf_sha256 FROM pdf_terms`).all();
  assert.ok(pdfs.length > 100, `premise: ${pdfs.length} PDFs`);
  const inCommit = new Set(execFileSync("git", ["-C", REPO, "ls-tree", "-r", "--name-only", commit, "--", "source"], { encoding: "utf8", maxBuffer: 64 << 20 }).split("\n"));
  for (const p of pdfs) {
    assert.ok(existsSync(join(REPO, p.source_pdf)), p.source_pdf);
    assert.ok(inCommit.has(p.source_pdf), `${p.source_pdf} at ${commit}`);
  }
});

test("the query layer labels every row and serves reviewed or closed rows only", () => {
  // FAILS if any function returns a row without a known status label.
  const commit = COMMIT();
  const all = [
    ...searchScheduleC(db, commit, { limit: 500 }).rows,
    ...searchTransparency(db, commit, { limit: 500 }).rows,
    ...searchCapitalBook(db, commit, { limit: 500 }).rows,
    ...searchTerms(db, commit, { limit: 100 }).rows,
  ];
  assert.ok(all.length >= 1500);
  for (const s of all) {
    assert.ok(["reviewed", "closed"].includes(s.row.status));
    assert.equal(s.status_label, STATUS_LABEL[s.row.status]);
  }
});

test("hidden text is always served, and always labeled", async () => {
  // FAILS if a row's hidden_text is dropped, or shown without "hidden text, not visible on the
  // printed page".
  const hidden = db.prepare("SELECT fiscal_year, resolution_number, row_id, org, member, hidden_text FROM pdf_transparency WHERE hidden_text <> ''").all();
  assert.ok(hidden.length >= 40, `premise: hidden text in the tables (${hidden.length})`);
  for (const h of hidden) {
    const args = { fiscal_year: h.fiscal_year, resolution_number: h.resolution_number, limit: 500 };
    if (h.org) args.organization = h.org;
    else if (h.member) args.member = h.member;
    const { text } = await call("search_transparency_changes", args);
    const block = rowBlocks(text).find((b) => b.includes(`row ${h.row_id}\n`));
    assert.ok(block, `${h.row_id} shown`);
    assert.ok(block.includes(`    ${HIDDEN_TEXT_LABEL}: ${JSON.stringify(h.hidden_text)}`), `${h.row_id} labeled`);
  }
  // Nowhere does the label appear without hidden text after it, or hidden text without the label.
  const { text } = await call("search_transparency_changes", { fiscal_year: 2026, limit: 500 });
  for (const line of text.split("\n").filter((l) => l.includes("hidden text"))) assert.match(line, /^    hidden text, not visible on the printed page: ".+"$/);
});

test("review entries show the decision and note where decided, else that none is recorded", async () => {
  // FAILS if a decided row hides its decision, or an open one reads as decided.
  const decided = db.prepare("SELECT r.fiscal_year, r.review_id, r.decision, r.decision_note, a.org, a.amount FROM pdf_review r JOIN pdf_schedule_c a ON a.fiscal_year = r.fiscal_year AND (';' || a.review_id || ';') LIKE ('%;' || r.review_id || ';%') WHERE r.family = 'schedule_c' AND r.decision <> '' LIMIT 3").all();
  assert.ok(decided.length >= 1, "premise: decided Schedule C rows");
  for (const d of decided) {
    const { text } = await call("search_schedule_c_awards", { fiscal_year: d.fiscal_year, organization: d.org, limit: 500 });
    assert.ok(text.includes(`review ${d.review_id} (`), d.review_id);
    assert.match(text, new RegExp(`review ${d.review_id} \\([^\\n]*\\n      decision: [^\\n]*\\(${d.decision}\\)`));
  }
  const { text } = await call("search_transparency_changes", { fiscal_year: 2026, organization: "South Asian Youth Action, Inc. - Elmhurst Center", action: "purpose_to" });
  assert.match(text, /review 977106b18980 \(warn, W\.clipped_text\)[^\n]*\n      no decision recorded yet; suggested \(not a decision\): kept as printed/);
});

test("needs_info: an open question, or after 30 days the date it was sent", () => {
  assert.match(needsInfoLabel(null), /an open question to Council Finance \(no date sent is recorded yet\)/);
  assert.equal(needsInfoLabel("2026-09-01", new Date("2026-10-22T12:00:00Z")), "Question sent to Council Finance on 2026-09-01, no answer yet; published as printed");
  assert.match(needsInfoLabel("2026-10-10", new Date("2026-10-22T12:00:00Z")), /question sent to Council Finance on 2026-10-10 \(12 day\(s\) ago\), waiting for an answer/);
});

// ---------------------------------------------------------------- sums

test('"no dollar amount" rows are counted but never summed (Beating Hearts)', async () => {
  // FAILS if a no_dollar_amount row adds to a total, or disappears from the count.
  const nd = db.prepare("SELECT fiscal_year, COUNT(*) AS n FROM pdf_transparency WHERE amount_kind = 'no_dollar_amount' GROUP BY 1 ORDER BY 1").all();
  assert.deepEqual(nd.map((r) => [r.fiscal_year, r.n]), [[2018, 136], [2019, 112], [2020, 73], [2021, 28], [2022, 91]]);
  for (const { fiscal_year: fy, n } of nd) {
    const res = searchTransparency(db, COMMIT(), { fiscal_year: fy, limit: 1 });
    assert.equal(res.no_dollar_amount, n, `FY${fy}`);
    const csv = readCsv(`data/fy${String(fy).slice(2)}/pdf/transparency/fy${String(fy).slice(2)}_tr_rows.csv`);
    const sum = csv.filter((r) => r.amount !== "").reduce((t, r) => t + Number(r.amount), 0);
    assert.equal(res.by_action.reduce((t, a) => t + a.amount, 0), sum, `FY${fy} net equals the CSV's sum of printed amounts`);
    assert.equal(res.matched, csv.length);
    const listed = res.by_action.find((a) => a.action === "listed");
    assert.equal(listed.with_amount, 0);
    assert.equal(listed.amount, 0);
    const { text } = await call("search_transparency_changes", { fiscal_year: fy, action: "listed", limit: 1 });
    assert.match(text, new RegExp(`listed with no dollar amount: ${n} row\\(s\\), ${n} with no dollar amount \\(in no sum\\)`));
  }
});

test("Schedule C totals equal the PDF's own (pdf_years notes) and never include sub-awards", async () => {
  // FAILS if a total drifts from the promoted CSV, or the Jobs to Build On partners are added.
  const res = searchScheduleC(db, COMMIT(), { fiscal_year: 2027, limit: 1 });
  assert.equal(res.matched, 9979);
  assert.equal(res.amount, 655045412);
  for (const fy of [2018, 2019]) {
    const csv = readCsv(`data/fy${String(fy).slice(2)}/pdf/schedule_c/fy${String(fy).slice(2)}_sc_awards.csv`);
    const r = searchScheduleC(db, COMMIT(), { fiscal_year: fy, limit: 1 });
    assert.equal(r.amount, csv.reduce((t, x) => t + (x.amount === "" ? 0 : Number(x.amount)), 0), `FY${fy}`);
    const { text } = await call("search_schedule_c_awards", { fiscal_year: fy, ein: "13-3564313", min_amount: 5154200, max_amount: 5154200 });
    assert.match(text, /sub-awards printed under this award \(28, \$4,463,500; in no total\)/, `FY${fy} CWE's partners listed under it`);
    assert.match(text, /Totals over all 1 match\(es\): 1 row\(s\) with an amount, \$5,154,200\./);
  }
});

test("capital book totals count Part I once: Part II reprints Part I rows", () => {
  const r = searchCapitalBook(db, COMMIT(), { fiscal_year: 2027, limit: 1 });
  const printed = db.prepare("SELECT printed_y1 FROM pdf_capital_sd_totals WHERE fiscal_year = 2027 AND kind = 'totals_for' AND part = 'I' AND name = 'ALL'").get().printed_y1;
  assert.equal(r.totals.y1, printed, "the book's own printed Part I total");
  assert.ok(r.part_ii_rows > 0);
});

// ---------------------------------------------------------------- parity with the explorer

/** Run one of the explorer's DuckDB queries on SQLite, with DuckDB's functions supplied. */
function explorerDb() {
  const x = new Database(TABLES_DB, { readonly: true });
  const key = (v) => String(v ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "");
  x.function("strip_accents", { deterministic: true }, (v) => key(v));
  x.function("contains", { deterministic: true }, (a, b) => (String(a ?? "").includes(String(b ?? "")) ? 1 : 0));
  x.function("starts_with", { deterministic: true }, (a, b) => (String(a ?? "").startsWith(String(b ?? "")) ? 1 : 0));
  // DuckDB's lower() folds every letter; SQLite's only ASCII. The samples below are ASCII.
  return x;
}
const run = (x, q, all = true) => (all ? x.prepare(q.sql).all(...q.params) : x.prepare(q.sql).get(...q.params));

test("Terms and Conditions: the MCP answers what the explorer's Terms view finds", () => {
  // FAILS if the MCP's agency / unit / text filters select different items than termsQuery /
  // termsCountQuery (viz/explorer/src/query/pdf.js) for the same filters.
  const x = explorerDb();
  try {
    const cases = [
      {}, { fiscal_year: 2027 }, { agency: "correction" }, { agency: "072" }, { text: "report" }, { text: "shelter", fiscal_year: 2024 },
      { unit: "001" }, { unit: "All" }, { agency: "education", unit: "401" }, { fiscal_year: 2018, text: "quarterly" },
    ];
    for (const f of cases) {
      const ex = run(x, explorer.termsCountQuery(f), false);
      const page = run(x, explorer.termsQuery(f, 0)).map((r) => `${r.fiscal_year}|${r.item_number}`);
      const mcp = searchTerms(db, COMMIT(), { ...f, limit: 100 });
      assert.equal(mcp.matched, ex.n, JSON.stringify(f));
      assert.equal(mcp.agencies, ex.agencies, JSON.stringify(f));
      assert.deepEqual(mcp.rows.slice(0, page.length).map((s) => `${s.row.fiscal_year}|${s.row.item_number}`), page, JSON.stringify(f));
    }
  } finally {
    x.close();
  }
});

test("Schedule C: the MCP's unmatched rows are the explorer's 'Schedule C only' rows", () => {
  // FAILS if search_schedule_c_awards with disclosure_status unmatched disagrees with
  // scOnlyQuery / scOnlyTotalsQuery (the explorer's Awards view, Schedule C side).
  const x = explorerDb();
  try {
    const cases = [
      [{}, {}],
      [{ fiscal_year: 2027 }, { fiscal_year: 2027 }],
      [{ fiscal_year: 2026, legal_name: "council district" }, { fiscal_year: 2026, organization: "council district" }],
      [{ council_member: "speaker" }, { member: "speaker" }],
      [{ agency: "dycd", min_amount: 10000 }, { agency: "dycd", min_amount: 10000 }],
      [{ program_name: "youth", max_amount: 5000 }, { purpose: "youth", max_amount: 5000 }],
      [{ ein: "13-6400434" }, { ein: "13-6400434" }],
    ];
    for (const [ef, mf] of cases) {
      const ex = run(x, explorer.scOnlyTotalsQuery(ef), false);
      const mcp = searchScheduleC(db, COMMIT(), { ...mf, disclosure_status: "unmatched", limit: 500 });
      assert.equal(mcp.matched, ex.n, JSON.stringify(ef));
      assert.equal(mcp.amount, ex.amount, JSON.stringify(ef));
      const exIds = new Set(run(x, explorer.scOnlyQuery(ef, 0)).map((r) => `${r.fiscal_year}|${r.award_id}`));
      const mcpIds = new Set(mcp.rows.map((s) => `${s.row.fiscal_year}|${s.row.award_id}`));
      // Both show the highest amounts first; the explorer's page is a prefix of what the MCP shows.
      if (mcp.matched <= 500) for (const id of exIds) assert.ok(mcpIds.has(id), `${JSON.stringify(ef)}: ${id}`);
    }
  } finally {
    x.close();
  }
});

test("capital book: the MCP's Part I rows are the explorer's Part I matches", () => {
  // FAILS if search_capital_book's Part I for a year is not capitalPdfMatchesQuery's rows.
  const x = explorerDb();
  try {
    for (const fy of [2018, 2023, 2027]) {
      const ex = run(x, explorer.capitalPdfMatchesQuery([fy]));
      const mcp = searchCapitalBook(db, COMMIT(), { fiscal_year: fy, part: "I", limit: 500 });
      assert.equal(mcp.matched, ex.length, `FY${fy}`);
      assert.equal(mcp.totals.y1, ex.reduce((t, r) => t + (r.amount_y1 ?? 0), 0), `FY${fy}`);
    }
  } finally {
    x.close();
  }
});

test("transparency: the MCP's totals equal the committed CSVs, per resolution", () => {
  // FAILS if a resolution's rows or net disagree with data/fyNN/pdf/transparency/fyNN_tr_rows.csv.
  for (const fy of [2019, 2023, 2026]) {
    const csv = readCsv(`data/fy${String(fy).slice(2)}/pdf/transparency/fy${String(fy).slice(2)}_tr_rows.csv`);
    for (const reso of [...new Set(csv.map((r) => r.resolution_number))].slice(0, 4)) {
      const mine = csv.filter((r) => r.resolution_number === reso);
      const res = searchTransparency(db, COMMIT(), { fiscal_year: fy, resolution_number: reso, limit: 1 });
      // resolution_number is a substring filter: "Res 1" would also match "Res 10"; compare that resolution only.
      const exact = res.resolutions.find((r) => r.resolution_number === reso);
      assert.equal(exact.rows, mine.length, `FY${fy} ${reso}`);
    }
    const res = searchTransparency(db, COMMIT(), { fiscal_year: fy, organization: "Inc", limit: 1 });
    const want = csv.filter((r) => fold(r.org).includes("inc"));
    assert.equal(res.matched, want.length, `FY${fy} organization ~ Inc`);
  }
});

// ---------------------------------------------------------------- the gate, on planted rows

/** A small file with the real schema and planted rows that must never be served. */
function plant(meta) {
  rmSync(SYNTH, { recursive: true, force: true });
  mkdirSync(join(SYNTH, "pdf-tables"), { recursive: true });
  const path = join(SYNTH, "pdf-tables", "pdf-tables.db");
  const s = new Database(path);
  for (const { sql } of db.prepare("SELECT sql FROM sqlite_master WHERE type = 'table'").all()) s.exec(sql);
  const cols = (t) => db.prepare(`PRAGMA table_info(${t})`).all().map((c) => c.name);
  const copy = (t, where) => {
    const c = cols(t);
    const rows = db.prepare(`SELECT * FROM ${t} WHERE ${where}`).all();
    const ins = s.prepare(`INSERT INTO ${t} (${c.map((x) => `"${x}"`).join(",")}) VALUES (${c.map(() => "?").join(",")})`);
    for (const r of rows) ins.run(...c.map((x) => r[x]));
    return rows;
  };
  copy("pdf_years", "fiscal_year = 2027 AND family IN ('schedule_c', 'terms', 'capital_sd') OR fiscal_year = 2026 AND family = 'transparency'");
  const sc = copy("pdf_schedule_c", "fiscal_year = 2027 AND org LIKE 'Medicare Rights%'");
  copy("pdf_terms", "fiscal_year = 2027 AND item_number <= 3");
  copy("pdf_capital_sd", "fiscal_year = 2027 AND sub_id = 'AG CC1053'");
  copy("pdf_transparency", "fiscal_year = 2026 AND row_id = 'fy26-tr01-p085-r013'");
  copy("pdf_review", "fiscal_year = 2026 AND review_id = '977106b18980'");
  // Planted: an old-parser year, a status pdf_years does not give, a status no build writes.
  const ins = (t, row) => s.prepare(`INSERT INTO ${t} (${Object.keys(row).map((x) => `"${x}"`).join(",")}) VALUES (${Object.keys(row).map(() => "?").join(",")})`).run(...Object.values(row));
  const base = sc[0];
  ins("pdf_schedule_c", { ...base, fiscal_year: 2015, award_id: "planted-old-year", org: "Medicare Rights PLANTED old year" });
  ins("pdf_schedule_c", { ...base, status: "closed", award_id: "planted-status", org: "Medicare Rights PLANTED wrong status" });
  ins("pdf_schedule_c", { ...base, status: "old_parser", award_id: "planted-old", org: "Medicare Rights PLANTED old parser" });
  ins("pdf_schedule_c", { ...base, amount: null, amount_printed: "", award_id: "planted-no-amount", org: "Medicare Rights no amount" });
  ins("pdf_years", { fiscal_year: 2015, family: "schedule_c", source_pdf: "x", pdf_sha256: "x", issue: 0, status: "old_parser", rows: 1, flagged: 0, printed_totals_tied: "", note: "" });
  ins("pdf_terms", { ...db.prepare("SELECT * FROM pdf_terms WHERE fiscal_year = 2027 AND item_number = 1").get(), fiscal_year: 2016, status: "reviewed" });
  s.prepare("UPDATE pdf_review SET decision = 'needs_info', decision_note = 'asked', detail = ? WHERE review_id = '977106b18980'").run(JSON.stringify({ question_sent: "2026-08-01" }));
  for (const [k, v] of Object.entries(meta)) ins("meta", { key: k, value: v });
  s.close();
  useDir(SYNTH);
}

test("planted rows of an unlisted year or another status are never served, and amountless rows never summed", async () => {
  // FAILS if the query gate lets through a row whose family-year is not in pdf_years at that
  // status, or a row with no amount adds to a total.
  plant({ pdf_tables_format: "nyc-budget-pdf-tables/1", built_at: "2026-10-22T00:00:00Z", source_commit: COMMIT(), source_commit_check: "pdfs_match" });
  try {
    const { text } = await call("search_schedule_c_awards", { organization: "medicare rights", limit: 500 });
    assert.doesNotMatch(text, /PLANTED/);
    assert.match(text, /Totals over all 12 match\(es\): 11 row\(s\) with an amount, \$198,000; 1 row\(s\) with no amount read, in no sum/);
    assert.match(text, /Medicare Rights no amount \(EIN [^)]*\)/);
    assert.match((await call("search_schedule_c_awards", { fiscal_year: 2015 })).text, /FY2015 is not available yet/);
    assert.doesNotMatch((await call("search_terms_conditions", { limit: 100 })).text, /^FY2016 /m);
    // needs_info with a sent date over 30 days ago: labeled with the date.
    const tr = await call("search_transparency_changes", { fiscal_year: 2026 });
    assert.match(tr.text, /decision: Question sent to Council Finance on 2026-08-01, no answer yet; published as printed; note: asked/);
  } finally {
    useDir(WITH);
  }
});

test("no commit, or a commit the PDFs were not checked against, means no GitHub link", async () => {
  // FAILS if a link is built from a branch name, or from a commit whose files differ.
  for (const meta of [
    { source_commit: "main", source_commit_check: "pdfs_match" },
    { source_commit: COMMIT(), source_commit_check: "mismatch: source/FY27/x.pdf" },
    { source_commit: "", source_commit_check: "no_git" },
  ]) {
    plant({ pdf_tables_format: "nyc-budget-pdf-tables/1", built_at: "2026-10-22T00:00:00Z", ...meta });
    try {
      const { text } = await call("search_schedule_c_awards", { fiscal_year: 2027, organization: "medicare rights" });
      assert.ok(rowBlocks(text).length > 0);
      assert.doesNotMatch(text, /github\.com\/BetaNYC\/New-York-City-Budget\/blob\//, JSON.stringify(meta));
      assert.match(text, /see the row on its page: https:\/\/betanyc\.github\.io/);
    } finally {
      useDir(WITH);
    }
  }
});

test("a download of another format is refused with a way forward", async () => {
  plant({ pdf_tables_format: "nyc-budget-pdf-tables/0", built_at: "x", source_commit: "", source_commit_check: "" });
  try {
    const r = await call("search_terms_conditions", {});
    assert.equal(r.isError, false);
    assert.match(r.text, /cannot be used: its format is "nyc-budget-pdf-tables\/0"/);
    assert.match(r.text, /download --pdf-tables/);
  } finally {
    useDir(WITH);
  }
});

test("the PDF tools refuse bad filters before they read anything", async () => {
  const bad = [
    ["search_schedule_c_awards", { ein: "12345678" }, /ein must be 9 digits/],
    ["search_schedule_c_awards", { organization: "  " }, /organization is empty/],
    ["search_schedule_c_awards", { legal_name: "x" }, /Use `organization` instead of `legal_name`/],
    ["search_schedule_c_awards", { min_amount: 10, max_amount: 1 }, /min_amount \(10\) is greater than max_amount/],
    ["search_transparency_changes", { resolution_date: "8/14/2025" }, /resolution_date must be a date as YYYY-MM-DD/],
    ["search_capital_book", { budget_line: "PD018" }, /budget_line must be an agency code/],
    ["search_capital_book", { borough: "Brooklyn" }, /borough must be one printed code letter/],
    ["search_terms_conditions", { limit: 0 }, /limit must be at least 1/],
  ];
  for (const [name, args, re] of bad) {
    const r = await call(name, args);
    assert.equal(r.isError, true, `${name} ${JSON.stringify(args)}`);
    assert.match(r.text, re);
  }
});
