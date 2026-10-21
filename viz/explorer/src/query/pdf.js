/**
 * Queries over the reviewed PDF tables (pdf_*; mcp/scripts/pdf-families.mjs), as pure functions
 * returning { sql, params }, like sql.js. These tables are not in the MCP's tools, so there is no
 * MCP answer to match; test/parity.test.mjs checks the tables themselves, per family and status.
 *
 * Text filters are case- and accent-insensitive substrings (strip_accents + lower on both sides).
 */
import { PAGE_SIZE, normBudgetLine } from "./sql.js";

export const REVIEWED_LABEL = "checked, review in progress";

const blank = (v) => v === null || v === undefined || (typeof v === "string" && v.trim() === "");
/** The value side of a text filter: lower-case, accents removed (DuckDB's strip_accents twin). */
export const textKey = (v) => String(v).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

class Where {
  constructor() {
    this.clauses = [];
    this.params = [];
  }
  add(c, ...p) {
    this.clauses.push(c);
    this.params.push(...p);
  }
  text(cols, v) {
    if (blank(v)) return;
    const k = textKey(v);
    this.add(`(${cols.map((c) => `contains(strip_accents(lower(COALESCE(${c}, ''))), ?)`).join(" OR ")})`, ...cols.map(() => k));
  }
  eq(c, v) {
    if (v === null || v === undefined || v === "") return;
    this.add(`${c} = ?`, v);
  }
  sql() {
    return this.clauses.length ? ` WHERE ${this.clauses.join(" AND ")}` : "";
  }
}

/** Which families have rows, and their status (pdf_years). */
export const pdfYearsQuery = () => ({
  sql: "SELECT fiscal_year, family, source_pdf, pdf_sha256, issue, status, rows, flagged, printed_totals_tied, note FROM pdf_years ORDER BY fiscal_year DESC, family",
  params: [],
});

// ---------------------------------------------------------------- capital §254, Part I matches

/**
 * Part I rows for the report years on screen, to match capital_council rows on (report year,
 * Council ID, budget line). The workbook prints the ID without its agency code (`CC0001`); the
 * PDF prints it with (`HO CC0001`). 1,213 rows at most per year, so the match is done in JS.
 */
export function capitalPdfMatchesQuery(years) {
  const ys = [...new Set(years.filter((y) => Number.isInteger(y)))];
  if (!ys.length) return null;
  return {
    sql: `SELECT fiscal_year, status, sub_id, budget_line, sponsor, title, amount_y1, amount_y2, amount_y3, amount_y4,
            pdf_page, bbox_pt, source_pdf, review_id, flags
          FROM pdf_capital_sd WHERE part = 'I' AND fiscal_year IN (${ys.map(() => "?").join(", ")})`,
    params: ys,
  };
}

const matchKey = (year, id, line) => `${year}|${String(id ?? "").trim().toUpperCase()}|${normBudgetLine(line) ?? ""}`;

/** Map "year|ID|line" -> the Part I row. */
export function indexPdfMatches(rows) {
  const m = new Map();
  for (const r of rows) m.set(matchKey(Number(r.fiscal_year), String(r.sub_id).split(" ").at(-1), r.budget_line), r);
  return m;
}

/** The Part I row for a capital_council row, or undefined. */
export const pdfMatchFor = (index, c) => index.get(matchKey(Number(c.report_year), c.project_id, c.budget_line_norm || c.budget_line));

/** Printed totals and the summary page for a year (pdf_capital_sd_totals). */
export const capitalTotalsPdfQuery = (fy) => ({
  sql: `SELECT fiscal_year, status, kind, part, name, printed_count, rows, printed_y1, printed_y2, printed_y3, printed_y4,
          sum_y1, tie_status, pdf_page, source_pdf, review_id, flags
        FROM pdf_capital_sd_totals WHERE fiscal_year = ? ORDER BY rowid`,
  params: [fy],
});

// ---------------------------------------------------------------- organizations (Part III)

export const orgFilters = (s) => ({ fiscal_year: s.gfy, organization: s.org, budget_line: s.gline });

function orgWhere(f) {
  const w = new Where();
  w.eq("fiscal_year", f.fiscal_year);
  w.text(["organization"], f.organization);
  if (!blank(f.budget_line)) w.eq("budget_line", normBudgetLine(f.budget_line) ?? String(f.budget_line).trim().toUpperCase());
  return w;
}

/** One row per organization: its printed line and the number of budget lines. */
export function orgsQuery(f, page) {
  const w = orgWhere(f);
  return {
    sql: `SELECT fiscal_year, status, organization, org_pdf_page, org_bbox_pt, source_pdf,
            ANY_VALUE(org_printed_y1) AS org_printed_y1, ANY_VALUE(org_printed_y2) AS org_printed_y2,
            ANY_VALUE(org_printed_y3) AS org_printed_y3, ANY_VALUE(org_printed_y4) AS org_printed_y4,
            ANY_VALUE(org_status) AS org_status, COUNT(*) AS n_lines,
            -- JSON text, not a LIST: DuckDB-WASM hands a LIST back as an Arrow vector (orgLines()).
            CAST(to_json(list({ budget_line: budget_line, y1: amount_y1, y2: amount_y2, y3: amount_y3, y4: amount_y4,
                   pdf_page: pdf_page, bbox_pt: bbox_pt, flags: flags, review_id: review_id } ORDER BY org_line_in_org)) AS VARCHAR) AS lines,
            string_agg(NULLIF(flags, ''), ';') AS flags, string_agg(NULLIF(review_id, ''), ';') AS review_id
          FROM pdf_capital_sd_orgs${w.sql()}
          GROUP BY fiscal_year, status, organization, org_pdf_page, org_bbox_pt, source_pdf
          ORDER BY fiscal_year DESC, organization
          LIMIT ${PAGE_SIZE} OFFSET ${Math.max(0, Number(page) || 0) * PAGE_SIZE}`,
    params: w.params,
  };
}

/** An organization row's budget lines (orgsQuery's `lines`, JSON text). */
export const orgLines = (o) => (typeof o.lines === "string" ? JSON.parse(o.lines) : []);

export function orgsTotalsQuery(f) {
  const w = orgWhere(f);
  return {
    sql: `SELECT COUNT(DISTINCT fiscal_year || '|' || organization) AS orgs, COUNT(*) AS lines,
            COALESCE(SUM(amount_y1), 0) AS y1, COALESCE(SUM(amount_y2), 0) AS y2,
            COALESCE(SUM(amount_y3), 0) AS y3, COALESCE(SUM(amount_y4), 0) AS y4
          FROM pdf_capital_sd_orgs${w.sql()}`,
    params: w.params,
  };
}

// ---------------------------------------------------------------- Terms and Conditions

export const termsFilters = (s) => ({ fiscal_year: s.tfy, agency: s.tagency, unit: s.tunit, text: s.tq, kind: s.tkind });

function termsWhere(f) {
  const w = new Where();
  w.eq("fiscal_year", f.fiscal_year);
  w.text(["agency_name", "agency_code"], f.agency);
  w.text(["condition_text", "heading_raw"], f.text);
  w.eq("kind", f.kind);
  if (!blank(f.unit)) {
    // A unit as printed in the heading ("001", "All"), or the start of a budget line, which is
    // printed with its scope ("HD-0009 – All Projects").
    w.add(
      `EXISTS (SELECT 1 FROM pdf_terms_units u WHERE u.fiscal_year = pdf_terms.fiscal_year AND u.item_number = pdf_terms.item_number
               AND (lower(u.unit_of_appropriation) = lower(?) OR starts_with(lower(u.budget_line), lower(?))))`,
      String(f.unit).trim(),
      String(f.unit).trim()
    );
  }
  return w;
}

export function termsQuery(f, page) {
  const w = termsWhere(f);
  return {
    sql: `SELECT fiscal_year, status, item_number, page_start, page_end, page_boxes, kind, agency_name, agency_code,
            units_of_appropriation, num_units, budget_lines, report_deadlines, dates_mentioned, heading_raw,
            condition_text, pdf_page, bbox_pt, source_pdf, review_id, flags
          FROM pdf_terms${w.sql()}
          ORDER BY fiscal_year DESC, item_number
          LIMIT ${PAGE_SIZE} OFFSET ${Math.max(0, Number(page) || 0) * PAGE_SIZE}`,
    params: w.params,
  };
}

export function termsCountQuery(f) {
  const w = termsWhere(f);
  return { sql: `SELECT COUNT(*) AS n, COUNT(DISTINCT agency_name) AS agencies FROM pdf_terms${w.sql()}`, params: w.params };
}

export const termsFsrQuery = (fy) => ({
  sql: `SELECT financial_status_report, report_content, issue_date, anticipated_meeting_date, pdf_page, flags, review_id
        FROM pdf_terms_fsr WHERE fiscal_year = ? ORDER BY rowid`,
  params: [fy],
});

// ---------------------------------------------------------------- Schedule C beside the disclosure

/** "matched" / "pdf_only" / "disclosure_only" in plain words. */
export const SC_SIDE_LABEL = { matched: "In both", disclosure_only: "Spreadsheet only", pdf_only: "Schedule C only" };

/**
 * Why a row has no partner (code/schedc/disclosure.py waterfall reasons, as the Schedule C review
 * words them).
 */
export const SC_REASON = {
  matched: "Same EIN and amount in both.",
  key_already_claimed: "The spreadsheet has this EIN and amount, but every such row is already paired with another Schedule C row.",
  amount_differs: "The spreadsheet has this EIN, but not at this amount.",
  ein_fully_claimed: "The spreadsheet's rows for this EIN are all paired with other Schedule C rows.",
  ein_not_in_disclosure: "This EIN is not in the spreadsheet for the year.",
  city_ein_name_mismatch: "The City's own EIN (13-6400434): pairs only when the spreadsheet's name starts the PDF's organization text, and none does.",
  pdf_value_unreadable: "The PDF's EIN or amount could not be read.",
  amount_or_count_differs: "Schedule C has this EIN, but not at this amount, or not as many times.",
  city_ein_pending: "A Pending row on the City's own EIN: usually post-adoption money not printed in Schedule C.",
  ein_not_in_pdf: "This EIN is not in Schedule C for the year.",
};

/** Whole-year counts and dollars by side (amount: Schedule C's for matched and PDF-only rows). */
export const scSummaryQuery = (fy) => ({
  sql: `SELECT m.fiscal_year, m.status, m.side, COUNT(*) AS n,
          COALESCE(SUM(CASE WHEN m.side = 'disclosure_only' THEN m.disclosure_amount ELSE m.amount END), 0) AS amount,
          SUM(m.ambiguous) AS ambiguous
        FROM pdf_sc_disclosure m${fy == null ? "" : " WHERE m.fiscal_year = ?"}
        GROUP BY 1, 2, 3 ORDER BY 1 DESC, 3`,
  params: fy == null ? [] : [fy],
});

/** The Schedule C side of the spreadsheet rows on screen: [{fiscal_year, source_row}]. */
export function scForDisclosureRowsQuery(rows) {
  const keys = rows.map((r) => [Number(r.fiscal_year), Number(r.source_row)]);
  if (!keys.length) return null;
  return {
    sql: `SELECT m.fiscal_year, m.disclosure_row, m.side, m.reason, m.ambiguous, a.award_id, a.pdf_page, a.bbox_pt,
            a.org, a.amount, a.section, a.member, a.flags, a.review_id, a.status, a.source_pdf
          FROM pdf_sc_disclosure m LEFT JOIN pdf_schedule_c a ON a.fiscal_year = m.fiscal_year AND a.award_id = m.award_id
          WHERE (m.fiscal_year, m.disclosure_row) IN (${keys.map(() => "(?, ?)").join(", ")})`,
    params: keys.flat(),
  };
}

export const scKey = (fy, row) => `${Number(fy)}|${Number(row)}`;

/** Schedule C rows with no spreadsheet partner, filtered like the Awards view where the fields map. */
function scOnlyWhere(f) {
  const w = new Where();
  w.add("m.side = 'pdf_only'");
  w.eq("a.fiscal_year", f.fiscal_year == null || f.fiscal_year === "" ? null : Number(f.fiscal_year));
  w.text(["a.org"], f.legal_name);
  w.text(["a.member", "a.sponsor"], f.council_member);
  w.text(["a.agency"], f.agency);
  w.text(["a.purpose"], f.program_name);
  if (!blank(f.ein)) w.eq("a.ein", String(f.ein).replace(/\D/g, ""));
  if (!blank(f.min_amount) && Number.isFinite(Number(f.min_amount))) w.add("a.amount >= ?", Number(f.min_amount));
  if (!blank(f.max_amount) && Number.isFinite(Number(f.max_amount))) w.add("a.amount <= ?", Number(f.max_amount));
  return w;
}

const SC_FROM = "pdf_schedule_c a JOIN pdf_sc_disclosure m ON m.fiscal_year = a.fiscal_year AND m.award_id = a.award_id";

export function scOnlyQuery(f, page) {
  const w = scOnlyWhere(f);
  return {
    sql: `SELECT a.fiscal_year, a.status, a.award_id, a.section, a.category, a.initiative, a.org, a.ein, a.amount, a.member,
            a.pdf_page, a.bbox_pt, a.source_pdf, a.flags, a.review_id, m.reason, m.disclosure_amount AS nearest_amount
          FROM ${SC_FROM}${w.sql()} ORDER BY a.amount DESC, a.award_id
          LIMIT ${PAGE_SIZE} OFFSET ${Math.max(0, Number(page) || 0) * PAGE_SIZE}`,
    params: w.params,
  };
}

export function scOnlyTotalsQuery(f) {
  const w = scOnlyWhere(f);
  return { sql: `SELECT COUNT(*) AS n, COALESCE(SUM(a.amount), 0) AS amount FROM ${SC_FROM}${w.sql()}`, params: w.params };
}

// ---------------------------------------------------------------- review notes

/** The review entries behind a row's `review_id` (`;`-joined ids). */
export function reviewNotesQuery(reviewIds) {
  const ids = [...new Set(String(reviewIds ?? "").split(";").map((s) => s.trim()).filter(Boolean))];
  if (!ids.length) return null;
  return {
    sql: `SELECT review_id, family, check_id, severity, pdf_page, note FROM pdf_review WHERE review_id IN (${ids.map(() => "?").join(", ")}) ORDER BY severity, review_id`,
    params: ids,
  };
}

// ---------------------------------------------------------------- the review queue

/** Every review row of every loaded family, with its suggested decision. */
export const reviewQueueQuery = () => ({
  sql: `SELECT r.fiscal_year, r.family, r.status, r.review_id, r.check_id, r.severity, r.pdf_page, r.field, r.dollars,
          r.expected, r.observed, r.note, r.detail, r.source_pdf,
          s.suggested_decision, s.suggested_note, s.source AS suggestion_source
        FROM pdf_review r LEFT JOIN pdf_review_suggestions s
          ON s.fiscal_year = r.fiscal_year AND s.family = r.family AND s.review_id = r.review_id`,
  params: [],
});

/** The data row a review id points at, in one of its family's tables (rows carry review_id). */
export const reviewRowQuery = (table, fy, reviewId) => ({
  sql: `SELECT * FROM "${table}" WHERE fiscal_year = ? AND contains(';' || COALESCE(review_id, '') || ';', ?) LIMIT 1`,
  params: [Number(fy), `;${reviewId};`],
});

// ---------------------------------------------------------------- the source viewer

/** "x0,top,x1,bottom" -> numbers, or null. */
export function parseBbox(s) {
  const p = String(s ?? "").split(",").map(Number);
  return p.length === 4 && p.every(Number.isFinite) ? p : null;
}

/**
 * A row box (`bbox_pt`: x0,top,x1,bottom in points on the unrotated page, origin top-left) as a
 * PDF user-space rectangle [x0, y0, x1, y1] (origin bottom-left), for pdf.js's
 * viewport.convertToViewportPoint (two corners), which applies the page's /Rotate. `view` is the page's
 * MediaBox as pdf.js reports it ([x0, y0, x1, y1]).
 */
export function bboxToPdfRect(bbox, view) {
  const b = Array.isArray(bbox) ? bbox : parseBbox(bbox);
  if (!b) return null;
  const [vx0, , , vy1] = view;
  return [vx0 + b[0], vy1 - b[3], vx0 + b[2], vy1 - b[1]];
}

/** Two viewport corners [x0, y0, x1, y1], in either order -> {left, top, width, height} in CSS px. */
export function viewportBox(r) {
  const left = Math.min(r[0], r[2]);
  const top = Math.min(r[1], r[3]);
  return { left, top, width: Math.abs(r[2] - r[0]), height: Math.abs(r[3] - r[1]) };
}
