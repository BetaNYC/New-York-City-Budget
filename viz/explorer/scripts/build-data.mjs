#!/usr/bin/env node
/**
 * build-data.mjs — the explorer's data build. ONE loader: this script never parses a CSV.
 *
 *   1. Runs the MCP's own index build (mcp/scripts/build-index.mjs), which reads the repo's
 *      structured datasets, checks them and atomically writes mcp/data/budget.db. A rule change
 *      there reaches the explorer on the next build, by construction.
 *   2. Copies the index's tables, column for column, into Parquet with DuckDB (@duckdb/node-api):
 *        disclosure, disclosure_years, capital_council, capital_sources, capital_vs_omb, meta,
 *        the pdf_* tables, and the open_data_* tables (is each record on NYC Open Data?)
 *      The SQLite rows are read with better-sqlite3 (the MCP's own driver) and appended with
 *      DuckDB's appender under the column types the index declares (INTEGER -> BIGINT, REAL ->
 *      DOUBLE, TEXT -> VARCHAR). A value whose JS type does not fit its declared column is a stop,
 *      never a silent cast. DuckDB's `sqlite` extension would read budget.db directly, but it is
 *      not built into @duckdb/node-api: INSTALL downloads it at run time, and this build should not
 *      need the network.
 *   3. Writes public/data/manifest.json: the source commit, the index's build time and counts,
 *      each Parquet file's sha256 and rows, and the capital gap years with the README's reason.
 *
 * test/parity.test.mjs then proves the Parquet equals budget.db, year by year.
 *
 * Which PDF families load (the gate; decided in #190 / PLAN.md "The rules both front ends share"):
 *
 *   node scripts/build-data.mjs              the PUBLIC build (deploy-viz.yml): every PDF family
 *       data/pdf_years.csv lists as reviewed or closed. Built with the MCP's own loader and its
 *       existing flags (build-index.mjs --include-reviewed --out .cache/budget-public.db), never
 *       into mcp/data/budget.db, so the MCP's own gate is untouched here. Every row the app shows
 *       says "checked, review in progress" (reviewed) or "checked and reviewed" (closed). The
 *       review screen is off: the manifest says review_screen: false.
 *   node scripts/build-data.mjs --include-reviewed
 *       the local REVIEW build: the same rows, into .cache/budget-reviewed.db, plus the review
 *       screen (the Review tab; review_screen: true). Never deployed.
 *   node scripts/build-data.mjs --closed-only
 *       closed families only, exported from mcp/data/budget.db: what the public build was before
 *       #213. Kept so the old gate is one flag away.
 *   --skip-index                             export the chosen index as it is, without rebuilding
 *
 * Old-parser output (data/fyNN/schedule_c/ and the like, data/retired/) is never loaded: the
 * loader reads only the data/fyNN/pdf/ families that data/pdf_years.csv lists.
 *
 * The pdf_* tables (mcp/scripts/pdf-families.mjs PDF_TABLES) are always exported, empty when no
 * family is loaded, so the app and the parity test never branch on which tables exist. The one
 * exception: a public build withholds pdf_review_suggestions (manifest `withheld`), which only the
 * review screen reads.
 *
 * Needs `npm ci` in mcp/ first (the index build uses the MCP's dependencies and dist/fold.js).
 */
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Database from "better-sqlite3";
import { DuckDBInstance } from "@duckdb/node-api";

import { capitalGaps } from "./lib/capital-gaps.mjs";
import { CAPITAL_REPORT_YEARS } from "../../../mcp/scripts/verify-index.mjs";
import { PDF_FAMILIES, PDF_TABLES, SUGGESTIONS } from "../../../mcp/scripts/pdf-families.mjs";
import { OPEN_DATA_TABLES } from "../../../mcp/scripts/open-data.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..");
const REPO = resolve(APP, "..", "..");
const MCP = join(REPO, "mcp");
const REVIEW_SCREEN = process.argv.includes("--include-reviewed");
const CLOSED_ONLY = process.argv.includes("--closed-only");
if (REVIEW_SCREEN && CLOSED_ONLY) throw new Error("build-data: --include-reviewed and --closed-only do not go together");
/** public: reviewed + closed, no review screen; review: the same plus the review screen; closed: closed only. */
const BUILD = REVIEW_SCREEN ? "review" : CLOSED_ONLY ? "closed" : "public";
const DB_PATH = {
  review: join(APP, ".cache", "budget-reviewed.db"),
  public: join(APP, ".cache", "budget-public.db"),
  closed: join(MCP, "data", "budget.db"),
}[BUILD];
const OUT_DIR = join(APP, "public", "data");

/**
 * Tables the public build does not ship: the reviewers' suggested decisions are for the review
 * screen only, so a public build writes no Parquet file for them and the manifest lists them as
 * withheld (#224 review). A decision a person recorded is in pdf_review and is shown.
 */
const WITHHELD = BUILD === "public" ? [SUGGESTIONS.table] : [];

/** The tables the explorer reads, in the order they are written. */
const ALL_TABLES = ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta",
  ...PDF_TABLES, ...OPEN_DATA_TABLES];
const TABLES = ALL_TABLES.filter((t) => !WITHHELD.includes(t));

const DUCK_TYPE = { INTEGER: "BIGINT", REAL: "DOUBLE", TEXT: "VARCHAR" };

function log(event, detail = {}) {
  console.error(JSON.stringify({ script: "build-data", event, ...detail, ts: new Date().toISOString() }));
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function sourceCommit() {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO, encoding: "utf8" }).trim();
  } catch {
    throw new Error("build-data: cannot resolve the source commit (no GITHUB_SHA and `git rev-parse HEAD` failed)");
  }
}

function buildIndex() {
  if (!existsSync(join(MCP, "node_modules"))) {
    throw new Error("build-data: mcp/node_modules is missing. Run `npm ci` in mcp/ first.");
  }
  for (const f of ["fold.js", "rowlinks.js"]) {
    if (!existsSync(join(MCP, "dist", f))) throw new Error(`build-data: mcp/dist/${f} is missing. Run \`npm run build\` in mcp/ first.`);
  }
  log("index_start", { build: BUILD, out: DB_PATH });
  mkdirSync(dirname(DB_PATH), { recursive: true });
  const args = BUILD === "closed" ? [] : ["--include-reviewed", "--out", DB_PATH];
  execFileSync(process.execPath, [join(MCP, "scripts", "build-index.mjs"), ...args], { cwd: MCP, stdio: "inherit" });
}

/** Append one SQLite value under its declared column type. */
function append(appender, type, value, where) {
  if (value === null || value === undefined) return appender.appendNull();
  if (type === "INTEGER") {
    if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new Error(`${where}: ${JSON.stringify(value)} is not an integer`);
    return appender.appendBigInt(BigInt(value));
  }
  if (type === "REAL") {
    if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${where}: ${JSON.stringify(value)} is not a number`);
    return appender.appendDouble(value);
  }
  if (typeof value !== "string") throw new Error(`${where}: ${JSON.stringify(value)} is not text`);
  return appender.appendVarchar(value);
}

async function exportTables(sqlite, conn) {
  const files = {};
  for (const table of TABLES) {
    const cols = sqlite.prepare(`PRAGMA table_info(${table})`).all();
    if (cols.length === 0) throw new Error(`budget.db has no table ${table}`);
    for (const c of cols) {
      if (!(c.type in DUCK_TYPE)) throw new Error(`${table}.${c.name}: unmapped SQLite type ${c.type}`);
    }
    await conn.run(`CREATE TABLE "${table}" (${cols.map((c) => `"${c.name}" ${DUCK_TYPE[c.type]}`).join(", ")})`);
    const appender = await conn.createAppender(table);
    let n = 0;
    // rowid order: the order build-index.mjs inserted, i.e. the CSVs' order.
    for (const row of sqlite.prepare(`SELECT * FROM ${table} ORDER BY rowid`).iterate()) {
      for (const c of cols) append(appender, c.type, row[c.name], `${table} rowid ${n + 1} ${c.name}`);
      appender.endRow();
      n++;
    }
    appender.closeSync();
    const out = join(OUT_DIR, `${table}.parquet`);
    const tmp = `${out}.tmp-${process.pid}`;
    await conn.run(`COPY "${table}" TO '${tmp.replace(/'/g, "''")}' (FORMAT parquet, COMPRESSION zstd)`);
    renameSync(tmp, out);
    files[`${table}.parquet`] = { rows: n, bytes: statSync(out).size, sha256: sha256(out) };
    log("exported", { table, rows: n });
  }
  return files;
}

async function main() {
  if (!process.argv.includes("--skip-index")) buildIndex();
  if (!existsSync(DB_PATH)) throw new Error(`build-data: ${DB_PATH} not found. Run without --skip-index.`);
  mkdirSync(OUT_DIR, { recursive: true });
  // A withheld table's file from an earlier review build would still be served: remove it.
  for (const t of WITHHELD) rmSync(join(OUT_DIR, `${t}.parquet`), { force: true });
  // Delete-then-write would leave a stale table behind if one were dropped; every table in TABLES
  // is rewritten below, and the manifest lists exactly those.

  const sqlite = new Database(DB_PATH, { readonly: true, fileMustExist: true });
  const meta = Object.fromEntries(sqlite.prepare("SELECT key, value FROM meta").all().map((r) => [r.key, r.value]));
  const instance = await DuckDBInstance.create(":memory:");
  const conn = await instance.connect();
  let files;
  try {
    files = await exportTables(sqlite, conn);
  } finally {
    conn.closeSync();
    instance.closeSync();
    sqlite.close();
  }

  const manifest = {
    generated_at: new Date().toISOString(),
    source_repo: "BetaNYC/New-York-City-Budget",
    source_commit: sourceCommit(),
    index_built_at: meta.built_at,
    index_counts: JSON.parse(meta.counts),
    // Which index was exported (repo-relative), and whether it holds reviewed PDF rows.
    index: DB_PATH.slice(REPO.length + 1),
    include_reviewed: meta.include_reviewed === "yes",
    // public | review | closed (above). The review screen is only in a review build.
    build: BUILD,
    review_screen: BUILD === "review",
    withheld: WITHHELD,
    pdf_families: Object.fromEntries(Object.entries(PDF_FAMILIES).map(([k, f]) => [k, { label: f.label, main: f.main, tables: f.tables.map((t) => t.table), decisions: f.decisions ?? {} }])),
    capital: capitalGaps(readFileSync(join(REPO, "data", "capital", "README.md"), "utf8"), CAPITAL_REPORT_YEARS),
    files,
  };
  writeFileSync(join(OUT_DIR, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  log("built", { out: OUT_DIR, commit: manifest.source_commit, files: Object.keys(files).length });
}

main().catch((err) => {
  log("failed", { error: String(err?.message ?? err) });
  process.exitCode = 1;
});
