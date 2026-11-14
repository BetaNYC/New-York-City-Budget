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
 *
 * #301: a query a fast view runs also carries a `json` form, { files, run(files) }, that answers
 * the same question from the Council JSON files (data/council/, src/council/data.js) with no query
 * engine. test/council-parity.test.mjs holds each json form to its SQL, row for row.
 */
import { fold } from "../../../../mcp/dist/fold.js";
import { awardsIndexPath, awardsYearPath, capitalYearPath, councilYearsPath, decodeRows, ombPath, rowsOf } from "../council/paths.js";

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

/** Ascending, as DuckDB orders these values (numbers by value, ASCII text by code point). */
export const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

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
  // Explorer only, with Schedule C loaded (pdf_sc_disclosure; never set by the parity cases, and
  // the MCP has no such filter): the spreadsheet rows Schedule C matches, or does not.
  if (f.sc_side === "matched" || f.sc_side === "disclosure_only") {
    w.add(
      `EXISTS (SELECT 1 FROM pdf_sc_disclosure m WHERE m.fiscal_year = disclosure.fiscal_year AND m.disclosure_row = disclosure.source_row AND m.side = ?)`,
      f.sc_side
    );
  }
  return w;
}

export const DISCLOSURE_LIST_COLUMNS =
  "fiscal_year, source_row, legal_name, ein, council_member, source, agency, program_name, status, status_norm, amount, row_flag, duplicate_group";
const LIST_KEYS = DISCLOSURE_LIST_COLUMNS.split(", ");

/**
 * disclosureWhere, in JS, for one fiscal year's file (#301): the same filters, the text ones on
 * the same folded twin with the same fold() (DuckDB: contains(lower(COALESCE(x_fold, x)), q)).
 * null when the filter needs the engine: no fiscal year, or the Schedule C pairing.
 */
export function disclosureMatches(f = {}) {
  if (num(f.fiscal_year) === null || f.sc_side === "matched" || f.sc_side === "disclosure_only") return null;
  const tests = [];
  if (DISCLOSURE_STATUSES.includes(f.status)) tests.push((r) => r.status_norm === f.status);
  if (!blank(f.ein) && normEin(f.ein) !== "") {
    const ein = normEin(f.ein);
    tests.push((r) => r.ein === ein);
  }
  for (const c of DISCLOSURE_TEXT) {
    if (blank(f[c])) continue;
    const q = fold(f[c]);
    if (q === "") continue;
    const twin = `${c}_fold`;
    tests.push((r) => {
      const v = r[twin] ?? r[c];
      return v != null && v.toLowerCase().includes(q);
    });
  }
  const min = num(f.min_amount);
  const max = num(f.max_amount);
  if (min !== null) tests.push((r) => r.amount >= min);
  if (max !== null) tests.push((r) => r.amount <= max);
  return (r) => tests.every((t) => t(r));
}

/** Whether a filter is the unfiltered list over all years (awards/index.json answers its first page). */
const noFilter = (f = {}) =>
  num(f.fiscal_year) === null && !DISCLOSURE_STATUSES.includes(f.status) && (blank(f.ein) || normEin(f.ein) === "") &&
  DISCLOSURE_TEXT.every((c) => blank(f[c]) || fold(f[c]) === "") && num(f.min_amount) === null && num(f.max_amount) === null &&
  f.sc_side !== "matched" && f.sc_side !== "disclosure_only";

/** One year's matching rows, from its file. */
const yearRows = (f, file) => rowsOf(file).filter(disclosureMatches(f));

/** The json form of a disclosure query: one year's file, or index.json for the unfiltered list. */
function disclosureJson(f, fromYear, fromIndex) {
  if (disclosureMatches(f)) return { files: [awardsYearPath(num(f.fiscal_year))], run: ([file]) => fromYear(yearRows(f, file)) };
  if (fromIndex && noFilter(f)) return { files: [awardsIndexPath()], run: ([ix]) => fromIndex(ix) };
  return undefined;
}

/** Group matching rows as disclosureTotalsQuery does. */
function totalsOf(rows) {
  const g = new Map();
  for (const r of rows) {
    const k = `${r.fiscal_year}|${r.status_norm}`;
    const t = g.get(k) ?? { fiscal_year: r.fiscal_year, status_norm: r.status_norm, n: 0, amount: 0 };
    t.n++;
    t.amount += r.amount;
    g.set(k, t);
  }
  return [...g.values()].sort((a, b) => a.fiscal_year - b.fiscal_year || cmp(a.status_norm, b.status_norm));
}

export function disclosureRowsQuery(f = {}, page = 0) {
  const w = disclosureWhere(f);
  const p = Math.max(0, Math.trunc(Number(page) || 0));
  const offset = p * PAGE_SIZE;
  return {
    sql: `SELECT ${DISCLOSURE_LIST_COLUMNS} FROM disclosure ${w.sql}
          ORDER BY amount DESC, fiscal_year, source_row LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
    json: disclosureJson(
      f,
      (rows) =>
        [...rows]
          .sort((a, b) => b.amount - a.amount || a.fiscal_year - b.fiscal_year || a.source_row - b.source_row)
          .slice(offset, offset + PAGE_SIZE)
          .map((r) => Object.fromEntries(LIST_KEYS.map((k) => [k, r[k]]))),
      p === 0 ? (ix) => ix.rows : null
    ),
  };
}

/** Rows and amount per (fiscal_year, status_norm) over every match. */
export function disclosureTotalsQuery(f = {}) {
  const w = disclosureWhere(f);
  return {
    sql: `SELECT fiscal_year, status_norm, COUNT(*) AS n, SUM(amount) AS amount
          FROM disclosure ${w.sql} GROUP BY fiscal_year, status_norm ORDER BY fiscal_year, status_norm`,
    params: w.params,
    json: disclosureJson(f, totalsOf, (ix) => ix.totals),
  };
}

/** Matched rows carrying a row_flag, per flag (all counted in the totals). */
export function disclosureFlagsQuery(f = {}) {
  const w = disclosureWhere(f);
  return {
    sql: `SELECT row_flag, COUNT(*) AS n, SUM(amount) AS amount FROM disclosure ${w.and("row_flag <> ''")}
          GROUP BY row_flag ORDER BY row_flag`,
    params: w.params,
    json: disclosureJson(
      f,
      (rows) => {
        const g = new Map();
        for (const r of rows) {
          if (r.row_flag == null || r.row_flag === "") continue;
          const t = g.get(r.row_flag) ?? { row_flag: r.row_flag, n: 0, amount: 0 };
          t.n++;
          t.amount += r.amount;
          g.set(r.row_flag, t);
        }
        return [...g.values()].sort((a, b) => cmp(a.row_flag, b.row_flag));
      },
      (ix) => ix.flags
    ),
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
  const fy = Number(fiscal_year);
  const row = Number(source_row);
  return {
    sql: `SELECT d.*, y.source_path, y.url AS source_url, y.sheet, y.retrieved, y.sha256, y.wayback_timestamp,
                 y.source_kind, y.early_snapshot, y.note AS year_note
          FROM disclosure d JOIN disclosure_years y USING (fiscal_year)
          WHERE d.fiscal_year = ? AND d.source_row = ?`,
    params: [fy, row],
    // #301: the row from its year's file, joined to the year's source in years.json.
    json: {
      files: [awardsYearPath(fy), councilYearsPath()],
      optional: [awardsYearPath(fy)],
      run: ([file, years]) => {
        const y = years.disclosure_years.find((x) => x.fiscal_year === fy);
        const d = file && y ? rowsOf(file).find((r) => r.source_row === row) : null;
        if (!d) return [];
        return [{ ...d, source_path: y.source_path, source_url: y.url, sheet: y.sheet, retrieved: y.retrieved, sha256: y.sha256,
          wayback_timestamp: y.wayback_timestamp, source_kind: y.source_kind, early_snapshot: y.early_snapshot, year_note: y.note }];
      },
    },
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
const CAPITAL_KEYS = CAPITAL_LIST_COLUMNS.split(", ");

/** capitalWhere, in JS, for one report year's file (#301); null without a report year. */
export function capitalMatches(f = {}) {
  if (num(f.fiscal_year) === null) return null;
  const tests = [];
  const afy = num(f.amount_fy);
  if (afy !== null) tests.push((r) => r.amount_fy === afy);
  if (!blank(f.budget_line)) {
    const line = normBudgetLine(f.budget_line) ?? "\u0000unreadable";
    tests.push((r) => r.budget_line_norm === line);
  }
  if (!blank(f.borough)) tests.push((r) => r.borough === String(f.borough));
  if (num(f.council_district) !== null) {
    const tok = `,${Math.trunc(num(f.council_district))},`;
    tests.push((r) => r.district_tokens != null && r.district_tokens.includes(tok));
  }
  for (const c of CAPITAL_TEXT) {
    if (blank(f[c])) continue;
    const q = fold(f[c]);
    if (q === "") continue;
    const twin = `${c}_fold`;
    tests.push((r) => {
      const v = r[twin] ?? r[c];
      return v != null && v.toLowerCase().includes(q);
    });
  }
  const min = num(f.min_amount);
  const max = num(f.max_amount);
  if (min !== null) tests.push((r) => r.amount !== null && r.amount >= min);
  if (max !== null) tests.push((r) => r.amount !== null && r.amount <= max);
  return (r) => tests.every((t) => t(r));
}

function capitalJson(f, run) {
  const m = capitalMatches(f);
  return m ? { files: [capitalYearPath(num(f.fiscal_year))], run: ([file]) => run(rowsOf(file).filter(m)) } : undefined;
}

export function capitalRowsQuery(f = {}, page = 0) {
  const w = capitalWhere(f);
  const offset = Math.max(0, Math.trunc(Number(page) || 0)) * PAGE_SIZE;
  return {
    sql: `SELECT ${CAPITAL_LIST_COLUMNS} FROM capital_council ${w.sql}
          ORDER BY amount IS NULL, amount DESC, report_year, source_file, seq LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
    json: capitalJson(f, (rows) =>
      [...rows]
        .sort((a, b) => cmp(a.amount === null, b.amount === null) || (b.amount ?? 0) - (a.amount ?? 0) || a.report_year - b.report_year || cmp(a.source_file, b.source_file) || a.seq - b.seq)
        .slice(offset, offset + PAGE_SIZE)
        .map((r) => Object.fromEntries(CAPITAL_KEYS.map((k) => [k, r[k]])))
    ),
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
    json: capitalJson(f, (rows) => {
      const g = new Map();
      for (const r of rows) {
        const kind = r.amount === null ? "unknown" : r.amount_fy === r.report_year ? "report" : "out";
        const t = g.get(kind) ?? { report_year: r.report_year, kind, n: 0, amount: 0 };
        t.n++;
        t.amount += r.amount ?? 0;
        g.set(kind, t);
      }
      return [...g.values()].sort((a, b) => a.report_year - b.report_year || cmp(a.kind, b.kind));
    }),
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
  const n = Number(seq);
  return {
    sql: `SELECT c.*, s.url AS source_url, s.retrieved, s.sha256, s.wayback_timestamp, s.note AS source_note
          FROM capital_council c LEFT JOIN capital_sources s USING (report_year) WHERE c.seq = ?`,
    params: [n],
    // #301: years.json says which report year holds this seq; that year's file has the row.
    json: {
      files: [councilYearsPath()],
      next: ([years]) => {
        const at = years.capital_seq.find((g) => n >= g.first && n <= g.last);
        if (!at) return { files: [], run: () => [] };
        return {
          files: [capitalYearPath(at.report_year)],
          run: ([file]) => {
            const c = rowsOf(file).find((r) => r.seq === n);
            if (!c) return [];
            const s = years.capital_sources.find((x) => x.report_year === c.report_year) ?? {};
            return [{ ...c, source_url: s.url ?? null, retrieved: s.retrieved ?? null, sha256: s.sha256 ?? null, wayback_timestamp: s.wayback_timestamp ?? null, source_note: s.note ?? null }];
          },
        };
      },
    },
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

/** ombWhere, in JS, for the JSON form: the same three filters. */
export function ombMatches(f = {}) {
  const year = num(f.report_year);
  const line = blank(f.budget_line) ? null : normBudgetLine(f.budget_line) ?? "\u0000unreadable";
  const verdict = OMB_VERDICTS.includes(f.verdict) ? f.verdict : null;
  return (r) => (year === null || r.report_year === year) && (line === null || r.budget_line_norm === line) && (verdict === null || r.verdict === verdict);
}


/** Lines that disagree first, then the largest absolute first-year difference (as the MCP). */
export function ombRowsQuery(f = {}, page = 0) {
  const w = ombWhere(f);
  const offset = Math.max(0, Math.trunc(Number(page) || 0)) * PAGE_SIZE;
  const gap = (r) => Math.abs((r.council_y1 ?? 0) - (r.omb_y1 ?? 0));
  return {
    sql: `SELECT * FROM capital_vs_omb ${w.sql}
          ORDER BY verdict = 'match', ABS(COALESCE(council_y1, 0) - COALESCE(omb_y1, 0)) DESC, report_year, budget_line_norm
          LIMIT ${PAGE_SIZE} OFFSET ${offset}`,
    params: w.params,
    json: {
      files: [ombPath()],
      run: ([o]) =>
        decodeRows(o)
          .filter(ombMatches(f))
          .sort((a, b) => cmp(a.verdict === "match", b.verdict === "match") || gap(b) - gap(a) || a.report_year - b.report_year || cmp(a.budget_line_norm, b.budget_line_norm))
          .slice(offset, offset + PAGE_SIZE),
    },
  };
}

export function ombCountsQuery(f = {}) {
  const w = ombWhere(f);
  return {
    sql: `SELECT report_year, omb_pub_date, verdict, COUNT(*) AS n FROM capital_vs_omb ${w.sql}
          GROUP BY report_year, omb_pub_date, verdict ORDER BY report_year, verdict`,
    params: w.params,
    json: {
      files: [ombPath()],
      run: ([o]) => {
        const groups = new Map();
        for (const r of decodeRows(o).filter(ombMatches(f))) {
          const k = JSON.stringify([r.report_year, r.omb_pub_date, r.verdict]);
          const g = groups.get(k) ?? { report_year: r.report_year, omb_pub_date: r.omb_pub_date, verdict: r.verdict, n: 0 };
          g.n++;
          groups.set(k, g);
        }
        return [...groups.values()].sort((a, b) => a.report_year - b.report_year || cmp(a.verdict, b.verdict));
      },
    },
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
  // Pre-run by the build (scripts/council-json.mjs runs this very SQL).
  json: { files: [councilYearsPath()], run: ([y]) => y.year_disclosure },
};

export const YEAR_CAPITAL_QUERY = { ...capitalTotalsQuery({}), json: { files: [councilYearsPath()], run: ([y]) => y.year_capital } };

// ---------------------------------------------------------------- lookups every view reads

/** The year lists every view is built from (App.jsx Ready), from the tables or years.json. */
export const LOOKUP_QUERIES = {
  years: {
    sql: "SELECT fiscal_year, loaded, early_snapshot, note FROM disclosure_years ORDER BY fiscal_year DESC",
    params: [],
    json: {
      files: [councilYearsPath()],
      run: ([y]) =>
        [...y.disclosure_years]
          .sort((a, b) => b.fiscal_year - a.fiscal_year)
          .map(({ fiscal_year, loaded, early_snapshot, note }) => ({ fiscal_year, loaded, early_snapshot, note })),
    },
  },
  capYears: {
    sql: "SELECT report_year FROM capital_sources ORDER BY report_year",
    params: [],
    json: { files: [councilYearsPath()], run: ([y]) => y.capital_sources.map(({ report_year }) => ({ report_year })).sort((a, b) => a.report_year - b.report_year) },
  },
  ombYears: {
    sql: "SELECT DISTINCT report_year FROM capital_vs_omb ORDER BY report_year",
    params: [],
    json: { files: [councilYearsPath()], run: ([y]) => y.omb_years.map((report_year) => ({ report_year })) },
  },
};
