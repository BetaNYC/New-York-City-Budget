#!/usr/bin/env node
/**
 * agency-csv.mjs — write viz/agencies/data/nyc_budget.csv, the City agency budgets download, from
 * the MCP index's agency_budget table (#270, #288). One loader: the figures come from
 * mcp/scripts/agency-budget.mjs, which applies the year rule; this script only lays them out.
 *
 * The file keeps its address and its shape (Noel's defaults for #270, 2026-11-12), so scripts and
 * spreadsheets that fetch it keep working:
 *   - columns Fund, Department, Department ID, then "Adopted Y", "Modified Y" for FY2017 on;
 *   - one row per agency x unit of appropriation, ordered by agency number, then unit number;
 *     names as published in the newest release the unit is in;
 *   - a unit not in a year's budget is 0 (the view and the MCP say "not in this year's budget";
 *     this file keeps its 0s), and the newest year's Modified is empty (not yet published);
 *   - whole dollars as integers, CRLF line ends and minimal quoting, as Python's csv module wrote
 *     it before (code/agency_budget_cleanup.py, retired here).
 *
 *   node scripts/agency-csv.mjs            write the file from mcp/data/budget.db
 *   node scripts/agency-csv.mjs --check    exit 1 if the committed file differs from what the
 *                                          index gives (test/agency-csv.test.mjs runs this check)
 *   --db <path>                            another index (default mcp/data/budget.db)
 */
import { existsSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Database from "better-sqlite3";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..");
export const CSV_PATH = join(REPO, "viz", "agencies", "data", "nyc_budget.csv");
export const DEFAULT_DB = join(REPO, "mcp", "data", "budget.db");

/** One CSV field, quoted the way Python's csv.QUOTE_MINIMAL does. */
function field(v) {
  const s = String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** Whole dollars as integers; cents only when present. */
function amount(v) {
  const r = Math.round(v);
  return Math.abs(v - r) < 0.005 ? String(r) : v.toFixed(2);
}

/** The CSV text, from the agency_budget rows. */
export function agencyCsv(rows) {
  const years = [...new Set(rows.map((r) => r.fiscal_year))].sort((a, b) => a - b);
  const newest = years.at(-1);
  const units = new Map();
  for (const r of rows) {
    const k = `${r.agency_number}|${r.unit_number}`;
    const u = units.get(k) ?? { agency: r.agency_number, unit: r.unit_number, newest: -1, cells: new Map() };
    if (r.fiscal_year > u.newest) Object.assign(u, { newest: r.fiscal_year, agency_name: r.agency_name, unit_name: r.unit_name });
    u.cells.set(r.fiscal_year, r);
    units.set(k, u);
  }
  const head = ["Fund", "Department", "Department ID", ...years.flatMap((y) => [`Adopted ${y}`, `Modified ${y}`])];
  const lines = [head.map(field).join(",")];
  const sorted = [...units.values()].sort((a, b) => (a.agency === b.agency ? a.unit.localeCompare(b.unit) : a.agency.localeCompare(b.agency)));
  for (const u of sorted) {
    const cells = [u.agency_name, u.unit_name, u.unit];
    for (const y of years) {
      const c = u.cells.get(y);
      cells.push(amount(c?.adopted ?? 0));
      cells.push(y === newest ? "" : amount(c?.modified ?? 0));
    }
    lines.push(cells.map(field).join(","));
  }
  return lines.join("\r\n") + "\r\n";
}

export function readRows(dbPath = DEFAULT_DB) {
  if (!existsSync(dbPath)) throw new Error(`agency-csv: ${dbPath} is missing. Build the index first (cd mcp && npm ci).`);
  const db = new Database(dbPath, { readonly: true, fileMustExist: true });
  try {
    return db.prepare("SELECT * FROM agency_budget ORDER BY fiscal_year, agency_number, unit_number").all();
  } finally {
    db.close();
  }
}

function main() {
  const args = process.argv.slice(2);
  const at = args.indexOf("--db");
  const dbPath = at >= 0 ? resolve(args[at + 1]) : DEFAULT_DB;
  const text = agencyCsv(readRows(dbPath));
  if (args.includes("--check")) {
    const now = existsSync(CSV_PATH) ? readFileSync(CSV_PATH, "utf8") : "";
    if (now !== text) {
      console.error("agency-csv: viz/agencies/data/nyc_budget.csv differs from the index. Run `node viz/explorer/scripts/agency-csv.mjs`.");
      process.exitCode = 1;
      return;
    }
    console.error("agency-csv: viz/agencies/data/nyc_budget.csv equals the index");
    return;
  }
  const tmp = `${CSV_PATH}.tmp-${process.pid}`;
  writeFileSync(tmp, text);
  renameSync(tmp, CSV_PATH);
  console.error(`agency-csv: wrote ${CSV_PATH} (${text.split("\r\n").length - 2} units)`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
