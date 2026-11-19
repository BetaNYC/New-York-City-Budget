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

test("each tool with text filters states the rule itself, in one line, without pointing at the instructions", async () => {
  // FAILS if a tool's description or its whole_word parameter only says "see the server
  // instructions": some AI apps never show a model the instructions, so the hint must stand alone.
  const { tools } = await client.listTools();
  const withRule = tools.filter((t) => t.inputSchema.properties?.whole_word);
  assert.equal(withRule.length, 6, withRule.map((t) => t.name).join(", "));
  for (const t of withRule) {
    const ww = t.inputSchema.properties.whole_word.description;
    for (const [what, text] of [["description", t.description], ["whole_word", ww]]) {
      assert.doesNotMatch(text, /instructions/i, `${t.name} ${what} points at the instructions`);
      assert.match(text, /3 or fewer letters and digits matches whole words/, `${t.name} ${what}: no short-term rule`);
      assert.match(text, /a longer one (matches )?anywhere/, `${t.name} ${what}: no long-term rule`);
    }
    assert.match(t.description, /whole_word true or false overrides/, `${t.name}: no override`);
    assert.match(ww, /true, whole words only.*false, anywhere/, `${t.name}: whole_word does not say what true and false do`);
  }
});
