/**
 * In server mode stdout carries only the MCP protocol (#343; BetaNYC MCP practice 20): every line
 * the built server writes there is one JSON-RPC 2.0 message, and diagnostics go to stderr. Each
 * test says what result would make it FAIL.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { LATEST_PROTOCOL_VERSION } from "@modelcontextprotocol/sdk/types.js";

const MCP = join(dirname(fileURLToPath(import.meta.url)), "..");

test("initialize, tools/list and a tool call write only JSON-RPC messages to stdout", async () => {
  // FAILS if anything (a log line, a progress message, a stray console.log) reaches stdout.
  const dir = mkdtempSync(join(tmpdir(), "nyc-budget-stdout-"));
  const env = { ...process.env, NYC_BUDGET_DATA_DIR: dir };
  delete env.NYC_BUDGET_PDF_DATA;
  const p = spawn(process.execPath, [join(MCP, "dist", "index.js")], { env, stdio: ["pipe", "pipe", "pipe"] });
  let out = "";
  p.stdout.on("data", (d) => (out += d));
  p.stderr.resume();
  const send = (m) => p.stdin.write(JSON.stringify({ jsonrpc: "2.0", ...m }) + "\n");
  send({ id: 1, method: "initialize", params: { protocolVersion: LATEST_PROTOCOL_VERSION, capabilities: {}, clientInfo: { name: "stdout-test", version: "0" } } });
  send({ method: "notifications/initialized" });
  send({ id: 2, method: "tools/list" });
  send({ id: 3, method: "tools/call", params: { name: "list_available_fiscal_years", arguments: {} } });
  send({ id: 4, method: "tools/call", params: { name: "search_schedule_c_awards", arguments: { limit: 1 } } });
  const deadline = Date.now() + 60_000;
  while (!/"id":4[,}]/.test(out) && Date.now() < deadline) await new Promise((r) => setTimeout(r, 50));
  p.kill();
  rmSync(dir, { recursive: true, force: true });
  const lines = out.split("\n").filter((l) => l !== "");
  assert.ok(lines.length >= 4, `only ${lines.length} lines: ${out.slice(0, 500)}`);
  for (const l of lines) {
    let m;
    assert.doesNotThrow(() => (m = JSON.parse(l)), `not JSON: ${l.slice(0, 200)}`);
    assert.equal(m.jsonrpc, "2.0", l.slice(0, 200));
  }
  assert.deepEqual(lines.map((l) => JSON.parse(l).id).filter((id) => id != null).sort(), [1, 2, 3, 4]);
});
