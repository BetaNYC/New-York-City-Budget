/**
 * SQLite-backed query layer for the NYC budget MCP (2.0: structured sources only).
 *
 * The database (data/budget.db) is built by scripts/build-index.mjs from the repo's
 * structured datasets: the Council's expense funding disclosure workbooks
 * (data/fyNN/expense_disclosure/, provenance in data/disclosure_years.csv) and the Council
 * capital dataset (data/capital/, from Council workbooks and NYC Open Data). Nothing extracted
 * from a PDF is indexed; test/no-pdf-data.test.js fails if any of it comes back.
 *
 * This module opens the index read-only and exposes one function per tool. Text filters are
 * case-insensitive substrings with LIKE wildcards taken literally; every search returns the
 * true match count and totals computed in SQL over every match, never over the page.
 */
import Database from "better-sqlite3";
import type { Database as DB } from "better-sqlite3";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { fold } from "./fold.js";

export { fold };

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "..", "data", "budget.db");

let _db: DB | null = null;

export function getDb(): DB {
  if (_db) return _db;
  if (!existsSync(DB_PATH)) {
    throw new Error(`Budget index not found at ${DB_PATH}. Run: npm run build-index`);
  }
  _db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
  return _db;
}

/** Digits-only EIN so "13-2612524" and "132612524" match. */
export function normEin(v: string): string {
  return (v ?? "").replace(/\D/g, "");
}

function eqClause(column: string, params: unknown[], value?: number): string | null {
  if (value == null) return null;
  params.push(value);
  return `${column} = ?`;
}

function where(clauses: (string | null)[]): string {
  const active = clauses.filter((c): c is string => c !== null);
  return active.length ? `WHERE ${active.join(" AND ")}` : "";
}

function cap(limit?: number, def = 50, max = 500): number {
  if (limit == null || Number.isNaN(limit)) return def;
  return Math.min(Math.max(1, Math.trunc(limit)), max);
}

/**
 * Substring match on the column's folded twin (`<column>_fold`, written by build-index.mjs with
 * fold()), so case, accents, curly quotes and dashes do not matter: "Women's" finds "Women’s",
 * "jewish emigre" finds "Jewish Émigré". LIKE's wildcards are taken literally: a filter of "_" or
 * "100%" means those characters (legal_name "_" used to match every row). A blank value is
 * refused by the tool before it gets here (red team S3); it is never a silent "no filter".
 */
function likeLiteral(column: string, params: unknown[], value?: string): string | null {
  if (value == null) return null;
  const q = fold(value);
  if (q === "") throw new Error(`${column} is empty; omit it, or give a value.`);
  params.push(`%${q.replace(/[\\%_]/g, (c) => "\\" + c)}%`);
  // The twin is NULL where folding changes only ASCII case; NOCASE covers that case.
  return `COALESCE(${column}_fold, ${column}) LIKE ? ESCAPE '\\' COLLATE NOCASE`;
}

/** Exact match ignoring case and surrounding whitespace. */
function eqNoCase(column: string, params: unknown[], value?: string): string | null {
  if (value == null) return null;
  params.push(value.trim());
  return `${column} = ? COLLATE NOCASE`;
}

// ===========================================================================
// Council expense funding disclosure
// ===========================================================================

export const DISCLOSURE_STATUSES = ["cleared", "pending", "other"] as const;
export type DisclosureStatus = (typeof DISCLOSURE_STATUSES)[number];

/**
 * #70: how the 5-digit `zip` was read from the published `postal_code`, checked against the
 * Census Bureau's 2020 ZCTAs (code/zcta_states.py; DATA-DICTIONARY.md). valid / padded /
 * trimmed / repaired_extra_digit / not_a_zcta / state_mismatch carry a zip; ambiguous_extra_digit,
 * invalid and blank do not (ambiguous_extra_digit lists its candidates in zip_candidates).
 */
export const ZIP_STATUSES = [
  "valid", "padded", "trimmed", "repaired_extra_digit", "ambiguous_extra_digit",
  "not_a_zcta", "state_mismatch", "invalid", "blank",
] as const;
export type ZipStatus = (typeof ZIP_STATUSES)[number];

export interface DisclosureRow {
  fiscal_year: number;
  /** MOCS ID# as the Council's workbook prints it — FY2024+ only; "" before. */
  mocs_id: string;
  /**
   * #89 A4: the MOCS ID NYC Open Data 4d7f-74pe gives the same designation, FY2009–FY2021 only,
   * set only on an unambiguous (EIN, whole-dollar amount) pair. A cross-reference, not a source.
   */
  od_mocs_id: string;
  /** How the od_mocs_id pair's amounts agree: exact / rounded_cents / rounded_dollars; "" when no od_mocs_id. */
  od_match: string;
  /** Funding stream as the workbook names it: Local, Youth, Aging, Speaker's Initiative, or a citywide initiative. */
  source: string;
  /** The Council's roster when the workbook was exported — not the sponsoring member at adoption. */
  council_member: string;
  /** #72: the Legistar person ID the printed name resolves to for that fiscal year; "" when none. */
  council_member_id: string;
  council_member_type: string;
  legal_name: string;
  ein: string;
  /** Raw Status cell, verbatim (case varies by year). */
  status: string;
  status_norm: DisclosureStatus;
  /** The workbook's own value; can be fractional. */
  amount: number;
  agency: string;
  program_name: string;
  /** Grantee MAILING address as printed — not where services were delivered. Never rewritten. */
  address1: string;
  address2: string;
  city: string;
  state: string;
  postal_code: string;
  zip: string;
  zip_status: ZipStatus;
  zip_candidates: string;
  fiscal_conduit: string;
  fiscal_conduit_ein: string;
  source_row: number;
  duplicate_group: number | null;
  /** "" for nearly every row; else flags joined by ";": `not_an_award` (#89 B13, decided) or `no_grantee_ein` (a rule). Counted in totals. */
  row_flag: string;
}

export interface DisclosureFilters {
  fiscal_year?: number;
  ein?: string;
  legal_name?: string;
  council_member?: string;
  council_member_id?: string;
  source?: string;
  source_exact?: string;
  agency?: string;
  program_name?: string;
  zip?: string;
  zip_status?: ZipStatus;
  city?: string;
  status?: DisclosureStatus;
  /** Exact, case- and whitespace-insensitive: the workbook's own MOCS ID (FY2024+). */
  mocs_id?: string;
  /** Exact, case- and whitespace-insensitive: NYC Open Data's MOCS ID (FY2009–FY2021). */
  od_mocs_id?: string;
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

/** One row of data/disclosure_years.csv: where a fiscal year's workbook came from. */
export interface DisclosureYear {
  fiscal_year: number;
  /** 1 = in the dataset; 0 = a workbook exists but is deliberately not loaded (FY2010). */
  loaded: number;
  /** council_rnd (rnd.council.nyc.gov) or internet_archive (a Wayback capture). */
  source_kind: string;
  file: string;
  source_path: string;
  url: string;
  wayback_timestamp: string;
  sheet: string;
  /** Date BetaNYC downloaded this exact file. */
  retrieved: string;
  sha256: string;
  award_rows: number;
  /** 1 = a workbook frozen while much of it was Pending and never revised: do not headline its Cleared total. */
  early_snapshot: number;
  note: string;
}

export interface DisclosureTotal {
  rows: number;
  amount: number;
}

export interface DisclosureValueCount {
  value: string;
  council_member_id?: string;
  rows: number;
  amount: number;
}

export interface DisclosureResult {
  rows: DisclosureRow[];
  matched: number;
  totals: Record<DisclosureStatus, DisclosureTotal>;
  by_year: { fiscal_year: number; totals: Record<DisclosureStatus, DisclosureTotal> }[];
  /** Provenance for every year in the match (or the filtered year, if nothing matched). */
  snapshots: DisclosureYear[];
  matched_values: Partial<Record<"council_member" | "source" | "agency", DisclosureValueCount[]>>;
  ein_legal_names?: number;
  duplicates: { rows: number; groups: number; extra_rows: number; extra_amount: number };
  /** Matched rows carrying a row_flag, per flag (all counted in the totals). */
  flagged: { row_flag: string; rows: number; amount: number }[];
  /** Matched rows that print no grantee EIN (counted in the totals). */
  no_ein: { rows: number; amount: number };
  /**
   * For each matched fiscal year that prints any status outside Cleared/Pending ANYWHERE in the
   * year (FY2011, FY2012), that year's whole-year rows per raw status. Per year, not per match:
   * the label is about comparing a year's Cleared total with other years' (review S7).
   */
  other_statuses: { fiscal_year: number; status: string; rows: number; amount: number }[];
}

const emptyTotals = (): Record<DisclosureStatus, DisclosureTotal> => ({
  cleared: { rows: 0, amount: 0 },
  pending: { rows: 0, amount: 0 },
  other: { rows: 0, amount: 0 },
});

/**
 * Search the disclosure. The WHERE clause is built once and used for the page, the totals and
 * every breakdown, so the totals always describe exactly the rows the filters select, however
 * many of them the page leaves out (issues #42, #49).
 */
export function searchDisclosure(f: DisclosureFilters): DisclosureResult {
  const p: unknown[] = [];
  const w = where([
    eqClause("fiscal_year", p, f.fiscal_year),
    f.ein ? (p.push(normEin(f.ein)), "ein = ?") : null,
    likeLiteral("legal_name", p, f.legal_name),
    likeLiteral("council_member", p, f.council_member),
    f.council_member_id != null ? (p.push(f.council_member_id), "council_member_id = ?") : null,
    likeLiteral("source", p, f.source),
    eqNoCase("source", p, f.source_exact),
    likeLiteral("agency", p, f.agency),
    likeLiteral("program_name", p, f.program_name),
    f.zip != null ? (p.push(f.zip.trim()), "zip = ?") : null,
    f.zip_status != null ? (p.push(f.zip_status), "zip_status = ?") : null,
    eqNoCase("city", p, f.city),
    f.status ? (p.push(f.status), "status_norm = ?") : null,
    eqNoCase("mocs_id", p, f.mocs_id),
    eqNoCase("od_mocs_id", p, f.od_mocs_id),
    f.min_amount != null ? (p.push(f.min_amount), "amount >= ?") : null,
    f.max_amount != null ? (p.push(f.max_amount), "amount <= ?") : null,
  ]);
  const db = getDb();
  // Highest amount first BEFORE the limit (#41); the remaining keys only make ties deterministic.
  const rows = db
    .prepare(
      `SELECT fiscal_year, mocs_id, od_mocs_id, od_match, source, council_member, council_member_id,
         council_member_type, legal_name, ein, status, status_norm,
         amount, agency, program_name, address1, address2, city, state, postal_code, zip, zip_status,
         zip_candidates, fiscal_conduit, fiscal_conduit_ein, source_row, duplicate_group, row_flag
       FROM disclosure ${w}
       ORDER BY amount DESC, fiscal_year, source_row LIMIT ${cap(f.limit)}`
    )
    .all(...p) as DisclosureRow[];
  const grouped = db
    .prepare(
      `SELECT fiscal_year, status_norm, COUNT(*) AS n, SUM(amount) AS amount
       FROM disclosure ${w} GROUP BY fiscal_year, status_norm ORDER BY fiscal_year`
    )
    .all(...p) as { fiscal_year: number; status_norm: string; n: number; amount: number }[];

  const totals = emptyTotals();
  const years = new Map<number, Record<DisclosureStatus, DisclosureTotal>>();
  let matched = 0;
  for (const g of grouped) {
    const s = (DISCLOSURE_STATUSES as readonly string[]).includes(g.status_norm)
      ? (g.status_norm as DisclosureStatus)
      : "other";
    const y = years.get(g.fiscal_year) ?? emptyTotals();
    y[s].rows += g.n;
    y[s].amount += g.amount;
    years.set(g.fiscal_year, y);
    totals[s].rows += g.n;
    totals[s].amount += g.amount;
    matched += g.n;
  }

  const snapYears = years.size ? [...years.keys()] : f.fiscal_year != null ? [f.fiscal_year] : [];
  const snapshots = snapYears.length
    ? (db
        .prepare(
          `SELECT * FROM disclosure_years WHERE fiscal_year IN (${snapYears.map(() => "?").join(",")})
           ORDER BY fiscal_year`
        )
        .all(...snapYears) as DisclosureYear[])
    : [];

  const matched_values: DisclosureResult["matched_values"] = {};
  for (const col of ["council_member", "source", "agency"] as const) {
    if (f[col] == null || f[col]!.trim() === "") continue;
    // council_member is grouped with its person ID: one printed surname can be two people in
    // different years ('Rivera' is Joel Rivera in FY2013 and Carlina Rivera from FY2019).
    const idCol = col === "council_member" ? ", council_member_id" : "";
    matched_values[col] = db
      .prepare(
        `SELECT ${col} AS value${idCol}, COUNT(*) AS rows, SUM(amount) AS amount FROM disclosure ${w}
         GROUP BY ${col}${idCol} ORDER BY rows DESC, value`
      )
      .all(...p) as DisclosureValueCount[];
  }
  const ein_legal_names = f.ein
    ? (db.prepare(`SELECT COUNT(DISTINCT legal_name) AS n FROM disclosure ${w}`).get(...p) as { n: number }).n
    : undefined;

  const and = w ? `${w} AND` : "WHERE";
  const d = db
    .prepare(
      `SELECT COUNT(*) AS rows, COUNT(DISTINCT fiscal_year || ':' || duplicate_group) AS groups,
         COALESCE(SUM(source_row <> duplicate_group), 0) AS extra_rows,
         COALESCE(SUM(CASE WHEN source_row <> duplicate_group THEN amount ELSE 0 END), 0) AS extra_amount
       FROM disclosure ${and} duplicate_group IS NOT NULL`
    )
    .get(...p) as { rows: number; groups: number; extra_rows: number; extra_amount: number };
  const flagged = db
    .prepare(
      `SELECT row_flag, COUNT(*) AS rows, SUM(amount) AS amount FROM disclosure ${and} row_flag <> ''
       GROUP BY row_flag ORDER BY row_flag`
    )
    .all(...p) as { row_flag: string; rows: number; amount: number }[];

  const no_ein = db
    .prepare(`SELECT COUNT(*) AS rows, COALESCE(SUM(amount), 0) AS amount FROM disclosure ${and} ein = ''`)
    .get(...p) as { rows: number; amount: number };

  const matchedYears = [...years.keys()];
  const other_statuses = matchedYears.length
    ? (db
        .prepare(
          `SELECT fiscal_year, status, COUNT(*) AS rows, COALESCE(SUM(amount), 0) AS amount FROM disclosure
           WHERE status_norm = 'other' AND fiscal_year IN (${matchedYears.map(() => "?").join(",")})
           GROUP BY fiscal_year, status ORDER BY fiscal_year, amount DESC, status`
        )
        .all(...matchedYears) as { fiscal_year: number; status: string; rows: number; amount: number }[])
    : [];

  return {
    rows,
    matched,
    totals,
    other_statuses,
    by_year: [...years.entries()].map(([fiscal_year, t]) => ({ fiscal_year, totals: t })),
    snapshots,
    matched_values,
    ein_legal_names,
    duplicates: d,
    flagged,
    no_ein,
  };
}

/** Every row of data/disclosure_years.csv, loaded or not. */
export function listDisclosureYears(): DisclosureYear[] {
  return getDb()
    .prepare(`SELECT * FROM disclosure_years ORDER BY fiscal_year`)
    .all() as DisclosureYear[];
}

// ===========================================================================
// Council capital (data/capital/)
// ===========================================================================

export interface CapitalRow {
  /** The Council's capital list the row comes from (workbook year, or t474's `Reported`). */
  report_year: number;
  /** The fiscal year the amount is for: the report year or an out-year; null only on a flagged split record. */
  amount_fy: number | null;
  project_id: string;
  borough: string;
  budget_line: string;
  budget_line_norm: string;
  council_district: string;
  sponsor: string;
  title: string;
  description: string;
  /** Dollars as printed; null only on a `split_record_amount_unknown` row. */
  amount: number | null;
  source_kind: string;
  source_file: string;
  source_row: string;
  row_flag: string;
}

/** Where one report year's Council capital list came from. */
export interface CapitalSource {
  report_year: number;
  source_kind: string;
  source_file: string;
  url: string;
  wayback_timestamp: string;
  /** Date BetaNYC retrieved the file (ISO date). */
  retrieved: string;
  /** sha256 of the committed file, computed at index build and checked against its manifest. */
  sha256: string;
  rows: number;
  note: string;
}

export interface CapitalFilters {
  /** report_year */
  fiscal_year?: number;
  amount_fy?: number;
  /** Normal form "AGENCY LINE" (normBudgetLine). */
  budget_line?: string;
  /** Normal form: whitespace collapsed, upper case (normProjectId). */
  project_id?: string;
  sponsor?: string;
  sponsor_exact?: string;
  borough?: string;
  council_district?: number;
  title?: string;
  description?: string;
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

const BUDGET_LINE = /^([A-Z]{1,2})[\s-]+([A-Z0-9]+)$/;

/**
 * A budget line in the dataset's normal form, "AGENCY LINE" ("P D018", "PW DN846"), the same rule
 * as code/build_capital_council.py norm_line: upper case, agency code of one or two letters, then
 * whitespace or '-', then the line. Null when the value has no such shape (e.g. "PD018": where the
 * agency code ends cannot be told, so it is refused, never guessed).
 */
export function normBudgetLine(v: string): string | null {
  const m = BUDGET_LINE.exec(v.trim().toUpperCase().replace(/\s+/g, " "));
  return m ? `${m[1]} ${m[2]}` : null;
}

/** A Council project ID compared as printed, ignoring case and runs of whitespace ("E  CN459" = "e cn459"). */
export function normProjectId(v: string): string {
  return v.trim().replace(/\s+/g, " ").toUpperCase();
}

export interface CapitalTotal {
  rows: number;
  amount: number;
}

export interface CapitalResult {
  rows: CapitalRow[];
  matched: number;
  /** Rows whose amount is for the report year itself (amount_fy = report_year). */
  report_year_amounts: CapitalTotal;
  /** Rows whose amount is for a later year, per amount_fy. */
  out_years: { amount_fy: number; rows: number; amount: number }[];
  /** Rows with no amount (split_record_amount_unknown). */
  amount_unknown: number;
  by_report_year: { report_year: number; report_year_amounts: CapitalTotal; out_year_amounts: CapitalTotal; amount_unknown: number }[];
  sources: CapitalSource[];
  /** Distinct sponsor values a substring sponsor filter matched. */
  matched_sponsors?: { value: string; rows: number; amount: number }[];
  /** Report years whose rows cannot match a council_district filter (t474: lists collapsed). */
  district_unusable_years: number[];
}

export function searchCapital(f: CapitalFilters): CapitalResult {
  const p: unknown[] = [];
  const w = where([
    eqClause("report_year", p, f.fiscal_year),
    eqClause("amount_fy", p, f.amount_fy),
    f.budget_line != null ? (p.push(f.budget_line), "budget_line_norm = ?") : null,
    f.project_id != null ? (p.push(f.project_id), "project_id_norm = ?") : null,
    likeLiteral("sponsor", p, f.sponsor),
    eqNoCase("sponsor", p, f.sponsor_exact),
    f.borough != null ? (p.push(f.borough), "borough = ?") : null,
    // District tokens are stored as ",N," with numbers unpadded (",8,22,"), workbook years only.
    f.council_district != null ? (p.push(`%,${f.council_district},%`), "district_tokens LIKE ?") : null,
    likeLiteral("title", p, f.title),
    likeLiteral("description", p, f.description),
    f.min_amount != null ? (p.push(f.min_amount), "amount >= ?") : null,
    f.max_amount != null ? (p.push(f.max_amount), "amount <= ?") : null,
  ]);
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT report_year, amount_fy, project_id, borough, budget_line, budget_line_norm,
         council_district, sponsor, title, description, amount, source_kind, source_file, source_row,
         row_flag
       FROM capital_council ${w}
       ORDER BY amount IS NULL, amount DESC, report_year, source_file, seq LIMIT ${cap(f.limit)}`
    )
    .all(...p) as CapitalRow[];
  const grouped = db
    .prepare(
      `SELECT report_year,
         CASE WHEN amount IS NULL THEN 'unknown' WHEN amount_fy = report_year THEN 'report' ELSE 'out' END AS kind,
         COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount
       FROM capital_council ${w} GROUP BY report_year, kind ORDER BY report_year`
    )
    .all(...p) as { report_year: number; kind: string; n: number; amount: number }[];
  const out_years = db
    .prepare(
      `SELECT amount_fy, COUNT(*) AS rows, SUM(amount) AS amount FROM capital_council
       ${w ? `${w} AND` : "WHERE"} amount IS NOT NULL AND amount_fy <> report_year
       GROUP BY amount_fy ORDER BY amount_fy`
    )
    .all(...p) as { amount_fy: number; rows: number; amount: number }[];

  const byYear = new Map<number, CapitalResult["by_report_year"][number]>();
  const report_year_amounts = { rows: 0, amount: 0 };
  let amount_unknown = 0;
  let matched = 0;
  for (const g of grouped) {
    const y = byYear.get(g.report_year) ?? {
      report_year: g.report_year,
      report_year_amounts: { rows: 0, amount: 0 },
      out_year_amounts: { rows: 0, amount: 0 },
      amount_unknown: 0,
    };
    if (g.kind === "report") {
      y.report_year_amounts = { rows: g.n, amount: g.amount };
      report_year_amounts.rows += g.n;
      report_year_amounts.amount += g.amount;
    } else if (g.kind === "out") {
      y.out_year_amounts = { rows: g.n, amount: g.amount };
    } else {
      y.amount_unknown = g.n;
      amount_unknown += g.n;
    }
    byYear.set(g.report_year, y);
    matched += g.n;
  }

  const srcYears = byYear.size ? [...byYear.keys()] : f.fiscal_year != null ? [f.fiscal_year] : [];
  const sources = srcYears.length
    ? (db
        .prepare(
          `SELECT * FROM capital_sources WHERE report_year IN (${srcYears.map(() => "?").join(",")})
           ORDER BY report_year`
        )
        .all(...srcYears) as CapitalSource[])
    : [];
  const matched_sponsors =
    f.sponsor != null && f.sponsor.trim() !== ""
      ? (db
          .prepare(
            `SELECT sponsor AS value, COUNT(*) AS rows, COALESCE(SUM(amount), 0) AS amount FROM capital_council ${w}
             GROUP BY sponsor ORDER BY rows DESC, value`
          )
          .all(...p) as { value: string; rows: number; amount: number }[])
      : undefined;
  const district_unusable_years = (db
    .prepare(`SELECT DISTINCT report_year FROM capital_council WHERE district_tokens IS NULL ORDER BY report_year`)
    .all() as { report_year: number }[]).map((r) => r.report_year);

  return {
    rows,
    matched,
    report_year_amounts,
    out_years,
    amount_unknown,
    by_report_year: [...byYear.values()],
    sources,
    matched_sponsors,
    district_unusable_years,
  };
}

/** Every capital report year's provenance. */
export function listCapitalSources(): CapitalSource[] {
  return getDb().prepare(`SELECT * FROM capital_sources ORDER BY report_year`).all() as CapitalSource[];
}

// ---------------------------------------------------------------------------
// Council capital vs OMB's adopted capital budget, by budget line (this repo's arithmetic)
// ---------------------------------------------------------------------------

export const OMB_VERDICTS = ["match", "differ", "council_only", "omb_only"] as const;
export type OmbVerdict = (typeof OMB_VERDICTS)[number];

export interface OmbComparisonRow {
  report_year: number;
  budget_line_norm: string;
  /** OMB 46m8-77gv release used: the last release of that first fiscal year (July), YYYYMMDD. */
  omb_pub_date: string;
  council_rows: number;
  /** null when the line is not on the Council side (omb_only). */
  council_y1: number | null;
  /** null when the line is not in OMB's release (council_only). */
  omb_y1: number | null;
  council_y2: number | null;
  omb_y2: number | null;
  verdict: OmbVerdict;
}

export interface OmbComparisonFilters {
  report_year?: number;
  budget_line?: string;
  verdict?: OmbVerdict;
  limit?: number;
}

export interface OmbComparisonResult {
  rows: OmbComparisonRow[];
  matched: number;
  verdicts: Record<OmbVerdict, number>;
  by_year: { report_year: number; omb_pub_date: string; verdicts: Record<OmbVerdict, number> }[];
  /** Distinct budget lines among the matched (report year, line) pairs. */
  distinct_lines: number;
  /**
   * Council rows in a compared report year on a budget line outside the Council series (D, DN):
   * the comparison leaves them out, so the answer lists them (red team S2: FY2021 PW MN02A).
   * Filtered by report_year and budget_line like the comparison; empty when a verdict is asked for.
   */
  not_compared: { report_year: number; budget_line_norm: string; sponsor: string; title: string; amount: number | null; amount_fy: number | null }[];
}

export function compareCapitalToOmb(f: OmbComparisonFilters): OmbComparisonResult {
  const p: unknown[] = [];
  const w = where([
    eqClause("report_year", p, f.report_year),
    f.budget_line != null ? (p.push(f.budget_line), "budget_line_norm = ?") : null,
    f.verdict != null ? (p.push(f.verdict), "verdict = ?") : null,
  ]);
  const db = getDb();
  // Lines that disagree first, then the largest absolute first-year difference.
  const rows = db
    .prepare(
      `SELECT * FROM capital_vs_omb ${w}
       ORDER BY verdict = 'match', ABS(COALESCE(council_y1, 0) - COALESCE(omb_y1, 0)) DESC, report_year, budget_line_norm
       LIMIT ${cap(f.limit)}`
    )
    .all(...p) as OmbComparisonRow[];
  const g = db
    .prepare(
      `SELECT report_year, omb_pub_date, verdict, COUNT(*) AS n FROM capital_vs_omb ${w}
       GROUP BY report_year, omb_pub_date, verdict ORDER BY report_year`
    )
    .all(...p) as { report_year: number; omb_pub_date: string; verdict: OmbVerdict; n: number }[];
  const zero = (): Record<OmbVerdict, number> => ({ match: 0, differ: 0, council_only: 0, omb_only: 0 });
  const verdicts = zero();
  const years = new Map<number, { report_year: number; omb_pub_date: string; verdicts: Record<OmbVerdict, number> }>();
  let matched = 0;
  for (const r of g) {
    const y = years.get(r.report_year) ?? { report_year: r.report_year, omb_pub_date: r.omb_pub_date, verdicts: zero() };
    y.verdicts[r.verdict] += r.n;
    years.set(r.report_year, y);
    verdicts[r.verdict] += r.n;
    matched += r.n;
  }
  const distinct_lines = (db
    .prepare(`SELECT COUNT(DISTINCT budget_line_norm) AS n FROM capital_vs_omb ${w}`)
    .get(...p) as { n: number }).n;
  const q: unknown[] = [];
  const wn = where([
    "report_year IN (SELECT DISTINCT report_year FROM capital_vs_omb)",
    "budget_line_norm <> ''",
    "substr(budget_line_norm, instr(budget_line_norm, ' ') + 1) NOT LIKE 'D%'",
    eqClause("report_year", q, f.report_year),
    f.budget_line != null ? (q.push(f.budget_line), "budget_line_norm = ?") : null,
  ]);
  const not_compared =
    f.verdict != null
      ? []
      : (db
          .prepare(
            `SELECT report_year, budget_line_norm, sponsor, title, amount, amount_fy FROM capital_council ${wn}
             ORDER BY report_year, budget_line_norm, seq`
          )
          .all(...q) as OmbComparisonResult["not_compared"]);
  return { rows, matched, verdicts, by_year: [...years.values()], distinct_lines, not_compared };
}

/** Report years present in the comparison. */
export function listOmbComparisonYears(): number[] {
  return (getDb()
    .prepare(`SELECT DISTINCT report_year FROM capital_vs_omb ORDER BY report_year`)
    .all() as { report_year: number }[]).map((r) => r.report_year);
}

/** Build metadata (built_at, inputs, counts). */
export function getMeta(key: string): string | null {
  const r = getDb().prepare(`SELECT value FROM meta WHERE key = ?`).get(key) as { value: string } | undefined;
  return r ? r.value : null;
}
