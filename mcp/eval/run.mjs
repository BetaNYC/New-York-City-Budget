#!/usr/bin/env node
/**
 * Runs the evaluation set (eval/questions.json, #345) against the built server, offline: the
 * shipped index, and the PDF tables at --tables (default: pretest's .pdf-test/release). Prints one
 * line per question and exits 1 if any fails. --record saves the run as eval/runs/<date>.json
 * (<date>-2.json and so on for a later run the same day).
 *
 * It tests the answers of the named tools: each question names the tool and its arguments. It does
 * not test whether a model picks the right tool for a question.
 *   node eval/run.mjs [--tables <pdf-tables.db>] [--record]
 */
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");

export async function runEval({ tables = join(MCP, ".pdf-test", "release", "pdf-tables.db") } = {}) {
  const { questions } = JSON.parse(readFileSync(join(HERE, "questions.json"), "utf8"));
  const dir = mkdtempSync(join(tmpdir(), "nyc-budget-eval-"));
  const haveTables = existsSync(tables);
  if (haveTables) {
    mkdirSync(join(dir, "pdf-tables"));
    symlinkSync(resolve(tables), join(dir, "pdf-tables", "pdf-tables.db"));
  }
  process.env.NYC_BUDGET_DATA_DIR = dir;
  delete process.env.NYC_BUDGET_PDF_DATA;
  const { server } = await import("../dist/server.js");
  const { closePdfTables } = await import("../dist/pdfdata.js");
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await server.connect(st);
  const client = new Client({ name: "nyc-budget-eval", version: "0" }, { capabilities: {} });
  await client.connect(ct);
  const results = [];
  try {
    for (const q of questions) {
      if (q.tables && !haveTables) {
        results.push({ id: q.id, result: "skipped", why: `no PDF tables at ${tables}` });
        continue;
      }
      const r = await client.callTool({ name: q.tool, arguments: q.args });
      const text = r.content.map((c) => c.text).join("\n");
      const missing = (q.contains ?? []).filter((s) => !text.includes(s));
      const unwanted = (q.not_contains ?? []).filter((s) => text.includes(s));
      const pass = !r.isError && !missing.length && !unwanted.length;
      results.push({ id: q.id, result: pass ? "pass" : "fail", ...(pass ? {} : { isError: !!r.isError, missing, unwanted }) });
    }
  } finally {
    await client.close();
    closePdfTables();
    rmSync(dir, { recursive: true, force: true });
  }
  return results;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const at = args.indexOf("--tables");
  const results = await runEval(at >= 0 ? { tables: args[at + 1] } : {});
  for (const r of results) console.log(`${r.id} ${r.result}${r.result === "pass" ? "" : ` ${JSON.stringify({ ...r, id: undefined, result: undefined })}`}`);
  const count = (k) => results.filter((r) => r.result === k).length;
  console.log(`${count("pass")} pass, ${count("fail")} fail, ${count("skipped")} skipped, of ${results.length}`);
  if (args.includes("--record")) {
    const version = JSON.parse(readFileSync(join(MCP, "package.json"), "utf8")).version;
    const ran = new Date().toISOString();
    mkdirSync(join(HERE, "runs"), { recursive: true });
    // One file per run, never overwriting an earlier one of the same day (eval/runs/ is the record).
    let file = join(HERE, "runs", `${ran.slice(0, 10)}.json`);
    for (let k = 2; existsSync(file); k++) file = join(HERE, "runs", `${ran.slice(0, 10)}-${k}.json`);
    writeFileSync(file, JSON.stringify({ ran, version, results }, null, 2) + "\n");
  }
  process.exit(count("fail") ? 1 : 0);
}
