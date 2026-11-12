/**
 * City agency budgets (#270, #286): queries over agency_budget (mcp/scripts/agency-budget.mjs,
 * NYC Open Data mwzb-yiwb under the year rule), as pure { sql, params } builders. DuckDB-WASM runs
 * them in the browser; test/agency-parity.test.mjs runs them with @duckdb/node-api and checks the
 * answers against the old /agencies/ app.
 *
 * NULL is kept, never turned into 0: `adopted` is NULL for a unit not in that year's budget, and
 * `modified` for a unit not in the next year's release or a year whose modified budget is not
 * published yet. A SUM over only NULLs is NULL ("not yet published"), so the newest year's
 * modified total reads that way, not $0. `units_no_adopted` / `units_no_modified` count the units
 * a total leaves out.
 */

const blank = (v) => v === null || v === undefined || String(v).trim() === "";
/** "56" -> "056"; anything else as given (trimmed). */
export const pad3 = (v) => (/^\d{1,3}$/.test(String(v ?? "").trim()) ? String(v).trim().padStart(3, "0") : String(v ?? "").trim());

/** The name a row group shows: as published in that year's adopted release, else the modified one. */
const NAME = (col) => `COALESCE(MAX(${col}) FILTER (WHERE adopted_release IS NOT NULL), MAX(${col}))`;

const TOTALS = `SUM(adopted) AS adopted, SUM(modified) AS modified,
  COUNT(*) AS units,
  COUNT(*) FILTER (WHERE adopted IS NULL) AS units_no_adopted,
  COUNT(*) FILTER (WHERE modified IS NULL) AS units_no_modified`;

/** Every fiscal year the table holds, newest first, with whether its modified budget is out. */
export function agencyFiscalYearsQuery() {
  return {
    sql: `SELECT fiscal_year, COUNT(modified) > 0 AS has_modified FROM agency_budget GROUP BY fiscal_year ORDER BY fiscal_year DESC`,
    params: [],
  };
}

/** All agencies in one fiscal year, with their totals, largest adopted first. */
export function agencyListQuery({ abfy }) {
  return {
    sql: `SELECT agency_number, ${NAME("agency_name")} AS agency_name, ${TOTALS}
      FROM agency_budget WHERE fiscal_year = ?
      GROUP BY agency_number
      ORDER BY adopted DESC NULLS LAST, agency_number`,
    params: [Number(abfy)],
  };
}

/** One agency's units in one fiscal year. */
export function agencyUnitsQuery({ abfy, abag }) {
  return {
    sql: `SELECT unit_number, unit_name, agency_name, adopted, modified, adopted_release, modified_release
      FROM agency_budget WHERE fiscal_year = ? AND agency_number = ?
      ORDER BY unit_number`,
    params: [Number(abfy), pad3(abag)],
  };
}

/**
 * Adopted and modified for every fiscal year: citywide (abag blank), one agency, or one unit
 * (abag and abunit). Years in order, oldest first.
 */
export function agencyYearsQuery({ abag, abunit }) {
  const where = [];
  const params = [];
  if (!blank(abag)) {
    where.push("agency_number = ?");
    params.push(pad3(abag));
    if (!blank(abunit)) {
      where.push("unit_number = ?");
      params.push(pad3(abunit));
    }
  }
  return {
    sql: `SELECT fiscal_year, ${NAME("agency_name")} AS agency_name, ${NAME("unit_name")} AS unit_name, ${TOTALS},
      MAX(adopted_release) AS adopted_release, MAX(modified_release) AS modified_release
      FROM agency_budget ${where.length ? `WHERE ${where.join(" AND ")}` : ""}
      GROUP BY fiscal_year ORDER BY fiscal_year`,
    params,
  };
}

/** Every agency and unit name ever published, for old links (src/agency/legacy.js resolveLegacy). */
export function agencyNamesQuery() {
  return {
    sql: `SELECT DISTINCT agency_number, agency_name, unit_number, unit_name FROM agency_budget ORDER BY agency_number, unit_number`,
    params: [],
  };
}

/** Change from one figure to another: { dollars, pct } or null when either is missing. */
export function change(from, to) {
  if (from == null || to == null) return null;
  const dollars = Math.round((Number(to) - Number(from)) * 100) / 100;
  const pct = Number(from) === 0 ? null : (dollars / Number(from)) * 100;
  return { dollars, pct };
}
