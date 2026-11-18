/**
 * Every data answer names its source with a link and says how current it is (#338, #339; BetaNYC
 * MCP practices 12 and 13), and every list says how many it shows of how many, caps its limit, and
 * says how to see more (#340; practice 14). Run against the shipped index and pretest's PDF
 * tables, which are large enough that limit 1 always leaves more. Each test says what result would
 * make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, rmSync, symlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { closePdfTables } from "../dist/pdfdata.js";
import { BETANYC_TOOL_NAMES } from "../dist/betanyc-tools.js";

const MCP = join(dirname(fileURLToPath(import.meta.url)), "..");
const TMP = join(MCP, ".pdf-test", "provenance-lists");
const TABLES_DB = join(MCP, ".pdf-test", "release", "pdf-tables.db");

let client;
before(async () => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "pdf-tables"), { recursive: true });
  symlinkSync(TABLES_DB, join(TMP, "pdf-tables", "pdf-tables.db"));
  process.env.NYC_BUDGET_DATA_DIR = TMP;
  delete process.env.NYC_BUDGET_PDF_DATA;
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "provenance-lists-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
  closePdfTables();
  rmSync(TMP, { recursive: true, force: true });
});

async function call(name, args) {
  const r = await client.callTool({ name, arguments: args });
  const text = r.content.map((c) => c.text).join("\n");
  assert.ok(!r.isError, `${name}: ${text}`);
  return text;
}

/** One ordinary call per data tool (the shared tools carry their own provenance). */
const CALLS = {
  search_disclosure_awards: { fiscal_year: 2025, limit: 1 },
  search_council_capital: { fiscal_year: 2025, limit: 1 },
  compare_capital_to_omb: { limit: 1 },
  search_capital_plan: { budget_line: "P D018", limit: 1 },
  search_schedule_c_awards: { fiscal_year: 2025, limit: 1 },
  search_transparency_changes: { limit: 1 },
  search_capital_book: { limit: 1 },
  search_terms_conditions: { limit: 1 },
  search_agency_budget: { fiscal_year: 2025, limit: 1 },
  compare_adopted_modified: { agency: "056", fiscal_year: 2025 },
  list_available_fiscal_years: {},
};

test("every data tool is covered here", () => {
  // FAILS if a tool is added without a provenance check.
  const domain = budgetServer.TOOLS.map((t) => t.name).filter((n) => !BETANYC_TOOL_NAMES.includes(n));
  assert.deepEqual(domain.sort(), Object.keys(CALLS).sort());
});

test("every data answer has a link a person can open and a date", async () => {
  // FAILS if an answer names its source without a link, or gives no as-of date.
  for (const [name, args] of Object.entries(CALLS)) {
    const text = await call(name, args);
    assert.match(text, /https:\/\/\S+/, `${name}: no link`);
    assert.match(text, /\b20\d\d-\d\d-\d\d(?!\d)/, `${name}: no date`);
  }
});

test("the OMB comparison links its dataset and dates the Council side", async () => {
  // FAILS if #338 or #339 regress.
  const text = await call("compare_capital_to_omb", { limit: 1 });
  assert.match(text, /https:\/\/data\.cityofnewyork\.us\/d\/46m8-77gv/);
  assert.match(text, /The Council side as BetaNYC retrieved it: FY\d{4}.* retrieved 20\d\d-\d\d-\d\d/);
});

test("the capital plan links its three datasets", async () => {
  // FAILS if #338 regresses.
  const text = await call("search_capital_plan", { budget_line: "P D018", limit: 1 });
  for (const id of ["2cmn-uidm", "djxg-kcfi", "fi59-268w"]) assert.ok(text.includes(`https://data.cityofnewyork.us/d/${id}`), id);
});

/** List tools: the "showing N of M" line, and the most a call may show. */
const LISTS = {
  search_disclosure_awards: [{ fiscal_year: 2025 }, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
  search_council_capital: [{ fiscal_year: 2025 }, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
  compare_capital_to_omb: [{}, /Showing (\d+) of ([\d,]+)/, 500],
  search_schedule_c_awards: [{ fiscal_year: 2025 }, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
  search_transparency_changes: [{}, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
  search_capital_book: [{}, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
  search_terms_conditions: [{}, /Showing (\d+) of ([\d,]+).*raise limit \(max 100\)/, 100],
  search_agency_budget: [{ fiscal_year: 2025 }, /\(first (\d+) of (\d+); give agency to see one\)/, 500],
  search_capital_plan: [{ budget_line: "P D018" }, /showing (\d+) of ([\d,]+); raise limit, max 500, to see more/, 500],
};
const num = (s) => Number(s.replaceAll(",", ""));

test("limit 1 shows one, says how many match, and how to see more", async () => {
  // FAILS if a list hides how many it left out, or drops the way to see them.
  for (const [name, [args, re]] of Object.entries(LISTS)) {
    const m = re.exec(await call(name, { ...args, limit: 1 }));
    assert.ok(m, `${name}: no "showing N of M" signal`);
    assert.equal(num(m[1]), 1, name);
    assert.ok(num(m[2]) > 1, `${name}: the fixture should leave more than one`);
  }
});

test("a limit above the maximum is capped, and the count still covers every match", async () => {
  // FAILS if a list has no hard maximum.
  for (const [name, [args, , max]] of Object.entries(LISTS)) {
    const text = await call(name, { ...args, limit: 100_000 });
    const m = /(?:Showing|showing|first) (\d+) of ([\d,]+)/.exec(text) ?? /Showing all (\d+)/.exec(text);
    // Fewer agencies than the cap: search_agency_budget lists them all, with no "first N of M".
    if (!m && name === "search_agency_budget" && /^Agencies, largest adopted first:$/m.test(text)) continue;
    assert.ok(m, `${name}: no count`);
    assert.ok(num(m[1]) <= max, `${name}: showed ${m[1]}, over ${max}`);
  }
});
