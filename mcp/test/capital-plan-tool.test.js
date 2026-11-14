/**
 * search_capital_plan (#250, PR C; docs/plans/2026-11-13-250-capital-plan-and-cpdb.md §2, §3, §5):
 * for a budget line, OMB's Capital Commitment Plan (2cmn-uidm, THOUSANDS of dollars) newest release
 * first and how it moved; DCP's CPDB planned commitments on the line (djxg-kcfi, dollars) by
 * project; each project's own CPDB totals (fi59-268w, the WHOLE project, never this line's share);
 * and the Council's own capital rows on the line, apart. For a CPDB project (project_id), the
 * project's totals and its commitments on every line.
 *
 * Expected figures are recomputed HERE from the committed snapshots and data/capital/, with code
 * that shares nothing with the server. Three lines: P D018 (Council-heavy; 248 CPDB projects, 154
 * of them on other lines too), HD 0201 (Non City funding in every release), E D001 (the most
 * Council rows). Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const opts = { columns: true, skip_empty_lines: true, bom: true };
const gzCsv = (id) => parse(gunzipSync(readFileSync(join(REPO, `source/open-data-${id}/${id}.csv.gz`))).toString("utf8"), opts);
const csvOf = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), opts);
const PLAN = gzCsv("2cmn-uidm");
const COMMIT = gzCsv("djxg-kcfi");
const PROJ = new Map(gzCsv("fi59-268w").map((r) => [r.maprojid, r]));
const COUNCIL = csvOf("data/capital/council_capital_awards.csv");

/** "P D018" -> "PD018": the key every source's line reduces to. */
const key = (s) => s.replace(/[\s-]/g, "").toUpperCase();
const num = (s) => (s === "" || s == null ? 0 : Number(s));
const sign = (v, s) => (v < 0 ? `-$${s}` : `$${s}`);
const money = (v) => sign(v, Math.abs(Math.round(v)).toLocaleString("en-US"));
const thousands = (v) => `${sign(Number(v), Math.abs(Number(v)).toLocaleString("en-US", { maximumFractionDigits: 2 }))} thousand`;
const fyOf = (d) => Number(d.slice(0, 4)) + (Number(d.slice(5, 7)) >= 7 ? 1 : 0);
const iso = (d) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "capital-plan-tool-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});
const call = (args) => client.callTool({ name: "search_capital_plan", arguments: args });
const text = (r) => r.content.map((c) => c.text).join("\n");

test("search_capital_plan is listed, read-only, with a strict schema", async () => {
  // FAILS if the tool is missing, takes unknown keys, or lacks the read-only hint.
  const t = (await client.listTools()).tools.find((x) => x.name === "search_capital_plan");
  assert.ok(t);
  assert.equal(t.inputSchema.additionalProperties, false);
  assert.deepEqual(Object.keys(t.inputSchema.properties).sort(), ["budget_line", "funding", "limit", "project_id", "release"]);
  assert.match(t.description, /thousands of dollars/);
  assert.match(t.description, /budget line/);
});

test("bad arguments are refused by name", async () => {
  // FAILS if an unknown key, a line with no separator, an unknown release, or no line and no
  // project is answered instead of refused.
  for (const [args, re] of [
    [{ budget_line: "P D018", district: 3 }, /district/],
    [{ budget_line: "PD018" }, /budget_line/],
    [{ budget_line: "P D018", release: "2026-09-29" }, /release/],
    [{}, /budget_line or project_id/],
    [{ budget_line: "P D018", funding: "STATE" }, /funding/],
  ]) {
    const r = await call(args);
    assert.equal(r.isError, true, JSON.stringify(args));
    assert.match(text(r), re, JSON.stringify(args));
  }
});

/** The newest release's rows for a line, from the raw snapshot. */
function planRows(line, release) {
  const rel = release ?? PLAN.filter((r) => key(r.budline) === key(line)).map((r) => r.pub_date).sort().at(-1);
  return { rel, rows: PLAN.filter((r) => r.pub_date === rel && key(r.budline) === key(line)) };
}

for (const line of ["P D018", "HD 0201", "E D001"]) {
  test(`${line}: the plan's figures are OMB's, in thousands, City and Non City apart`, async () => {
    // FAILS if a plan figure is scaled, shown without "thousand", the wrong release is used, or
    // City and Non City are added together.
    const t = text(await call({ budget_line: line }));
    const { rel, rows } = planRows(line);
    assert.ok(rows.length >= 1);
    assert.match(t, new RegExp(`release ${iso(rel)}`));
    for (const r of rows) {
      for (let i = 1; i <= 5; i++) {
        if (r[`year${i}_amt`] === "") continue;
        const fy = Number(r.yr1_fy) + i - 1;
        assert.ok(t.includes(`${r.funding}: `) || t.includes(`${r.funding} `), `${line} ${r.funding}`);
        assert.ok(t.includes(`FY${fy} ${thousands(r[`year${i}_amt`])}`), `${line} ${r.funding} FY${fy} ${thousands(r[`year${i}_amt`])}`);
      }
    }
    assert.ok(!/CITY \+ NON CITY|City and Non City combined/i.test(t));
  });

  test(`${line}: CPDB's planned commitments on the line equal djxg-kcfi's, in dollars, by fiscal year`, async () => {
    // FAILS if a CPDB figure on the line is wrong, scaled, or labeled as thousands.
    const t = text(await call({ budget_line: line, limit: 500 }));
    const mine = COMMIT.filter((r) => key(r.budgetline) === key(line));
    const byFy = new Map();
    for (const r of mine) {
      const fy = fyOf(r.plancommdate);
      const v = byFy.get(fy) ?? [0, 0];
      v[0] += num(r.totalcityplannedcommit);
      v[1] += num(r.totalnoncityplannedcommit);
      byFy.set(fy, v);
    }
    assert.match(t, new RegExp(`${mine.length.toLocaleString("en-US")} planned commitment`));
    for (const [fy, [c, nc]] of byFy) assert.ok(t.includes(`FY${fy} City ${money(c)} / Non-City ${money(nc)}`), `${line} FY${fy} City ${money(c)} / Non-City ${money(nc)}`);
    assert.match(t, /DCP does not state the unit/);
  });

  test(`${line}: the Council's own rows on the line are shown apart, from data/capital/`, async () => {
    // FAILS if the Council's rows are missing, miscounted, or summed into OMB's or CPDB's figures.
    const t = text(await call({ budget_line: line }));
    const mine = COUNCIL.filter((r) => key(r.budget_line_norm) === key(line));
    if (!mine.length) return assert.match(t, /no Council capital rows/i);
    assert.match(t, new RegExp(`${mine.length.toLocaleString("en-US")} Council capital row`));
  });
}

test("a project on several budget lines: its CPDB totals are the WHOLE project's, never this line's", async () => {
  // FAILS if a multi-line project's spent or planned total is shown as this line's, or summed
  // into the line's total.
  const lines = new Map();
  for (const r of COMMIT) lines.set(r.maprojid, (lines.get(r.maprojid) ?? new Set()).add(key(r.budgetline)));
  const multi = COMMIT.find((r) => key(r.budgetline) === key("P D018") && lines.get(r.maprojid).size > 1).maprojid;
  const t = text(await call({ budget_line: "P D018", limit: 500 }));
  const at = t.indexOf(multi);
  assert.ok(at >= 0, multi);
  const block = t.slice(at, t.indexOf("\n\n", at) > 0 ? t.indexOf("\n\n", at) : undefined);
  assert.match(block, /whole project, all \d+ of its budget lines/);
  assert.ok(block.includes(`spent ${money(num(PROJ.get(multi).spent_total))}`), block);
});

test("project_id: one project's totals and its commitments on every line", async () => {
  // FAILS if the project's totals differ from fi59-268w, or a line it sits on is left out.
  const lines = new Map();
  for (const r of COMMIT) lines.set(r.maprojid, (lines.get(r.maprojid) ?? new Set()).add(r.budgetline));
  const [id, ls] = [...lines].find(([, s]) => s.size === 3);
  const p = PROJ.get(id);
  const t = text(await call({ project_id: id.toLowerCase() }));
  assert.match(t, new RegExp(id));
  for (const l of ls) assert.ok(t.includes(l.replace("-", " ")), `${id} ${l}`);
  assert.ok(t.includes(`planned ${money(num(p.totalplannedcommit))}`));
  assert.ok(t.includes(`committed ${money(num(p.commit_total))}`));
  assert.ok(t.includes(`Checkbook NYC checks ${money(num(p.spent_total_checkbooknyc))}`));
  assert.match(t, /nyc-checkbook-mcp/);
});

test("release: an older release is served as published, and the history shows how the plan moved", async () => {
  // FAILS if release is ignored, or the history leaves a release out.
  const { rows } = planRows("E D001", "20171106");
  assert.ok(rows.length >= 1, "premise: E D001 in the 2017-11-06 release");
  const t = text(await call({ budget_line: "E D001", release: "2017-11-06" }));
  assert.match(t, /release 2017-11-06/);
  const r = rows[0];
  assert.ok(t.includes(`FY${r.yr1_fy} ${thousands(r.year1_amt)}`));
  const releases = new Set(PLAN.filter((x) => key(x.budline) === key("E D001")).map((x) => iso(x.pub_date)));
  for (const d of releases) assert.ok(t.includes(d), d);
});

test("funding: CITY shows the City plan only", async () => {
  // FAILS if funding is ignored.
  const t = text(await call({ budget_line: "HD 0201", funding: "CITY" }));
  assert.ok(!/NON CITY: FY/.test(t));
  assert.match(t, /CITY: FY/);
});

test("every answer that shows a plan figure says thousands, and every CPDB figure says dollars", async () => {
  // FAILS if any answer shows OMB's figures without the unit, or calls CPDB thousands.
  for (const args of [{ budget_line: "P D018" }, { budget_line: "HD 0201" }, { budget_line: "E D001", release: "2017-11-06" }]) {
    const t = text(await call(args));
    assert.match(t, /In THOUSANDS of dollars/);
    assert.ok(!/CPDB[^\n]*thousands of dollars/.test(t.replace(/OMB's \(in thousands\)/g, "")), JSON.stringify(args));
    assert.match(t, /by budget line only/);
    assert.match(t, /Source: /);
  }
});

test("a budget line in no source says so plainly, without an error", async () => {
  // FAILS if an unknown line is an error, or the answer pretends to show figures.
  const r = await call({ budget_line: "ZZ D999" });
  assert.equal(r.isError, undefined);
  assert.match(text(r), /not in OMB's Capital Commitment Plan/);
});
