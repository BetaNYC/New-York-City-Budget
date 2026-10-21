/**
 * Is this record on NYC Open Data? Queries over the open_data_* tables (mcp/scripts/open-data.mjs,
 * built from data/open_data/; research/2026-10-21-open-data-tracking/PLAN.md §5).
 *
 * A record has one crosswalk row per dataset that covers its year. No row and a dataset that does
 * not cover the year reads "No NYC Open Data dataset covers this", never "not on Open Data".
 */

/** Badge text and tone per status (PLAN §1). */
export const OD_STATUS = {
  same: { label: "On NYC Open Data", tone: "ok" },
  differs: { label: "On NYC Open Data, with differences", tone: "warn" },
  ambiguous: { label: "On NYC Open Data, row not identifiable", tone: "info" },
  absent: { label: "Not on NYC Open Data", tone: "bad" },
  context: { label: "Line on NYC Open Data", tone: "info" },
  not_covered: { label: "No NYC Open Data dataset covers this", tone: "none" },
};

/** An ambiguous row whose bucket holds as many of ours as the portal's, with the same key values,
 * is on the portal; only which portal row is unknown. Otherwise the counts differ. */
export const equalBucket = (x) => /equal counts/.test(x.match_rule ?? "");

/** The portal page for a dataset, and (one row) the SODA URL that returns exactly that row. */
export const datasetUrl = (id) => `https://data.cityofnewyork.us/d/${id}`;
export const rowUrl = (id, rowId) =>
  `https://data.cityofnewyork.us/resource/${id}.json?$where=${encodeURIComponent(`:id='${rowId}'`)}`;

const SELECT = `SELECT x.family, x.fiscal_year, x.record_row, x.record_amount_fy, x.record_pdf, x.record_part, x.dataset_id,
  x.portal_row_id, x.candidates, x.match_status, r.match_rule, x.differing_fields, x.portal_value,
  x.portal_status, x.portal_as_of, d.name AS dataset_name, d.snapshot_date
  FROM open_data_crosswalk x
  LEFT JOIN open_data_rules r ON r.rule_id = x.rule_id
  LEFT JOIN open_data_datasets d ON d.dataset_id = x.dataset_id`;

/**
 * Crosswalk rows for the records on screen. `keys` are [fiscal_year, record_row, amount_fy?]
 * (amount_fy only for capital awards; undefined for the others). Null when there is nothing to ask.
 */
export function odForRecordsQuery(family, keys, { pdf = 0 } = {}) {
  if (!keys.length) return null;
  const withFy = family === "capital_award";
  const one = withFy
    ? "(x.fiscal_year = ? AND x.record_row = ? AND x.record_amount_fy IS NOT DISTINCT FROM ?)"
    : "(x.fiscal_year = ? AND x.record_row = ?)";
  const params = [family, pdf];
  for (const k of keys) {
    params.push(Number(k[0]), String(k[1]));
    if (withFy) params.push(k[2] == null ? null : Number(k[2]));
  }
  return {
    sql: `${SELECT} WHERE x.family = ? AND x.record_pdf = ? AND (${keys.map(() => one).join(" OR ")})
          ORDER BY x.dataset_id`,
    params,
  };
}

/** Context rows for capital budget lines, by (report year, normalized line). */
export function odForLinesQuery(lines) {
  if (!lines.length) return null;
  const params = ["capital_line"];
  for (const [fy, line] of lines) params.push(Number(fy), line);
  return {
    sql: `${SELECT} WHERE x.family = ? AND (${lines.map(() => "(x.fiscal_year = ? AND x.record_row = ?)").join(" OR ")})
          ORDER BY x.dataset_id`,
    params,
  };
}

/** The per-year coverage strip for one family. */
export function coverageQuery(family) {
  return {
    sql: `SELECT c.*, d.name AS dataset_name FROM open_data_coverage c
          LEFT JOIN open_data_datasets d ON d.dataset_id = c.dataset_id
          WHERE c.family = ? ORDER BY c.dataset_id, c.fiscal_year`,
    params: [family],
  };
}

/** Index crosswalk rows by record: key -> [rows, one per dataset]. */
export function indexByRecord(rows, withFy = false) {
  const m = new Map();
  for (const r of rows ?? []) {
    const k = recordKey(r.fiscal_year, r.record_row, withFy ? r.record_amount_fy : undefined);
    if (!m.has(k)) m.set(k, []);
    m.get(k).push(r);
  }
  return m;
}

export const recordKey = (fy, row, amountFy) => `${Number(fy)}|${row}${amountFy === undefined ? "" : `|${amountFy ?? ""}`}`;

/**
 * The datasets that cover a family's year, from the coverage rows: [{dataset_id, name, covered}].
 */
export function coveringDatasets(coverage, fy) {
  return (coverage ?? []).filter((c) => Number(c.fiscal_year) === Number(fy) && Number(c.covered) === 1);
}
