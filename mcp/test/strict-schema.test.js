/**
 * Strict tool schemas — issue #37.
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

test("search_awards rejects the district-shaped guess instead of answering it", async () => {
  const res = await client.callTool({
    name: "search_awards",
    // limit:15 is the issue's exact reproduction — before the fix this returned
    // the FY2026 citywide top-15, totalling $47,500,647.
    arguments: { council_district: 10, fiscal_year: 2026, limit: 15 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(
    res.isError,
    true,
    `council_district is not a parameter and must raise, not return citywide awards. Got: ${text.slice(0, 300)}`
  );
  assert.match(text, /unrecognized|unknown|does not accept|council_member/i);
  assert.doesNotMatch(text, /\$47,500,647/);
});

test("the error points at the right parameter, not just the wrong one", async () => {
  const res = await client.callTool({
    name: "search_awards",
    arguments: { council_district: 10 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.match(text, /council_member/, "must name the parameter the caller should have used");
  assert.match(text, /district/i, "must explain that Schedule C carries no district filter");
});

test("a per-tool alias hint does not leak a parameter that tool lacks", async () => {
  // `sponsor` is real on search_capital_projects but NOT on search_awards, so a
  // global alias table would be wrong. council_member is the reverse.
  const res = await client.callTool({
    name: "search_capital_projects",
    arguments: { council_district: 10 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true);
  assert.match(text, /sponsor/, "search_capital_projects filters by sponsor");
  assert.doesNotMatch(
    text,
    /council_member/,
    "council_member is not a search_capital_projects parameter and must not be suggested"
  );
});

test("query is redirected to the real text filters", async () => {
  const res = await client.callTool({
    name: "search_awards",
    arguments: { query: "zzzznotarealorganization", fiscal_year: 2026 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true);
  assert.match(text, /organization/);
  assert.match(text, /program/);
});

test("regression guard — the supported parameter still works", async () => {
  const res = await client.callTool({
    name: "search_awards",
    arguments: { council_member: "De La Rosa", fiscal_year: 2026 },
  });
  const text = res.content.map((c) => c.text).join("\n");
  assert.ok(!res.isError, `valid call must not be rejected: ${text.slice(0, 300)}`);
  assert.match(text, /De La Rosa/);
  assert.match(text, /^\d+ award\(s\)/m);
});

test("regression guard — a no-argument tool still works", async () => {
  const res = await client.callTool({ name: "list_available_fiscal_years", arguments: {} });
  assert.ok(!res.isError);
  assert.match(res.content.map((c) => c.text).join("\n"), /Schedule C awards:/);
});
