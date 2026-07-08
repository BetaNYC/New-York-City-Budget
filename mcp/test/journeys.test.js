/**
 * Journey tests — re-run each of the 8 user journeys from
 * people/noel/work/2026-07-07-mcp-budget-user-journeys.md against the real MCP
 * tools, using the same real example data validated by hand in that doc
 * (BetaNYC EIN 13-2612524, Council District 33 / Restler, FY2026 Transparency
 * Resolution 1's Noel Pointer → El Puente CASA transfer).
 *
 * Tools are driven through the actual MCP protocol: an in-process Client is
 * linked to the server via InMemoryTransport, so every assertion exercises
 * tools/call end-to-end (not just the DB layer). This proves the MCP works,
 * not merely that it starts.
 *
 * The budget MCP owns only the budget half of each journey. Steps that belong
 * to sibling MCPs (nyc-checkbook, nyc-council, nyc-record, nyc-charter,
 * socrata) are out of scope here and noted in comments — see the journeys doc
 * for the full cross-MCP chains and their verdicts.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { server } from "../dist/server.js";

let client;

before(async () => {
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);
  client = new Client({ name: "journey-test", version: "0" }, { capabilities: {} });
  await client.connect(clientTransport);
});

after(async () => {
  await client.close();
});

async function callText(name, args = {}) {
  const res = await client.callTool({ name, arguments: args });
  assert.ok(!res.isError, `${name} returned an error: ${JSON.stringify(res.content)}`);
  return res.content.map((c) => c.text).join("\n");
}

test("tools/list exposes the 7 budget tools", async () => {
  const { tools } = await client.listTools();
  const names = tools.map((t) => t.name).sort();
  assert.deepEqual(names, [
    "get_awards_by_ein",
    "get_legistar_link",
    "get_terms_conditions",
    "list_available_fiscal_years",
    "search_awards",
    "search_capital_projects",
    "search_transparency_resolutions",
  ]);
});

test("Journey 1 — watchdog: FY2026 Reso 1 rescind of Noel Pointer, re-designate to El Puente (Restler, CASA)", async () => {
  const rescind = await callText("search_transparency_resolutions", {
    council_member: "Restler",
    fiscal_year: 2026,
    action: "rescind",
  });
  assert.match(rescind, /Noel Pointer Foundation/);
  assert.match(rescind, /-\$20,000/);
  assert.match(rescind, /DCLA/);
  assert.match(rescind, /2025-08-14/);
  assert.match(rescind, /Cultural After-School Adventure/);

  const designate = await callText("search_transparency_resolutions", {
    organization: "El Puente",
    fiscal_year: 2026,
    action: "designate",
  });
  assert.match(designate, /El Puente de Williamsburg/);
  assert.match(designate, /\$20,000/);
  // (Checkbook payment-history step is nyc-checkbook-mcp's — out of scope here.)
});

test("Journey 2 — community board: District 33 (Restler) FY2026 discretionary awards incl. JustFix", async () => {
  const out = await callText("search_awards", { council_member: "Restler", fiscal_year: 2026, limit: 500 });
  assert.match(out, /JustFix/);
  assert.match(out, /\$5,000/); // JustFix anti-poverty designation
  assert.match(out, /\$25,000/); // BetaNYC District 33 designation
  // (Contract-status cross-check is nyc-checkbook-mcp's — out of scope here.)
});

test("Journey 3 & 7 — BetaNYC (EIN 13-2612524) discretionary history FY25/26/27 + adoption status", async () => {
  // EIN 13-2612524 is the Fund for the City of New York, a fiscal sponsor — narrow by program to isolate BetaNYC.
  const out = await callText("search_awards", { ein: "13-2612524", program: "BetaNYC", limit: 500 });
  assert.match(out, /FY2025: 6 award\(s\), \$115,000/);
  assert.match(out, /FY2026: 6 award\(s\), \$115,000/);
  assert.match(out, /FY2027: 5 award\(s\), \$95,000/);
  assert.match(out, /Restler/); // $25,000 sponsor present all three years
  assert.match(out, /Digital Inclusion and Literacy/);

  // Adoption status via the crosswalk (FY2027 Schedule C omnibus).
  const link = await callText("get_legistar_link", { fiscal_year: 2027, document_type: "schedule_c" });
  assert.match(link, /Res 0540-2026/);
  assert.match(link, /\[confirmed\]/);
  assert.match(link, /legistar\.council\.nyc\.gov/);
});

test("Journey 3 sanity — get_awards_by_ein returns the full fiscal-sponsor pool (not just BetaNYC)", async () => {
  const out = await callText("get_awards_by_ein", { ein: "132612524" });
  // EIN 13-2612524 is the Fund for the City of New York, a fiscal sponsor whose
  // EIN aggregates many programs. The unfiltered call returns the whole pool
  // (hundreds of awards across many orgs), far exceeding BetaNYC's slice —
  // proving the tool honestly returns everything on the EIN, not just BetaNYC.
  assert.match(out, /Fund for the City of New York/);
  assert.match(out, /Center for Court Innovation/); // a large non-BetaNYC program on the same EIN
  assert.match(out, /FY2025:/);
  assert.match(out, /FY2026:/);
  assert.match(out, /FY2027:/);
});

test("Journey 4 — capital oversight: Restler FY2026 §254 projects (12 projects, $18,750,000)", async () => {
  const out = await callText("search_capital_projects", { sponsor: "Restler", fiscal_year: 2026, limit: 500 });
  assert.match(out, /12 project\(s\)/);
  assert.match(out, /\$18,750,000/);
  // (Checkbook capital-commitment join is a genuine data gap — see journeys doc J4.)
});

test("Journey 5 — legal/compliance: Digital Inclusion initiative present across years + crosswalk link", async () => {
  const out = await callText("search_awards", { initiative: "Digital Inclusion and Literacy", program: "BetaNYC", limit: 500 });
  assert.match(out, /FY2025:/);
  assert.match(out, /FY2026:/);
  assert.match(out, /FY2027:/);
  const link = await callText("get_legistar_link", { fiscal_year: 2026, document_type: "schedule_c" });
  assert.match(link, /Res 0974-2025/);
  // (The initiative has no standalone Legistar matter; §107(e) authority and the
  //  MN-N omnibus resolution are nyc-council-mcp / nyc-charter-laws-rules findings.)
});

test("Journey 6 — procurement: FY2026 Noel Pointer CASA designation exists (budget side of the City Record cross-check)", async () => {
  const out = await callText("search_transparency_resolutions", { organization: "Noel Pointer", fiscal_year: 2026 });
  assert.match(out, /Noel Pointer Foundation/);
  assert.match(out, /DCLA/);
  // (City Record solicitation/notice cross-check is nyc-record-mcp's — out of scope here.)
});

test("Journey 8 — build-time validation: MCP honestly reports its expanded coverage + the FY2009–FY2014 gap", async () => {
  // Awards now reach back to FY2015 (the first EIN-level year). What the MCP must
  // still get right: FY2009–FY2014 are initiatives-only (no EIN) and are NOT in
  // the award tools, and the crosswalk spans the full range.
  const out = await callText("list_available_fiscal_years");
  assert.match(out, /Schedule C awards:\s+FY2015, FY2016, FY2017, FY2018, FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025, FY2026, FY2027/);
  assert.match(out, /Legistar crosswalk:\s+FY2008–FY2027/);
  assert.match(out, /FY2009–FY2014 Schedule C is INITIATIVES-ONLY/);
  // Award coverage line must never claim FY2014 (or earlier) EIN-level award data.
  assert.doesNotMatch(out, /Schedule C awards:[^\n]*FY2014/);
});

test("get_terms_conditions returns FY2026 reporting mandates", async () => {
  const out = await callText("get_terms_conditions", { fiscal_year: 2026, limit: 500 });
  assert.match(out, /FY2026/);
  assert.match(out, /term\(s\)/);
});
