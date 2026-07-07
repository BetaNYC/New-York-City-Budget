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
}

export interface TransparencyRow {
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
  limit?: number;
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
  ])} ORDER BY fiscal_year, member, amount DESC LIMIT ${cap(f.limit)}`;
  return getDb().prepare(sql).all(...p) as AwardRow[];
}

export function getAwardsByEin(ein: string, fiscalYear?: number): AwardRow[] {
  const p: unknown[] = [normEin(ein)];
  const sql = `SELECT * FROM awards WHERE ein = ? ${
    fiscalYear != null ? (p.push(fiscalYear), "AND fiscal_year = ?") : ""
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
  const sql = `SELECT resolution, date, chart, fiscal_year, action, council_member,
      organization, program, ein, amount, agency, purpose
    FROM transparency ${where([
      f.ein ? (p.push(normEin(f.ein)), "ein = ?") : null,
      likeClause("council_member", p, f.council_member),
      eqClause("fiscal_year", p, f.fiscal_year),
      f.action ? (p.push(f.action), "action = ? COLLATE NOCASE") : null,
      likeClause("organization", p, f.organization),
    ])} ORDER BY resolution, chart LIMIT ${cap(f.limit)}`;
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
  return {
    awards: distinct("awards"),
    terms: distinct("terms"),
    capital: distinct("capital"),
    transparency: distinct("transparency"),
    crosswalk: cwRange,
  };
}
