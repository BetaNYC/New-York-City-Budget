/**
 * agency-json.mjs — the City agency budgets view's data, as small JSON files (#299).
 *
 * build-data.mjs calls writeAgencyJson after it exports the Parquet: it reads the index's
 * agency_budget table (mcp/scripts/agency-budget.mjs: one loader, one year rule), lays it out
 * with src/agency/data.js, writes public/data/agency_budget/, and then checks every file against
 * the table with plain SQL (verifyAgencyJson). Any difference stops the build: the JSON and the
 * table can never disagree on a published site.
 *
 * No figure is computed here beyond sums of the table's own cells; NULL stays null.
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";

import { AGENCY_JSON_DIR, agencyJsonFiles, agencyPath, agenciesPath, citywidePath } from "../src/agency/data.js";

const COLS = "fiscal_year, agency_number, agency_name, unit_number, unit_name, adopted, modified, adopted_release, modified_release";

/** The agency_budget rows from an open better-sqlite3 database, in a fixed order. */
export const tableRows = (sqlite) => sqlite.prepare(`SELECT ${COLS} FROM agency_budget ORDER BY fiscal_year, agency_number, unit_number`).all();

/**
 * Write every file under <outDir>/agency_budget/, replacing what was there (an agency dropped from
 * the data leaves no stale file). Returns { files, bytes, sha256 } for the manifest.
 */
export function writeAgencyJson(sqlite, outDir, stamp) {
  const files = agencyJsonFiles(tableRows(sqlite), stamp);
  const dir = join(outDir, AGENCY_JSON_DIR);
  const tmp = `${dir}.tmp-${process.pid}`;
  rmSync(tmp, { recursive: true, force: true });
  let bytes = 0;
  const hash = createHash("sha256");
  for (const [path, obj] of Object.entries(files).sort(([a], [b]) => (a < b ? -1 : 1))) {
    const out = join(tmp, path.slice(AGENCY_JSON_DIR.length + 1));
    mkdirSync(join(out, ".."), { recursive: true });
    const text = JSON.stringify(obj);
    writeFileSync(out, text);
    bytes += Buffer.byteLength(text);
    hash.update(path).update(text);
  }
  const old = `${dir}.old-${process.pid}`;
  if (existsSync(dir)) renameSync(dir, old);
  renameSync(tmp, dir);
  rmSync(old, { recursive: true, force: true });
  return { files: Object.keys(files).length, bytes, sha256: hash.digest("hex") };
}

const read = (dir, path) => JSON.parse(readFileSync(join(dir, path), "utf8"));
const cents = (v) => (v === null || v === undefined ? null : Math.round(Number(v) * 100));

/**
 * Check the written files against the table, with SQL that does not share code with
 * src/agency/data.js: citywide and per-agency totals by year, and every unit's cells. Returns the
 * list of differences (empty when they agree) and how many cells were compared.
 */
export function verifyAgencyJson(sqlite, outDir) {
  const diffs = [];
  let cells = 0;
  const same = (where, got, want, money = false) => {
    cells++;
    const g = money ? cents(got) : got ?? null;
    const w = money ? cents(want) : want ?? null;
    if (g !== w) diffs.push(`${where}: JSON ${JSON.stringify(got)}, table ${JSON.stringify(want)}`);
  };
  const totalsSql = (where) => `SELECT fiscal_year, SUM(adopted) AS adopted, SUM(modified) AS modified, COUNT(*) AS units,
      SUM(adopted IS NULL) AS units_no_adopted, SUM(modified IS NULL) AS units_no_modified
    FROM agency_budget ${where} GROUP BY fiscal_year ORDER BY fiscal_year`;
  const checkTotals = (label, got, want) => {
    same(`${label} years`, got.map((y) => y.fiscal_year).join(","), want.map((y) => y.fiscal_year).join(","));
    want.forEach((w, i) => {
      const g = got[i] ?? {};
      same(`${label} FY${w.fiscal_year} adopted`, g.adopted, w.adopted, true);
      same(`${label} FY${w.fiscal_year} modified`, g.modified, w.modified, true);
      for (const k of ["units", "units_no_adopted", "units_no_modified"]) same(`${label} FY${w.fiscal_year} ${k}`, g[k], w[k]);
    });
  };

  const city = read(outDir, citywidePath());
  checkTotals("citywide", city.years, sqlite.prepare(totalsSql("")).all());

  const agencies = read(outDir, agenciesPath()).agencies;
  const codes = sqlite.prepare("SELECT DISTINCT agency_number FROM agency_budget ORDER BY agency_number").all().map((r) => r.agency_number);
  same("agency list", agencies.map((a) => a.agency_number).join(","), codes.join(","));
  const onDisk = existsSync(join(outDir, AGENCY_JSON_DIR, "agency")) ? readdirSync(join(outDir, AGENCY_JSON_DIR, "agency")).sort() : [];
  same("agency files", onDisk.join(","), codes.map((c) => `${c}.json`).join(","));

  const totalsStmt = sqlite.prepare(totalsSql("WHERE agency_number = ?"));
  const namesStmt = sqlite.prepare("SELECT DISTINCT agency_name FROM agency_budget WHERE agency_number = ? ORDER BY agency_name");
  const unitStmt = sqlite.prepare(`SELECT ${COLS} FROM agency_budget WHERE agency_number = ? ORDER BY unit_number, fiscal_year`);
  for (const a of agencies) {
    const want = totalsStmt.all(a.agency_number);
    checkTotals(`agencies.json ${a.agency_number}`, a.years, want);
    same(`agencies.json ${a.agency_number} names`, JSON.stringify(a.names), JSON.stringify(namesStmt.all(a.agency_number).map((r) => r.agency_name)));
    const file = read(outDir, agencyPath(a.agency_number));
    checkTotals(`agency ${a.agency_number}`, file.years, want);
    const flat = file.units.flatMap((u) => u.years.map((y) => ({ unit_number: u.unit_number, ...y })));
    const rows = unitStmt.all(a.agency_number);
    same(`agency ${a.agency_number} unit rows`, flat.length, rows.length);
    rows.forEach((w, i) => {
      const g = flat[i] ?? {};
      const at = `agency ${a.agency_number} unit ${w.unit_number} FY${w.fiscal_year}`;
      for (const k of ["fiscal_year", "unit_number", "agency_name", "unit_name", "adopted_release", "modified_release"]) same(`${at} ${k}`, g[k], w[k]);
      same(`${at} adopted`, g.adopted, w.adopted, true);
      same(`${at} modified`, g.modified, w.modified, true);
    });
  }
  return { diffs, cells };
}
