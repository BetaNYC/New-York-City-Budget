/**
 * Where the Council explorer's JSON files live under public/data/ (#301). Shared by the build
 * (scripts/council-json.mjs) and the app, so both name a file the same way.
 */
export const COUNCIL_JSON_DIR = "council";
export const councilYearsPath = () => `${COUNCIL_JSON_DIR}/years.json`;
export const ombPath = () => `${COUNCIL_JSON_DIR}/omb.json`;
export const awardsIndexPath = () => `${COUNCIL_JSON_DIR}/awards/index.json`;
export const awardsYearPath = (fy) => `${COUNCIL_JSON_DIR}/awards/fy${fy}.json`;
export const capitalYearPath = (fy) => `${COUNCIL_JSON_DIR}/capital/fy${fy}.json`;

/**
 * A row file's rows as objects. Columns listed in `dicts` hold each cell's position in that
 * column's list of values (scripts/council-json.mjs).
 */
const decoded = new WeakMap();
/** decodeRows, once per parsed file (a view re-runs its queries on every filter change). */
export function rowsOf(file) {
  if (!decoded.has(file)) decoded.set(file, decodeRows(file));
  return decoded.get(file);
}

export function decodeRows({ columns, rows, dicts = {} }) {
  const lookups = columns.map((c) => dicts[c] ?? null);
  return rows.map((r) => {
    const o = {};
    for (let j = 0; j < columns.length; j++) o[columns[j]] = lookups[j] ? lookups[j][r[j]] : r[j];
    return o;
  });
}
