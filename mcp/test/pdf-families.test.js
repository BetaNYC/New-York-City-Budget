/**
 * The checked PDF tables (scripts/pdf-families.mjs, viz/explorer/INTEGRATION.md §3) and how they
 * are built for the MCP's optional download (scripts/build-pdf-release.mjs, #215).
 *
 * 2.0.0 asserted here that no tool reads a pdf_* table. #212 serves them on purpose, so those two
 * tests are replaced by the rules the serving must keep (W5, #214):
 *   1. --include-reviewed is refused when it would write data/budget.db.
 *   2. A reviewed build loads exactly what data/pdf_years.csv lists, and only from the new
 *      process's files: no old-parser CSV (data/fyNN/schedule_c/, terms/, capital/, transparency
 *      resolutions, data/retired/, data/combined/) is ever an input.
 *   3. The download holds the pdf_* tables and the build's meta only, every row of a family-year
 *      pdf_years lists as reviewed or closed, with the commit its links are built from.
 *   4. The spreadsheet tools answer the same, byte for byte, with the PDF tables installed or not.
 * test/pdf-tools.test.js covers the four tools themselves.
 */
import { test, after } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, symlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";

import { DERIVED, PDF_FAMILIES, PDF_TABLES, SUGGESTIONS } from "../scripts/pdf-families.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
// Built once by pretest (scripts/build-pdf-release.mjs --out .pdf-test/release --keep-full).
const RELEASE = join(MCP, ".pdf-test", "release");
const REVIEWED_DB = join(RELEASE, "full.db");
const TABLES_DB = join(RELEASE, "pdf-tables.db");
const years = parse(readFileSync(join(REPO, "data", "pdf_years.csv"), "utf8"), { columns: true, skip_empty_lines: true });
const TMP = join(MCP, ".pdf-test", "families");
after(() => rmSync(TMP, { recursive: true, force: true }));

const count = (db, sql) => db.prepare(sql).get().n;

test("--include-reviewed is refused for data/budget.db", () => {
  // FAILS if a reviewed build could replace the MCP's own index.
  const r = spawnSync(process.execPath, [join(MCP, "scripts", "build-index.mjs"), "--include-reviewed"], { cwd: MCP, encoding: "utf8" });
  assert.notEqual(r.status, 0);
  assert.match(r.stderr, /--include-reviewed must not write data\/budget\.db/);
});

test("a reviewed build loads exactly the families data/pdf_years.csv lists", () => {
  // FAILS if a listed family is missing, its main table count differs from pdf_years.rows, or a
  // row lacks the row contract's provenance.
  const db = new Database(REVIEWED_DB, { readonly: true });
  try {
    assert.equal(db.prepare("SELECT value FROM meta WHERE key = 'include_reviewed'").get().value, "yes");
    assert.ok(years.length >= 2, "premise: pdf_years.csv lists the FY2027 families");
    for (const y of years) {
      const main = PDF_FAMILIES[y.family].main;
      const n = count(db, `SELECT COUNT(*) AS n FROM ${main} WHERE fiscal_year = ${Number(y.fiscal_year)} AND family = '${y.family}' AND status = '${y.status}'`);
      assert.equal(n, Number(y.rows), `${y.fiscal_year} ${y.family}`);
    }
    for (const t of PDF_TABLES.filter((t) => t !== "pdf_years" && t !== "pdf_review" && t !== SUGGESTIONS.table && !(t in DERIVED))) {
      assert.equal(count(db, `SELECT COUNT(*) AS n FROM ${t} WHERE source_pdf NOT LIKE 'source/%.pdf' OR length(pdf_sha256) <> 64 OR pdf_page IS NULL`), 0, t);
    }
  } finally {
    db.close();
  }
});

test("the schema fields decided in #209 load (W8, #217)", () => {
  // FAILS if a sub-award loses its award, a sub-award is counted as an award, or a "no dollar
  // amount" row carries an amount (every SUM must skip it).
  const db = new Database(REVIEWED_DB, { readonly: true });
  try {
    for (const fy of [2019, 2018]) {
      const subs = db.prepare(`SELECT s.amount, a.amount AS parent_amount, a.ein AS parent_ein FROM pdf_schedule_c_subawards s
        LEFT JOIN pdf_schedule_c a ON a.fiscal_year = s.fiscal_year AND a.award_id = s.parent_award_id WHERE s.fiscal_year = ?`).all(fy);
      assert.equal(subs.length, 28, `FY${fy} sub-awards`);
      assert.equal(subs.reduce((t, r) => t + r.amount, 0), 4463500, `FY${fy} sub-award total`);
      assert.ok(subs.every((r) => r.parent_amount === 5154200 && r.parent_ein === "133564313"), `FY${fy} parent is CWE's Jobs to Build On award`);
    }
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_schedule_c_subawards WHERE fiscal_year NOT IN (2018, 2019)"), 0);
    const nd = db.prepare("SELECT fiscal_year AS fy, COUNT(*) AS n, COUNT(amount) AS with_amount FROM pdf_transparency WHERE amount_kind = 'no_dollar_amount' GROUP BY 1 ORDER BY 1").all();
    assert.deepEqual(nd.map((r) => [r.fy, r.n, r.with_amount]), [[2018, 136, 0], [2019, 112, 0], [2020, 73, 0], [2021, 28, 0], [2022, 91, 0]]);
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_transparency WHERE amount_kind = 'dollar_amount' AND amount IS NULL"), 0);
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_schedule_c WHERE fiscal_year = 2019 AND review_not_completed = 1"), 304);
    // 49 conduits (p.271's drafting note in the conduit column is not one), 48 with an EIN.
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_schedule_c WHERE fiscal_year = 2018 AND fiscal_conduit <> ''"), 49);
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_schedule_c WHERE fiscal_year = 2018 AND fiscal_conduit_ein <> ''"), 48);
  } finally {
    db.close();
  }
});

test("Schedule C's disclosure alignment is the Schedule C session's own (code/schedc/disclosure.py)", () => {
  // FAILS if the port in scripts/pdf-families.mjs drifts from the promoted file (the build also
  // stops on that), or the counts move. FY2027: 9,850 matched (City-EIN name rule on), 129 PDF
  // only, 557 spreadsheet only, 994 ambiguous (research/2026-10-20-fy27-schedule-c-review/README.md).
  const db = new Database(REVIEWED_DB, { readonly: true });
  try {
    const n = (fy, side) => count(db, `SELECT COUNT(*) AS n FROM pdf_sc_disclosure WHERE fiscal_year = ${fy} AND side = '${side}'`);
    assert.deepEqual([n(2027, "matched"), n(2027, "pdf_only"), n(2027, "disclosure_only")], [9850, 129, 557]);
    assert.equal(count(db, "SELECT SUM(ambiguous) AS n FROM pdf_sc_disclosure WHERE fiscal_year = 2027 AND side <> 'pdf_only'"), 994);
    // FY2026 (research/2026-10-21-fy26-schedule-c-review/README.md: 9,510 with the City-EIN name rule).
    assert.equal(n(2026, "matched"), 9510);
    const mr = db.prepare("SELECT pdf_page, amount, ein, bbox_pt FROM pdf_schedule_c WHERE fiscal_year = 2027 AND org LIKE 'Medicare Rights%' AND amount = 135000").all();
    assert.deepEqual(mr.map((r) => [r.pdf_page, r.amount]), [[279, 135000]], "p.279 Medicare Rights $135,000 (dropped by the old parser)");
  } finally {
    db.close();
  }
});

test("no old-parser file is an input of the PDF tables, and every PDF input is a listed family's", () => {
  // FAILS if the reviewed build reads a retired or old-parser CSV, or a data/fyNN/pdf/ file of a
  // family-year data/pdf_years.csv does not list.
  const db = new Database(REVIEWED_DB, { readonly: true });
  let inputs;
  try {
    inputs = JSON.parse(db.prepare("SELECT value FROM meta WHERE key = 'inputs'").get().value);
  } finally {
    db.close();
  }
  const OLD = [/^data\/fy\d{2}\/(schedule_c|terms|capital|transparency-resolutions)\//, /^data\/(combined|recovered|retired)\//, /legistar_crosswalk/];
  const listedDir = new Set(years.map((y) => `data/fy${String(y.fiscal_year).slice(2)}/pdf/${y.family}/`));
  for (const f of inputs) {
    assert.ok(!OLD.some((re) => re.test(f)), `old-parser input: ${f}`);
    if (/^data\/fy\d{2}\/pdf\//.test(f)) assert.ok(listedDir.has(f.slice(0, f.lastIndexOf("/") + 1)), `not a listed family-year: ${f}`);
    if (f.endsWith(".pdf")) assert.ok(years.some((y) => f === y.source_pdf || f.startsWith(y.source_pdf)), `a PDF no family-year lists: ${f}`);
  }
  assert.ok(inputs.some((f) => f.includes("/pdf/schedule_c/")), "premise: the families were read");
});

test("the download holds the pdf_* tables only, all rows of listed reviewed or closed family-years", () => {
  // FAILS if a spreadsheet table is shipped twice, a row's family-year is not in pdf_years (or at
  // another status), or the build recorded no commit to link to.
  const db = new Database(TABLES_DB, { readonly: true });
  try {
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").all().map((r) => r.name);
    assert.deepEqual(tables, [...PDF_TABLES, "meta"].sort());
    const meta = Object.fromEntries(db.prepare("SELECT key, value FROM meta").all().map((r) => [r.key, r.value]));
    assert.equal(meta.pdf_tables_format, "nyc-budget-pdf-tables/1");
    assert.equal(meta.pdf_gate, "reviewed_and_closed");
    assert.match(meta.source_commit, /^[0-9a-f]{40}$/);
    assert.equal(meta.source_commit_check, "pdfs_match", "every cited PDF has these bytes at the recorded commit");
    const key = (y) => `${y.fiscal_year}|${y.family}|${y.status}|${y.rows}`;
    assert.deepEqual(
      db.prepare("SELECT fiscal_year, family, status, rows FROM pdf_years").all().map(key).sort(),
      years.map((y) => key({ fiscal_year: Number(y.fiscal_year), family: y.family, status: y.status, rows: Number(y.rows) })).sort()
    );
    for (const [fam, cfg] of Object.entries(PDF_FAMILIES)) {
      for (const t of cfg.tables) {
        const bad = count(db, `SELECT COUNT(*) AS n FROM ${t.table} r WHERE r.status NOT IN ('reviewed', 'closed') OR NOT EXISTS
          (SELECT 1 FROM pdf_years y WHERE y.fiscal_year = r.fiscal_year AND y.family = '${fam}' AND y.status = r.status)`);
        assert.equal(bad, 0, t.table);
      }
    }
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_years WHERE fiscal_year < 2018"), 0, "no old-parser year");
  } finally {
    db.close();
  }
});

/** Call the spreadsheet tools with a fixed set of arguments, with NYC_BUDGET_DATA_DIR = `dataDir`. */
function answers(dataDir) {
  const script = `
    import { Client } from "@modelcontextprotocol/sdk/client/index.js";
    import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
    const { server } = await import(${JSON.stringify(join(MCP, "dist", "server.js"))});
    const [ct, st] = InMemoryTransport.createLinkedPair();
    await server.connect(st);
    const client = new Client({ name: "pdf-test", version: "0" }, { capabilities: {} });
    await client.connect(ct);
    const calls = [
      ["search_council_capital", { fiscal_year: 2027 }],
      ["search_council_capital", { title: "ali forney" }],
      ["search_council_capital", { sponsor: "sanchez", fiscal_year: 2027 }],
      ["search_council_capital", { budget_line: "PV 0N042" }],
      ["compare_capital_to_omb", { report_year: 2027 }],
      ["search_disclosure_awards", { fiscal_year: 2027, legal_name: "medicare rights" }],
      ["search_disclosure_awards", { fiscal_year: 2027, ein: "13-6400434" }],
      ["search_disclosure_awards", { fiscal_year: 2027, min_amount: 135000, max_amount: 135000 }],
    ];
    const out = [];
    for (const [name, args] of calls) out.push(await client.callTool({ name, arguments: args }));
    await client.close();
    process.stdout.write(JSON.stringify(out));
  `;
  const r = spawnSync(process.execPath, ["--input-type=module", "-e", script], {
    cwd: MCP, encoding: "utf8", maxBuffer: 64 << 20, env: { ...process.env, NYC_BUDGET_DATA_DIR: dataDir, NYC_BUDGET_PDF_DATA: "" },
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout;
}

test("the spreadsheet tools answer the same with the PDF tables installed or not", () => {
  // FAILS if installing the download changes any answer of the three spreadsheet tools.
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "with", "pdf-tables"), { recursive: true });
  mkdirSync(join(TMP, "without"), { recursive: true });
  symlinkSync(TABLES_DB, join(TMP, "with", "pdf-tables", "pdf-tables.db"));
  const a = answers(join(TMP, "without"));
  const b = answers(join(TMP, "with"));
  assert.ok(a.length > 1000, "premise: the tools answered");
  assert.equal(b, a);
});
