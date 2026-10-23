/**
 * Queries over the checked PDF tables (GitHub #212): Schedule C, the transparency resolutions,
 * the capital §254 supporting detail ("the capital book") and Terms and Conditions, read from the
 * optional download (src/pdfdata.ts). One function per tool, like db.ts.
 *
 * The serving rules (#190, research/2026-10-22-mcp-pdf-tables/PLAN.md), enforced here for every
 * row, whatever the file holds:
 *   - only family-years data/pdf_years.csv lists as `reviewed` or `closed`, and only rows whose
 *     own status is the one pdf_years gives their family-year (SERVED, below). The old parser's
 *     output is never in these tables (scripts/pdf-families.mjs reads data/fyNN/pdf/ only), and
 *     the years only it covers (FY2008–FY2017) answer "not available yet".
 *   - values as printed; every row carries its status label, flags, review entries (decision and
 *     note where decided), and its links (src/rowlinks.ts), built from the commit the tables were
 *     built from, never a branch.
 *   - a "no dollar amount" row (amount NULL) is never in a sum; COUNT(amount) and SUM(amount)
 *     skip it, and the answer counts it separately.
 *
 * Text filters are case- and accent-insensitive substrings on the same columns the explorer
 * searches (viz/explorer/src/query/pdf.js), folded with src/fold.ts on both sides (the fold() SQL
 * function pdfdata.ts registers). LIKE wildcards are not used, so % and _ are literal.
 */
import type { Database as DB } from "better-sqlite3";
import { fold } from "./fold.js";
import { rowLinks, type RowLinks } from "./rowlinks.js";
import { localPdfPath } from "./pdfdata.js";
import { existsSync } from "fs";

export const STATUS_LABEL: Record<string, string> = {
  reviewed: "checked, review in progress",
  closed: "checked and reviewed",
};
export const HIDDEN_TEXT_LABEL = "hidden text, not visible on the printed page";
export const PDF_FAMILY_LABEL: Record<string, string> = {
  schedule_c: "Schedule C",
  transparency: "Transparency resolutions",
  capital_sd: "Capital §254 supporting detail (the capital book)",
  terms: "Terms and Conditions",
};

/** A row may be served only when its family-year is listed and its status is the listed one. */
const SERVED = (alias: string, family: string) =>
  `${alias}.status IN ('reviewed', 'closed') AND EXISTS (SELECT 1 FROM pdf_years y WHERE y.fiscal_year = ${alias}.fiscal_year AND y.family = '${family}' AND y.status = ${alias}.status)`;

class Where {
  clauses: string[] = [];
  params: unknown[] = [];
  add(c: string, ...p: unknown[]) {
    this.clauses.push(c);
    this.params.push(...p);
  }
  /** Substring in any of `cols`, folded on both sides. */
  text(cols: string[], v?: string) {
    if (v == null) return;
    const q = fold(v);
    if (q === "") throw new Error(`a text filter is empty; omit it, or give a value.`);
    this.add(`(${cols.map((c) => `instr(fold(${c}), ?) > 0`).join(" OR ")})`, ...cols.map(() => q));
  }
  eq(c: string, v: unknown) {
    if (v == null) return;
    this.add(`${c} = ?`, v);
  }
  sql() {
    return this.clauses.length ? `WHERE ${this.clauses.join(" AND ")}` : "";
  }
}

const cap = (limit: number | undefined, def: number, max: number) =>
  limit == null || Number.isNaN(limit) ? def : Math.min(Math.max(1, Math.trunc(limit)), max);

export type Row = Record<string, any>;

// ---------------------------------------------------------------- shared per-row parts

export interface ReviewEntry {
  review_id: string;
  check_id: string;
  severity: string;
  note: string;
  decision: string;
  decision_note: string;
  suggested_decision: string;
  suggested_note: string;
  /** The date the question was sent to Council Finance, where recorded (`detail.question_sent`). */
  question_sent: string | null;
}

export interface ServedRow {
  row: Row;
  status_label: string;
  reviews: ReviewEntry[];
  links: RowLinks;
  /** The downloaded PDF's path on this machine (download --pdfs), or null. */
  local_pdf: string | null;
}

/** pdf_review entries (with their suggestion) for the page's rows, keyed "fy|family|review_id". */
function reviewsFor(db: DB, family: string, rows: Row[]): Map<string, ReviewEntry> {
  const ids = [...new Set(rows.flatMap((r) => String(r.review_id ?? "").split(";").map((s) => s.trim()).filter(Boolean)))];
  const out = new Map<string, ReviewEntry>();
  for (let i = 0; i < ids.length; i += 500) {
    const chunk = ids.slice(i, i + 500);
    const got = db
      .prepare(
        `SELECT r.fiscal_year, r.review_id, r.check_id, r.severity, r.note, r.detail, r.decision, r.decision_note,
           COALESCE(s.suggested_decision, '') AS suggested_decision, COALESCE(s.suggested_note, '') AS suggested_note
         FROM pdf_review r LEFT JOIN pdf_review_suggestions s
           ON s.fiscal_year = r.fiscal_year AND s.family = r.family AND s.review_id = r.review_id
         WHERE r.family = ? AND r.review_id IN (${chunk.map(() => "?").join(",")})`
      )
      .all(family, ...chunk) as Row[];
    for (const g of got) {
      let sent: string | null = null;
      try {
        const d = g.detail ? JSON.parse(g.detail) : {};
        sent = typeof d.question_sent === "string" && /^\d{4}-\d{2}-\d{2}$/.test(d.question_sent) ? d.question_sent : null;
      } catch {
        sent = null;
      }
      out.set(`${g.fiscal_year}|${family}|${g.review_id}`, {
        review_id: g.review_id, check_id: g.check_id, severity: g.severity, note: g.note ?? "",
        decision: g.decision ?? "", decision_note: g.decision_note ?? "",
        suggested_decision: g.suggested_decision, suggested_note: g.suggested_note, question_sent: sent,
      });
    }
  }
  return out;
}

/** Attach the status label, review entries, links and local PDF to each row. */
function serve(db: DB, family: string, rows: Row[], commit: string, label: (r: Row) => string): ServedRow[] {
  const rev = reviewsFor(db, family, rows);
  return rows.map((row) => {
    const ids = String(row.review_id ?? "").split(";").map((s) => s.trim()).filter(Boolean);
    const local = localPdfPath(String(row.source_pdf ?? ""));
    return {
      row,
      status_label: STATUS_LABEL[row.status] ?? `unknown status ${row.status}`,
      reviews: ids.flatMap((id) => rev.get(`${row.fiscal_year}|${family}|${id}`) ?? []),
      links: rowLinks(row, { label: label(row), commit }),
      local_pdf: local && existsSync(local) ? local : null,
    };
  });
}

const DAY = 86_400_000;

/**
 * The words for a `needs_info` decision (PLAN.md "What closed means", rule 3): an open question
 * to Council Finance. Once 30 days have passed since it was sent, the row is published as printed
 * with the sent date; with no sent date recorded, it is plainly an open question.
 */
export function needsInfoLabel(sent: string | null, today: Date = new Date()): string {
  if (!sent) return "needs more information: an open question to Council Finance (no date sent is recorded yet); published as printed";
  const days = Math.floor((today.getTime() - Date.parse(`${sent}T00:00:00Z`)) / DAY);
  return days >= 30
    ? `Question sent to Council Finance on ${sent}, no answer yet; published as printed`
    : `needs more information: question sent to Council Finance on ${sent} (${days} day(s) ago), waiting for an answer; published as printed`;
}

/** The pdf_years rows of a family: which years exist and at what status. */
export function familyYears(db: DB, family: string): { fiscal_year: number; status: string; rows: number }[] {
  return db
    .prepare(`SELECT fiscal_year, status, rows FROM pdf_years WHERE family = ? AND status IN ('reviewed', 'closed') ORDER BY fiscal_year`)
    .all(family) as { fiscal_year: number; status: string; rows: number }[];
}

export interface StatusTotal {
  fiscal_year: number;
  status: string;
  rows: number;
}

// ---------------------------------------------------------------- Schedule C

export const SC_DISCLOSURE_STATUSES = ["cleared", "pending", "unmatched"] as const;

export interface ScheduleCFilters {
  fiscal_year?: number;
  organization?: string;
  ein?: string;
  member?: string;
  category?: string;
  initiative?: string;
  agency?: string;
  purpose?: string;
  disclosure_status?: (typeof SC_DISCLOSURE_STATUSES)[number];
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

function scWhere(f: ScheduleCFilters): Where {
  const w = new Where();
  w.add(SERVED("a", "schedule_c"));
  w.eq("a.fiscal_year", f.fiscal_year);
  w.text(["a.org"], f.organization);
  if (f.ein != null) w.eq("a.ein", f.ein.replace(/\D/g, ""));
  w.text(["a.member", "a.sponsor"], f.member);
  w.text(["a.category"], f.category);
  w.text(["a.initiative"], f.initiative);
  w.text(["a.agency"], f.agency);
  w.text(["a.purpose"], f.purpose);
  w.eq("a.disclosure_status", f.disclosure_status);
  if (f.min_amount != null) w.add("a.amount >= ?", f.min_amount);
  if (f.max_amount != null) w.add("a.amount <= ?", f.max_amount);
  return w;
}

export interface ScheduleCResult {
  rows: ServedRow[];
  matched: number;
  /** Rows with an amount, and their sum. Rows without one are `no_amount`, in no sum. */
  with_amount: number;
  amount: number;
  no_amount: number;
  by_year: (StatusTotal & { amount: number })[];
  by_disclosure: { disclosure_status: string; rows: number; amount: number }[];
  /** Sub-awards (a list under one award saying who it passes money to) of the rows shown. */
  subawards: Map<string, Row[]>;
  /** Sub-awards whose own organization matches the organization filter (never in a total). */
  subaward_matches: { rows: number; amount: number };
}

export function searchScheduleC(db: DB, commit: string, f: ScheduleCFilters): ScheduleCResult {
  const w = scWhere(f);
  const rows = db
    .prepare(`SELECT a.* FROM pdf_schedule_c a ${w.sql()} ORDER BY a.amount IS NULL, a.amount DESC, a.fiscal_year, a.award_id LIMIT ${cap(f.limit, 50, 500)}`)
    .all(...w.params) as Row[];
  const by_year = db
    .prepare(
      `SELECT a.fiscal_year, a.status, COUNT(*) AS rows, COALESCE(SUM(a.amount), 0) AS amount
       FROM pdf_schedule_c a ${w.sql()} GROUP BY 1, 2 ORDER BY 1`
    )
    .all(...w.params) as (StatusTotal & { amount: number })[];
  const t = db
    .prepare(`SELECT COUNT(*) AS n, COUNT(a.amount) AS with_amount, COALESCE(SUM(a.amount), 0) AS amount FROM pdf_schedule_c a ${w.sql()}`)
    .get(...w.params) as { n: number; with_amount: number; amount: number };
  const by_disclosure = db
    .prepare(
      `SELECT a.disclosure_status, COUNT(*) AS rows, COALESCE(SUM(a.amount), 0) AS amount FROM pdf_schedule_c a ${w.sql()}
       GROUP BY 1 ORDER BY rows DESC`
    )
    .all(...w.params) as ScheduleCResult["by_disclosure"];
  const subawards = new Map<string, Row[]>();
  for (const r of rows) {
    const subs = db
      .prepare(`SELECT * FROM pdf_schedule_c_subawards WHERE fiscal_year = ? AND parent_award_id = ? ORDER BY row_index`)
      .all(r.fiscal_year, r.award_id) as Row[];
    if (subs.length) subawards.set(`${r.fiscal_year}|${r.award_id}`, subs);
  }
  let subaward_matches = { rows: 0, amount: 0 };
  if (f.organization != null) {
    const s = new Where();
    s.add(SERVED("s", "schedule_c"));
    s.eq("s.fiscal_year", f.fiscal_year);
    s.text(["s.org"], f.organization);
    if (f.ein != null) s.eq("s.ein", f.ein.replace(/\D/g, ""));
    subaward_matches = db
      .prepare(`SELECT COUNT(*) AS rows, COALESCE(SUM(s.amount), 0) AS amount FROM pdf_schedule_c_subawards s ${s.sql()}`)
      .get(...s.params) as { rows: number; amount: number };
  }
  const usd = (v: unknown) => (typeof v === "number" ? `$${v.toLocaleString("en-US")}` : "no amount");
  return {
    rows: serve(db, "schedule_c", rows, commit, (r) => `${r.org}, ${usd(r.amount)}`),
    matched: t.n,
    with_amount: t.with_amount,
    amount: t.amount,
    no_amount: t.n - t.with_amount,
    by_year,
    by_disclosure,
    subawards,
    subaward_matches,
  };
}

// ---------------------------------------------------------------- transparency resolutions

export const TR_ACTIONS = ["designate", "rescind", "purpose_from", "purpose_to", "listed"] as const;

export interface TransparencyFilters {
  fiscal_year?: number;
  budget_fiscal_year?: number;
  organization?: string;
  ein?: string;
  member?: string;
  resolution_number?: string;
  resolution_date?: string;
  action?: (typeof TR_ACTIONS)[number];
  limit?: number;
}

function trWhere(f: TransparencyFilters): Where {
  const w = new Where();
  w.add(SERVED("t", "transparency"));
  w.eq("t.fiscal_year", f.fiscal_year);
  w.eq("t.budget_fiscal_year", f.budget_fiscal_year);
  w.text(["t.org"], f.organization);
  if (f.ein != null) w.eq("t.ein", f.ein.replace(/\D/g, ""));
  w.text(["t.member"], f.member);
  w.text(["t.resolution_number"], f.resolution_number);
  w.eq("t.resolution_date", f.resolution_date);
  w.eq("t.action", f.action);
  return w;
}

export interface TransparencyResult {
  rows: ServedRow[];
  matched: number;
  by_action: { action: string; rows: number; with_amount: number; amount: number }[];
  /** amount_kind = no_dollar_amount: a chart that prints no amount (Beating Hearts); in no sum. */
  no_dollar_amount: number;
  by_year: (StatusTotal & { amount: number })[];
  resolutions: { fiscal_year: number; resolution_number: string; resolution_date: string; rows: number }[];
}

export function searchTransparency(db: DB, commit: string, f: TransparencyFilters): TransparencyResult {
  const w = trWhere(f);
  const rows = db
    .prepare(
      `SELECT t.* FROM pdf_transparency t ${w.sql()}
       ORDER BY t.fiscal_year DESC, t.resolution_seq, t.chart_number, t.pdf_page, t.row_index LIMIT ${cap(f.limit, 50, 500)}`
    )
    .all(...w.params) as Row[];
  const by_action = db
    .prepare(
      `SELECT t.action, COUNT(*) AS rows, COUNT(t.amount) AS with_amount, COALESCE(SUM(t.amount), 0) AS amount
       FROM pdf_transparency t ${w.sql()} GROUP BY 1 ORDER BY 1`
    )
    .all(...w.params) as TransparencyResult["by_action"];
  const nd = db
    // w.sql() always starts with WHERE: the serving gate is always a clause.
    .prepare(`SELECT COUNT(*) AS n FROM pdf_transparency t ${w.sql()} AND t.amount_kind = 'no_dollar_amount'`)
    .get(...w.params) as { n: number };
  const by_year = db
    .prepare(`SELECT t.fiscal_year, t.status, COUNT(*) AS rows, COALESCE(SUM(t.amount), 0) AS amount FROM pdf_transparency t ${w.sql()} GROUP BY 1, 2 ORDER BY 1`)
    .all(...w.params) as TransparencyResult["by_year"];
  const resolutions = db
    .prepare(
      `SELECT t.fiscal_year, t.resolution_number, t.resolution_date, COUNT(*) AS rows FROM pdf_transparency t ${w.sql()}
       GROUP BY 1, 2, 3 ORDER BY 1 DESC, 3`
    )
    .all(...w.params) as TransparencyResult["resolutions"];
  const usd = (v: unknown) => (typeof v === "number" ? `${v < 0 ? "-" : ""}$${Math.abs(v).toLocaleString("en-US")}` : "no dollar amount");
  return {
    rows: serve(db, "transparency", rows, commit, (r) => `${r.org || r.agency || r.purpose || r.row_id}, ${usd(r.amount)}`),
    matched: by_action.reduce((s, a) => s + a.rows, 0),
    by_action,
    no_dollar_amount: nd.n,
    by_year,
    resolutions,
  };
}

// ---------------------------------------------------------------- capital book (§254 supporting detail)

export interface CapitalBookFilters {
  fiscal_year?: number;
  project_id?: string;
  budget_line?: string;
  sponsor?: string;
  borough?: string;
  agency?: string;
  title?: string;
  part?: "I" | "II";
  limit?: number;
}

function cbWhere(f: CapitalBookFilters): Where {
  const w = new Where();
  w.add(SERVED("c", "capital_sd"));
  w.eq("c.fiscal_year", f.fiscal_year);
  if (f.project_id != null) {
    const id = f.project_id.trim().replace(/\s+/g, " ").toUpperCase();
    // The book prints "HO CC0001"; the Council's workbooks "CC0001". Either form matches.
    if (id.includes(" ")) w.add("upper(c.sub_id) = ?", id);
    else w.add("substr(upper(c.sub_id), instr(c.sub_id, ' ') + 1) = ?", id);
  }
  w.eq("c.budget_line", f.budget_line);
  w.text(["c.sponsor"], f.sponsor);
  w.eq("c.boro", f.borough);
  w.text(["c.agency"], f.agency);
  w.text(["c.title"], f.title);
  w.eq("c.part", f.part);
  return w;
}

export interface CapitalBookResult {
  rows: ServedRow[];
  matched: number;
  /**
   * Sums of the four printed year columns over Part I rows only (y1 is the book's own fiscal year,
   * y2..y4 the next three). Part II reprints Part I rows (code/review_capital_sd.py check C3), so
   * adding it would count them twice; its rows are counted, never summed.
   */
  totals: { y1: number; y2: number; y3: number; y4: number };
  part_ii_rows: number;
  by_year: (StatusTotal & { y1: number })[];
}

export function searchCapitalBook(db: DB, commit: string, f: CapitalBookFilters): CapitalBookResult {
  const w = cbWhere(f);
  const rows = db
    .prepare(`SELECT c.* FROM pdf_capital_sd c ${w.sql()} ORDER BY c.amount_y1 IS NULL, c.amount_y1 DESC, c.fiscal_year, c.pdf_page, c.row_in_page LIMIT ${cap(f.limit, 50, 500)}`)
    .all(...w.params) as Row[];
  const totals = db
    .prepare(
      `SELECT COUNT(*) AS n, SUM(c.part = 'II') AS part_ii,
         ${[1, 2, 3, 4].map((k) => `COALESCE(SUM(CASE WHEN c.part = 'I' THEN c.amount_y${k} END), 0) AS y${k}`).join(", ")}
       FROM pdf_capital_sd c ${w.sql()}`
    )
    .get(...w.params) as { n: number; part_ii: number | null; y1: number; y2: number; y3: number; y4: number };
  const by_year = db
    .prepare(`SELECT c.fiscal_year, c.status, COUNT(*) AS rows, COALESCE(SUM(CASE WHEN c.part = 'I' THEN c.amount_y1 END), 0) AS y1 FROM pdf_capital_sd c ${w.sql()} GROUP BY 1, 2 ORDER BY 1`)
    .all(...w.params) as CapitalBookResult["by_year"];
  return {
    rows: serve(db, "capital_sd", rows, commit, (r) => `${r.sub_id} ${r.title}`.trim()),
    matched: totals.n,
    totals: { y1: totals.y1, y2: totals.y2, y3: totals.y3, y4: totals.y4 },
    part_ii_rows: totals.part_ii ?? 0,
    by_year,
  };
}

// ---------------------------------------------------------------- Terms and Conditions

export interface TermsFilters {
  fiscal_year?: number;
  agency?: string;
  unit?: string;
  text?: string;
  limit?: number;
}

/** The explorer's termsWhere (viz/explorer/src/query/pdf.js), with the serving gate. */
function termsWhere(f: TermsFilters): Where {
  const w = new Where();
  w.add(SERVED("pdf_terms", "terms"));
  w.eq("pdf_terms.fiscal_year", f.fiscal_year);
  w.text(["pdf_terms.agency_name", "pdf_terms.agency_code"], f.agency);
  w.text(["pdf_terms.condition_text", "pdf_terms.heading_raw"], f.text);
  if (f.unit != null) {
    // A unit as printed in the heading ("001", "All"), or the start of a budget line, which is
    // printed with its scope ("HD-0009 – All Projects").
    const u = f.unit.trim();
    w.add(
      `EXISTS (SELECT 1 FROM pdf_terms_units u WHERE u.fiscal_year = pdf_terms.fiscal_year AND u.item_number = pdf_terms.item_number
         AND (lower(u.unit_of_appropriation) = lower(?) OR substr(lower(u.budget_line), 1, length(?)) = lower(?)))`,
      u, u, u
    );
  }
  return w;
}

export interface TermsResult {
  rows: ServedRow[];
  matched: number;
  agencies: number;
  by_year: StatusTotal[];
}

export function searchTerms(db: DB, commit: string, f: TermsFilters): TermsResult {
  const w = termsWhere(f);
  const rows = db
    .prepare(`SELECT pdf_terms.* FROM pdf_terms ${w.sql()} ORDER BY pdf_terms.fiscal_year DESC, pdf_terms.item_number LIMIT ${cap(f.limit, 20, 100)}`)
    .all(...w.params) as Row[];
  const c = db
    .prepare(`SELECT COUNT(*) AS n, COUNT(DISTINCT agency_name) AS agencies FROM pdf_terms ${w.sql()}`)
    .get(...w.params) as { n: number; agencies: number };
  const by_year = db
    .prepare(`SELECT fiscal_year, status, COUNT(*) AS rows FROM pdf_terms ${w.sql()} GROUP BY 1, 2 ORDER BY 1`)
    .all(...w.params) as StatusTotal[];
  return {
    rows: serve(db, "terms", rows, commit, (r) => `Terms and Conditions item ${r.item_number}`),
    matched: c.n,
    agencies: c.agencies,
    by_year,
  };
}
