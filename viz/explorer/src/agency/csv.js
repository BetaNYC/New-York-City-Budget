/**
 * The "Download this table" CSV of the Agency budgets view (#286): what is on screen, as RFC 4180
 * text. A figure that does not exist is an empty cell (never 0 here; the old full download,
 * agencies/data/nyc_budget.csv, keeps its 0s).
 */

/** One cell: quoted when it holds a comma, quote or line break. */
export function csvCell(v) {
  if (v === null || v === undefined) return "";
  const s = String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/**
 * @param {object[]} rows
 * @param {Array<[string, string | ((row: object) => unknown)]>} columns  header, then a key or a function
 */
export function toCsv(rows, columns) {
  const head = columns.map(([h]) => csvCell(h)).join(",");
  const body = rows.map((r) => columns.map(([, k]) => csvCell(typeof k === "function" ? k(r) : r[k])).join(","));
  return [head, ...body].join("\r\n") + "\r\n";
}

/** A data: URL for a download link (the tables are small: at most a few hundred rows). */
export const csvHref = (rows, columns) => `data:text/csv;charset=utf-8,${encodeURIComponent(toCsv(rows, columns))}`;
