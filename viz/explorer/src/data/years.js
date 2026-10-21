/**
 * The year overview's model, as a pure function: one entry per fiscal year from the first year
 * either dataset covers to the last, each side either data or a gap with its reason. A gap is
 * never a zero: the view renders `kind: "gap"` as "no data for this year" and the reason.
 *
 * Reasons come from the data, not from this file:
 *   disclosure  data/disclosure_years.csv `note` (FY2010: not loaded, and why)
 *   capital     data/capital/README.md "Which source each year comes from" (FY2018), and the
 *               dataset's first published year (nothing before FY2015), via manifest.json
 */

export const CAPITAL_BEFORE_FIRST = (first) =>
  `The Council capital dataset starts at FY${first} (data/capital/README.md); no Council capital list before it is in this repository.`;

const DISCLOSURE_NOT_IN_CSV = "No Council expense funding disclosure workbook for this year is in this repository (data/disclosure_years.csv).";

/**
 * Whether a year's Cleared total may be shown as a headline figure. Not for an early snapshot
 * (frozen while much of it was Pending: FY2009, FY2013), and not for a year that prints statuses
 * other than Cleared/Pending (FY2011, FY2012), whose Cleared totals are not comparable with other
 * years'. The MCP drops its "(headline)" label for the same years.
 */
export function headlineOk(d) {
  return d.kind === "data" && !d.early_snapshot && !(d.other_rows > 0);
}

/**
 * @param disclosureYears rows of YEAR_DISCLOSURE_QUERY
 * @param capitalYears    rollupCapital(...).by_report_year
 * @param capitalManifest manifest.json `capital`: { first, last, gaps: [{year, reason}] }
 */
export function buildYears(disclosureYears, capitalYears, capitalManifest) {
  const disc = new Map(disclosureYears.map((r) => [Number(r.fiscal_year), r]));
  const cap = new Map(capitalYears.map((r) => [Number(r.report_year), r]));
  const gapReason = new Map((capitalManifest?.gaps ?? []).map((g) => [Number(g.year), g.reason]));
  const all = [...disc.keys(), ...cap.keys()];
  if (all.length === 0) return [];
  const first = Math.min(...all);
  const last = Math.max(...all);
  const out = [];
  for (let year = first; year <= last; year++) {
    const d = disc.get(year);
    let disclosure;
    if (!d) disclosure = { kind: "gap", reason: DISCLOSURE_NOT_IN_CSV };
    else if (!Number(d.loaded)) disclosure = { kind: "gap", reason: d.note || "Not loaded (data/disclosure_years.csv gives no reason)." };
    else {
      disclosure = {
        kind: "data",
        rows: Number(d.rows),
        cleared: { rows: Number(d.cleared_rows), amount: Number(d.cleared_amount) },
        pending: { rows: Number(d.pending_rows), amount: Number(d.pending_amount) },
        other: { rows: Number(d.other_rows), amount: Number(d.other_amount) },
        other_rows: Number(d.other_rows),
        early_snapshot: Boolean(Number(d.early_snapshot)),
        note: d.note || "",
        source_kind: d.source_kind,
      };
    }
    const c = cap.get(year);
    let capital;
    if (c) {
      capital = {
        kind: "data",
        report_year_amounts: c.report_year_amounts,
        out_year_amounts: c.out_year_amounts,
        amount_unknown: c.amount_unknown,
      };
    } else if (gapReason.has(year)) {
      capital = { kind: "gap", reason: gapReason.get(year) };
    } else if (capitalManifest && year < capitalManifest.first) {
      capital = { kind: "gap", reason: CAPITAL_BEFORE_FIRST(capitalManifest.first) };
    } else {
      capital = { kind: "gap", reason: "No Council capital list for this year is in this repository." };
    }
    out.push({ fiscal_year: year, disclosure, capital });
  }
  return out;
}
