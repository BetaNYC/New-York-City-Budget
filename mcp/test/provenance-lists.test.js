/**
 * Every data answer names its source with a link and says how current it is (#338, #339; BetaNYC
 * MCP practices 12 and 13), and every list says how many it shows of how many, caps its limit, and
 * says how to see more (#340; practice 14). Run against the shipped index and pretest's PDF
 * tables, which are large enough that limit 1 always leaves more. Each test says what result would
 * make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync, rmSync, symlinkSync } from "node:fs";
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

/**
 * The link to the data's own source each tool's answer must carry: the publisher's page, dataset
 * or file. BetaNYC's repo link alone does not count. The four PDF tools link each row on its page
 * of the Council's PDF in the explorer (`#view=source&spdf=source/...`), which is the source
 * document itself; in a published release they also link the PDF on GitHub and the publisher's
 * copy, which a local test release (no checked commit) leaves out. No data tool is exempt.
 */
const EXPLORER_PDF = /https:\/\/betanyc\.github\.io\/New-York-City-Budget\/explorer\/#view=source&spdf=source%2F\S+/;
const SOURCE_LINK = {
  search_disclosure_awards: /https:\/\/rnd\.council\.nyc\.gov\/\S+/,
  search_council_capital: /https:\/\/data\.cityofnewyork\.us\/\S*t474-a92g/,
  compare_capital_to_omb: /https:\/\/data\.cityofnewyork\.us\/d\/46m8-77gv/,
  search_capital_plan: /https:\/\/data\.cityofnewyork\.us\/d\/2cmn-uidm/,
  search_schedule_c_awards: EXPLORER_PDF,
  search_transparency_changes: EXPLORER_PDF,
  search_capital_book: EXPLORER_PDF,
  search_terms_conditions: EXPLORER_PDF,
  search_agency_budget: /https:\/\/data\.cityofnewyork\.us\/d\/mwzb-yiwb/,
  compare_adopted_modified: /https:\/\/data\.cityofnewyork\.us\/d\/mwzb-yiwb/,
  list_available_fiscal_years: /^(?=[\s\S]*https:\/\/data\.cityofnewyork\.us\/d\/\S+)(?=[\s\S]*https:\/\/rnd\.council\.nyc\.gov\/\S+)/,
};
const REPO_LINK = /^https:\/\/github\.com\/BetaNYC\/New-York-City-Budget\/?[.,;)]*$/;

test("every data answer links the data's own source, not only BetaNYC's repo, and has a date", async () => {
  // FAILS if an answer's only link is the GitHub repo (list_available_fiscal_years had only that),
  // if it names its source without linking it, or if it gives no as-of date.
  assert.deepEqual(Object.keys(SOURCE_LINK).sort(), Object.keys(CALLS).sort());
  for (const [name, args] of Object.entries(CALLS)) {
    const text = await call(name, args);
    const links = text.match(/https:\/\/\S+/g) ?? [];
    assert.ok(links.some((l) => !REPO_LINK.test(l)), `${name}: no link but the repo's`);
    assert.match(text, SOURCE_LINK[name], `${name}: no link to the data's source`);
    assert.match(text, /\b20\d\d-\d\d-\d\d(?!\d)/, `${name}: no date`);
  }
});

/** The repo's DATA-SOURCES.json, the file about_data reads (the package ships a copy). */
const SOURCES = JSON.parse(readFileSync(join(MCP, "..", "DATA-SOURCES.json"), "utf8")).sources;
const byId = Object.fromEntries(SOURCES.map((s) => [s.id, s]));

/** What about_data says of each source behind `tool`: its "is this official?" lines. */
async function aboutDataWords(tool) {
  const r = await client.callTool({ name: "about_data", arguments: { topic: tool } });
  const text = r.content.map((c) => c.text).join("\n");
  return text.split("\n").filter((l) => /^(BetaNYC modified this data: |BetaNYC produced this\. |Publisher: )/.test(l));
}

test("each data answer says what about_data says of its sources: BetaNYC modified or produced them", async () => {
  // FAILS if an answer leaves out, for a source DATA-SOURCES.json lists the tool for, about_data's
  // own sentence on whether it is official (and its official record and link); if an answer links
  // or names a source (its link, or its NYC Open Data id) without that sentence; or if about_data
  // gives a tool no source.
  for (const [name, args] of Object.entries(CALLS)) {
    const text = await call(name, args);
    const words = await aboutDataWords(name);
    const listed = SOURCES.filter((s) => s.tools.includes(name));
    assert.equal(words.length, listed.length, `${name}: about_data gives ${words.length} source(s), DATA-SOURCES.json lists ${listed.length}`);
    for (const w of words) {
      assert.match(w, /^BetaNYC (modified this data|produced this)\b/, `${name}: about_data calls a source official`);
      assert.ok(text.includes(w), `${name}: the answer does not say what about_data says:\n  ${w}`);
    }
    for (const s of SOURCES) {
      const id = /data\.cityofnewyork\.us\/d\/([a-z0-9]{4}-[a-z0-9]{4})$/.exec(s.source_url)?.[1];
      const named = text.includes(s.source_url) || (id && new RegExp(`\\b${id}\\b`).test(text));
      if (named) assert.ok(s.tools.includes(name), `${name}: names ${s.id} (${s.source_url}), which DATA-SOURCES.json does not list for it`);
    }
  }
});

/** Every source list_available_fiscal_years reports on, by DATA-SOURCES.json id (not the crosswalk). */
const YEARS_DEPEND_ON = [
  "expense-disclosure", "wayback-copies", "council-capital-workbook", "council-capital-open-data", "fy2018-capital-book",
  "pdf-tables", "agency-budgets", "omb-capital-budget", "capital-plan", "cpdb-commitments", "cpdb-projects",
];

test("list_available_fiscal_years links every source its years come from, from DATA-SOURCES.json", async () => {
  // FAILS if the Sources block leaves out a source the answer reports years of (the Internet
  // Archive copies, the FY2018 Legistar book, the PDF tables, agency budgets...), if a line of it is
  // deleted, if it lists one it does not report, or if DATA-SOURCES.json stops listing the tool for one.
  const text = await call("list_available_fiscal_years", {});
  const block = text.slice(text.indexOf("\nSources (as about_data gives them):\n") + 1).split("\n").slice(1).filter((l) => l.startsWith("  "));
  assert.equal(block.length, YEARS_DEPEND_ON.length, block.join("\n"));
  for (const id of YEARS_DEPEND_ON) {
    const s = byId[id];
    assert.ok(s?.tools.includes("list_available_fiscal_years"), `DATA-SOURCES.json does not list list_available_fiscal_years for ${id}`);
    const line = block.find((l) => l.startsWith(`  ${s.title}: `));
    assert.ok(line, `no Sources line for ${id} (${s.title})`);
    assert.ok(line.includes(s.source_url), `${id}: the line does not link ${s.source_url}`);
  }
  assert.ok(block.some((l) => l.includes("https://web.archive.org/")), "the Internet Archive copies");
  assert.ok(block.some((l) => l.includes("https://nyc.legistar1.com/")), "the FY2018 book on Legistar");
});

test("search_schedule_c_awards names the disclosure spreadsheet it joins rows to; DATA-SOURCES.json claims no Terms and Conditions amounts", () => {
  // FAILS if about_data for Schedule C leaves out the disclosure (disclosure_status comes from it),
  // or if DATA-SOURCES.json says the Terms and Conditions tables carry a unit amount the tool does
  // not serve (search_terms_conditions serves the conditions as printed, with no unit amounts).
  assert.ok(byId["expense-disclosure"].tools.includes("search_schedule_c_awards"));
  const pdf = JSON.stringify(byId["pdf-tables"]);
  assert.doesNotMatch(pdf, /adopted amount|mwzb-yiwb/);
  assert.ok(!byId["agency-budgets"].tools.includes("search_terms_conditions"));
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
  compare_capital_to_omb: [{}, /Showing (\d+) of ([\d,]+).*raise limit \(max 500\)/, 500],
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
