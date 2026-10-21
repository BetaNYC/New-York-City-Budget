/**
 * Query building for the explorer, as pure functions: each returns { sql, params } with `?`
 * placeholders, run by DuckDB-WASM in the browser and by @duckdb/node-api in the parity test.
 *
 * The filters mean exactly what the MCP's do (mcp/src/db.ts), and test/parity.test.mjs runs both
 * on the same filters and compares the answers:
 *   - text filters are case-, accent- and punctuation-insensitive substrings, matched on the
 *     index's folded twin column (`<column>_fold`, NULL where folding changes only ASCII case)
 *     with the MCP's own fold() — imported, not copied, from mcp/dist/fold.js;
 *   - an EIN is compared digits-only; a status is status_norm (cleared / pending / other);
 *   - totals are computed over EVERY matching row, never over the page shown;
 *   - rows sort the way the MCP sorts them.
 * The one deliberate difference: a blank text filter is "no filter" here (a form field left
 * empty), where the MCP refuses it.
 */
import { fold } from "../../../../mcp/dist/fold.js";

export { fold };

export const PAGE_SIZE = 50;
export const DISCLOSURE_STATUSES = ["cleared", "pending", "other"];
export const OMB_VERDICTS = ["match", "differ", "council_only", "omb_only"];
export const BOROUGHS = { C: "Citywide", K: "Brooklyn", M: "Manhattan", Q: "Queens", R: "Staten Island", X: "Bronx" };

/** Digits-only EIN so "13-2612524" and "132612524" match (mcp/src/db.ts normEin). */
export const normEin = (v) => String(v ?? "").replace(/\D/g, "");

const BUDGET_LINE = /^([A-Z]{1,2})[\s-]+([A-Z0-9]+)$/;
/**
 * A budget line in the dataset's normal form, "AGENCY LINE" ("P D018"); null when it has no such
 * shape. Same rule as mcp/src/db.ts normBudgetLine; the parity test checks they agree.
 */
export function normBudgetLine(v) {
  const m = BUDGET_LINE.exec(String(v ?? "").trim().toUpperCase().replace(/\s+/g, " "));
  return m ? `${m[1]} ${m[2]}` : null;
}

const blank = (v) => v === null || v === undefined || (typeof v === "string" && v.trim() === "");
const num = (v) => (blank(v) ? null : Number.isFinite(Number(v)) ? Number(v) : null);

/** Collects WHERE clauses and their parameters in step. */
class Where {
  constructor() {
    this.clauses = [];
    this.params = [];
  }
  add(clause, ...params) {
    this.clauses.push(clause);
    this.params.push(...params);
  }
  /** Substring on the folded twin; skipped when the value is blank or folds to nothing. */
  text(column, value) {
    if (blank(value)) return;
    const q = fold(value);
    if (q === "") return;
    this.add(`contains(lower(COALESCE(${column}_fold, ${column})), ?)`, q);
  }
  eq(column, value) {
    if (value === null || value === undefined || value === "") return;
    this.add(`${column} = ?`, value);
  }
  get sql() {
    return this.clauses.length ? `WHERE ${this.clauses.join(" AND ")}` : "";
  }
  /** The same filter plus one more condition. */
  and(extra) {
    return this.clauses.length ? `WHERE ${this.clauses.join(" AND ")} AND ${extra}` : `WHERE ${extra}`;
  }
}

// ---------------------------------------------------------------- disclosure

export const DISCLOSURE_TEXT = ["legal_name", "council_member", "agency", "program_name", "source"];

/** Filters: fiscal_year, status, ein, min_amount, max_amount, and the DISCLOSURE_TEXT columns. */
export function disclosureWhere(f = {}) {
  const w = new Where();
  w.eq("fiscal_year", num(f.fiscal_year));
  if (DISCLOSURE_STATUSES.includes(f.status)) w.add("status_norm = ?", f.status);
  if (!blank(f.ein) && normEin(f.ein) !== "") w.add("ein = ?", normEin(f.ein));
  for (const c of DISCLOSURE_TEXT) w.text(c, f[c]);
  if (num(f.min_amount) !== null) w.add("amount >= ?", num(f.min_amount));
  if (num(f.max_amount) !== null) w.add("amount <= ?", num(f.max_amount));
  return w;
}

export const DISCLOSURE_LIST_COLUMNS =
  "fiscal_year, source_row, legal_name, ein, council_member, source, agency, program_name, status, status_norm, amount, row_flag, duplicate_group";

export function disclosureRowsQuery(f = {}, page = 0) {
  const w = disclosureWhere(f);
  const offset = Math.max(0, Math.trunc(Number(page) || 0)) * PAGE_SIZE;
  return {
    sql: `SELECT ${DISCLOSURE_LIST_COLUMNS} FROM disclosure ${w.sql}
          ORDER BY amount DESC, fiscal_year, source_row LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
  };
}

/** Rows and amount per (fiscal_year, status_norm) over every match. */
export function disclosureTotalsQuery(f = {}) {
  const w = disclosureWhere(f);
  return {
    sql: `SELECT fiscal_year, status_norm, COUNT(*) AS n, SUM(amount) AS amount
          FROM disclosure ${w.sql} GROUP BY fiscal_year, status_norm ORDER BY fiscal_year, status_norm`,
    params: w.params,
  };
}

/** Matched rows carrying a row_flag, per flag (all counted in the totals). */
export function disclosureFlagsQuery(f = {}) {
  const w = disclosureWhere(f);
  return {
    sql: `SELECT row_flag, COUNT(*) AS n, SUM(amount) AS amount FROM disclosure ${w.and("row_flag <> ''")}
          GROUP BY row_flag ORDER BY row_flag`,
    params: w.params,
  };
}

/** Fold grouped (fiscal_year, status_norm) counts into overall and per-year totals by status. */
export function rollupDisclosure(grouped) {
  const empty = () => ({ cleared: { rows: 0, amount: 0 }, pending: { rows: 0, amount: 0 }, other: { rows: 0, amount: 0 } });
  const totals = empty();
  const years = new Map();
  let matched = 0;
  for (const g of grouped) {
    const s = DISCLOSURE_STATUSES.includes(g.status_norm) ? g.status_norm : "other";
    const year = Number(g.fiscal_year);
    const y = years.get(year) ?? empty();
    const n = Number(g.n);
    const a = Number(g.amount ?? 0);
    y[s].rows += n;
    y[s].amount += a;
    years.set(year, y);
    totals[s].rows += n;
    totals[s].amount += a;
    matched += n;
  }
  return { matched, totals, by_year: [...years.entries()].map(([fiscal_year, t]) => ({ fiscal_year, totals: t })) };
}

export function awardQuery(fiscal_year, source_row) {
  return {
    sql: `SELECT d.*, y.source_path, y.url AS source_url, y.sheet, y.retrieved, y.sha256, y.wayback_timestamp,
                 y.source_kind, y.early_snapshot, y.note AS year_note
          FROM disclosure d JOIN disclosure_years y USING (fiscal_year)
          WHERE d.fiscal_year = ? AND d.source_row = ?`,
    params: [Number(fiscal_year), Number(source_row)],
  };
}

// ---------------------------------------------------------------- capital

export const CAPITAL_TEXT = ["sponsor", "title", "description"];

/**
 * Filters: fiscal_year (report year), amount_fy, budget_line (normalized; an unreadable one
 * matches nothing, as the MCP refuses it), borough, council_district, min/max_amount, and the
 * CAPITAL_TEXT columns.
 */
export function capitalWhere(f = {}) {
  const w = new Where();
  w.eq("report_year", num(f.fiscal_year));
  w.eq("amount_fy", num(f.amount_fy));
  if (!blank(f.budget_line)) w.add("budget_line_norm = ?", normBudgetLine(f.budget_line) ?? "\u0000unreadable");
  if (!blank(f.borough)) w.add("borough = ?", String(f.borough));
  // Workbook years only: t474 lists collapsed into one number, so those rows have no tokens.
  if (num(f.council_district) !== null) w.add("contains(district_tokens, ?)", `,${Math.trunc(num(f.council_district))},`);
  for (const c of CAPITAL_TEXT) w.text(c, f[c]);
  if (num(f.min_amount) !== null) w.add("amount >= ?", num(f.min_amount));
  if (num(f.max_amount) !== null) w.add("amount <= ?", num(f.max_amount));
  return w;
}

export const CAPITAL_LIST_COLUMNS =
  "seq, report_year, amount_fy, project_id, borough, budget_line, budget_line_norm, council_district, sponsor, title, description, amount, source_kind, source_file, source_row, row_flag";

export function capitalRowsQuery(f = {}, page = 0) {
  const w = capitalWhere(f);
  const offset = Math.max(0, Math.trunc(Number(page) || 0)) * PAGE_SIZE;
  return {
    sql: `SELECT ${CAPITAL_LIST_COLUMNS} FROM capital_council ${w.sql}
          ORDER BY amount IS NULL, amount DESC, report_year, source_file, seq LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
  };
}

/** Per report year: report-year amounts, out-year amounts, and rows with no amount. */
export function capitalTotalsQuery(f = {}) {
  const w = capitalWhere(f);
  return {
    sql: `SELECT report_year,
                 CASE WHEN amount IS NULL THEN 'unknown' WHEN amount_fy = report_year THEN 'report' ELSE 'out' END AS kind,
                 COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount
          FROM capital_council ${w.sql} GROUP BY report_year, kind ORDER BY report_year, kind`,
    params: w.params,
  };
}

export function rollupCapital(grouped) {
  const years = new Map();
  const report_year_amounts = { rows: 0, amount: 0 };
  const out_year_amounts = { rows: 0, amount: 0 };
  let amount_unknown = 0;
  let matched = 0;
  for (const g of grouped) {
    const year = Number(g.report_year);
    const n = Number(g.n);
    const a = Number(g.amount ?? 0);
    const y = years.get(year) ?? {
      report_year: year,
      report_year_amounts: { rows: 0, amount: 0 },
      out_year_amounts: { rows: 0, amount: 0 },
      amount_unknown: 0,
    };
    if (g.kind === "report") {
      y.report_year_amounts = { rows: n, amount: a };
      report_year_amounts.rows += n;
      report_year_amounts.amount += a;
    } else if (g.kind === "out") {
      y.out_year_amounts = { rows: n, amount: a };
      out_year_amounts.rows += n;
      out_year_amounts.amount += a;
    } else {
      y.amount_unknown = n;
      amount_unknown += n;
    }
    years.set(year, y);
    matched += n;
  }
  return { matched, report_year_amounts, out_year_amounts, amount_unknown, by_report_year: [...years.values()] };
}

export function capitalRowQuery(seq) {
  return {
    sql: `SELECT c.*, s.url AS source_url, s.retrieved, s.sha256, s.wayback_timestamp, s.note AS source_note
          FROM capital_council c LEFT JOIN capital_sources s USING (report_year) WHERE c.seq = ?`,
    params: [Number(seq)],
  };
}

// ---------------------------------------------------------------- Council vs OMB

export function ombWhere(f = {}) {
  const w = new Where();
  w.eq("report_year", num(f.report_year));
  if (!blank(f.budget_line)) w.add("budget_line_norm = ?", normBudgetLine(f.budget_line) ?? "\u0000unreadable");
  if (OMB_VERDICTS.includes(f.verdict)) w.add("verdict = ?", f.verdict);
  return w;
}

/** Lines that disagree first, then the largest absolute first-year difference (as the MCP). */
export function ombRowsQuery(f = {}, page = 0) {
  const w = ombWhere(f);
  const offset = Math.max(0, Math.trunc(Number(page) || 0)) * PAGE_SIZE;
  return {
    sql: `SELECT * FROM capital_vs_omb ${w.sql}
          ORDER BY verdict = 'match', ABS(COALESCE(council_y1, 0) - COALESCE(omb_y1, 0)) DESC, report_year, budget_line_norm
          LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
  };
}

export function ombCountsQuery(f = {}) {
  const w = ombWhere(f);
  return {
    sql: `SELECT report_year, omb_pub_date, verdict, COUNT(*) AS n FROM capital_vs_omb ${w.sql}
          GROUP BY report_year, omb_pub_date, verdict ORDER BY report_year, verdict`,
    params: w.params,
  };
}

// ---------------------------------------------------------------- year overview

export const YEAR_DISCLOSURE_QUERY = {
  sql: `SELECT y.fiscal_year, y.loaded, y.early_snapshot, y.note, y.source_kind, y.source_path, y.retrieved,
               COALESCE(SUM(d.amount) FILTER (WHERE d.status_norm = 'cleared'), 0) AS cleared_amount,
               COUNT(d.fiscal_year) FILTER (WHERE d.status_norm = 'cleared') AS cleared_rows,
               COALESCE(SUM(d.amount) FILTER (WHERE d.status_norm = 'pending'), 0) AS pending_amount,
               COUNT(d.fiscal_year) FILTER (WHERE d.status_norm = 'pending') AS pending_rows,
               COALESCE(SUM(d.amount) FILTER (WHERE d.status_norm = 'other'), 0) AS other_amount,
               COUNT(d.fiscal_year) FILTER (WHERE d.status_norm = 'other') AS other_rows,
               COUNT(d.fiscal_year) AS rows
        FROM disclosure_years y LEFT JOIN disclosure d USING (fiscal_year)
        GROUP BY ALL ORDER BY y.fiscal_year`,
  params: [],
};

export const YEAR_CAPITAL_QUERY = capitalTotalsQuery({});
