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
 * Filters follow the explorer's search rules (viz/explorer/src/query/pdf.js, PR #224) so the two
 * answer alike: the same columns per filter, an EIN matching the organization's or its fiscal
 * conduit's, the same row order, and the same totals. Text filters are case- and
 * accent-insensitive substrings, folded with src/fold.ts on both sides (the fold() SQL function
 * pdfdata.ts registers). LIKE wildcards are not used, so % and _ are literal. One difference from
 * the explorer (#259): a short term (3 or fewer letters and digits) matches whole words, through
 * the word_match() SQL function (src/textmatch.ts), unless the call passes whole_word: false.
 */
import type { Database as DB } from "better-sqlite3";
import { fold } from "./fold.js";
import { useWholeWord, type WordFilter } from "./textmatch.js";
import { rowLinks, type RowLinks } from "./rowlinks.js";
import { localPdfPath } from "./pdfdata.js";
import { plainReviewNote } from "./checkwords.js";
import { questionsByReviewId, type CouncilQuestion, type Part2Series } from "./questions.js";
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
  /** Filters matched as whole words (#259), for the answer's note. */
  words: WordFilter[] = [];
  /** The call's whole_word argument: undefined means the per-term default (src/textmatch.ts). */
  constructor(private wholeWord?: boolean) {}
  add(c: string, ...p: unknown[]) {
    this.clauses.push(c);
    this.params.push(...p);
  }
  /**
   * Filter `name`: a substring in any of `cols`, folded on both sides, or whole words there when
   * the term is short or whole_word is true (src/textmatch.ts).
   */
  text(name: string, cols: string[], v?: string) {
    if (v == null) return;
    const q = fold(v);
    if (q === "") throw new Error(`${name} is empty; omit it, or give a value.`);
    if (useWholeWord(v, this.wholeWord)) {
      this.words.push({ filter: name, value: v });
      this.add(`(${cols.map((c) => `word_match(${c}, ?)`).join(" OR ")})`, ...cols.map(() => q));
    } else {
      this.add(`(${cols.map((c) => `instr(fold(${c}), ?) > 0`).join(" OR ")})`, ...cols.map(() => q));
    }
  }
  /**
   * An identifier filter (project_id, resolution_number): always a folded substring, never the
   * whole-word default or whole_word (#259), because people search ID fragments ("CC1", "101").
   */
  id(name: string, cols: string[], v?: string) {
    if (v == null) return;
    const q = fold(v);
    if (q === "") throw new Error(`${name} is empty; omit it, or give a value.`);
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

// ---------------------------------------------------------------- council members (#51)

/**
 * How a printed `member` resolves, per (family, fiscal_year, printed name): the crosswalk
 * code/build_member_crosswalk.py builds with #72's rules (data/pdf_council_member_crosswalk.csv,
 * loaded into the npm index as member_crosswalk, so it works with any installed download).
 */
export interface MemberResolution {
  family: string;
  fiscal_year: number;
  council_member: string;
  rows: number;
  /** member, member_outside_fy, ambiguous, unresolved, speaker, delegation, citywide, district_label, blank. */
  type: string;
  /** Legistar person ID: only for member and member_outside_fy. */
  id: string;
  name: string;
  /** ambiguous only: the people it could be. */
  candidates: string[];
  method: string;
}

export class MemberCrosswalk {
  private byKey = new Map<string, MemberResolution>();
  /** Legistar person ID -> full name, from every resolved row. */
  readonly names = new Map<string, string>();
  constructor(readonly entries: MemberResolution[]) {
    for (const e of entries) {
      this.byKey.set(MemberCrosswalk.key(e.family, e.fiscal_year, e.council_member), e);
      if (e.id && e.name) this.names.set(e.id, e.name);
    }
  }
  private static key = (family: string, fy: number, printed: string) => `${family}|${fy}|${printed}`;
  /** A row's resolution, or null where the crosswalk has none (an older index). */
  of(family: string, fy: number, printed: unknown): MemberResolution | null {
    return this.byKey.get(MemberCrosswalk.key(family, fy, String(printed ?? ""))) ?? null;
  }
  /** The (year, printed name) pairs that resolve to `id` in a family. */
  pairs(family: string, id: string, fy?: number): MemberResolution[] {
    return this.entries.filter((e) => e.family === family && e.id === id && (fy == null || e.fiscal_year === fy));
  }
  /** The ambiguous (year, printed name) pairs that could be `id`: never counted for it. */
  maybe(family: string, id: string, fy?: number): MemberResolution[] {
    return this.entries.filter((e) => e.family === family && e.type === "ambiguous" && e.candidates.includes(id) && (fy == null || e.fiscal_year === fy));
  }
  person(id: string): string {
    const n = this.names.get(id);
    return n ? `${n} (Legistar person ${id})` : `Legistar person ${id}`;
  }
}

export const NO_MEMBERS = new MemberCrosswalk([]);

/** A printed name and the person it resolved to, with the rows the filter matched. */
export interface MatchedMember {
  council_member: string;
  type: string;
  id: string;
  name: string;
  candidates: string[];
  years: number[];
  rows: number;
  amount: number;
}

/**
 * The matched rows grouped by printed name and resolution, over (fiscal_year, printed name)
 * counts: 'Williams' is two people in different years, so it is two entries.
 */
function matchedMembers(family: string, members: MemberCrosswalk, counts: { fiscal_year: number; member: string; rows: number; amount: number }[]): MatchedMember[] {
  const out = new Map<string, MatchedMember>();
  for (const c of counts) {
    const m = members.of(family, c.fiscal_year, c.member);
    const type = m?.type ?? "unknown";
    const id = m?.id ?? "";
    const k = `${c.member}|${type}|${id}|${type === "ambiguous" ? m!.candidates.join(";") : ""}`;
    const e = out.get(k) ?? { council_member: c.member, type, id, name: m?.name ?? "", candidates: m?.candidates ?? [], years: [], rows: 0, amount: 0 };
    e.years.push(c.fiscal_year);
    e.rows += c.rows;
    e.amount += c.amount ?? 0;
    out.set(k, e);
  }
  return [...out.values()].map((e) => ({ ...e, years: [...new Set(e.years)].sort((a, b) => a - b) })).sort((a, b) => b.rows - a.rows || a.council_member.localeCompare(b.council_member));
}

/** council_member_id: the row's (fiscal_year, printed member) is one of the person's pairs. */
function memberIdClause(w: Where, alias: string, family: string, members: MemberCrosswalk, id?: string, fy?: number) {
  if (id == null) return;
  const pairs = members.pairs(family, id, fy);
  if (!pairs.length) return w.add("0");
  w.add(`(${pairs.map(() => `(${alias}.fiscal_year = ? AND ${alias}.member = ?)`).join(" OR ")})`, ...pairs.flatMap((p) => [p.fiscal_year, p.council_member]));
}

/** What a council_member_id search found and could not count. */
export interface MemberIdReport {
  id: string;
  person: string;
  /** The printed names counted for the person, with their years. */
  printed: { council_member: string; years: number[] }[];
  /** Ambiguous names that could be the person: not counted. */
  not_counted: MemberResolution[];
}

function memberIdReport(family: string, members: MemberCrosswalk, id: string | undefined, fy?: number): MemberIdReport | null {
  if (id == null) return null;
  const by = new Map<string, number[]>();
  for (const p of members.pairs(family, id, fy)) by.set(p.council_member, [...(by.get(p.council_member) ?? []), p.fiscal_year]);
  return {
    id,
    person: members.person(id),
    printed: [...by].map(([council_member, years]) => ({ council_member, years: years.sort((a, b) => a - b) })),
    not_counted: members.maybe(family, id, fy),
  };
}

const cap = (limit: number | undefined, def: number, max: number) =>
  limit == null || Number.isNaN(limit) ? def : Math.min(Math.max(1, Math.trunc(limit)), max);

export type Row = Record<string, any>;

// ---------------------------------------------------------------- shared per-row parts

/**
 * A row's review entry, as the public explorer shows it (PR #224, FlagBadge): the note in plain
 * words (src/checkwords.ts) and the decision in plain words, never a check id or a severity (a
 * "critical" beside an organization's name reads as a charge against it; it is about our reading
 * of the PDF), and never the reviewers' suggested decisions, which the public build withholds
 * (pdf_review_suggestions).
 */
export interface ReviewEntry {
  review_id: string;
  /** The note in plain words, derived from the check id and field (plainReviewNote). */
  note: string;
  decision: string;
  decision_note: string;
  /** The question to Council Finance that covers this entry (data/council_questions.csv), or null. */
  question: CouncilQuestion | null;
}

export interface ServedRow {
  row: Row;
  status_label: string;
  reviews: ReviewEntry[];
  links: RowLinks;
  /** The downloaded PDF's path on this machine (download --pdfs), or null. */
  local_pdf: string | null;
  /** #51: how the row's printed member resolved (Schedule C and transparency only). */
  member?: MemberResolution | null;
}

/** The questions to Council Finance in the tables, or none when the download predates them. */
export function councilQuestions(db: DB): CouncilQuestion[] {
  const has = db.prepare("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'pdf_council_questions'").get();
  return has ? (db.prepare("SELECT question_id, review_ids, issue, sent_on, answered_on, answer, question_status AS status FROM pdf_council_questions ORDER BY question_id").all() as CouncilQuestion[]) : [];
}

/** pdf_review entries for the page's rows, keyed "fy|family|review_id". */
function reviewsFor(db: DB, family: string, rows: Row[]): Map<string, ReviewEntry> {
  const ids = [...new Set(rows.flatMap((r) => String(r.review_id ?? "").split(";").map((s) => s.trim()).filter(Boolean)))];
  const out = new Map<string, ReviewEntry>();
  const questions = questionsByReviewId(councilQuestions(db));
  for (let i = 0; i < ids.length; i += 500) {
    const chunk = ids.slice(i, i + 500);
    const got = db
      .prepare(
        `SELECT r.fiscal_year, r.review_id, r.check_id, r.field, r.decision, r.decision_note
         FROM pdf_review r
         WHERE r.family = ? AND r.review_id IN (${chunk.map(() => "?").join(",")})`
      )
      .all(family, ...chunk) as Row[];
    for (const g of got) {
      out.set(`${g.fiscal_year}|${family}|${g.review_id}`, {
        review_id: g.review_id, note: plainReviewNote(g),
        decision: g.decision ?? "", decision_note: g.decision_note ?? "", question: questions.get(g.review_id) ?? null,
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
  /** #259: true or false matches every text filter as whole words or substrings; omitted, short terms match whole words. */
  whole_word?: boolean;
  fiscal_year?: number;
  organization?: string;
  ein?: string;
  member?: string;
  /** #51: exact Legistar person ID, matched on the row's printed member as resolved for its year. */
  council_member_id?: string;
  category?: string;
  initiative?: string;
  agency?: string;
  purpose?: string;
  disclosure_status?: (typeof SC_DISCLOSURE_STATUSES)[number];
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

function scWhere(f: ScheduleCFilters, members: MemberCrosswalk): Where {
  const w = new Where(f.whole_word);
  w.add(SERVED("a", "schedule_c"));
  w.eq("a.fiscal_year", f.fiscal_year);
  w.text("organization", ["a.org"], f.organization);
  // The organization's EIN, or its fiscal conduit's (the group that receives the money for it).
  if (f.ein != null) w.add("(a.ein = ? OR a.fiscal_conduit_ein = ?)", f.ein.replace(/\D/g, ""), f.ein.replace(/\D/g, ""));
  // A member, the Speaker, or a delegation: whichever the row prints.
  w.text("member", ["a.member", "a.sponsor", "a.delegation"], f.member);
  memberIdClause(w, "a", "schedule_c", members, f.council_member_id, f.fiscal_year);
  w.text("category", ["a.category"], f.category);
  w.text("initiative", ["a.initiative"], f.initiative);
  w.text("agency", ["a.agency"], f.agency);
  w.text("purpose", ["a.purpose"], f.purpose);
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
  /** Filters matched as whole words (#259). */
  word_filters: WordFilter[];
  /** #51, with a member filter: the printed members it matched, each with its person. */
  matched_members: MatchedMember[];
  /** #51, with a member filter: rows matched through the sponsor or delegation column only. */
  member_other_columns: { rows: number; amount: number };
  /** #51, with council_member_id: the person, the names counted, and the names not counted. */
  member_id: MemberIdReport | null;
}

export function searchScheduleC(db: DB, commit: string, f: ScheduleCFilters, members: MemberCrosswalk = NO_MEMBERS): ScheduleCResult {
  const w = scWhere(f, members);
  const rows = db
    .prepare(`SELECT a.* FROM pdf_schedule_c a ${w.sql()} ORDER BY a.amount IS NULL, a.amount DESC, a.fiscal_year DESC, a.award_id LIMIT ${cap(f.limit, 50, 500)}`)
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
    const s = new Where(f.whole_word);
    s.add(SERVED("s", "schedule_c"));
    s.eq("s.fiscal_year", f.fiscal_year);
    s.text("organization", ["s.org"], f.organization);
    if (f.ein != null) s.eq("s.ein", f.ein.replace(/\D/g, ""));
    subaward_matches = db
      .prepare(`SELECT COUNT(*) AS rows, COALESCE(SUM(s.amount), 0) AS amount FROM pdf_schedule_c_subawards s ${s.sql()}`)
      .get(...s.params) as { rows: number; amount: number };
  }
  let matched_members: MatchedMember[] = [];
  let member_other_columns = { rows: 0, amount: 0 };
  if (f.member != null) {
    // The member filter's own match on the printed member column, beside every other filter.
    const m = new Where(f.whole_word);
    m.text("member", ["a.member"], f.member);
    const counts = db
      .prepare(`SELECT a.fiscal_year, COALESCE(a.member, '') AS member, COUNT(*) AS rows, COALESCE(SUM(a.amount), 0) AS amount FROM pdf_schedule_c a ${w.sql()} AND ${m.clauses[0]} GROUP BY 1, 2`)
      .all(...w.params, ...m.params) as { fiscal_year: number; member: string; rows: number; amount: number }[];
    matched_members = matchedMembers("schedule_c", members, counts);
    const inMember = counts.reduce((t, c) => ({ rows: t.rows + c.rows, amount: t.amount + c.amount }), { rows: 0, amount: 0 });
    member_other_columns = { rows: t.n - inMember.rows, amount: t.amount - inMember.amount };
  }
  const usd = (v: unknown) => (typeof v === "number" ? `$${v.toLocaleString("en-US")}` : "no amount");
  return {
    rows: serve(db, "schedule_c", rows, commit, (r) => `${r.org}, ${usd(r.amount)}`).map((s) => ({ ...s, member: members.of("schedule_c", s.row.fiscal_year, s.row.member) })),
    matched: t.n,
    with_amount: t.with_amount,
    amount: t.amount,
    no_amount: t.n - t.with_amount,
    by_year,
    by_disclosure,
    subawards,
    subaward_matches,
    word_filters: w.words,
    matched_members,
    member_other_columns,
    member_id: memberIdReport("schedule_c", members, f.council_member_id, f.fiscal_year),
  };
}

// ---------------------------------------------------------------- transparency resolutions

export const TR_ACTIONS = ["designate", "rescind", "purpose_from", "purpose_to", "listed"] as const;

export interface TransparencyFilters {
  /** #259: true or false matches every text filter as whole words or substrings; omitted, short terms match whole words. */
  whole_word?: boolean;
  fiscal_year?: number;
  budget_fiscal_year?: number;
  organization?: string;
  ein?: string;
  member?: string;
  /** #51: exact Legistar person ID, matched on the row's printed member as resolved for its year. */
  council_member_id?: string;
  resolution_number?: string;
  resolution_date?: string;
  /** Resolutions dated on or after / on or before (YYYY-MM-DD). */
  date_from?: string;
  date_to?: string;
  action?: (typeof TR_ACTIONS)[number];
  limit?: number;
}

function trWhere(f: TransparencyFilters, members: MemberCrosswalk): Where {
  const w = new Where(f.whole_word);
  w.add(SERVED("t", "transparency"));
  w.eq("t.fiscal_year", f.fiscal_year);
  w.eq("t.budget_fiscal_year", f.budget_fiscal_year);
  w.text("organization", ["t.org"], f.organization);
  if (f.ein != null) w.add("(t.ein = ? OR t.fiscal_conduit_ein = ?)", f.ein.replace(/\D/g, ""), f.ein.replace(/\D/g, ""));
  w.text("member", ["t.member"], f.member);
  memberIdClause(w, "t", "transparency", members, f.council_member_id, f.fiscal_year);
  w.id("resolution_number", ["t.resolution_number"], f.resolution_number);
  w.eq("t.resolution_date", f.resolution_date);
  if (f.date_from != null) w.add("t.resolution_date >= ?", f.date_from);
  if (f.date_to != null) w.add("t.resolution_date <= ?", f.date_to);
  w.eq("t.action", f.action);
  return w;
}

export interface TransparencyResult {
  rows: ServedRow[];
  matched: number;
  /**
   * Per action and side. agency_side 1 marks a chart's City-agency lines: the agency's own lines,
   * not money to or from an organization (code/transreso/structure.py keeps them apart, and so
   * does the explorer's trTotalsQuery), so they are totaled separately.
   */
  by_action: { action: string; agency_side: number; rows: number; with_amount: number; amount: number }[];
  /** amount_kind = no_dollar_amount: a chart that prints no amount (Beating Hearts); in no sum. */
  no_dollar_amount: number;
  /** Per year and side (agency_side 1: City-agency lines): never one net of both. */
  by_year: (StatusTotal & { agency_side: number; amount: number })[];
  resolutions: { fiscal_year: number; resolution_number: string; resolution_date: string; rows: number }[];
  /** Filters matched as whole words (#259). */
  word_filters: WordFilter[];
  /** #51, with a member filter: the printed members it matched, each with its person. */
  matched_members: MatchedMember[];
  /** #51, with council_member_id: the person, the names counted, and the names not counted. */
  member_id: MemberIdReport | null;
}

export function searchTransparency(db: DB, commit: string, f: TransparencyFilters, members: MemberCrosswalk = NO_MEMBERS): TransparencyResult {
  const w = trWhere(f, members);
  const rows = db
    .prepare(
      `SELECT t.* FROM pdf_transparency t ${w.sql()}
       ORDER BY t.resolution_date DESC, t.fiscal_year DESC, t.resolution_seq DESC, t.pdf_page, t.table_index, t.row_index, t.row_id LIMIT ${cap(f.limit, 50, 500)}`
    )
    .all(...w.params) as Row[];
  const by_action = db
    .prepare(
      `SELECT t.action, COALESCE(t.agency_side, 0) AS agency_side, COUNT(*) AS rows, COUNT(t.amount) AS with_amount,
         COALESCE(SUM(t.amount), 0) AS amount
       FROM pdf_transparency t ${w.sql()} GROUP BY 1, 2 ORDER BY 2, 1`
    )
    .all(...w.params) as TransparencyResult["by_action"];
  const nd = db
    // w.sql() always starts with WHERE: the serving gate is always a clause.
    .prepare(`SELECT COUNT(*) AS n FROM pdf_transparency t ${w.sql()} AND t.amount_kind = 'no_dollar_amount'`)
    .get(...w.params) as { n: number };
  const by_year = db
    .prepare(
      `SELECT t.fiscal_year, t.status, COALESCE(t.agency_side, 0) AS agency_side, COUNT(*) AS rows, COALESCE(SUM(t.amount), 0) AS amount
       FROM pdf_transparency t ${w.sql()} GROUP BY 1, 2, 3 ORDER BY 1, 3`
    )
    .all(...w.params) as TransparencyResult["by_year"];
  const resolutions = db
    .prepare(
      `SELECT t.fiscal_year, t.resolution_number, t.resolution_date, COUNT(*) AS rows FROM pdf_transparency t ${w.sql()}
       GROUP BY 1, 2, 3 ORDER BY 1 DESC, 3`
    )
    .all(...w.params) as TransparencyResult["resolutions"];
  // The member filter searches the printed member only, so every matched row is in these counts.
  const matched_members =
    f.member == null
      ? []
      : matchedMembers(
          "transparency",
          members,
          db
            .prepare(`SELECT t.fiscal_year, COALESCE(t.member, '') AS member, COUNT(*) AS rows, COALESCE(SUM(t.amount), 0) AS amount FROM pdf_transparency t ${w.sql()} GROUP BY 1, 2`)
            .all(...w.params) as { fiscal_year: number; member: string; rows: number; amount: number }[]
        );
  const usd = (v: unknown) => (typeof v === "number" ? `${v < 0 ? "-" : ""}$${Math.abs(v).toLocaleString("en-US")}` : "no dollar amount");
  return {
    rows: serve(db, "transparency", rows, commit, (r) => `${r.org || r.agency || r.purpose || r.row_id}, ${usd(r.amount)}`).map((s) => ({ ...s, member: members.of("transparency", s.row.fiscal_year, s.row.member) })),
    matched: by_action.reduce((s, a) => s + a.rows, 0),
    by_action,
    no_dollar_amount: nd.n,
    by_year,
    resolutions,
    word_filters: w.words,
    matched_members,
    member_id: memberIdReport("transparency", members, f.council_member_id, f.fiscal_year),
  };
}

// ---------------------------------------------------------------- capital book (§254 supporting detail)

export interface CapitalBookFilters {
  /** #259: true or false matches every text filter as whole words or substrings; omitted, short terms match whole words. */
  whole_word?: boolean;
  fiscal_year?: number;
  project_id?: string;
  budget_line?: string;
  sponsor?: string;
  borough?: string;
  agency?: string;
  title?: string;
  part?: "I" | "II";
  /** On the book's own year's column (amount_y1); reductions compare as negative numbers. */
  min_amount?: number;
  max_amount?: number;
  limit?: number;
}

/** A sponsor cell that names a district with no member (#206), e.g. "CD 22" (the explorer's VACANT_DISTRICT). */
export const VACANT_DISTRICT = /^CD *\d+$/i;

function cbWhere(f: CapitalBookFilters): Where {
  const w = new Where(f.whole_word);
  w.add(SERVED("c", "capital_sd"));
  w.eq("c.fiscal_year", f.fiscal_year);
  // Substrings, as the explorer's book search: "CC1053" finds "AG CC1053".
  w.id("project_id", ["c.sub_id"], f.project_id);
  if (f.budget_line != null) w.eq("c.budget_line", f.budget_line);
  w.text("sponsor", ["c.sponsor", "c.sponsor_raw"], f.sponsor);
  if (f.borough != null) w.add("upper(c.boro) = ?", f.borough.trim().toUpperCase());
  w.text("agency", ["c.agency"], f.agency);
  // FY2019's book also prints a description under each title (#206).
  w.text("title", ["c.title", "c.description"], f.title);
  w.eq("c.part", f.part);
  if (f.min_amount != null) w.add("c.amount_y1 >= ?", f.min_amount);
  if (f.max_amount != null) w.add("c.amount_y1 <= ?", f.max_amount);
  return w;
}

type YearSums = { rows: number; y1: number; y2: number; y3: number; y4: number };

/**
 * The capital book's totals, as decided by Noel Hidalgo on 2026-10-23 (for the MCP and the
 * explorer alike): the total is Part I's, which ties to the book's printed grand total. Part II is
 * the list of non-city groups. "Of which … went to non-city groups" is the Part I rows the book lists
 * again in Part II, so it is part of the total. Rows printed only in Part II (FY2027: 30, all of the
 * `MA` series; FY2026: 42, 39 of them its `MM` series) are listed on their own and never added. The
 * series is the year's config (pdf_capital_sd_series, from config/capital_sd/fyYYYY.toml).
 * A row is "the same project in the other part" by year, SUB ID and budget line, the explorer's rule
 * (viz/explorer/src/query/pdf.js IN_OTHER_PART).
 */
export interface CapitalBookResult {
  rows: ServedRow[];
  matched: number;
  /** The total: matched Part I rows, per printed year column (y1 the book's own year, y2..y4 the next three). */
  part_i: YearSums;
  /** Of which went to non-city groups: matched Part I rows the book lists again in Part II. */
  noncity: YearSums;
  /** Matched Part II rows, as Part II prints them (the non-city list, with its Part-II-only rows). */
  part_ii: YearSums;
  /** Matched Part II rows printed only in Part II: in no Part I total. */
  part_ii_only: YearSums;
  /** Of those, the year's Part II series ("MA"; FY2026 "MM"): one question to Council Finance covers them (#209). */
  part_ii_only_series: number;
  /** The series prefixes of those rows' years ("MA", "MM"). */
  series_prefixes: string[];
  /** Each loaded year's Part II series, for labeling rows (inPart2Series). */
  series: Part2Series[];
  /** Rows with a reduction (a negative amount) in any year column, and the first year's reductions. */
  negative_rows: number;
  negative_y1: number;
  /** Rows whose sponsor is a district with no member ("CD 22"). */
  vacant_rows: number;
  /** Per year: Part I rows and their first-year total. */
  by_year: (StatusTotal & { y1: number })[];
  /** Filters matched as whole words (#259). */
  word_filters: WordFilter[];
}

/** The same project (year, SUB ID, budget line) printed in the other part: the explorer's IN_OTHER_PART. */
const IN_OTHER_PART = (other: "I" | "II") =>
  `EXISTS (SELECT 1 FROM pdf_capital_sd o WHERE o.part = '${other}' AND o.fiscal_year = c.fiscal_year AND o.sub_id = c.sub_id AND o.budget_line IS c.budget_line)`;

/** Each year's Part II series (config/capital_sd/fyYYYY.toml), or none when the download predates the table. */
export function part2Series(db: DB): Part2Series[] {
  const has = db.prepare("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'pdf_capital_sd_series'").get();
  return has ? (db.prepare("SELECT fiscal_year, id_prefix, line_prefix FROM pdf_capital_sd_series ORDER BY fiscal_year").all() as Part2Series[]) : [];
}

/** In the row's year's Part II series, as src/questions.ts inPart2Series (the text after the agency code). */
const SERIES_SQL = `EXISTS (SELECT 1 FROM pdf_capital_sd_series s WHERE s.fiscal_year = c.fiscal_year
  AND substr(trim(c.sub_id), instr(trim(c.sub_id), ' ') + 1) GLOB s.id_prefix || '*'
  AND substr(trim(c.budget_line), instr(trim(c.budget_line), ' ') + 1) GLOB s.line_prefix || '*')`;

const sums = (when: string) =>
  `SUM(CASE WHEN ${when} THEN 1 ELSE 0 END), ` +
  [1, 2, 3, 4].map((k) => `COALESCE(SUM(CASE WHEN ${when} THEN c.amount_y${k} END), 0)`).join(", ");

export function searchCapitalBook(db: DB, commit: string, f: CapitalBookFilters): CapitalBookResult {
  const w = cbWhere(f);
  const series = part2Series(db);
  const rows = db
    .prepare(
      `SELECT c.*, CASE WHEN c.part = 'I' THEN ${IN_OTHER_PART("II")} ELSE ${IN_OTHER_PART("I")} END AS in_other_part
       FROM pdf_capital_sd c ${w.sql()} ORDER BY c.fiscal_year DESC, c.part, c.pdf_page, c.row_in_page LIMIT ${cap(f.limit, 50, 500)}`
    )
    .all(...w.params) as Row[];
  const t = db
    .prepare(
      `SELECT COUNT(*) AS n, ${sums("c.part = 'I'")}, ${sums(`c.part = 'I' AND ${IN_OTHER_PART("II")}`)}, ${sums("c.part = 'II'")},
         ${sums(`c.part = 'II' AND NOT ${IN_OTHER_PART("I")}`)},
         SUM(CASE WHEN c.part = 'II' AND NOT ${IN_OTHER_PART("I")} AND ${series.length ? SERIES_SQL : "0"} THEN 1 ELSE 0 END),
         COALESCE(SUM(${[1, 2, 3, 4].map((k) => `c.amount_y${k} < 0`).join(" OR ")}), 0) AS negative_rows,
         COALESCE(SUM(CASE WHEN c.amount_y1 < 0 THEN c.amount_y1 END), 0) AS negative_y1,
         COALESCE(SUM(upper(trim(COALESCE(c.sponsor, ''))) GLOB 'CD*' AND trim(substr(trim(c.sponsor), 3)) GLOB '[0-9]*' AND trim(substr(trim(c.sponsor), 3)) NOT GLOB '*[^0-9]*'), 0) AS vacant_rows
       FROM pdf_capital_sd c ${w.sql()}`
    )
    .raw()
    .get(...w.params) as number[];
  const pick = (at: number): YearSums => ({ rows: t[at] ?? 0, y1: t[at + 1], y2: t[at + 2], y3: t[at + 3], y4: t[at + 4] });
  const part_i = pick(1);
  const noncity = pick(6);
  const part_ii = pick(11);
  const part_ii_only = pick(16);
  const by_year = db
    .prepare(
      `SELECT c.fiscal_year, c.status, COUNT(*) AS rows, COALESCE(SUM(c.amount_y1), 0) AS y1 FROM pdf_capital_sd c ${w.sql()} AND c.part = 'I'
       GROUP BY 1, 2 ORDER BY 1`
    )
    .all(...w.params) as CapitalBookResult["by_year"];
  return {
    rows: serve(db, "capital_sd", rows, commit, (r) => `${r.sub_id} ${r.title}`.trim()),
    matched: t[0],
    part_i,
    noncity,
    part_ii,
    part_ii_only,
    part_ii_only_series: t[21],
    series_prefixes: series.length
      ? (db.prepare(`SELECT DISTINCT y.id_prefix FROM pdf_capital_sd c JOIN pdf_capital_sd_series y ON y.fiscal_year = c.fiscal_year
          ${w.sql()} AND c.part = 'II' AND NOT ${IN_OTHER_PART("I")} AND ${SERIES_SQL} ORDER BY 1`).pluck().all(...w.params) as string[])
      : [],
    series,
    negative_rows: t[22],
    negative_y1: t[23],
    vacant_rows: t[24],
    by_year,
    word_filters: w.words,
  };
}

// ---------------------------------------------------------------- Terms and Conditions

export interface TermsFilters {
  /** #259: true or false matches every text filter as whole words or substrings; omitted, short terms match whole words. */
  whole_word?: boolean;
  fiscal_year?: number;
  agency?: string;
  unit?: string;
  text?: string;
  limit?: number;
}

/** The explorer's termsWhere (viz/explorer/src/query/pdf.js), with the serving gate. */
function termsWhere(f: TermsFilters): Where {
  const w = new Where(f.whole_word);
  w.add(SERVED("pdf_terms", "terms"));
  w.eq("pdf_terms.fiscal_year", f.fiscal_year);
  w.text("agency", ["pdf_terms.agency_name", "pdf_terms.agency_code"], f.agency);
  w.text("text", ["pdf_terms.condition_text", "pdf_terms.heading_raw"], f.text);
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
  /** Filters matched as whole words (#259). */
  word_filters: WordFilter[];
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
    word_filters: w.words,
  };
}
