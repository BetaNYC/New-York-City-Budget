/**
 * Strict tool schemas — issue #37. (2.0.0: the original reproduction was on search_awards, which
 * is retired; the same guard is asserted on the tools that replace it.)
 *
 * Before this guard, every tool accepted parameters that were not in its schema,
 * silently dropped them (zod strips unknown keys by default), and returned
 * UNFILTERED results with no error. The dangerous case is district-shaped:
 *
 *   search_awards({ council_district: 10, fiscal_year: 2026 })
 *     → $47,500,647 of CITYWIDE awards, formatted exactly like a real answer
 *
 * There is no district filter on Schedule C — it keys on the sponsoring
 * member's surname (`council_member`). The caller gets correct, correctly
 * sourced data answering a different question, with nothing in the response
 * signalling that a filter was dropped.
 *
 * Two layers are asserted here:
 *   (a) the ADVERTISED inputSchema sets `additionalProperties: false`, so the
 *       calling model knows the parameter is invalid before it calls;
 *   (b) the handler's zod schema is `.strict()`, so anything slipping through
 *       raises instead of being silently stripped — with an error naming the
 *       right parameter.
 *
 * Namespace import (not named) is deliberate: a missing `TOOLS` export must
 * fail test 1 as an assertion, not link-error the whole file and hide tests 2
 * and 3.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

let client;

before(async () => {
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(serverTransport);
  client = new Client({ name: "strict-schema-test", version: "0" }, { capabilities: {} });
  await client.connect(clientTransport);
});

after(async () => {
  await client.close();
});

test("every tool advertises that unknown parameters are invalid", () => {
  const tools = budgetServer.TOOLS;
  assert.ok(Array.isArray(tools), "server.ts must export TOOLS so this check covers tools added later");
  assert.ok(tools.length > 0, "TOOLS must not be empty");
  for (const tool of tools) {
    assert.equal(
      tool.inputSchema.additionalProperties,
      false,
      `${tool.name} must set additionalProperties:false`
    );
  }
});

test("the advertised strictness survives the wire (tools/list)", async () => {
  const { tools } = await client.listTools();
  for (const tool of tools) {
    assert.equal(
      tool.inputSchema.additionalProperties,
      false,
      `${tool.name} must advertise additionalProperties:false over the MCP protocol`
    );
  }
});

test("search_disclosure_awards rejects the district-shaped guess instead of answering it", async () => {
  // The issue's reproduction, on the tool that now answers award questions. Before #40 an
  // unknown filter was stripped and the citywide rows came back as if filtered.
  const res = await client.callTool({
    name: "search_disclosure_awards",
    arguments: { council_district: 10, fiscal_year: 2026, limit: 15 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true, `council_district must raise. Got: ${text.slice(0, 300)}`);
  assert.match(text, /does not accept `council_district`/);
  assert.doesNotMatch(text, /matching designation/);
});

test("the error points at the right parameter, not just the wrong one", async () => {
  const res = await client.callTool({ name: "search_disclosure_awards", arguments: { council_district: 10 } });
  const text = res.content.map((c) => c.text).join("\n");
  assert.match(text, /Use `council_member` or `council_member_id` instead of `council_district`/);
  assert.match(text, /names a council member .*not a district/i, "must explain that the disclosure carries no district");
});

test("a per-tool alias hint does not leak a parameter that tool lacks", async () => {
  // council_member is real on search_disclosure_awards but NOT on search_council_capital (which
  // has sponsor); district is a guess on both, but only capital has council_district.
  const res = await client.callTool({ name: "search_council_capital", arguments: { council_member: "Restler" } });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true);
  assert.match(text, /Use `sponsor` or `sponsor_exact` instead of `council_member`/);
  const d = await client.callTool({ name: "search_council_capital", arguments: { district: 33 } });
  const dt = d.content.map((c) => c.text).join("\n");
  assert.match(dt, /Use `council_district` instead of `district`/);
  assert.doesNotMatch(dt, /council_member/, "capital has no council_member parameter to suggest");
  const o = await client.callTool({ name: "compare_capital_to_omb", arguments: { fiscal_year: 2027 } });
  const ot = o.content.map((c) => c.text).join("\n");
  assert.equal(o.isError, true);
  assert.match(ot, /Accepted parameters: report_year, budget_line, verdict, limit\./);
});

test("query is redirected to the real text filters", async () => {
  const res = await client.callTool({ name: "search_council_capital", arguments: { query: "library" } });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true);
  assert.match(text, /Use `title` or `description` instead of `query`/);
});

test("regression guard — the supported parameter still works", async () => {
  const res = await client.callTool({
    name: "search_council_capital",
    arguments: { sponsor_exact: "Restler", fiscal_year: 2026, limit: 1 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.ok(!res.isError, `valid call must not be rejected: ${text.slice(0, 300)}`);
  assert.match(text, /^\d[\d,]* matching row\(s\)/m);
});

test("regression guard — a no-argument tool still works", async () => {
  const res = await client.callTool({ name: "list_available_fiscal_years", arguments: {} });
  assert.ok(!res.isError);
  assert.match(res.content.map((c) => c.text).join("\n"), /FY2009 · disclosure:/);
});
