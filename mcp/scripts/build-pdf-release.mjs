#!/usr/bin/env node
/**
 * build-pdf-release.mjs — build the optional PDF-tables download (GitHub #215) in a local folder:
 * the files a GitHub Release of this repo carries for `nyc-budget-mcp download`. Publishing them
 * is W7's job (#216); this script only builds and checks them, and never talks to GitHub.
 *
 *   node scripts/build-pdf-release.mjs --out <dir> [--pdfs] [--keep-full]
 *
 * Steps:
 *   1. build-index.mjs --include-reviewed --out <dir>/full.db: every family-year data/pdf_years.csv
 *      lists as reviewed or closed (the old parser's CSVs are never inputs), plus the spreadsheet
 *      tables the Schedule C alignment is derived from;
 *   2. copy the pdf_* tables and the build's meta into <dir>/pdf-tables.db, VACUUMed;
 *   3. gzip it to <dir>/pdf-tables.db.gz;
 *   4. with --pdfs, copy every PDF the rows cite to <dir>/<sha256>.pdf (one flat name per file,
 *      as a release asset must be);
 *   5. write <dir>/pdf-tables.manifest.json (the format is in mcp/README.md, "The PDF tables
 *      download"), which lists every asset with its size and sha256.
 *
 * full.db is deleted at the end unless --keep-full is given (the tests reuse it).
 */
import Database from "better-sqlite3";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { copyFileSync, createReadStream, createWriteStream, mkdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { pipeline } from "node:stream/promises";
import { createGzip } from "node:zlib";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { PDF_TABLES } from "./pdf-families.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");

/** The download's format; src/pdfdata.ts refuses any other. */
export const FORMAT = "nyc-budget-pdf-tables/1";
export const MANIFEST = "pdf-tables.manifest.json";
export const DB_ASSET = "pdf-tables.db.gz";

const ARGS = process.argv.slice(2);
const at = ARGS.indexOf("--out");
if (at < 0 || !ARGS[at + 1]) {
  console.error("usage: node scripts/build-pdf-release.mjs --out <dir> [--pdfs] [--keep-full]");
  process.exit(2);
}
const OUT = resolve(ARGS[at + 1]);
const WITH_PDFS = ARGS.includes("--pdfs");
const KEEP_FULL = ARGS.includes("--keep-full");

const sha256File = async (p) => {
  const h = createHash("sha256");
  await pipeline(createReadStream(p), h);
  return h.digest("hex");
};

function log(event, detail = {}) {
  console.error(JSON.stringify({ script: "build-pdf-release", event, ...detail, ts: new Date().toISOString() }));
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const full = join(OUT, "full.db");
  const tables = join(OUT, "pdf-tables.db");
  for (const f of [tables, `${tables}-wal`, `${tables}-shm`]) rmSync(f, { force: true });

  execFileSync(process.execPath, [join(HERE, "build-index.mjs"), "--include-reviewed", "--out", full], { cwd: MCP, stdio: "inherit" });

  // Only the pdf_* tables and the meta: no spreadsheet table is shipped twice.
  const src = new Database(full, { readonly: true });
  const meta = Object.fromEntries(src.prepare("SELECT key, value FROM meta").all().map((r) => [r.key, r.value]));
  const ddl = PDF_TABLES.map((t) => src.prepare("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?").get(t)?.sql);
  src.close();
  if (ddl.some((d) => !d)) throw new Error("build-pdf-release: a pdf_* table is missing from the full build");

  const db = new Database(tables);
  db.exec(ddl.join(";\n") + ";");
  db.exec("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)");
  db.prepare("ATTACH DATABASE ? AS full").run(full);
  db.transaction(() => {
    for (const t of PDF_TABLES) db.exec(`INSERT INTO main.${t} SELECT * FROM full.${t}`);
  })();
  db.exec("DETACH DATABASE full");
  const families = db.prepare("SELECT fiscal_year, family, status, rows FROM pdf_years ORDER BY fiscal_year, family").all();
  const set = db.prepare("INSERT INTO meta (key, value) VALUES (?, ?)");
  set.run("pdf_tables_format", FORMAT);
  for (const k of ["built_at", "source_commit", "source_commit_check", "pdf_gate", "inputs", "counts"]) set.run(k, meta[k] ?? "");
  // The lookups the tools (src/pdfquery.ts) and the explorer's queries make by year and key.
  db.exec("CREATE INDEX idx_pdf_sc_year ON pdf_schedule_c(fiscal_year, award_id)");
  db.exec("CREATE INDEX idx_pdf_sc_sub ON pdf_schedule_c_subawards(fiscal_year, parent_award_id)");
  db.exec("CREATE INDEX idx_pdf_sc_disc ON pdf_sc_disclosure(fiscal_year, award_id)");
  db.exec("CREATE INDEX idx_pdf_tr_year ON pdf_transparency(fiscal_year)");
  db.exec("CREATE INDEX idx_pdf_review ON pdf_review(fiscal_year, family, review_id)");
  db.exec("VACUUM");
  // The PDFs the rows cite, with the sha256 each row carries (checked against the bytes by the build).
  const pdfs = db
    .prepare(PDF_TABLES.filter((t) => !["pdf_years", "pdf_review", "pdf_review_suggestions", "pdf_sc_disclosure"].includes(t))
      .map((t) => `SELECT source_pdf, pdf_sha256 FROM ${t}`).join(" UNION ") + " ORDER BY source_pdf")
    .all();
  db.close();

  const gz = join(OUT, DB_ASSET);
  await pipeline(createReadStream(tables), createGzip({ level: 9 }), createWriteStream(gz));

  const files = [
    {
      name: DB_ASSET,
      kind: "pdf_tables",
      bytes: statSync(gz).size,
      sha256: await sha256File(gz),
      unpacked: { name: "pdf-tables.db", bytes: statSync(tables).size, sha256: await sha256File(tables) },
    },
  ];
  if (WITH_PDFS) {
    for (const p of pdfs) {
      const from = join(REPO, p.source_pdf);
      const sha = await sha256File(from);
      if (sha !== p.pdf_sha256) throw new Error(`${p.source_pdf}: sha256 ${sha}, the rows say ${p.pdf_sha256}`);
      const name = `${sha}.pdf`;
      copyFileSync(from, join(OUT, name));
      files.push({ name, kind: "pdf", path: p.source_pdf, bytes: statSync(from).size, sha256: sha });
    }
  }
  const manifest = {
    format: FORMAT,
    built_at: meta.built_at,
    source_commit: meta.source_commit,
    source_commit_check: meta.source_commit_check,
    families,
    pdfs_included: WITH_PDFS,
    files,
  };
  writeFileSync(join(OUT, MANIFEST), JSON.stringify(manifest, null, 2) + "\n");
  if (!KEEP_FULL) for (const f of [full, `${full}-wal`, `${full}-shm`]) rmSync(f, { force: true });
  log("built", { out: OUT, families: families.length, pdfs: files.length - 1, db_bytes: files[0].unpacked.bytes, gz_bytes: files[0].bytes, source_commit: meta.source_commit });
}

await main();
