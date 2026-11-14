/**
 * OMB's capital commitment plan and DCP's Capital Projects Database (CPDB) in the MCP's index
 * (#250, PR B; docs/plans/2026-11-13-250-capital-plan-and-cpdb.md):
 *
 *   capital_plan          NYC Open Data 2cmn-uidm, every release. Amounts in THOUSANDS of dollars,
 *                         as OMB publishes them (columns year1_amt_k ... year5_amt_k).
 *   cpdb_commitments      NYC Open Data djxg-kcfi, one CPDB version. Dollars (with cents). The
 *                         project's description, agency and ID come from cpdb_projects, and
 *                         code names from cpdb_codes; the test below rebuilds every raw row.
 *   cpdb_projects         NYC Open Data fi59-268w, the same version. Dollars. No budget line.
 *   capital_plan_sources  one row per dataset: file, rows, sha256, rowsUpdatedAt, unit, version.
 *
 * Every expected figure is recomputed HERE from the committed snapshots (source/open-data-<id>/),
 * with code that shares nothing with the loader (scripts/capital-plan.mjs). Budget lines are
 * checked against the Python build's own normal form (data/capital/
 * omb_commitment_plan_council_lines.csv, code/build_capital_council.py norm_line).
 *
 * Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const DB_PATH = join(MCP, "data", "budget.db");

const csvOf = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const gzCsv = (id) =>
  parse(gunzipSync(readFileSync(join(REPO, `source/open-data-${id}/${id}.csv.gz`))).toString("utf8"), { columns: true, skip_empty_lines: true, bom: true });
const manifestRows = (id) => Number(csvOf(`source/open-data-${id}/MANIFEST.csv`).find((m) => m.file === `${id}.csv.gz`).rows);
const num = (s) => (s === "" || s == null ? 0 : Number(s));
/** Sums in whole thousandths, so float order never matters. */
const milli = (s) => Math.round(num(s) * 1000);

const PLAN = gzCsv("2cmn-uidm");
const COMMIT = gzCsv("djxg-kcfi");
const PROJ = gzCsv("fi59-268w");

let db;
let client;
before(async () => {
  db = new Database(DB_PATH, { readonly: true });
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "capital-plan-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  db?.close();
  await client?.close();
});

test("every row of each snapshot is in the index, but 2cmn-uidm's one total row", () => {
  // FAILS if a row is dropped or doubled, or the row with no release, line or year (amounts that
  // look like grand totals; code/build_capital_council.py strips it too) is loaded as a line.
  const stripped = PLAN.filter((r) => r.pub_date === "" && r.budline === "");
  assert.equal(stripped.length, 1);
  assert.equal(db.prepare("SELECT COUNT(*) n FROM capital_plan").get().n, manifestRows("2cmn-uidm") - 1);
  assert.equal(db.prepare("SELECT COUNT(*) n FROM cpdb_commitments").get().n, manifestRows("djxg-kcfi"));
  assert.equal(db.prepare("SELECT COUNT(*) n FROM cpdb_projects").get().n, manifestRows("fi59-268w"));
  assert.equal(db.prepare("SELECT COUNT(*) n FROM capital_plan WHERE source_row = ?").get(stripped[0][":id"]).n, 0);
});

test("the commitment plan's amounts equal the snapshot's, per release, in thousands", () => {
  // FAILS if an amount is scaled (x 1000), shifted to another year column, or lost.
  const want = new Map();
  for (const r of PLAN) {
    if (r.pub_date === "" && r.budline === "") continue;
    const w = want.get(r.pub_date) ?? [0, 0, 0, 0, 0];
    for (let i = 0; i < 5; i++) w[i] += milli(r[`year${i + 1}_amt`]);
    want.set(r.pub_date, w);
  }
  const got = db
    .prepare(`SELECT pub_date, ${[1, 2, 3, 4, 5].map((i) => `SUM(ROUND(COALESCE(year${i}_amt_k, 0) * 1000)) y${i}`).join(", ")} FROM capital_plan GROUP BY pub_date`)
    .all();
  assert.equal(got.length, want.size);
  assert.equal(want.size, 32);
  for (const g of got) assert.deepEqual([g.y1, g.y2, g.y3, g.y4, g.y5], want.get(g.pub_date), g.pub_date);
});

test("a fifth year OMB did not publish is NULL, never 0", () => {
  // FAILS if a 4-year release's year5_amt_k is stored as 0 (a planned commitment of nothing).
  const four = PLAN.filter((r) => r.num_yrs_prsnt === "4" && !(r.pub_date === "" && r.budline === "")).length;
  assert.ok(four > 0);
  assert.equal(db.prepare("SELECT COUNT(*) n FROM capital_plan WHERE num_yrs = 4 AND year5_amt_k IS NULL").get().n, four);
});

test("CPDB's amounts equal the snapshots', column by column, in dollars", () => {
  // FAILS if a CPDB amount is scaled, swapped with another column, or lost.
  const cCols = ["ccnonexempt", "ccexempt", "totalcityplannedcommit", "nccstate", "nccfederal", "nccother", "totalnoncityplannedcommit", "totalplannedcommit"];
  for (const c of cCols) {
    const want = COMMIT.reduce((s, r) => s + milli(r[c]), 0);
    const got = db.prepare(`SELECT SUM(ROUND(COALESCE(${c}, 0) * 1000)) s FROM cpdb_commitments`).get().s;
    assert.equal(got, want, c);
  }
  const pCols = Object.keys(PROJ[0]).filter((c) => /commit|^adopt_|^allocate_|^spent_|^ccexempt$|^ncc/.test(c) && !/date/.test(c));
  assert.ok(pCols.includes("spent_total_checkbooknyc") && pCols.length >= 40, pCols.join(","));
  for (const c of pCols) {
    const want = PROJ.reduce((s, r) => s + milli(r[c]), 0);
    const got = db.prepare(`SELECT SUM(ROUND(COALESCE(${c}, 0) * 1000)) s FROM cpdb_projects`).get().s;
    assert.equal(got, want, c);
  }
});

test("budget lines take the Python build's normal form, so they join data/capital", () => {
  // FAILS if the index normalizes a 2cmn-uidm line differently from code/build_capital_council.py
  // ("C 0074" and "AGD001" both have a space after the project type), or a CPDB line keeps its hyphen.
  const py = new Map(csvOf("data/capital/omb_commitment_plan_council_lines.csv").map((r) => [r.source_row, r.budget_line_norm]));
  assert.ok(py.size > 17000);
  const got = db.prepare("SELECT source_row, budget_line_norm FROM capital_plan").all();
  let checked = 0;
  for (const g of got) {
    if (!py.has(g.source_row)) continue;
    assert.equal(g.budget_line_norm, py.get(g.source_row), g.source_row);
    checked++;
  }
  assert.equal(checked, py.size);
  const cp = db.prepare("SELECT budgetline, budget_line_norm FROM cpdb_commitments WHERE budgetline = 'AG-DN04L' LIMIT 1").get();
  assert.equal(cp.budget_line_norm, "AG DN04L");
  assert.equal(db.prepare("SELECT COUNT(*) n FROM cpdb_commitments WHERE budget_line_norm NOT GLOB '[A-Z]* [A-Z0-9]*'").get().n, 0);
});

test("every raw CPDB commitment can be rebuilt from the index, field for field", () => {
  // FAILS if moving the project fields to cpdb_projects or the names to cpdb_codes loses or
  // changes anything: a description, an agency, a code's name, a date, a budget line.
  const got = new Map(
    db
      .prepare(
        `SELECT c.source_row, s.version AS ccpversion, c.maprojid, p.magency, p.projectid, p.description AS projectdescription,
                c.sagencyacro, sa.name AS sagencyname, c.budgetline, c.projecttype, c.plancommdate,
                cm.name AS commitmentdescription, c.commitmentcode, c.typc, c.typcname
         FROM cpdb_commitments c
         JOIN cpdb_projects p USING (maprojid)
         JOIN capital_plan_sources s ON s.dataset_id = 'djxg-kcfi'
         JOIN cpdb_codes sa ON sa.kind = 'sponsor_agency' AND sa.code = c.sagencyacro
         JOIN cpdb_codes cm ON cm.kind = 'commitment' AND cm.code = c.commitmentcode`
      )
      .all()
      .map((r) => [r.source_row, r])
  );
  assert.equal(got.size, COMMIT.length);
  const one = (v) => String(v).replace(/\s+/g, " ").trim();
  for (const r of COMMIT) {
    const g = got.get(r[":id"]);
    assert.ok(g, r[":id"]);
    for (const c of ["ccpversion", "maprojid", "magency", "projectid", "sagencyacro", "sagencyname", "budgetline", "projecttype",
      "commitmentdescription", "commitmentcode", "typc", "typcname"]) {
      assert.equal(String(g[c]), r[c], `${r[":id"]} ${c}`);
    }
    assert.equal(g.projectdescription, one(r.projectdescription), `${r[":id"]} projectdescription`);
    assert.equal(g.plancommdate, r.plancommdate.slice(0, 10), `${r[":id"]} plancommdate`);
  }
});

test("a planned commitment's fiscal year runs July to June", () => {
  // FAILS if plan_fy is the calendar year (a July 2026 commitment is FY2027, not 2026).
  const fy = (d) => Number(d.slice(0, 4)) + (Number(d.slice(5, 7)) >= 7 ? 1 : 0);
  const rows = db.prepare("SELECT plancommdate, plan_fy FROM cpdb_commitments").all();
  for (const r of rows) assert.equal(r.plan_fy, fy(r.plancommdate), r.plancommdate);
  assert.ok(rows.some((r) => r.plancommdate.slice(5, 7) === "07"));
});

test("CPDB is in dollars: its City totals are 1,000 times OMB's thousands", () => {
  // FAILS if DCP starts publishing CPDB in thousands (the ratio drops to 1). DCP never states the
  // unit in writing; this is the check the plan (§1) rests on, recomputed here on its own.
  const newest = PLAN.filter((r) => r.funding === "CITY").map((r) => r.pub_date).sort().at(-1);
  const omb = new Map();
  for (const r of PLAN) {
    if (r.pub_date !== newest || r.funding !== "CITY") continue;
    const line = r.budline.replace(/[\s-]/g, "");
    for (let i = 0; i < 5; i++) {
      const v = num(r[`year${i + 1}_amt`]);
      if (r[`year${i + 1}_amt`] !== "" && v !== 0) omb.set(`${line}|${Number(r.yr1_fy) + i}`, (omb.get(`${line}|${Number(r.yr1_fy) + i}`) ?? 0) + v);
    }
  }
  const cpdb = new Map();
  for (const r of COMMIT) {
    const d = r.plancommdate;
    const k = `${r.budgetline.replace(/[\s-]/g, "")}|${Number(d.slice(0, 4)) + (Number(d.slice(5, 7)) >= 7 ? 1 : 0)}`;
    cpdb.set(k, (cpdb.get(k) ?? 0) + num(r.totalcityplannedcommit));
  }
  const ratios = [...omb].filter(([k]) => cpdb.has(k)).map(([k, v]) => cpdb.get(k) / v).sort((a, b) => a - b);
  assert.ok(ratios.length > 1000, String(ratios.length));
  assert.equal(ratios[Math.floor(ratios.length / 2)], 1000);
});

test("each dataset's source row names its file, hash, rows, unit and version", () => {
  // FAILS if a source's unit is missing or wrong, its hash is not the manifest's, or CPDB's
  // version is not recorded.
  const src = Object.fromEntries(db.prepare("SELECT * FROM capital_plan_sources").all().map((r) => [r.dataset_id, r]));
  assert.deepEqual(Object.keys(src).sort(), ["2cmn-uidm", "djxg-kcfi", "fi59-268w"]);
  for (const id of Object.keys(src)) {
    const m = csvOf(`source/open-data-${id}/MANIFEST.csv`).find((x) => x.file === `${id}.csv.gz`);
    assert.equal(src[id].sha256, m.sha256, id);
    assert.equal(src[id].file, `source/open-data-${id}/${id}.csv.gz`);
    assert.match(src[id].retrieved, /^\d{4}-\d{2}-\d{2}$/);
    assert.match(src[id].rows_updated_at, /^\d{4}-\d{2}-\d{2}$/);
  }
  assert.match(src["2cmn-uidm"].unit, /^thousands of dollars/);
  assert.match(src["djxg-kcfi"].unit, /^dollars, not thousands/);
  assert.match(src["djxg-kcfi"].unit, /DCP does not state the unit/);
  assert.equal(src["fi59-268w"].unit, src["djxg-kcfi"].unit);
  assert.equal(src["djxg-kcfi"].version, "fisa_2026");
  assert.equal(src["fi59-268w"].version, "fisa_2026");
  assert.equal(src["2cmn-uidm"].rows_updated_at, "2026-09-28");
  assert.equal(src["djxg-kcfi"].rows_updated_at, "2026-08-24");
});

test("list_available_fiscal_years names the plan's releases and CPDB's version, with units", async () => {
  // FAILS if the year list leaves the new data out, or shows it without its unit.
  const r = await client.callTool({ name: "list_available_fiscal_years", arguments: {} });
  const t = r.content.map((c) => c.text).join("\n");
  assert.match(t, /Capital Commitment Plan/);
  assert.match(t, /32 releases, 2016-04-26 to 2026-09-28/);
  assert.match(t, /thousands of dollars/);
  assert.match(t, /CPDB.*fisa_2026/);
  assert.match(t, /published 2026-08-24/);
});
