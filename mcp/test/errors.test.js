/**
 * Failures are plain sentences (#341; BetaNYC MCP practice 17): isError true, what went wrong and
 * what to try, no JSON dump and no stack frame, through the shared module's toolError. Each test
 * says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { homedir } from "node:os";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "errors-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

async function fail(name, args) {
  const r = await client.callTool({ name, arguments: args });
  assert.equal(r.isError, true, `${name} ${JSON.stringify(args)} did not fail`);
  const text = r.content.map((c) => c.text).join("\n");
  assert.doesNotMatch(text, /^\s*at\s+\S/m, "a stack frame");
  assert.doesNotMatch(text, /[[{]\s*"(code|expected|path)"/, "a JSON dump");
  return text;
}

test("a wrong argument type names the parameter in one plain sentence", async () => {
  // FAILS if zod's raw issue list (JSON) reaches the model, or the parameter is not named.
  const text = await fail("search_disclosure_awards", { fiscal_year: "2025" });
  assert.match(text, /^Error: search_disclosure_awards could not use its arguments \(fiscal_year: Expected number, received string\)\. Check each parameter's type/);
  assert.equal(text.split("\n").length, 1);
});

test("a wrong type on every tool that takes a number fails the same way", async () => {
  // FAILS if any tool lets a type error through as JSON or a stack.
  for (const [name, args] of [
    ["search_council_capital", { fiscal_year: "x" }],
    ["compare_capital_to_omb", { limit: "x" }],
    ["search_capital_plan", { limit: "x", budget_line: "P D018" }],
    ["search_agency_budget", { fiscal_year: "x" }],
    ["compare_adopted_modified", { fiscal_year: "x", agency: "056" }],
  ]) {
    assert.match(await fail(name, args), /could not use its arguments \(.+\)\. Check each parameter's type/, name);
  }
});

test("an unknown tool and a guard both fail as plain sentences", async () => {
  // FAILS if either loses isError or its plain wording.
  assert.equal(await fail("no_such_tool", {}), "Error: Unknown tool: no_such_tool");
  assert.match(await fail("search_disclosure_awards", { limit: 0 }), /^Error: limit must be at least 1/);
});

test("a thrown error reaches the model as one plain line, with no home-folder path", async () => {
  // FAILS if the server's catch passes err.message through as it is: here zod's message carries
  // the value given, which holds the home folder's path and a second line. The answer must be the
  // first line only (the shared module's errorSummary), with the home folder (whose name is the
  // person's username) as words.
  const home = homedir();
  const text = await fail("search_disclosure_awards", { status: `${home}/nyc-budget-mcp/x\nsecond line` });
  assert.match(text, /^Error: search_disclosure_awards could not use its arguments \(status: Invalid enum value\..*received 'the home folder\/nyc-budget-mcp\/x$/);
  assert.equal(text.split("\n").length, 1, "one line");
  if (home.length > 1) assert.ok(!text.includes(home), "the home folder's path");
});
