#!/usr/bin/env node
/**
 * assemble-site.mjs — lay out the GitHub Pages site in viz/explorer/site/:
 *
 *   site/                 everything in viz/ except viz/explorer/ — the retirement notice
 *                         (index.html), the frozen legacy.html and its assets, exactly as the old
 *                         `git subtree split --prefix viz` deploy published them
 *   site/explorer/        the built explorer (viz/explorer/dist/, including dist/data/*.parquet)
 *
 * Run after `npm run data` and `npm run build`. A missing build or data file is a stop: a site
 * without its data would load and then fail in every visitor's browser. The output directory
 * must not exist or be empty: this script never deletes anything, so a stale file can never be
 * published by accident. It is gitignored; remove it yourself, or pass --out.
 *
 *   node scripts/assemble-site.mjs [--out <dir>]
 */
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..");
const VIZ = resolve(APP, "..");
const DIST = join(APP, "dist");

const outArg = process.argv.indexOf("--out");
const OUT = outArg > 0 ? resolve(process.argv[outArg + 1]) : join(APP, "site");

function log(event, detail = {}) {
  console.error(JSON.stringify({ script: "assemble-site", event, ...detail, ts: new Date().toISOString() }));
}

function main() {
  if (!existsSync(join(DIST, "index.html"))) throw new Error("assemble-site: viz/explorer/dist/index.html is missing. Run `npm run build` first.");
  const manifestPath = join(DIST, "data", "manifest.json");
  if (!existsSync(manifestPath)) throw new Error("assemble-site: dist/data/manifest.json is missing. Run `npm run data` before `npm run build`.");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  for (const name of Object.keys(manifest.files)) {
    if (!existsSync(join(DIST, "data", name))) throw new Error(`assemble-site: dist/data/${name} is missing`);
  }
  for (const f of ["index.html", "legacy.html"]) {
    if (!existsSync(join(VIZ, f))) throw new Error(`assemble-site: viz/${f} is missing`);
  }

  if (existsSync(OUT) && readdirSync(OUT).length > 0) {
    throw new Error(`assemble-site: ${OUT} is not empty. Remove it, or pass --out <new dir>.`);
  }
  mkdirSync(OUT, { recursive: true });

  for (const entry of readdirSync(VIZ)) {
    if (entry === "explorer") continue;
    cpSync(join(VIZ, entry), join(OUT, entry), { recursive: true });
  }
  cpSync(DIST, join(OUT, "explorer"), { recursive: true });
  log("assembled", { out: OUT, commit: manifest.source_commit });
}

try {
  main();
} catch (err) {
  log("failed", { error: String(err?.message ?? err) });
  process.exitCode = 1;
}
