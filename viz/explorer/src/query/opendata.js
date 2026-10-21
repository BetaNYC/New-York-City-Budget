/**
 * Is this record on NYC Open Data? Queries over the open_data_* tables (mcp/scripts/open-data.mjs,
 * built from data/open_data/; research/2026-10-21-open-data-tracking/PLAN.md §5).
 *
 * A record has one crosswalk row per dataset that covers its year. No row and a dataset that does
 * not cover the year reads "No Open Data to check", never "not found".
 */

/**
 * Four states, one per crosswalk row (Noel, 2026-10-21). Text carries the meaning; color only
 * repeats it; every state that searched a dataset names its snapshot date.
 *   found     "On NYC Open Data": a one-to-one match (same or differs), or a listed line/unit
 *   maybe     "Maybe on NYC Open Data": a bucket of look-alikes; we can't tell which row is ours,
 *             so presence is never claimed, whatever the counts
 *   notfound  "Not found on NYC Open Data": a dataset covers the year, no match
 *   nocheck   "No Open Data to check": no dataset covers the year (e.g. CPDB before FY2026)
 */
export const STATES = {
  found: { label: "On NYC Open Data", tone: "ok" },
  maybe: { label: "Maybe on NYC Open Data", tone: "warn" },
  notfound: { label: "Not found on NYC Open Data", tone: "bad" },
  nocheck: { label: "No Open Data to check", tone: "none" },
};

export const HOW_WE_CHECK =
  "How we check. The city publishes this data in several places that don't share an ID. We match records by year, amount, and organization or project. " +
  "A match is our best effort, not an official link. \"Maybe\" means more than one record fits. \"Not found\" means only that we didn't find it in the copy we " +
  "downloaded on that date. If you spot a wrong match, tell us.";

/** The state of one crosswalk row (undefined: no row, no dataset covers the year). */
export function stateOf(x) {
  if (!x) return "nocheck";
  if (["same", "differs", "context"].includes(x.match_status)) return "found";
  if (x.match_status === "ambiguous") return "maybe";
  if (x.match_status === "absent") return "notfound";
  return "nocheck";
}

/** [ours, portal] in an ambiguous row's bucket, from its rule text, or null. */
export const bucketCounts = (x) => {
  const m = /holds (\d+) of ours and (\d+) on the portal|(\d+) of ours, (\d+) on the portal/.exec(x.match_rule ?? "");
  return m ? [Number(m[1] ?? m[3]), Number(m[2] ?? m[4])] : null;
};

/** A coverage row's strip numbers: found = state 1 only; maybe = state 2, shown separately. */
export function stripShares(c) {
  const rec = Number(c.records);
  const found = Number(c.same) + Number(c.differs) + Number(c.context);
  const maybe = Number(c.ambiguous);
  const pct = (n) => (rec ? Math.round((100 * n) / rec) : 0);
  return { found, maybe, foundPct: pct(found), maybePct: pct(maybe) };
}

/** The covered fiscal years of a dataset, from the coverage rows: [first, last] or null. */
export function coveredRange(coverage, datasetId) {
  const ys = (coverage ?? []).filter((c) => c.dataset_id === datasetId && Number(c.covered) === 1).map((c) => Number(c.fiscal_year));
  return ys.length ? [Math.min(...ys), Math.max(...ys)] : null;
}

/** The tooltip sentence for a crosswalk row (or for no row). */
export function tooltipOf(x, range) {
  const st = stateOf(x);
  if (st === "nocheck") return "No NYC Open Data dataset covers this year, so we couldn't check.";
  const where = `${x.dataset_name ?? x.dataset_id} (${x.dataset_id})`;
  if (st === "found") {
    const ids = String(x.portal_row_id ?? "").split(";").filter(Boolean);
    return ids.length === 1
      ? `Matches row ${ids[0]} in ${where}, as of ${x.snapshot_date}.`
      : `Matches ${ids.length || "listed"} rows in ${where}, as of ${x.snapshot_date}.`;
  }
  if (st === "maybe") {
    const b = bucketCounts(x);
    const n = b ? b[0] : "Several";
    const m = b ? b[1] : x.candidates;
    return `${n} of our records and ${m} portal rows share this year and amount; we can't tell which. ${where}, as of ${x.snapshot_date}.`;
  }
  const r = range ? ` (covers FY${range[0]}–FY${range[1]})` : "";
  return `Searched ${x.dataset_name ?? x.dataset_id}${r} as of ${x.snapshot_date}; no match.`;
}

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
