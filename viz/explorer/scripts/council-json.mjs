/**
 * council-json.mjs — the Council explorer's fast views, as small JSON files (#301, third PR; plan
 * step 3 in https://github.com/BetaNYC/New-York-City-Budget/issues/301#issuecomment-6872266067).
 *
 * build-data.mjs calls writeCouncilJson after it exports the Parquet, and then verifyCouncilJson.
 * Any difference stops the build: the JSON and the tables can never disagree on a published site.
 *
 *   council/years.json             the lookups every view needs (disclosure years, capital and
 *                                  OMB years, PDF family-years), the source of each disclosure
 *                                  year and capital report year, and the Years view's totals
 *   council/omb.json               every Council-vs-OMB row (capital_vs_omb)
 *   council/awards/index.json      the expense list over all years with no filter: totals by
 *                                  year and status, flagged rows, and the first page
 *   council/awards/fyYYYY.json     every disclosure row of one loaded fiscal year, every column
 *   council/capital/fyYYYY.json    every Council capital row of one report year, every column
 *
 * Rows are stored as { columns, rows, dicts } (one array per row), in the index's own order
 * (rowid), with the index's values as they are: NULL stays null. A column that repeats a few
 * values (status, funding source, city) is stored once in `dicts[column]`, and its cells hold the
 * value's position there (src/council/paths.js decodeRows reads it back). The summaries in years.json and index.json are
 * the explorer's own queries (src/query/sql.js), run here by DuckDB on the tables just exported.
 *
 * verifyCouncilJson reads every file back and checks it against budget.db with better-sqlite3 and
 * SQL written here, sharing no code with the writer or with the app's JSON reader: every cell of
 * every row file, and every total.
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import * as Q from "../src/query/sql.js";
import { pdfYearsQuery } from "../src/query/pdf.js";
import { COUNCIL_JSON_DIR, awardsIndexPath, awardsYearPath, capitalYearPath, councilYearsPath, ombPath } from "../src/council/paths.js";

/** Plain JS rows from DuckDB, BIGINT as Number (every value here is a safe integer). */
async function duck(conn, { sql, params = [] }) {
  const reader = await conn.runAndReadAll(sql, params);
  return reader.getRowObjectsJS().map((r) =>
    Object.fromEntries(
      Object.entries(r).map(([k, v]) => {
        if (typeof v !== "bigint") return [k, v];
        if (v > BigInt(Number.MAX_SAFE_INTEGER) || v < BigInt(Number.MIN_SAFE_INTEGER)) throw new Error(`council-json: ${k} ${v} is not a safe integer`);
        return [k, Number(v)];
      })
    )
  );
}

/**
 * A table's rows as { columns, rows, dicts }, in the index's order. A column whose distinct values
 * are fewer than a quarter of its rows is dictionary-encoded.
 */
function columnar(sqlite, table, where = "", params = []) {
  const columns = sqlite.prepare(`PRAGMA table_info(${table})`).all().map((c) => c.name);
  const rows = sqlite.prepare(`SELECT ${columns.map((c) => `"${c}"`).join(", ")} FROM ${table} ${where} ORDER BY rowid`).raw().all(...params);
  const dicts = {};
  columns.forEach((c, j) => {
    const values = [...new Set(rows.map((r) => r[j]))];
    if (rows.length < 8 || values.length * 4 > rows.length) return;
    const at = new Map(values.map((v, i) => [v, i]));
    for (const r of rows) r[j] = at.get(r[j]);
    dicts[c] = values;
  });
  return { columns, rows, dicts };
}

/** Every file: { path: object }. */
export async function councilJsonFiles(sqlite, conn, stamp = {}) {
  const head = { schema: 1, generated_at: stamp.generated_at ?? null };
  const files = {};
  const all = (table) => columnar(sqlite, table);
  const disclosureYears = sqlite.prepare("SELECT * FROM disclosure_years ORDER BY fiscal_year").all();
  const capitalSources = sqlite.prepare("SELECT * FROM capital_sources ORDER BY report_year").all();
  files[councilYearsPath()] = {
    ...head,
    disclosure_years: disclosureYears,
    capital_sources: capitalSources,
    omb_years: sqlite.prepare("SELECT DISTINCT report_year FROM capital_vs_omb ORDER BY report_year").all().map((r) => r.report_year),
    pdf_years: await duck(conn, pdfYearsQuery()),
    year_disclosure: await duck(conn, Q.YEAR_DISCLOSURE_QUERY),
    year_capital: await duck(conn, Q.YEAR_CAPITAL_QUERY),
  };
  files[ombPath()] = { ...head, ...all("capital_vs_omb") };
  files[awardsIndexPath()] = {
    ...head,
    totals: await duck(conn, Q.disclosureTotalsQuery({})),
    flags: await duck(conn, Q.disclosureFlagsQuery({})),
    rows: await duck(conn, Q.disclosureRowsQuery({}, 0)),
  };
  for (const y of disclosureYears.filter((y) => y.loaded)) {
    files[awardsYearPath(y.fiscal_year)] = { ...head, fiscal_year: y.fiscal_year, ...columnar(sqlite, "disclosure", "WHERE fiscal_year = ?", [y.fiscal_year]) };
  }
  for (const s of capitalSources) {
    files[capitalYearPath(s.report_year)] = { ...head, report_year: s.report_year, ...columnar(sqlite, "capital_council", "WHERE report_year = ?", [s.report_year]) };
  }
  return files;
}

/**
 * Write every file under <outDir>/council/, replacing what was there (a year dropped from the data
 * leaves no stale file). Returns { files: { path: { bytes, sha256 } }, bytes, sha256 } for the
 * manifest: the app fetches each file with its sha256 as the cache key.
 */
export async function writeCouncilJson(sqlite, conn, outDir, stamp) {
  const files = await councilJsonFiles(sqlite, conn, stamp);
  const dir = join(outDir, COUNCIL_JSON_DIR);
  const tmp = `${dir}.tmp-${process.pid}`;
  rmSync(tmp, { recursive: true, force: true });
  const list = {};
  let bytes = 0;
  const hash = createHash("sha256");
  for (const [path, obj] of Object.entries(files).sort(([a], [b]) => (a < b ? -1 : 1))) {
    const out = join(tmp, path.slice(COUNCIL_JSON_DIR.length + 1));
    mkdirSync(join(out, ".."), { recursive: true });
    const text = JSON.stringify(obj);
    writeFileSync(out, text);
    const sha = createHash("sha256").update(text).digest("hex");
    list[path] = { bytes: Buffer.byteLength(text), sha256: sha };
    bytes += Buffer.byteLength(text);
    hash.update(path).update(text);
  }
  const old = `${dir}.old-${process.pid}`;
  if (existsSync(dir)) renameSync(dir, old);
  renameSync(tmp, dir);
  rmSync(old, { recursive: true, force: true });
  return { files: list, bytes, sha256: hash.digest("hex") };
}

// ---------------------------------------------------------------- the check

const read = (dir, path) => JSON.parse(readFileSync(join(dir, path), "utf8"));
const cents = (v) => Math.round(Number(v ?? 0) * 100);

/**
 * Every file against budget.db, with SQL written here. Returns { diffs, cells }: the differences
 * (empty when the files agree) and how many values were compared.
 */
export function verifyCouncilJson(sqlite, outDir) {
  const diffs = [];
  let cells = 0;
  const same = (where, got, want) => {
    cells++;
    if (got !== want && !(got == null && want == null)) diffs.push(`${where}: JSON ${JSON.stringify(got)}, table ${JSON.stringify(want)}`);
  };
  const sameMoney = (where, got, want) => {
    cells++;
    if (cents(got) !== cents(want)) diffs.push(`${where}: JSON ${got}, table ${want}`);
  };
  /** A row file against the table's rows, cell by cell, in rowid order (dictionary cells looked up here). */
  const rowsMatch = (path, table, where, params) => {
    const f = read(outDir, path);
    for (const [c, values] of Object.entries(f.dicts ?? {})) {
      const j = f.columns.indexOf(c);
      for (const r of f.rows) r[j] = Number.isInteger(r[j]) && r[j] < values.length ? values[r[j]] : `(no dictionary entry ${r[j]})`;
    }
    const want = sqlite.prepare(`SELECT * FROM ${table} ${where} ORDER BY rowid`).all(...params);
    if (f.rows.length !== want.length) return diffs.push(`${path}: ${f.rows.length} rows, table ${want.length}`);
    const cols = Object.keys(want[0] ?? {});
    if (JSON.stringify(f.columns) !== JSON.stringify(cols)) diffs.push(`${path}: columns ${f.columns.join(",")} vs ${cols.join(",")}`);
    f.rows.forEach((r, i) => cols.forEach((c, j) => same(`${path} row ${i + 1} ${c}`, r[j], want[i][c])));
  };
  const has = (p) => existsSync(join(outDir, p));

  // Row files: one per loaded disclosure year and per capital report year, and no other.
  const loaded = sqlite.prepare("SELECT fiscal_year FROM disclosure_years WHERE loaded = 1 ORDER BY fiscal_year").all().map((r) => r.fiscal_year);
  for (const y of loaded) rowsMatch(awardsYearPath(y), "disclosure", "WHERE fiscal_year = ?", [y]);
  const notLoaded = sqlite.prepare("SELECT fiscal_year FROM disclosure_years WHERE loaded = 0").all().map((r) => r.fiscal_year);
  for (const y of notLoaded) if (has(awardsYearPath(y))) diffs.push(`${awardsYearPath(y)}: written for a year that is not loaded`);
  const reports = sqlite.prepare("SELECT DISTINCT report_year FROM capital_council ORDER BY report_year").all().map((r) => r.report_year);
  for (const y of reports) rowsMatch(capitalYearPath(y), "capital_council", "WHERE report_year = ?", [y]);
  rowsMatch(ombPath(), "capital_vs_omb", "", []);

  // years.json: the lookups and sources as stored, and the Years view's totals recomputed.
  const yj = read(outDir, councilYearsPath());
  const tableRows = (table, order) => sqlite.prepare(`SELECT * FROM ${table} ORDER BY ${order}`).all();
  for (const [key, table, order] of [["disclosure_years", "disclosure_years", "fiscal_year"], ["capital_sources", "capital_sources", "report_year"]]) {
    const want = tableRows(table, order);
    if (yj[key].length !== want.length) diffs.push(`years.json ${key}: ${yj[key].length} rows, table ${want.length}`);
    want.forEach((w, i) => Object.keys(w).forEach((c) => same(`years.json ${key}[${i}].${c}`, yj[key][i]?.[c], w[c])));
  }
  same("years.json omb_years", JSON.stringify(yj.omb_years), JSON.stringify(sqlite.prepare("SELECT DISTINCT report_year y FROM capital_vs_omb ORDER BY 1").all().map((r) => r.y)));
  const pdfWant = sqlite.prepare("SELECT fiscal_year, family, status, rows FROM pdf_years ORDER BY fiscal_year DESC, family").all();
  if (yj.pdf_years.length !== pdfWant.length) diffs.push(`years.json pdf_years: ${yj.pdf_years.length} rows, table ${pdfWant.length}`);
  pdfWant.forEach((w, i) => Object.keys(w).forEach((c) => same(`years.json pdf_years[${i}].${c}`, yj.pdf_years[i]?.[c], w[c])));

  const disc = sqlite
    .prepare(
      `SELECT y.fiscal_year, d.status_norm, COUNT(d.fiscal_year) n, TOTAL(d.amount) amount
       FROM disclosure_years y LEFT JOIN disclosure d ON d.fiscal_year = y.fiscal_year GROUP BY 1, 2`
    )
    .all();
  for (const y of yj.year_disclosure) {
    for (const s of ["cleared", "pending", "other"]) {
      const w = disc.find((r) => r.fiscal_year === y.fiscal_year && r.status_norm === s) ?? { n: 0, amount: 0 };
      same(`years.json FY${y.fiscal_year} ${s} rows`, Number(y[`${s}_rows`]), w.n);
      sameMoney(`years.json FY${y.fiscal_year} ${s} amount`, y[`${s}_amount`], w.amount);
    }
  }
  same("years.json year_disclosure years", yj.year_disclosure.length, sqlite.prepare("SELECT COUNT(*) n FROM disclosure_years").get().n);
  const cap = sqlite
    .prepare(
      `SELECT report_year, CASE WHEN amount IS NULL THEN 'unknown' WHEN amount_fy = report_year THEN 'report' ELSE 'out' END kind,
              COUNT(*) n, TOTAL(amount) amount FROM capital_council GROUP BY 1, 2`
    )
    .all();
  same("years.json year_capital groups", yj.year_capital.length, cap.length);
  for (const g of yj.year_capital) {
    const w = cap.find((r) => r.report_year === g.report_year && r.kind === g.kind) ?? { n: -1, amount: 0 };
    same(`years.json capital FY${g.report_year} ${g.kind} rows`, g.n, w.n);
    sameMoney(`years.json capital FY${g.report_year} ${g.kind} amount`, g.amount, w.amount);
  }

  // awards/index.json: all years, no filter.
  const ix = read(outDir, awardsIndexPath());
  const tot = sqlite.prepare("SELECT fiscal_year, status_norm, COUNT(*) n, TOTAL(amount) amount FROM disclosure GROUP BY 1, 2 ORDER BY 1, 2").all();
  same("awards/index.json totals groups", ix.totals.length, tot.length);
  tot.forEach((w, i) => {
    const g = ix.totals[i] ?? {};
    same(`awards/index.json totals[${i}] year`, g.fiscal_year, w.fiscal_year);
    same(`awards/index.json totals[${i}] status`, g.status_norm, w.status_norm);
    same(`awards/index.json totals[${i}] rows`, g.n, w.n);
    sameMoney(`awards/index.json totals[${i}] amount`, g.amount, w.amount);
  });
  const fl = sqlite.prepare("SELECT row_flag, COUNT(*) n, TOTAL(amount) amount FROM disclosure WHERE row_flag <> '' GROUP BY 1 ORDER BY 1").all();
  same("awards/index.json flags", ix.flags.length, fl.length);
  fl.forEach((w, i) => {
    same(`awards/index.json flags[${i}]`, ix.flags[i]?.row_flag, w.row_flag);
    same(`awards/index.json flags[${i}] rows`, ix.flags[i]?.n, w.n);
    sameMoney(`awards/index.json flags[${i}] amount`, ix.flags[i]?.amount, w.amount);
  });
  const first = sqlite.prepare(`SELECT fiscal_year, source_row FROM disclosure ORDER BY amount DESC, fiscal_year, source_row LIMIT ${Q.PAGE_SIZE}`).all();
  same("awards/index.json first page", JSON.stringify(ix.rows.map((r) => [r.fiscal_year, r.source_row])), JSON.stringify(first.map((r) => [r.fiscal_year, r.source_row])));

  return { diffs, cells };
}
