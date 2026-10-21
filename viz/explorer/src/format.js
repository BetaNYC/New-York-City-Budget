/** Display formatting and the plain-language notes the views attach to flagged values. */

const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 2 });
const INT = new Intl.NumberFormat("en-US");

/** Dollars, rounded to cents for display (FY2009–FY2012 carry amounts like 7481.296758). */
export const money = (v) => (v === null || v === undefined || Number.isNaN(Number(v)) ? "—" : USD.format(Number(v)));
export const count = (v) => INT.format(Number(v ?? 0));
export const plural = (n, one, many = `${one}s`) => `${count(n)} ${Number(n) === 1 ? one : many}`;

export const STATUS_LABEL = { cleared: "Cleared", pending: "Pending", other: "Other status" };
export const VERDICT_LABEL = {
  match: "Match",
  differ: "Differ",
  council_only: "Council only",
  omb_only: "OMB only",
};

/**
 * What each disclosure row flag means. Wording from mcp/README.md and DATA-DICTIONARY.md; every
 * flagged row is still counted in the totals, as the Council published it.
 */
export const DISCLOSURE_FLAG_NOTE = {
  not_an_award: "Not an award: one of two FY2009 lump allocations on the City's own EIN. Kept and counted as published.",
  no_grantee_ein: "No grantee EIN printed by the Council. Often a city program rather than a nonprofit.",
};

export const CAPITAL_FLAG_NOTE = {
  split_record_amount_unknown:
    "A NYC Open Data (t474-a92g) record broken across rows; its amount cannot be proven from the Council's own files, so it is left blank and is not in the totals (data/capital/RECONCILIATION.md §2).",
};

export const OTHER_STATUS_NOTE =
  "Other statuses (FY2011, FY2012) are the workbook's own values beyond Cleared and Pending: Government (a City agency is the recipient), Pending FC Clearance, CBO Defunded. None is defined by the Council; they are never counted as cleared.";

export const flagNotes = (rowFlag, notes) =>
  String(rowFlag || "")
    .split(";")
    .filter(Boolean)
    .map((f) => ({ flag: f, note: notes[f] ?? "Flag recorded in the data; see DATA-DICTIONARY.md." }));
