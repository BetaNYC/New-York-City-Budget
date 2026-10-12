/**
 * SQLite-backed query layer for the NYC budget MCP.
 *
 * The database (data/budget.db) is built by scripts/build-index.mjs from the
 * committed CSV snapshot. This module opens it read-only and exposes one
 * function per tool. All text filters use case-insensitive substring (LIKE)
 * matching; EIN filters are normalized to digits-only so "13-2612524" and
 * "132612524" both match.
 */
import Database from "better-sqlite3";
import type { Database as DB } from "better-sqlite3";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "..", "data", "budget.db");

let _db: DB | null = null;

export function getDb(): DB {
  if (_db) return _db;
  if (!existsSync(DB_PATH)) {
    throw new Error(
      `Budget index not found at ${DB_PATH}. Run: npm run build-index`
    );
  }
  _db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
  return _db;
}

/** Digits-only EIN so "13-2612524" and "132612524" match. */
export function normEin(v: string): string {
  return (v ?? "").replace(/\D/g, "");
}

function likeClause(column: string, params: unknown[], value?: string): string | null {
  if (value == null || value.trim() === "") return null;
  params.push(`%${value.trim()}%`);
  return `${column} LIKE ? COLLATE NOCASE`;
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

// ---------------------------------------------------------------------------
// Row shapes
// ---------------------------------------------------------------------------

export interface AwardRow {
  fiscal_year: number;
  category: string;
  initiative: string;
  award_type: string;
  member: string;
  organization: string;
  program: string;
  ein: string;
  amount: number | null;
  agency: string;
  purpose: string;
  /**
   * Which Schedule C source the row came from — 'schedule_c' (the main-body award
   * tables) or 'appendix' (the aging/local/youth per-recipient breakouts). Added in
   * 1.4.0; before that the table held main-body rows only, so every published total
   * from an earlier version is the 'schedule_c' slice of what these tools now return.
   */
  source_table: string;
  /** 'aging' | 'local' | 'youth' for appendix rows; '' for main-body rows. */
  appendix_stream: string;
}

export interface TransparencyRow {
  source_fy: number;
  resolution: string;
  date: string;
  chart: string;
  fiscal_year: number | null;
  action: string;
  council_member: string;
  organization: string;
  program: string;
  ein: string;
  amount: number | null;
  agency: string;
  purpose: string;
  low_text_confidence: number;
}

export interface CapitalRow {
  fiscal_year: number;
  agency: string;
  budget_line: string;
  sub_id: string;
  boro: string;
  fy1: number | null;
  sponsor: string;
  title: string;
  action: string;
}

export interface TermRow {
  fiscal_year: number;
  item_number: string;
  agency_name: string;
  agency_code: string;
  units_of_appropriation: string;
  report_deadlines: string;
  coverage_period: string;
  condition_text: string;
}

export interface CrosswalkRow {
  fiscal_year: number | null;
  document_type: string;
  local_file: string;
  legistar_matter_number: string;
  legistar_url: string;
  adoption_date: string;
  status: string;
  notes: string;
  // Adopting City Council session — precomputed by scripts/enrich-crosswalk.mjs.
  // adopting_event_id is the OData EventId of the meeting where the matter was
  // adopted; it builds a WORKING Legistar link (see buildMeetingUrl). Empty when
  // no confirmed City Council adoption event exists for the row.
  adopting_event_id: string;
  adopting_body: string;
  adopting_action: string;
  adopting_datetime: string;
}

/**
 * Build a WORKING public Legistar link for an adopting meeting from its OData
 * EventId. Returns null for an empty/absent id (no link is better than a wrong one).
 *
 * The *meeting* URL scheme accepts the OData EventId; the *legislation* scheme
 * does NOT accept the OData MatterId (LegislationDetail.aspx?ID={MatterId}
 * resolves to "Invalid parameters!" — NYC runs two Legistar backends with
 * different ids and no formula between them). GID=61 is a verified term-stable
 * constant (resolves meetings 2007–2026). See issue #31.
 */
export function buildMeetingUrl(eventId: string | number | null | undefined): string | null {
  const id = eventId == null ? "" : String(eventId).trim();
  if (!id) return null;
  return `https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID=${id}&GID=61`;
}

// ---------------------------------------------------------------------------
// Tool query functions
// ---------------------------------------------------------------------------

export interface AwardFilters {
  ein?: string;
  organization?: string;
  program?: string;
  council_member?: string;
  fiscal_year?: number;
  category?: string;
  initiative?: string;
  /** 'schedule_c' | 'appendix'. Omitted = BOTH (see the note on sourceClause). */
  source_table?: string;
  limit?: number;
}

/**
 * The 1.4.0 behavior switch, in one place.
 *
 * Omitting `source_table` returns main-body AND appendix rows. That is a deliberate
 * default: the appendix rows are real designations (independently confirmed against the
 * Council's own published disclosure spreadsheet), and defaulting them off would have kept
 * 28,575 of them invisible — the bug this release fixes. The cost is that award counts and
 * dollar totals from these tools no longer match figures published from v1.3.x and earlier.
 *
 * Passing source_table='schedule_c' reproduces the pre-1.4.0 result set EXACTLY, which is the
 * cheap escape hatch if the default turns out to be the wrong call.
 */
function sourceClause(params: unknown[], value?: string): string | null {
  if (value == null || value.trim() === "") return null;
  params.push(value.trim());
  return `source_table = ?`;
}

export function searchAwards(f: AwardFilters): AwardRow[] {
  const p: unknown[] = [];
  const sql = `SELECT * FROM awards ${where([
    f.ein ? (p.push(normEin(f.ein)), "ein = ?") : null,
    likeClause("organization", p, f.organization),
    likeClause("program", p, f.program),
    likeClause("member", p, f.council_member),
    eqClause("fiscal_year", p, f.fiscal_year),
    likeClause("category", p, f.category),
    likeClause("initiative", p, f.initiative),
    sourceClause(p, f.source_table),
  ])} ORDER BY fiscal_year, amount DESC, member LIMIT ${cap(f.limit)}`;
  return getDb().prepare(sql).all(...p) as AwardRow[];
}

export function getAwardsByEin(ein: string, fiscalYear?: number, sourceTable?: string): AwardRow[] {
  const p: unknown[] = [normEin(ein)];
  const extra = [
    fiscalYear != null ? (p.push(fiscalYear), "fiscal_year = ?") : null,
    sourceClause(p, sourceTable),
  ].filter((c): c is string => c !== null);
  const sql = `SELECT * FROM awards WHERE ein = ?${
    extra.length ? ` AND ${extra.join(" AND ")}` : ""
  } ORDER BY fiscal_year, member, amount DESC`;
  return getDb().prepare(sql).all(...p) as AwardRow[];
}

export interface TransparencyFilters {
  ein?: string;
  council_member?: string;
  fiscal_year?: number;
  action?: string;
  organization?: string;
  limit?: number;
}

export function searchTransparency(f: TransparencyFilters): TransparencyRow[] {
  const p: unknown[] = [];
  // `fiscal_year` filters `source_fy` — the resolution document's fiscal year (the reliable,
  // always-present axis). The embedded row-level `fiscal_year` (designation year) is returned in
  // every row but is often blank in FY2010–FY2013, so it is not the filter key. See DATA-ANOMALIES #11.
  const sql = `SELECT source_fy, resolution, date, chart, fiscal_year, action, council_member,
      organization, program, ein, amount, agency, purpose, low_text_confidence
    FROM transparency ${where([
      f.ein ? (p.push(normEin(f.ein)), "ein = ?") : null,
      likeClause("council_member", p, f.council_member),
      eqClause("source_fy", p, f.fiscal_year),
      f.action ? (p.push(f.action), "action = ? COLLATE NOCASE") : null,
      likeClause("organization", p, f.organization),
    ])} ORDER BY source_fy, resolution, chart LIMIT ${cap(f.limit)}`;
  return getDb().prepare(sql).all(...p) as TransparencyRow[];
}

export interface CapitalFilters {
  agency?: string;
  fiscal_year?: number;
  sponsor?: string;
  title?: string;
  limit?: number;
}

export function searchCapital(f: CapitalFilters): CapitalRow[] {
  const p: unknown[] = [];
  const sql = `SELECT fiscal_year, agency, budget_line, sub_id, boro, fy1, sponsor, title, action
    FROM capital ${where([
      likeClause("agency", p, f.agency),
      eqClause("fiscal_year", p, f.fiscal_year),
      likeClause("sponsor", p, f.sponsor),
      likeClause("title", p, f.title),
    ])} ORDER BY fiscal_year, agency, fy1 DESC LIMIT ${cap(f.limit)}`;
  return getDb().prepare(sql).all(...p) as CapitalRow[];
}

export interface TermFilters {
  fiscal_year?: number;
  agency?: string;
  limit?: number;
}

export function getTerms(f: TermFilters): TermRow[] {
  const p: unknown[] = [];
  const sql = `SELECT fiscal_year, item_number, agency_name, agency_code,
      units_of_appropriation, report_deadlines, coverage_period, condition_text
    FROM terms ${where([
      eqClause("fiscal_year", p, f.fiscal_year),
      likeClause("agency_name", p, f.agency),
    ])} ORDER BY fiscal_year, agency_name, item_number LIMIT ${cap(f.limit)}`;
  return getDb().prepare(sql).all(...p) as TermRow[];
}

export interface LegistarFilters {
  fiscal_year?: number;
  document_type?: string;
  local_file?: string;
}

export function getLegistarLink(f: LegistarFilters): CrosswalkRow[] {
  const p: unknown[] = [];
  const sql = `SELECT * FROM crosswalk ${where([
    eqClause("fiscal_year", p, f.fiscal_year),
    // document_type match is a prefix-ish LIKE so "transparency_reso" catches the
    // per-resolution rows (transparency_reso_01 …) as well as the umbrella row.
    likeClause("document_type", p, f.document_type),
    likeClause("local_file", p, f.local_file),
  ])} ORDER BY fiscal_year DESC, document_type`;
  return getDb().prepare(sql).all(...p) as CrosswalkRow[];
}

export interface FiscalYearReport {
  awards: number[];
  /** Years that actually have appendix rows — a SUBSET of `awards`, not extra years. */
  awards_appendix: number[];
  terms: number[];
  capital: number[];
  transparency: number[];
  crosswalk: { min: number; max: number };
}

export function listFiscalYears(): FiscalYearReport {
  const db = getDb();
  const distinct = (table: string): number[] =>
    (db
      .prepare(`SELECT DISTINCT fiscal_year FROM ${table} WHERE fiscal_year IS NOT NULL ORDER BY fiscal_year`)
      .all() as { fiscal_year: number }[]).map((r) => r.fiscal_year);
  const cwRange = db
    .prepare(`SELECT MIN(fiscal_year) AS min, MAX(fiscal_year) AS max FROM crosswalk WHERE fiscal_year IS NOT NULL`)
    .get() as { min: number; max: number };
  // Transparency coverage is reported by source_fy (the resolution document year) — the reliable
  // per-year axis. The embedded row-level fiscal_year is blank for most FY2010–FY2013 rows, so
  // DISTINCT on it would misreport coverage (DATA-ANOMALIES #11).
  const transparency = (db
    .prepare(`SELECT DISTINCT source_fy AS fiscal_year FROM transparency WHERE source_fy IS NOT NULL ORDER BY source_fy`)
    .all() as { fiscal_year: number }[]).map((r) => r.fiscal_year);
  const awardsAppendix = (db
    .prepare(`SELECT DISTINCT fiscal_year FROM awards WHERE source_table = 'appendix' ORDER BY fiscal_year`)
    .all() as { fiscal_year: number }[]).map((r) => r.fiscal_year);
  return {
    awards: distinct("awards"),
    awards_appendix: awardsAppendix,
    terms: distinct("terms"),
    capital: distinct("capital"),
    transparency,
    crosswalk: cwRange,
  };
}

// ---------------------------------------------------------------------------
// Council expense funding disclosure (v1.5.0) — a separate source from `awards`
// ---------------------------------------------------------------------------

export const DISCLOSURE_STATUSES = ["cleared", "pending", "other"] as const;
export type DisclosureStatus = (typeof DISCLOSURE_STATUSES)[number];

export interface DisclosureRow {
  fiscal_year: number;
  /** MOCS ID# — FY2024+ only; "" before. Can change between snapshots for the same designation. */
  mocs_id: string;
  /** Funding stream as the workbook names it: Local, Youth, Aging, Speaker's Initiative, or a citywide initiative. */
  source: string;
  /** The Council's roster when the workbook was exported — not the sponsoring member at adoption. */
  council_member: string;
  legal_name: string;
  ein: string;
  /** Raw Status cell, verbatim (case varies by year). */
  status: string;
  status_norm: DisclosureStatus;
  /** The workbook's own value; can be fractional. */
  amount: number;
  agency: string;
  program_name: string;
  fiscal_conduit: string;
  fiscal_conduit_ein: string;
  /** Row number in the workbook (and in data/fyNN/expense_disclosure/fyNN_expense_awards.csv). */
  source_row: number;
}

export interface DisclosureFilters {
  fiscal_year?: number;
  ein?: string;
  legal_name?: string;
  council_member?: string;
  source?: string;
  agency?: string;
  program_name?: string;
  status?: DisclosureStatus;
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

export interface DisclosureSnapshot {
  fiscal_year: number;
  file: string;
  /** Sheet name; the Council stamps its own "last updated" date into it, e.g. "FY26 (09-14-26)". */
  sheet: string;
  /** Date BetaNYC downloaded this exact file (MANIFEST.csv). */
  retrieved: string;
  sha256: string;
}

export interface DisclosureTotal {
  rows: number;
  amount: number;
}

/** One distinct value a substring filter matched, with its share of the match. */
export interface DisclosureValueCount {
  value: string;
  rows: number;
  amount: number;
}

export interface DisclosureResult {
  /** The page: at most `limit` rows, highest amount first. */
  rows: DisclosureRow[];
  /** Every row matching the filters — the page may be shorter. */
  matched: number;
  /** Totals over ALL matches (never over the page), per status. */
  totals: Record<DisclosureStatus, DisclosureTotal>;
  /** Totals over ALL matches, per fiscal year and status. */
  by_year: { fiscal_year: number; totals: Record<DisclosureStatus, DisclosureTotal> }[];
  /** Snapshot provenance for every year in the match (or the filtered year, if nothing matched). */
  snapshots: DisclosureSnapshot[];
  /**
   * For each substring filter given (council_member, source, agency), the distinct values it
   * matched -- so 'Levin' matching Levin AND Levine, or 'Youth' matching the Youth stream AND
   * 'Summer Youth Employment Program', is visible instead of silently summed (#51).
   */
  matched_values: Partial<Record<"council_member" | "source" | "agency", DisclosureValueCount[]>>;
  /** Distinct grantee legal names among the matches, when an EIN was given. */
  ein_legal_names?: number;
}

/**
 * Case-insensitive substring match with LIKE's wildcards taken literally: a filter of "_" or
 * "100%" means those characters, not "any one character" / "anything" (legal_name "_" used to
 * match all 139,556 rows).
 */
function likeLiteral(column: string, params: unknown[], value?: string): string | null {
  if (value == null || value.trim() === "") return null;
  params.push(`%${value.trim().replace(/[\\%_]/g, (c) => "\\" + c)}%`);
  return `${column} LIKE ? ESCAPE '\\' COLLATE NOCASE`;
}

const emptyTotals = (): Record<DisclosureStatus, DisclosureTotal> => ({
  cleared: { rows: 0, amount: 0 },
  pending: { rows: 0, amount: 0 },
  other: { rows: 0, amount: 0 },
});

/**
 * Search the disclosure. The WHERE clause is built once and used three times — for the page,
 * for the totals and for the per-year split — so the totals always describe exactly the rows the
 * filters select, however many of them the page leaves out (issues #42, #49).
 */
export function searchDisclosure(f: DisclosureFilters): DisclosureResult {
  const p: unknown[] = [];
  const w = where([
    eqClause("fiscal_year", p, f.fiscal_year),
    f.ein ? (p.push(normEin(f.ein)), "ein = ?") : null,
    likeLiteral("legal_name", p, f.legal_name),
    likeLiteral("council_member", p, f.council_member),
    likeLiteral("source", p, f.source),
    likeLiteral("agency", p, f.agency),
    likeLiteral("program_name", p, f.program_name),
    f.status ? (p.push(f.status), "status_norm = ?") : null,
    f.min_amount != null ? (p.push(f.min_amount), "amount >= ?") : null,
    f.max_amount != null ? (p.push(f.max_amount), "amount <= ?") : null,
  ]);
  const db = getDb();
  // Highest amount first BEFORE the limit (as in #41); the remaining keys only make ties
  // deterministic.
  const rows = db
    .prepare(
      `SELECT fiscal_year, mocs_id, source, council_member, legal_name, ein, status, status_norm,
         amount, agency, program_name, fiscal_conduit, fiscal_conduit_ein, source_row
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
          `SELECT fiscal_year, file, sheet, retrieved, sha256 FROM disclosure_snapshots
           WHERE fiscal_year IN (${snapYears.map(() => "?").join(",")}) ORDER BY fiscal_year`
        )
        .all(...snapYears) as DisclosureSnapshot[])
    : [];

  const matched_values: DisclosureResult["matched_values"] = {};
  for (const col of ["council_member", "source", "agency"] as const) {
    if (f[col] == null || f[col]!.trim() === "") continue;
    matched_values[col] = db
      .prepare(
        `SELECT ${col} AS value, COUNT(*) AS rows, SUM(amount) AS amount FROM disclosure ${w}
         GROUP BY ${col} ORDER BY rows DESC, value`
      )
      .all(...p) as DisclosureValueCount[];
  }
  const ein_legal_names = f.ein
    ? (db.prepare(`SELECT COUNT(DISTINCT legal_name) AS n FROM disclosure ${w}`).get(...p) as { n: number }).n
    : undefined;

  return {
    rows,
    matched,
    totals,
    by_year: [...years.entries()].map(([fiscal_year, t]) => ({ fiscal_year, totals: t })),
    snapshots,
    matched_values,
    ein_legal_names,
  };
}

/** Years the disclosure index covers, with their snapshot provenance. */
export function listDisclosureSnapshots(): DisclosureSnapshot[] {
  return getDb()
    .prepare(
      `SELECT fiscal_year, file, sheet, retrieved, sha256 FROM disclosure_snapshots ORDER BY fiscal_year`
    )
    .all() as DisclosureSnapshot[];
}
