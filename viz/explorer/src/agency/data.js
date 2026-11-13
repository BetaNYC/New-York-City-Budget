/**
 * City agency budgets as small JSON files (#299), so the agency view opens without the DuckDB
 * engine (about 33 MB). Pure functions, shared by the build (scripts/agency-json.mjs writes the
 * files from the index's agency_budget table) and the view (src/views/Agencies.jsx reads them).
 *
 * Three kinds of file, under data/agency_budget/:
 *   citywide.json        every fiscal year's citywide totals (and the build stamp)
 *   agencies.json        every agency: the names it has had, and its totals by year
 *   agency/<NNN>.json    one agency: its totals by year, and each unit's figures by year;
 *                        fetched only when that agency is opened
 *
 * The rows the readers below return have the same fields as src/query/agency.js's SQL over the
 * same table, so test/agency-json.test.mjs can check the two cell by cell.
 *
 * NULL is kept, never turned into 0: `adopted` is null for a unit not in that year's budget,
 * `modified` for a unit not in the next year's release or a year not yet published. A total over
 * only nulls is null. Sums are taken in whole cents, so they are exact.
 */

export const AGENCY_JSON_DIR = "agency_budget";
export const AGENCY_JSON_SCHEMA = 1;
export const citywidePath = () => `${AGENCY_JSON_DIR}/citywide.json`;
export const agenciesPath = () => `${AGENCY_JSON_DIR}/agencies.json`;
export const agencyPath = (code) => `${AGENCY_JSON_DIR}/agency/${code}.json`;

const toCents = (v) => (v === null || v === undefined ? null : Math.round(Number(v) * 100));
const fromCents = (c) => (c === null ? null : c / 100);

/** SQL MAX over text: the largest by code unit, nulls skipped. */
const maxText = (vals) => vals.reduce((m, v) => (v == null ? m : m == null || v > m ? v : m), null);

/**
 * Totals for a group of rows, like src/query/agency.js TOTALS: adopted and modified summed
 * (null when every one is null), how many units, and how many lack each figure.
 */
function totals(rows) {
  let a = null;
  let m = null;
  let noA = 0;
  let noM = 0;
  for (const r of rows) {
    const ca = toCents(r.adopted);
    const cm = toCents(r.modified);
    if (ca === null) noA++;
    else a = (a ?? 0) + ca;
    if (cm === null) noM++;
    else m = (m ?? 0) + cm;
  }
  return { adopted: fromCents(a), modified: fromCents(m), units: rows.length, units_no_adopted: noA, units_no_modified: noM };
}

/** The name a group shows: as published in that year's adopted release, else the modified one. */
const groupName = (rows, col) => maxText(rows.filter((r) => r.adopted_release != null).map((r) => r[col])) ?? maxText(rows.map((r) => r[col]));

const groupBy = (rows, key) => {
  const out = new Map();
  for (const r of rows) {
    const k = key(r);
    if (!out.has(k)) out.set(k, []);
    out.get(k).push(r);
  }
  return out;
};
const byNum = (a, b) => a - b;
const byText = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

/**
 * Every file, from the agency_budget rows: { path: object }. `stamp` is what the files say about
 * the build ({ generated_at, source }).
 */
export function agencyJsonFiles(rows, stamp = {}) {
  const head = { schema: AGENCY_JSON_SCHEMA, generated_at: stamp.generated_at ?? null };
  const years = [...new Set(rows.map((r) => r.fiscal_year))].sort(byNum);
  const files = {};

  const cityYears = [...groupBy(rows, (r) => r.fiscal_year)].sort(([a], [b]) => a - b).map(([fy, rs]) => ({
    fiscal_year: fy,
    ...totals(rs),
    adopted_release: maxText(rs.map((r) => r.adopted_release)),
    modified_release: maxText(rs.map((r) => r.modified_release)),
  }));
  files[citywidePath()] = { ...head, source: stamp.source ?? null, first_year: years[0] ?? null, newest: years.at(-1) ?? null, years: cityYears };

  const agencies = [];
  for (const [code, rs] of [...groupBy(rows, (r) => r.agency_number)].sort(([a], [b]) => byText(a, b))) {
    const perYear = [...groupBy(rs, (r) => r.fiscal_year)].sort(([a], [b]) => a - b);
    agencies.push({
      agency_number: code,
      names: [...new Set(rs.map((r) => r.agency_name))].sort(byText),
      years: perYear.map(([fy, ys]) => ({ fiscal_year: fy, agency_name: groupName(ys, "agency_name"), ...totals(ys) })),
    });
    const units = [...groupBy(rs, (r) => r.unit_number)].sort(([a], [b]) => byText(a, b)).map(([unit, us]) => ({
      unit_number: unit,
      years: us
        .slice()
        .sort((x, y) => x.fiscal_year - y.fiscal_year)
        .map((u) => ({
          fiscal_year: u.fiscal_year,
          agency_name: u.agency_name,
          unit_name: u.unit_name,
          adopted: fromCents(toCents(u.adopted)),
          modified: fromCents(toCents(u.modified)),
          adopted_release: u.adopted_release ?? null,
          modified_release: u.modified_release ?? null,
        })),
    }));
    files[agencyPath(code)] = {
      ...head,
      agency_number: code,
      years: perYear.map(([fy, ys]) => ({
        fiscal_year: fy,
        agency_name: groupName(ys, "agency_name"),
        ...totals(ys),
        adopted_release: maxText(ys.map((r) => r.adopted_release)),
        modified_release: maxText(ys.map((r) => r.modified_release)),
      })),
      units,
    };
  }
  files[agenciesPath()] = { ...head, agencies };
  return files;
}

// ---------------------------------------------------------------- readers (the view's queries)

/** Every fiscal year, newest first, and whether its modified budget is out (agencyFiscalYearsQuery). */
export const fiscalYears = (city) => [...(city?.years ?? [])].sort((a, b) => b.fiscal_year - a.fiscal_year).map((y) => ({ fiscal_year: y.fiscal_year, has_modified: y.modified !== null }));

/** Citywide totals by year, oldest first (agencyYearsQuery with no agency). */
export const cityByYear = (city) => city?.years ?? [];

/** All agencies in one fiscal year, largest adopted first (agencyListQuery). */
export function agencyList(agencies, fy) {
  const rows = [];
  for (const a of agencies?.agencies ?? []) {
    const y = a.years.find((r) => r.fiscal_year === fy);
    if (!y) continue;
    const { fiscal_year: _fy, ...rest } = y;
    rows.push({ agency_number: a.agency_number, ...rest });
  }
  return rows.sort((a, b) => (a.adopted === b.adopted ? byText(a.agency_number, b.agency_number) : a.adopted === null ? 1 : b.adopted === null ? -1 : b.adopted - a.adopted));
}

/** Whether agencies.json lists this agency. */
export const hasAgency = (agencies, code) => (agencies?.agencies ?? []).some((a) => a.agency_number === code);

/** One agency's units in one fiscal year (agencyUnitsQuery). */
export function agencyUnits(file, fy) {
  const out = [];
  for (const u of file?.units ?? []) {
    const y = u.years.find((r) => r.fiscal_year === fy);
    if (y) out.push({ unit_number: u.unit_number, unit_name: y.unit_name, agency_name: y.agency_name, adopted: y.adopted, modified: y.modified, adopted_release: y.adopted_release, modified_release: y.modified_release });
  }
  return out;
}

/** One agency's totals by year, oldest first (agencyYearsQuery with abag). */
export const agencyByYear = (file) => file?.years ?? [];

/** One unit's figures by year, oldest first (agencyYearsQuery with abag and abunit). */
export const unitByYear = (file, unit) => (file?.units ?? []).find((u) => u.unit_number === unit)?.years ?? [];

/** Every agency name ever published, for old links (src/agency/legacy.js resolveLegacy). */
export const agencyNames = (agencies) => (agencies?.agencies ?? []).flatMap((a) => a.names.map((n) => ({ agency_number: a.agency_number, agency_name: n, unit_number: "", unit_name: "" })));

/** Every agency and unit name in one agency's file, for old links. */
export const unitNames = (file) => (file?.units ?? []).flatMap((u) => u.years.map((y) => ({ agency_number: file.agency_number, agency_name: y.agency_name, unit_number: u.unit_number, unit_name: y.unit_name })));
