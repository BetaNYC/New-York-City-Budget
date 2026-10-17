/**
 * The 2.0.0 tool surface: exactly four tools, the six 1.x tools answering with their migration
 * note, and list_available_fiscal_years rebuilt on the structured datasets.
 *
 * Expected values come from data/disclosure_years.csv and data/capital/*.csv. Each test says
 * what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const fmt = (n) => n.toLocaleString("en-US");

const TOOLS_2 = ["search_disclosure_awards", "search_council_capital", "compare_capital_to_omb", "list_available_fiscal_years"];
const REMOVED = {
  search_awards: "search_disclosure_awards",
  get_awards_by_ein: "search_disclosure_awards",
  search_transparency_resolutions: "nyc-council-mcp",
  search_capital_projects: "search_council_capital",
  get_terms_conditions: "source/FY27/FY27-FINAL-Terms-and-Conditions-6.30.26.pdf",
  get_legistar_link: "nyc-council-mcp",
};

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "tools-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

test("tools/list exposes exactly the four 2.0.0 tools", async () => {
  // FAILS if a retired tool is still listed, or a 2.0 tool is missing.
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map((t) => t.name).sort(), [...TOOLS_2].sort());
});

test("every retired 1.x tool answers with an error that names where its questions go", async () => {
  // FAILS if a 1.x tool still returns data, or fails with a bare "Unknown tool" that leaves a
  // 1.x client with no way forward.
  for (const [name, next] of Object.entries(REMOVED)) {
    const res = await client.callTool({ name, arguments: { fiscal_year: 2026 } });
    const text = res.content.map((c) => c.text).join("\n");
    assert.equal(res.isError, true, name);
    assert.ok(text.includes(`${name} was removed in @betanyc/nyc-budget-mcp 2.0.0.`), name);
    assert.ok(text.includes(next), `${name} -> ${next}`);
  }
  const res = await client.callTool({ name: "no_such_tool", arguments: {} });
  assert.match(res.content[0].text, /^Error: Unknown tool: no_such_tool$/);
});

test("list_available_fiscal_years reports every year from the datasets, gaps stated", async () => {
  // FAILS if a year's disclosure or capital line disagrees with the committed CSVs, if FY2010 or
  // FY2018 is presented as covered, if an early snapshot is unmarked, or if the retired PDF
  // datasets are listed as served.
  const res = await client.callTool({ name: "list_available_fiscal_years", arguments: {} });
  const text = res.content.map((c) => c.text).join("\n");
  assert.ok(!res.isError);
  const years = readCsv("data/disclosure_years.csv");
  const cap = readCsv("data/capital/council_capital_awards.csv");
  const cmpYears = new Set(readCsv("data/capital/council_vs_omb_by_budget_line.csv").map((r) => r.report_year));
  for (const y of years) {
    const line = new RegExp(`^  FY${y.fiscal_year} · (.*)$`, "m").exec(text);
    assert.ok(line, `FY${y.fiscal_year} line`);
    const l = line[1];
    if (y.loaded === "yes") {
      assert.ok(l.includes(`disclosure: ${fmt(Number(y.award_rows))} rows`), `FY${y.fiscal_year}: ${l}`);
      assert.equal(l.includes("EARLY SNAPSHOT"), y.early_snapshot === "yes", `FY${y.fiscal_year} early`);
      assert.ok(l.includes(`retrieved ${y.retrieved}`));
    } else {
      assert.ok(l.includes("disclosure: NOT LOADED"), `FY${y.fiscal_year}: ${l}`);
    }
    const capRows = cap.filter((r) => r.report_year === y.fiscal_year);
    if (capRows.length) assert.ok(l.includes(`capital: ${fmt(capRows.length)} rows`), `FY${y.fiscal_year}: ${l}`);
    else assert.match(l, y.fiscal_year === "2018" ? /capital: MISSING/ : /capital: none/);
    assert.equal(l.includes("in the OMB comparison"), cmpYears.has(y.fiscal_year), `FY${y.fiscal_year} OMB`);
  }
  assert.match(text, /• FY2010 disclosure is not loaded: the Council's workbook \(2,592 rows/);
  assert.match(text, /• FY2018 capital: no Council workbook was found/);
  assert.match(text, /Retired in 2\.0\.0 and not served: everything extracted from the adopted-budget PDFs/);
  assert.doesNotMatch(text, /Schedule C awards:|Terms & Conditions:|Transparency Resolutions:/);
});
