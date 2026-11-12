/**
 * The MCP's City agency budget tools (#270, built in #285).
 *
 * PENDING #285. Each suite is skipped until tools/list names its tool, so `npm test` stays green
 * now and these run, unchanged, the day the tools ship. (test/tools.test.js asserts exactly
 * eight tools; #285 updates that list in the same PR.)
 *
 * The tools' contract (docs/plans/2026-11-12-270-agency-budgets.md, "MCP tools"):
 *
 *   search_agency_budget     { agency?, unit?, fiscal_year?, limit? }
 *   compare_adopted_modified { agency?, unit?, fiscal_year }   (agency or unit required)
 *
 *   agency: an agency number ("056", "56") or words from its name ("police")
 *   unit:   a unit of appropriation number ("001") or words from its name
 *
 * Every answer: dollars as "$1,234,567"; says the amounts are gross (they include intra-city
 * transfers); names the Open Data release each figure comes from (mwzb-yiwb, publication date);
 * says "not yet published" for the newest year's modified and "not in that year's budget" for an
 * absent unit, never "$0" for either. Budget, not spending: each tool's description, and each
 * answer, points spending questions to @betanyc/nyc-checkbook-mcp.
 *
 * Expected values come from the index's agency_budget table (checked cell by cell against NYC
 * Open Data in test/agency-budget.test.js) and from OMB's printed Adopted Budget.
 * Each test says what result would make it FAIL.
 */
import { describe, test, before, after } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const DB_PATH = join(MCP, "data", "budget.db");
const usd = (v) => `$${Math.round(v).toLocaleString("en-US")}`;
const textOf = (res) => res.content.map((c) => c.text).join("\n");

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "agency-tools-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client?.close();
});

/** Whether a tool is listed. Read at definition time from the server module's own TOOLS list. */
const listed = (name) => (budgetServer.TOOLS ?? []).some((t) => t.name === name);
const skipUnless = (name) => (listed(name) ? false : `PENDING #285: the MCP does not list ${name} yet`);

function cell(year, agency, unit) {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    return db.prepare("SELECT * FROM agency_budget WHERE fiscal_year = ? AND agency_number = ? AND unit_number = ?").get(year, agency, unit);
  } finally {
    db.close();
  }
}
function agencyTotal(year, agency, col) {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    return db.prepare(`SELECT SUM(${col}) AS v FROM agency_budget WHERE fiscal_year = ? AND agency_number = ?`).get(year, agency).v;
  } finally {
    db.close();
  }
}
const newestYear = () => {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    return db.prepare("SELECT MAX(fiscal_year) AS y FROM agency_budget").get().y;
  } finally {
    db.close();
  }
};

describe("search_agency_budget", { skip: skipUnless("search_agency_budget") }, () => {
  test("is listed with a schema that takes agency, unit, fiscal_year and limit, and nothing else", async () => {
    // FAILS if the tool is missing, or its schema drifts from the contract above.
    const tool = (await client.listTools()).tools.find((t) => t.name === "search_agency_budget");
    assert.ok(tool);
    assert.deepEqual(Object.keys(tool.inputSchema.properties).sort(), ["agency", "fiscal_year", "limit", "unit"]);
    assert.equal(tool.inputSchema.additionalProperties, false);
  });

  test("its description says budget, not spending, and names nyc-checkbook-mcp for spending", async () => {
    // FAILS if a client can't tell from the tool list which server answers "how much was spent".
    const tool = (await client.listTools()).tools.find((t) => t.name === "search_agency_budget");
    assert.match(tool.description, /adopted/i);
    assert.match(tool.description, /modified/i);
    assert.match(tool.description, /nyc-checkbook-mcp/);
    assert.match(tool.description, /spending/i);
  });

  test("Manhattan CB 1 by agency number, FY2025: OMB's printed figures, each with its release", async () => {
    // FAILS if a figure is off by a year or a dollar, or the answer doesn't say where it's from.
    const res = await client.callTool({ name: "search_agency_budget", arguments: { agency: "341", fiscal_year: 2025 } });
    const text = textOf(res);
    assert.ok(!res.isError, text);
    assert.match(text, /MANHATTAN COMMUNITY BOARD #1/);
    assert.ok(text.includes("$267,484"), "unit 001 adopted (OMB p. 182E)");
    assert.ok(text.includes("$249,484"), "unit 001 modified");
    assert.ok(text.includes("$190,939"), "unit 002 modified");
    assert.match(text, /mwzb-yiwb/);
    assert.match(text, /20240630/, "the adopted figure's release (tag 2025)");
    assert.match(text, /20250630/, "the modified figure's release (tag 2026)");
  });

  test("an unpadded agency number finds the same agency (56 = 056)", async () => {
    // FAILS if "56" misses NYPD because the index stores "056".
    const a = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "56", fiscal_year: 2026 } }));
    const b = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "056", fiscal_year: 2026 } }));
    assert.match(a, /POLICE DEPARTMENT/);
    assert.equal(a, b);
  });

  test("words from the name find the agency, and the agency total equals the index", async () => {
    // FAILS if a name search misses, or the total disagrees with agency_budget.
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "police", fiscal_year: 2026 } }));
    assert.match(text, /POLICE DEPARTMENT/);
    assert.ok(text.includes(usd(agencyTotal(2026, "056", "adopted"))), `NYPD FY2026 adopted ${usd(agencyTotal(2026, "056", "adopted"))}`);
  });

  test("one unit by number: NYPD 001 Operations, FY2026 adopted", async () => {
    // FAILS if the unit filter is ignored or matched as a substring of other unit numbers.
    const c = cell(2026, "056", "001");
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "056", unit: "001", fiscal_year: 2026 } }));
    assert.match(text, /OPERATIONS/);
    assert.ok(text.includes(usd(c.adopted)), usd(c.adopted));
    assert.doesNotMatch(text, /EXECUTIVE MANAGEMENT/, "unit 002 is not asked for");
  });

  test("the answer says the amounts are gross, including intra-city transfers", async () => {
    // FAILS if a reader can mistake these totals for OMB's headline net budget.
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "056", fiscal_year: 2026 } }));
    assert.match(text, /gross/i);
    assert.match(text, /intra-city/i);
  });

  test("the newest year's modified says not yet published, never $0", async () => {
    // FAILS if NULL is shown as $0 or "—" with no reason.
    const y = newestYear();
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "341", fiscal_year: y } }));
    assert.match(text, /not yet published/i);
  });

  test("a unit absent from a year's budget says so, never $0", async () => {
    // FAILS if an absent unit is reported with $0 adopted. The unit-year is picked from the index:
    // the first row with no adopted release (the unit is only in the next year's release).
    const db = new Database(DB_PATH, { readonly: true });
    let r;
    try {
      r = db.prepare("SELECT * FROM agency_budget WHERE adopted_release IS NULL ORDER BY fiscal_year, agency_number, unit_number LIMIT 1").get();
    } finally {
      db.close();
    }
    assert.ok(r, "some unit-year has no adopted figure");
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: r.agency_number, unit: r.unit_number, fiscal_year: r.fiscal_year } }));
    assert.match(text, /not in (that|this|the FY\d{4}) (year's )?(adopted )?budget/i, text);
  });

  test("a year outside the data is an error that lists the years held", async () => {
    // FAILS if FY2016 or FY2030 returns an empty "$0" answer instead of saying what exists.
    for (const fiscal_year of [2016, 2030]) {
      const res = await client.callTool({ name: "search_agency_budget", arguments: { agency: "056", fiscal_year } });
      assert.equal(res.isError, true, String(fiscal_year));
      assert.match(textOf(res), /2017/);
    }
  });

  test("an unknown argument is refused", async () => {
    // FAILS if a misspelled filter (agency_name, year) is silently ignored and returns everything.
    const res = await client.callTool({ name: "search_agency_budget", arguments: { agency_name: "police", fiscal_year: 2026 } });
    assert.equal(res.isError, true);
  });
});

describe("compare_adopted_modified", { skip: skipUnless("compare_adopted_modified") }, () => {
  test("is listed with a schema that takes agency, unit and fiscal_year, fiscal_year required", async () => {
    // FAILS if the schema drifts from the contract.
    const tool = (await client.listTools()).tools.find((t) => t.name === "compare_adopted_modified");
    assert.ok(tool);
    assert.deepEqual(Object.keys(tool.inputSchema.properties).sort(), ["agency", "fiscal_year", "unit"]);
    assert.deepEqual(tool.inputSchema.required, ["fiscal_year"]);
    assert.match(tool.description, /nyc-checkbook-mcp/);
  });

  test("NYPD FY2025: adopted, modified, and the change in dollars, all equal to the index", async () => {
    // FAILS if the change is computed the wrong way round, or from the wrong year.
    const a = agencyTotal(2025, "056", "adopted");
    const m = agencyTotal(2025, "056", "modified");
    const text = textOf(await client.callTool({ name: "compare_adopted_modified", arguments: { agency: "056", fiscal_year: 2025 } }));
    assert.ok(text.includes(usd(a)), `adopted ${usd(a)}`);
    assert.ok(text.includes(usd(m)), `modified ${usd(m)}`);
    assert.ok(text.includes(usd(Math.abs(m - a))), `change ${usd(m - a)}`);
    assert.match(text, m >= a ? /increase|more|\+/i : /decrease|less|-|−/i);
  });

  test("Manhattan CB 1 unit 002, FY2025: $27,245 adopted, $190,939 modified (OMB p. 182E)", async () => {
    // FAILS on an off-by-one year: FY2025 adopted for unit 002 is in the release tagged 2025.
    const c = cell(2025, "341", "002");
    const text = textOf(await client.callTool({ name: "compare_adopted_modified", arguments: { agency: "341", unit: "002", fiscal_year: 2025 } }));
    assert.ok(text.includes(usd(c.adopted)), usd(c.adopted));
    assert.ok(text.includes("$190,939"));
  });

  test("the newest year: modified is not yet published, so there is no change to report", async () => {
    // FAILS if the tool reports "-100%" or a change against $0.
    const y = newestYear();
    const text = textOf(await client.callTool({ name: "compare_adopted_modified", arguments: { agency: "056", fiscal_year: y } }));
    assert.match(text, /not yet published/i);
    assert.doesNotMatch(text, /-100(\.0)?%/);
  });

  test("without agency or unit, it is an error", async () => {
    // FAILS if the tool answers for the whole city by accident when a filter was forgotten.
    const res = await client.callTool({ name: "compare_adopted_modified", arguments: { fiscal_year: 2025 } });
    assert.equal(res.isError, true);
  });
});

describe("the boundary with @betanyc/nyc-checkbook-mcp", { skip: skipUnless("search_agency_budget") }, () => {
  test("mcp/README.md says this server is budgets and Checkbook is spending", () => {
    // FAILS if the README doesn't tell a reader which server answers which question.
    const readme = readFileSync(join(MCP, "README.md"), "utf8");
    assert.match(readme, /search_agency_budget/);
    assert.match(readme, /compare_adopted_modified/);
    const section = readme.split(/\n#+ /).find((s) => /checkbook/i.test(s) && /budget/i.test(s) && /spending/i.test(s) && /search_agency_budget/.test(s));
    assert.ok(section, "a README section names both the agency tools and Checkbook, budget vs spending");
  });

  test("list_available_fiscal_years reports the agency budget years and the snapshot", async () => {
    // FAILS if a client can't learn which agency budget years exist and how fresh they are.
    const text = textOf(await client.callTool({ name: "list_available_fiscal_years", arguments: {} }));
    assert.match(text, /agency budget/i);
    assert.match(text, /mwzb-yiwb/);
    assert.match(text, /FY2017/);
    assert.match(text, new RegExp(`FY${newestYear()}`));
  });

  test("no agency budget answer offers payments, contracts or spending figures", async () => {
    // FAILS if the tool drifts into Checkbook's territory (spending), instead of pointing there.
    const text = textOf(await client.callTool({ name: "search_agency_budget", arguments: { agency: "056", fiscal_year: 2025 } }));
    assert.doesNotMatch(text, /\b(spent|expenditure|payments?)\b:\s*\$/i);
    assert.match(text, /nyc-checkbook-mcp|Checkbook NYC/);
  });
});

test("the server's TOOLS list is exported, so the suites above can see whether to run", () => {
  // FAILS if dist/server.js stops exporting TOOLS: every suite above would then skip forever.
  assert.ok(Array.isArray(budgetServer.TOOLS), "dist/server.js exports TOOLS");
  assert.ok(existsSync(DB_PATH));
});
