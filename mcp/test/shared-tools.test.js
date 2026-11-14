/**
 * BetaNYC's shared tools (#310; the What's changed standard, BetaNYC/betanyc-ai-workspace#1637
 * § 7): whats_changed, about_betanyc and about_data, from src/betanyc-tools.ts (copied in
 * unchanged), called through this server's own tools/list and tools/call. Each test says what
 * result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { BETANYC_TOOL_NAMES, SHARED_MODULE_VERSION } from "../dist/betanyc-tools.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const VERSION = JSON.parse(readFileSync(join(MCP, "package.json"), "utf8")).version;

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "shared-tools-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

const call = (name, args = {}) => client.callTool({ name, arguments: args });
const text = (r) => r.content.map((c) => c.text).join("\n");

test("the three shared tools are listed, read-only, with the module's own schemas", async () => {
  // FAILS if one is missing, renamed, or loses readOnlyHint or its strict input schema.
  const { tools } = await client.listTools();
  for (const name of BETANYC_TOOL_NAMES) {
    const t = tools.find((x) => x.name === name);
    assert.ok(t, name);
    assert.equal(t.annotations?.readOnlyHint, true, name);
    assert.equal(t.inputSchema.additionalProperties, false, name);
    assert.ok(t.outputSchema, name);
  }
});

test("about_betanyc names the server, its version, the repo and the module version", async () => {
  // FAILS if the server is wired with the wrong name, version or repo, or the stale-copy
  // check (shared_module_version) is lost.
  const r = await call("about_betanyc");
  assert.equal(r.isError, undefined);
  const s = r.structuredContent.server;
  assert.equal(s.name, "nyc-budget-mcp");
  assert.equal(s.version, VERSION);
  assert.equal(s.repository, "https://github.com/BetaNYC/New-York-City-Budget");
  assert.equal(s.shared_module_version, SHARED_MODULE_VERSION);
  assert.match(text(r), /BetaNYC, a project of the Fund for the City of New York/);
});

test("whats_changed answers from the repo's WHATS-CHANGED.md, corrections first-class", async () => {
  // FAILS if the package does not ship the file (the prebuild copy), the history start is lost,
  // or a correction comes back without its advice.
  const r = await call("whats_changed", { tag: "correction", limit: 50 });
  assert.equal(r.isError, undefined, text(r));
  const sc = r.structuredContent;
  assert.equal(sc.history_begins, "2026-07-06");
  assert.ok(sc.total_matching >= 10, `${sc.total_matching} corrections`);
  const late = sc.entries.find((e) => e.title === "Agency budget years were shown one year late");
  assert.ok(late, sc.entries.map((e) => e.title).join(" | "));
  assert.equal(late.date, "2026-11-09");
  assert.ok(late.tags.includes("Correction"));
  assert.match(late.if_you_used_the_old_numbers, /move each year back by one/);
  for (const e of sc.entries) assert.ok(e.if_you_used_the_old_numbers, e.title);
});

test("whats_changed serves the 2.1.0 entry under the CHANGELOG's 2.1.0 date, and every entry is dated", async () => {
  // FAILS if the 2.1.0 entry is still "Unreleased" (release.yml's check --release would refuse
  // to publish), or its date differs from the CHANGELOG's.
  const date = /^## 2\.1\.0 — (\d{4}-\d{2}-\d{2})$/m.exec(readFileSync(join(MCP, "CHANGELOG.md"), "utf8"))?.[1];
  assert.ok(date, "CHANGELOG.md has a dated 2.1.0 heading");
  const r = await call("whats_changed", { tag: "MCP", limit: 50 });
  const sc = r.structuredContent;
  assert.ok(sc.entries.every((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date)));
  const e = sc.entries.find((x) => x.title === "Server adds City agency budgets, FY2027 changes and Council Members by person");
  assert.ok(e, sc.entries.map((x) => x.title).join(" | "));
  assert.equal(e.date, date);
});

test("the copy the package ships is the repo's file", () => {
  // FAILS if mcp/WHATS-CHANGED.md (the prebuild copy) differs from the root file.
  assert.equal(readFileSync(join(MCP, "WHATS-CHANGED.md"), "utf8"), readFileSync(join(MCP, "..", "WHATS-CHANGED.md"), "utf8"));
});

test("about_data says plainly that this repo has no DATA-SOURCES.json yet, without an error", async () => {
  // FAILS if the missing file is an error, or the answer pretends to list sources.
  const r = await call("about_data");
  assert.equal(r.isError, undefined);
  assert.deepEqual(r.structuredContent.sources, []);
  assert.match(text(r), /has no DATA-SOURCES\.json yet/);
});

test("bad arguments are refused by name, as every tool here does", async () => {
  // FAILS if an unknown key or a bad date is ignored.
  const a = await call("whats_changed", { district: 10 });
  assert.equal(a.isError, true);
  assert.match(text(a), /district/);
  const b = await call("whats_changed", { since: "11/09/2026" });
  assert.equal(b.isError, true);
});
