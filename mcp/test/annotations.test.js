/**
 * Every tool says it only reads (#336). Each tool carries annotations with readOnlyHint true,
 * openWorldHint false (every tool answers from data on this machine: the shipped index or the
 * downloaded PDF tables) and a title, through the shared module's annotateTools. Each test says
 * what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { assertEveryToolAnnotated } from "../dist/betanyc-tools.js";

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "annotations-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

test("every tool in TOOLS is annotated", () => {
  // FAILS if a tool is added without going through annotateTools.
  assertEveryToolAnnotated(budgetServer.TOOLS);
});

test("tools/list gives every tool readOnlyHint true, openWorldHint false and a title", async () => {
  // FAILS if a client sees a tool that may write, one marked as reaching outside, or no title.
  const { tools } = await client.listTools();
  assert.equal(tools.length, budgetServer.TOOLS.length);
  assertEveryToolAnnotated(tools);
  for (const t of tools) {
    assert.equal(t.annotations.readOnlyHint, true, t.name);
    assert.equal(t.annotations.openWorldHint, false, t.name);
    assert.ok(t.annotations.title, `${t.name} has no title`);
  }
});
