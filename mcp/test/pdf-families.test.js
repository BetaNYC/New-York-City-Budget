/**
 * The reviewed PDF tables (scripts/pdf-families.mjs, viz/explorer/INTEGRATION.md §3): the MCP
 * never serves a status = reviewed row.
 *
 *   1. The MCP's own index (data/budget.db, built by pretest) holds no reviewed row in any pdf_*
 *      table, and records include_reviewed = no.
 *   2. --include-reviewed is refused when it would write data/budget.db.
 *   3. A reviewed build (--include-reviewed --out) loads exactly what data/pdf_years.csv lists.
 *   4. Every MCP tool answers the same, byte for byte, from that reviewed index as from the
 *      default one: no tool reads a pdf_* table, so reviewed rows are invisible to tools even when
 *      they are in the file. Also checked statically: no source file names a pdf_ table.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";

import { DERIVED, PDF_FAMILIES, PDF_TABLES, SUGGESTIONS } from "../scripts/pdf-families.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const DEFAULT_DB = join(MCP, "data", "budget.db");
// Inside mcp/ so the copied dist/ resolves mcp/node_modules. Gitignored.
const TMP = join(MCP, ".reviewed-test");
const REVIEWED_DB = join(TMP, "data", "budget.db");
const years = parse(readFileSync(join(REPO, "data", "pdf_years.csv"), "utf8"), { columns: true, skip_empty_lines: true });

before(() => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "data"), { recursive: true });
  cpSync(join(MCP, "dist"), join(TMP, "dist"), { recursive: true });
  cpSync(join(MCP, "package.json"), join(TMP, "package.json"));
  const r = spawnSync(process.execPath, [join(MCP, "scripts", "build-index.mjs"), "--include-reviewed", "--out", REVIEWED_DB], { cwd: MCP, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
});
after(() => rmSync(TMP, { recursive: true, force: true }));

const count = (db, sql) => db.prepare(sql).get().n;

test("the MCP's index holds no reviewed PDF row", () => {
  // FAILS if a default build loads a status = reviewed family.
  const db = new Database(DEFAULT_DB, { readonly: true });
  try {
    for (const t of PDF_TABLES) assert.equal(count(db, `SELECT COUNT(*) AS n FROM ${t} WHERE status <> 'closed'`), 0, t);
    assert.equal(db.prepare("SELECT value FROM meta WHERE key = 'include_reviewed'").get().value, "no");
  } finally {
    db.close();
  }
});

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
    assert.equal(count(db, "SELECT COUNT(*) AS n FROM pdf_schedule_c WHERE fiscal_year = 2018 AND fiscal_conduit <> ''"), 50);
  } finally {
    db.close();
  }
});

/** Call every tool with a fixed set of arguments against the server module at `serverPath`. */
function answers(serverPath) {
  const script = `
    import { Client } from "@modelcontextprotocol/sdk/client/index.js";
    import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
    const { server } = await import(${JSON.stringify(serverPath)});
    const [ct, st] = InMemoryTransport.createLinkedPair();
    await server.connect(st);
    const client = new Client({ name: "pdf-test", version: "0" }, { capabilities: {} });
    await client.connect(ct);
    const calls = [
      ["list_available_fiscal_years", {}],
      ["search_council_capital", { fiscal_year: 2027 }],
      ["search_council_capital", { title: "ali forney" }],
      ["search_council_capital", { title: "fornay" }],
      ["search_council_capital", { sponsor: "sanchez", fiscal_year: 2027 }],
      ["search_council_capital", { budget_line: "PV 0N042" }],
      ["compare_capital_to_omb", { report_year: 2027 }],
      ["search_disclosure_awards", { fiscal_year: 2027, legal_name: "ali forney" }],
      // Schedule C (pdf_schedule_c, pdf_sc_disclosure): p.279 Medicare Rights $135,000, the City's EIN
      ["search_disclosure_awards", { fiscal_year: 2027, legal_name: "medicare rights" }],
      ["search_disclosure_awards", { fiscal_year: 2027, ein: "13-6400434" }],
      ["search_disclosure_awards", { fiscal_year: 2027, min_amount: 135000, max_amount: 135000 }],
    ];
    const out = [(await client.listTools()).tools.map((t) => t.name)];
    for (const [name, args] of calls) out.push(await client.callTool({ name, arguments: args }));
    await client.close();
    process.stdout.write(JSON.stringify(out));
  `;
  const r = spawnSync(process.execPath, ["--input-type=module", "-e", script], { cwd: MCP, encoding: "utf8", maxBuffer: 64 << 20 });
  assert.equal(r.status, 0, r.stderr);
  // The index's build time is the one thing two builds may differ in.
  return r.stdout.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z/g, "<built_at>");
}

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

test("every MCP tool answers the same from a reviewed index as from the default one", () => {
  // FAILS if any tool's answer changes when reviewed PDF rows are in the index.
  const a = answers(join(MCP, "dist", "server.js"));
  const b = answers(join(TMP, "dist", "server.js"));
  assert.ok(a.length > 1000, "premise: the tools answered");
  assert.equal(b, a);
});

test("no MCP source file names a pdf_ table", () => {
  // FAILS if a tool (src/*.ts) starts reading the reviewed tables.
  for (const f of readdirSync(join(MCP, "src"))) {
    assert.doesNotMatch(readFileSync(join(MCP, "src", f), "utf8"), /\bpdf_[a-z_]+\b/, f);
  }
});
