#!/usr/bin/env node
/**
 * verify-pdf-release.mjs — check a PDF-tables release folder (build-pdf-release.mjs's output)
 * before W7 (#216, .github/workflows/pdf-tables-release.yml) publishes it. Never talks to GitHub.
 *
 *   node scripts/verify-pdf-release.mjs --dir <dir> --commit <40-digit sha> [--allow-local-commit]
 *
 * Fails (exit 1, every problem listed) unless:
 *   - the manifest parses as the downloader reads it (src/pdfdata.ts parseManifest: format, plain
 *     file names, sha256 and sizes, exactly one pdf_tables file);
 *   - every file it lists is in <dir>, with exactly that size and sha256, and the tables' gunzipped
 *     bytes match `unpacked`;
 *   - the tables were built from --commit: source_commit equals it, in the manifest and in the
 *     tables' meta, with source_commit_check "pdfs_match" (every cited PDF has these bytes there,
 *     the commit is on origin/main, data/ and source/ were clean) and source_commit_scope
 *     "origin/main", never "local";
 *   - data/ and source/ have no uncommitted change now, and HEAD is --commit.
 * --allow-local-commit (tests only) accepts scope "local" and skips the commit and clean-tree
 * checks, for a release built with build-pdf-release.mjs --allow-local-commit. W7 never passes it.
 *
 * On success, writes <dir>/release-assets.txt: the files to upload, one per line, the manifest
 * last, so the workflow uploads exactly what was checked.
 */
import Database from "better-sqlite3";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createReadStream, existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pipeline } from "node:stream/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createGunzip } from "node:zlib";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");

/** As build-pdf-release.mjs writes them (it runs on import, so they are not imported from it). */
const DB_ASSET = "pdf-tables.db.gz";

/** The file `release-assets.txt` the workflow uploads from. */
export const ASSET_LIST = "release-assets.txt";

/** The release tag for a build: pdf-tables-YYYY-MM-DD-<7-digit sha>, the date in UTC. */
export function releaseTag(date, commit) {
  if (!/^[0-9a-f]{40}$/.test(commit)) throw new Error(`releaseTag: not a full commit id: ${JSON.stringify(commit)}`);
  return `pdf-tables-${date.toISOString().slice(0, 10)}-${commit.slice(0, 7)}`;
}

/** The release's description, from its manifest: what it is, how to install it, its family-years. */
export function releaseNotes(dir, out) {
  const m = JSON.parse(readFileSync(join(dir, "pdf-tables.manifest.json"), "utf8"));
  const years = m.families.map((f) => `- FY${f.fiscal_year} ${f.family}: ${f.status}, ${f.rows} rows`);
  const text = [
    `The checked tables read from the Council's budget PDFs, built ${m.built_at} from commit ${m.source_commit}.`,
    "",
    "Install them with `npx @betanyc/nyc-budget-mcp download --pdf-tables` (add `--pdfs` for the PDF files too).",
    'Every file is checked against the sha256 values in `pdf-tables.manifest.json`. Format: mcp/README.md, "The release format".',
    "Values are as printed in the PDFs; each row says whether its review is complete.",
    "",
    "Published by .github/workflows/pdf-tables-release.yml (#216).",
    "",
    ...years,
    "",
  ].join("\n");
  writeFileSync(out, text);
  return text;
}

const sha256Of = async (stream) => {
  const h = createHash("sha256");
  let bytes = 0;
  await pipeline(stream, async function* (src) {
    for await (const c of src) {
      bytes += c.length;
      h.update(c);
    }
  });
  return { sha256: h.digest("hex"), bytes };
};

/** Every problem with the release in `dir` (empty: publishable). */
export async function verifyRelease(dir, { commit, allowLocal = false, repo = REPO } = {}) {
  const problems = [];
  const { MANIFEST_NAME: MANIFEST } = await import(pathToFileURL(join(MCP, "dist", "pdfdata.js")).href);
  const path = join(dir, MANIFEST);
  if (!existsSync(path)) return [`${MANIFEST} is missing from ${dir}`];
  // The downloader's own format and check of the manifest's shape (dist/, from `npm run build`).
  const { parseManifest, PDF_TABLES_FORMAT: FORMAT } = await import(pathToFileURL(join(MCP, "dist", "pdfdata.js")).href);
  let m;
  try {
    m = parseManifest(readFileSync(path, "utf8"));
  } catch (err) {
    return [`the downloader would refuse the manifest: ${err.message}`];
  }
  if (m.format !== FORMAT) problems.push(`format ${m.format}, expected ${FORMAT}`);

  for (const f of m.files) {
    const p = join(dir, f.name);
    if (!existsSync(p)) {
      problems.push(`${f.name}: listed in the manifest, missing from the folder`);
      continue;
    }
    const got = await sha256Of(createReadStream(p));
    if (got.bytes !== f.bytes || got.sha256 !== f.sha256) problems.push(`${f.name}: ${got.bytes} bytes, sha256 ${got.sha256}; the manifest says ${f.bytes}, ${f.sha256}`);
    if (f.unpacked) {
      const un = await sha256Of(createReadStream(p).pipe(createGunzip()));
      if (un.bytes !== f.unpacked.bytes || un.sha256 !== f.unpacked.sha256) problems.push(`${f.name}: unpacked ${un.bytes} bytes, sha256 ${un.sha256}; the manifest says ${f.unpacked.bytes}, ${f.unpacked.sha256}`);
    }
  }
  const tables = m.files.find((f) => f.kind === "pdf_tables");
  if (tables?.name !== DB_ASSET) problems.push(`the tables file is ${tables?.name}, expected ${DB_ASSET}`);

  // The commit, as the manifest and the tables themselves record it.
  const unpackedDb = join(dir, "pdf-tables.db");
  let meta = {};
  if (existsSync(unpackedDb)) {
    const db = new Database(unpackedDb, { readonly: true });
    meta = Object.fromEntries(db.prepare("SELECT key, value FROM meta").all().map((r) => [r.key, r.value]));
    db.close();
    if (meta.source_commit !== m.source_commit) problems.push(`the tables say source_commit ${JSON.stringify(meta.source_commit)}, the manifest ${JSON.stringify(m.source_commit)}`);
    if (meta.pdf_tables_format !== FORMAT) problems.push(`the tables' pdf_tables_format is ${JSON.stringify(meta.pdf_tables_format)}`);
  } else {
    problems.push("pdf-tables.db (the unpacked tables build-pdf-release.mjs leaves) is missing, so its meta cannot be checked");
  }
  if (m.source_commit_check !== "pdfs_match") problems.push(`source_commit_check is ${JSON.stringify(m.source_commit_check)}, not "pdfs_match": the rows' GitHub links would not be built`);
  if (allowLocal) {
    if (!["local", "origin/main"].includes(m.source_commit_scope)) problems.push(`source_commit_scope is ${JSON.stringify(m.source_commit_scope)}`);
  } else {
    if (m.source_commit_scope !== "origin/main") problems.push(`source_commit_scope is ${JSON.stringify(m.source_commit_scope)}, not "origin/main": a local build is never published`);
    const git = (...a) => execFileSync("git", ["-C", repo, ...a], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
    const dirty = git("status", "--porcelain", "--", "data", "source");
    if (dirty) problems.push(`data/ or source/ has uncommitted changes:\n${dirty}`);
    if (!/^[0-9a-f]{40}$/.test(commit ?? "")) problems.push(`--commit must be the full 40-digit commit pushed to main; got ${JSON.stringify(commit)}`);
    else {
      if (m.source_commit !== commit) problems.push(`built from ${JSON.stringify(m.source_commit)}, not the pushed commit ${commit}`);
      const head = git("rev-parse", "HEAD");
      if (head !== commit) problems.push(`the checkout is at ${head}, not ${commit}`);
      try {
        git("merge-base", "--is-ancestor", commit, "origin/main");
      } catch {
        problems.push(`${commit} is not on origin/main`);
      }
    }
  }
  if (!problems.length) {
    const assets = [...m.files.map((f) => f.name), MANIFEST];
    writeFileSync(join(dir, ASSET_LIST), assets.join("\n") + "\n");
  }
  return problems;
}

async function main() {
  const args = process.argv.slice(2);
  const val = (k) => {
    const i = args.indexOf(k);
    return i >= 0 ? args[i + 1] : undefined;
  };
  const dir = val("--dir");
  if (!dir) {
    console.error("usage: node scripts/verify-pdf-release.mjs --dir <dir> --commit <sha> [--allow-local-commit]");
    process.exit(2);
  }
  const problems = await verifyRelease(resolve(dir), { commit: val("--commit"), allowLocal: args.includes("--allow-local-commit") });
  if (problems.length) {
    console.error(`verify-pdf-release: ${problems.length} problem(s); do not publish:\n- ${problems.join("\n- ")}`);
    process.exit(1);
  }
  const m = JSON.parse(readFileSync(join(resolve(dir), "pdf-tables.manifest.json"), "utf8"));
  console.log(`verify-pdf-release: OK. ${m.files.length} file(s) plus the manifest, built ${m.built_at} from ${m.source_commit} (${m.source_commit_scope}).`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) await main();
