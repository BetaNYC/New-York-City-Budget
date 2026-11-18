/**
 * Text several tools share is said once, in the server instructions (#344; BetaNYC MCP practice
 * 6), and the instructions keep BetaNYC's shared about_data paragraph. Each test says what result
 * would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { BETANYC_INSTRUCTIONS } from "../dist/betanyc-tools.js";

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "instructions-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

// Phrases only the full text-matching rule has.
const FULL_RULE = ["'Fellow' but not 'Fellowship'", "Identifier filters (project_id, resolution_number) always match substrings"];

test("the client gets the text-matching rule once, and the about_data paragraph", () => {
  // FAILS if the rule leaves the instructions, appears twice, or the shared paragraph is dropped.
  const ins = client.getInstructions();
  assert.equal(ins, budgetServer.INSTRUCTIONS);
  for (const p of FULL_RULE) assert.equal(ins.split(p).length - 1, 1, p);
  assert.ok(ins.includes(BETANYC_INSTRUCTIONS));
});

test("no tool description or parameter repeats the full rule", async () => {
  // FAILS if the rule is copied back into a tool (it costs about 1,200 tokens every turn).
  const { tools } = await client.listTools();
  for (const t of tools) {
    const json = JSON.stringify(t);
    for (const p of FULL_RULE) assert.ok(!json.includes(p), `${t.name} repeats: ${p}`);
  }
});
