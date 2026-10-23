/**
 * Queries over the reviewed PDF tables (pdf_*; mcp/scripts/pdf-families.mjs), as pure functions
 * returning { sql, params }, like sql.js. These tables are not in the MCP's tools, so there is no
 * MCP answer to match; test/parity.test.mjs checks the tables themselves, per family and status.
 *
 * Text filters are case- and accent-insensitive substrings (strip_accents + lower on both sides).
 */
import { PAGE_SIZE, normBudgetLine } from "./sql.js";

export const REVIEWED_LABEL = "checked, review in progress";
export const CLOSED_LABEL = "checked and reviewed";
/** A PDF row's status (pdf_years.status) in the words every row shows (#190). */
export const statusLabel = (status) => (status === "closed" ? CLOSED_LABEL : status === "reviewed" ? REVIEWED_LABEL : "");

/** Labels for fields decided in #209 (W8, #217). */
export const HIDDEN_TEXT_LABEL = "hidden text, not visible on the printed page";
export const NO_AMOUNT_LABEL = "no dollar amount";
/** Schedule C's "*" mark (FY2019, FY2018), in the words of the PDF's own footnote. */
// (Its own words, so it is never confused with this site's "checked, review in progress".)
export const REVIEW_NOT_COMPLETED_LABEL = "* in the book: the City's review of this group wasn't finished at adoption";
export const REVIEW_NOT_COMPLETED_NOTE = "The book's footnote: either MOCS or the Council's review process has not yet been completed.";

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

/**
 * The years whose Terms and Conditions book prints no item numbers (#206): item_number there is
 * the condition's place in the book, counted by the reader, not a number printed on the page.
 */
export const TERMS_BOOK_ORDER_YEARS = [2018, 2021, 2022, 2023, 2024];
/** 1 -> "1st", 12 -> "12th", 23 -> "23rd". */
export const ordinal = (n) => {
  const v = Number(n);
  const t = v % 100;
  return `${v}${t >= 11 && t <= 13 ? "th" : ["th", "st", "nd", "rd"][v % 10] ?? "th"}`;
};
/** How to show a condition's item_number: "No. 7" where printed, else its place in the book. */
export const termsNumberLabel = (fy, n) => (TERMS_BOOK_ORDER_YEARS.includes(Number(fy)) ? `No. ${n} (book order)` : `No. ${n}`);

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

/**
 * The review entries behind a row's `review_id` (`;`-joined ids). `full` (a review build) also
 * asks for the check id and severity, which a public build's pdf_review does not carry.
 */
export function reviewNotesQuery(reviewIds, { full = true } = {}) {
  const ids = [...new Set(String(reviewIds ?? "").split(";").map((s) => s.trim()).filter(Boolean))];
  if (!ids.length) return null;
  return {
    sql: full
      ? `SELECT review_id, family, check_id, severity, pdf_page, note, decision, decision_note FROM pdf_review WHERE review_id IN (${ids.map(() => "?").join(", ")}) ORDER BY severity, review_id`
      : `SELECT review_id, family, pdf_page, note, decision, decision_note FROM pdf_review WHERE review_id IN (${ids.map(() => "?").join(", ")}) ORDER BY review_id`,
    params: ids,
  };
}

// ---------------------------------------------------------------- the review queue

/** Every review row of every loaded family, with its suggested decision. */
export const reviewQueueQuery = () => ({
  sql: `SELECT r.fiscal_year, r.family, r.status, r.review_id, r.check_id, r.severity, r.pdf_page, r.field, r.dollars,
          r.expected, r.observed, r.note, r.detail, r.source_pdf, r.decision, r.decision_note,
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
/** A recorded decision in plain words (PLAN.md §5.3 vocabulary). */
export const DECISION_WORDS = {
  accepted_as_printed: "kept as printed",
  source_error: "the PDF's own error",
  parser_bug: "our reading is wrong",
  needs_info: "needs more information",
  read_from_page_image: "read from the page image",
};

/** One badge state for a row's review entries: "decided" when every entry has a decision. */
export function flagState(notes) {
  if (!notes?.length) return { state: "unknown" };
  const open = notes.filter((n) => !n.decision);
  if (open.length) return { state: "open", open: open.length };
  const kinds = [...new Set(notes.map((n) => n.decision))];
  return { state: "decided", decisions: kinds };
}

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

/**
 * A row box on a pdf.js page viewport (the page's /Rotate and the zoom applied), as a CSS box in
 * the page's own pixels, or null. The highlight is drawn here and the viewer scrolls to it.
 */
export function rowBoxOnViewport(bbox, view, viewport) {
  const rect = bboxToPdfRect(bbox, view);
  if (!rect) return null;
  // pdf.js 6 has no convertToViewportRectangle; map the two corners.
  return viewportBox([...viewport.convertToViewportPoint(rect[0], rect[1]), ...viewport.convertToViewportPoint(rect[2], rect[3])]);
}

/**
 * Whether the viewer has to wait for the pages and jump on open: always for a page past the first,
 * and on page 1 too when there is a box to scroll to (it may sit low on the page).
 */
export const landsByJump = (page, bbox) => Number.isInteger(page) && page >= 1 && (page > 1 || !!parseBbox(bbox));

/**
 * Where on the page to scroll so a row box is in view when the page opens (#211): the spot, in
 * the page's pixels, to put at the pane's top-left corner. The box sits a quarter of the pane down,
 * with some of the page above it for context; a box too tall for that starts one margin down.
 * Horizontally the box's left edge sits one margin in (it matters only when zoomed past the pane).
 */
export function landingSpot(box, paneHeight, margin = 24) {
  const above = box.height + margin > paneHeight * 0.75 ? margin : Math.round(paneHeight / 4);
  return { left: Math.max(0, box.left - margin), top: Math.max(0, box.top - above) };
}

// ---------------------------------------------------------------- searching every row (#213)
//
// One search per PDF family, over every row of the family (not only the rows paired with the
// disclosure). Each returns { sql, params }; test/parity.test.mjs answers the same filters from
// budget.db with plain JavaScript and checks the counts, totals and first page agree.

const OFFSET = (page) => `LIMIT ${PAGE_SIZE} OFFSET ${Math.max(0, Number(page) || 0) * PAGE_SIZE}`;
const intOrNull = (v) => (v === null || v === undefined || v === "" || !Number.isFinite(Number(v)) ? null : Math.trunc(Number(v)));
const numOrNull = (v) => (blank(v) || !Number.isFinite(Number(v)) ? null : Number(v));
/** An EIN as digits ("13-2612524" -> "132612524"), or "" when it has none. */
export const einDigits = (v) => String(v ?? "").replace(/\D/g, "");
/** A typed EIN with no digits, which the filter cannot use (the page says so rather than ignoring it). */
export const einUnusable = (v) => String(v ?? "").trim() !== "" && einDigits(v) === "";

/** Schedule C search: the hash state's keys -> filters. */
export const scSearchFilters = (s) => ({
  fiscal_year: s.scfy,
  org: s.scorg,
  ein: s.scein,
  sponsor: s.scspon,
  category: s.sccat,
  initiative: s.scinit,
  agency: s.scagency,
  min_amount: s.scmin,
  max_amount: s.scmax,
  disclosure: s.scdisc,
});

/** Where each Schedule C row stands against the disclosure spreadsheet (pdf_schedule_c.disclosure_status). */
export const SC_DISCLOSURE_LABEL = {
  cleared: "In the spreadsheet: Cleared",
  pending: "In the spreadsheet: Pending",
  unmatched: "Not paired with a spreadsheet row",
};
/**
 * What Cleared and Pending mean, as far as the sources say: the spreadsheet's Status column is the
 * designation's clearance state, Cleared or Pending (source/expense-funding-disclosure/README.md);
 * the Council does not define the steps further, so neither do we.
 */
export const SC_DISCLOSURE_NOTE =
  "The Council's disclosure spreadsheet gives each designation a clearance status, Cleared or Pending. The Council does not publish what each step involves.";

function scSearchWhere(f) {
  const w = new Where();
  w.eq("a.fiscal_year", intOrNull(f.fiscal_year));
  w.text(["a.org"], f.org);
  // The organization's EIN, or its fiscal conduit's (the group that receives the money for it).
  if (einDigits(f.ein)) w.add("(a.ein = ? OR a.fiscal_conduit_ein = ?)", einDigits(f.ein), einDigits(f.ein));
  // A member, the Speaker, or a delegation: whichever the row prints.
  w.text(["a.member", "a.sponsor", "a.delegation"], f.sponsor);
  w.text(["a.category"], f.category);
  w.text(["a.initiative"], f.initiative);
  w.text(["a.agency"], f.agency);
  if (numOrNull(f.min_amount) !== null) w.add("a.amount >= ?", numOrNull(f.min_amount));
  if (numOrNull(f.max_amount) !== null) w.add("a.amount <= ?", numOrNull(f.max_amount));
  w.eq("a.disclosure_status", f.disclosure);
  return w;
}

/** One page of Schedule C rows, highest amount first, with the disclosure row each is paired with. */
export function scSearchQuery(f, page) {
  const w = scSearchWhere(f);
  return {
    sql: `SELECT a.fiscal_year, a.status, a.award_id, a.section, a.category, a.initiative, a.member, a.sponsor, a.delegation,
            a.org, a.ein, a.amount, a.amount_printed, a.agency, a.purpose, a.program_or_subheading, a.review_not_completed,
            a.fiscal_conduit, a.fiscal_conduit_ein, a.read_from_page_image, a.disclosure_status, a.disclosure_reason,
            a.pdf_page, a.bbox_pt, a.source_pdf, a.pdf_sha256, a.flags, a.review_id,
            (SELECT m.disclosure_row FROM pdf_sc_disclosure m WHERE m.fiscal_year = a.fiscal_year AND m.award_id = a.award_id AND m.side = 'matched' LIMIT 1) AS disclosure_row,
            (SELECT COUNT(*) FROM pdf_schedule_c_subawards s WHERE s.fiscal_year = a.fiscal_year AND s.parent_award_id = a.award_id) AS subawards
          FROM pdf_schedule_c a${w.sql()}
          ORDER BY a.amount DESC NULLS LAST, a.fiscal_year DESC, a.award_id
          ${OFFSET(page)}`,
    params: w.params,
  };
}

/**
 * Totals over every matching row. Sub-awards are in their own table and never counted here: they
 * are the parent award's money passed on (#209), so adding them would count it twice.
 */
export function scSearchTotalsQuery(f) {
  const w = scSearchWhere(f);
  return {
    sql: `SELECT COUNT(*) AS n, COALESCE(SUM(a.amount), 0) AS amount, COUNT(*) FILTER (WHERE a.amount IS NULL) AS no_amount,
            COUNT(DISTINCT a.fiscal_year) AS years
          FROM pdf_schedule_c a${w.sql()}`,
    params: w.params,
  };
}

/** The sub-awards printed under the awards on screen: [{fiscal_year, award_id}]. */
export function scSubawardsQuery(awards) {
  const keys = (awards ?? []).filter((a) => Number(a.subawards) > 0).map((a) => [Number(a.fiscal_year), String(a.award_id)]);
  if (!keys.length) return null;
  return {
    sql: `SELECT fiscal_year, status, subaward_id, parent_award_id, org, ein, amount, amount_printed, service_type,
            pdf_page, bbox_pt, source_pdf, pdf_sha256, flags, review_id
          FROM pdf_schedule_c_subawards WHERE (fiscal_year, parent_award_id) IN (${keys.map(() => "(?, ?)").join(", ")})
          ORDER BY fiscal_year, parent_award_id, table_index, row_index`,
    params: keys.flat(),
  };
}

// ---------------------------------------------------------------- transparency resolutions

/** Transparency search: the hash state's keys -> filters. */
export const trFilters = (s) => ({
  fiscal_year: s.trfy,
  budget_fiscal_year: s.trbfy,
  org: s.trorg,
  ein: s.trein,
  member: s.trmember,
  resolution: s.trreso,
  date_from: s.trfrom,
  date_to: s.trto,
  action: s.traction,
});

/** pdf_transparency.action in plain words. */
export const TR_ACTION_LABEL = {
  designate: "Money added",
  rescind: "Money taken back",
  purpose_from: "Purpose changed: old purpose",
  purpose_to: "Purpose changed: new purpose",
  listed: "Listed, no dollar amount",
};
export const TR_ACTIONS = ["designate", "rescind", "purpose_from", "purpose_to", "listed"];

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function trWhere(f) {
  const w = new Where();
  w.eq("fiscal_year", intOrNull(f.fiscal_year));
  w.eq("budget_fiscal_year", intOrNull(f.budget_fiscal_year));
  w.text(["org"], f.org);
  if (einDigits(f.ein)) w.add("(ein = ? OR fiscal_conduit_ein = ?)", einDigits(f.ein), einDigits(f.ein));
  w.text(["member"], f.member);
  w.text(["resolution_number"], f.resolution);
  if (ISO_DATE.test(String(f.date_from ?? "").trim())) w.add("resolution_date >= ?", String(f.date_from).trim());
  if (ISO_DATE.test(String(f.date_to ?? "").trim())) w.add("resolution_date <= ?", String(f.date_to).trim());
  w.eq("action", f.action);
  return w;
}

/** One page of rows, newest resolution first, then in the order the resolution prints them. */
export function trQuery(f, page) {
  const w = trWhere(f);
  return {
    sql: `SELECT fiscal_year, status, row_id, resolution_seq, resolution_number, resolution_date, chart_number, chart_title,
            budget_fiscal_year, chart_kind, action, agency_side, source, member, org, ein, agency, amount, amount_printed,
            amount_kind, purpose, hidden_text, fiscal_conduit, fiscal_conduit_ein, read_from_page_image,
            disclosure_status, pdf_page, bbox_pt, source_pdf, pdf_sha256, flags, review_id
          FROM pdf_transparency${w.sql()}
          ORDER BY resolution_date DESC, fiscal_year DESC, resolution_seq DESC, pdf_page, table_index, row_index, row_id
          ${OFFSET(page)}`,
    params: w.params,
  };
}

/**
 * Rows and dollars by action and side, over every match. A chart's agency-side lines
 * (agency_side = 1) are the City agency's own lines, not money to or from an organization; the
 * resolution pipeline keeps them apart (code/transreso/structure.py: org_designations vs
 * agency_side_net), and so do these totals. "No dollar amount" rows count as rows, never as dollars.
 */
export function trTotalsQuery(f) {
  const w = trWhere(f);
  return {
    sql: `SELECT action, COALESCE(agency_side, 0) AS agency_side, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount,
            COUNT(*) FILTER (WHERE amount IS NULL) AS no_amount
          FROM pdf_transparency${w.sql()} GROUP BY 1, 2 ORDER BY 2, 1`,
    params: w.params,
  };
}

/**
 * Rollup of trTotalsQuery's rows: { matched, byAction, agencyByAction }, each {action: {n, amount,
 * no_amount}}: byAction for organization lines, agencyByAction for the agency-side lines.
 */
export function rollupTr(rows) {
  const byAction = {};
  const agencyByAction = {};
  let matched = 0;
  for (const r of rows ?? []) {
    const into = Number(r.agency_side) === 1 ? agencyByAction : byAction;
    into[r.action] = { n: Number(r.n), amount: Number(r.amount), no_amount: Number(r.no_amount) };
    matched += Number(r.n);
  }
  return { matched, byAction, agencyByAction };
}

/** The resolutions of the years loaded, for the resolution picker: number, date, rows. */
export const trResolutionsQuery = () => ({
  sql: `SELECT fiscal_year, resolution_seq, resolution_number, resolution_date, rows FROM pdf_transparency_resolutions
        ORDER BY resolution_date DESC, fiscal_year DESC, resolution_seq DESC`,
  params: [],
});

// ---------------------------------------------------------------- the capital book (§254)

/** Capital-book search: the hash state's keys -> filters. */
export const bookFilters = (s) => ({
  fiscal_year: s.bkfy,
  sub_id: s.bkid,
  sponsor: s.bksponsor,
  boro: s.bkboro,
  agency: s.bkagency,
  title: s.bktitle,
  budget_line: s.bkline,
  part: s.bkpart,
  min_amount: s.bkmin,
  max_amount: s.bkmax,
});

/** A sponsor cell that names a district with no member (#206), e.g. "CD 22". */
export const VACANT_DISTRICT = /^CD *\d+$/i;
export const isVacantDistrict = (sponsor) => VACANT_DISTRICT.test(String(sponsor ?? "").trim());

function bookWhere(f) {
  const w = new Where();
  w.eq("fiscal_year", intOrNull(f.fiscal_year));
  w.text(["sub_id"], f.sub_id);
  w.text(["sponsor", "sponsor_raw"], f.sponsor);
  if (!blank(f.boro)) w.add("upper(boro) = ?", String(f.boro).trim().toUpperCase());
  w.text(["agency"], f.agency);
  // FY2019's book also prints a description under each title (#206).
  w.text(["title", "description"], f.title);
  if (!blank(f.budget_line)) w.eq("budget_line", normBudgetLine(f.budget_line) ?? String(f.budget_line).trim().toUpperCase());
  w.eq("part", f.part);
  // The book's own year's column; negative amounts (reductions) compare as numbers.
  if (numOrNull(f.min_amount) !== null) w.add("amount_y1 >= ?", numOrNull(f.min_amount));
  if (numOrNull(f.max_amount) !== null) w.add("amount_y1 <= ?", numOrNull(f.max_amount));
  return w;
}

/** One page of book rows, in book order (year, part, page, row). */
export function bookQuery(f, page) {
  const w = bookWhere(f);
  return {
    sql: `SELECT fiscal_year, status, part, agency, row_in_page, sub_id, budget_line, boro, title, sponsor, building_code, school_code,
            amount_y1, amount_y2, amount_y3, amount_y4, amount_y1_printed, amount_y2_printed, amount_y3_printed, amount_y4_printed,
            council_district, description,
            pdf_page, bbox_pt, source_pdf, pdf_sha256, flags, review_id,
            -- rows in the whole book that print this SUB ID (Part I and Part II often repeat one; odForBookRow)
            (SELECT COUNT(*) FROM pdf_capital_sd s WHERE s.fiscal_year = b.fiscal_year AND s.sub_id = b.sub_id) AS id_rows,
            -- the same project in the other part (Part I row listed again in Part II, or the reverse)
            CASE WHEN part = 'I' THEN ${IN_OTHER_PART("b", "II")} ELSE ${IN_OTHER_PART("b", "I")} END AS in_other_part
          FROM pdf_capital_sd b${w.sql()}
          ORDER BY fiscal_year DESC, part, pdf_page, row_in_page
          ${OFFSET(page)}`,
    params: w.params,
  };
}

/**
 * Whether the book prints the same project (year, SUB ID, budget line) in the other part. Part II
 * (the non-city list) repeats Part I rows for non-city groups, and prints some rows Part I does not.
 */
const IN_OTHER_PART = (t, other) =>
  `EXISTS (SELECT 1 FROM pdf_capital_sd o WHERE o.part = '${other}' AND o.fiscal_year = ${t}.fiscal_year AND o.sub_id = ${t}.sub_id AND o.budget_line IS NOT DISTINCT FROM ${t}.budget_line)`;

/**
 * Totals over every match (Noel, PR #224). The book's total is Part I only: it is what the book's
 * own grand total prints. Under it: the Part I rows the book lists again in Part II (money that went
 * to non-city groups), Part II's own total as printed, and the rows printed only in Part II, which
 * are never added to the Part I total. Reductions (negative amounts) and vacant-district sponsors
 * are counted on their own.
 */
export function bookTotalsQuery(f) {
  const w = bookWhere(f);
  const ys = [1, 2, 3, 4];
  const sumIf = (cond, k) => `COALESCE(SUM(amount_y${k}) FILTER (WHERE ${cond}), 0)`;
  const I = "part = 'I'";
  const II = "part = 'II'";
  const iInII = `${I} AND ${IN_OTHER_PART("b", "II")}`;
  const iiOnly = `${II} AND NOT ${IN_OTHER_PART("b", "I")}`;
  return {
    sql: `SELECT COUNT(*) AS n, COUNT(DISTINCT fiscal_year) AS years,
            COUNT(*) FILTER (WHERE ${I}) AS part1_n, ${ys.map((k) => `${sumIf(I, k)} AS y${k}`).join(", ")},
            COUNT(*) FILTER (WHERE ${iInII}) AS noncity_n, ${sumIf(iInII, 1)} AS noncity_y1,
            COUNT(*) FILTER (WHERE ${II}) AS part2_n, ${sumIf(II, 1)} AS part2_y1,
            COUNT(*) FILTER (WHERE ${iiOnly}) AS part2_only_n, ${ys.map((k) => `${sumIf(iiOnly, k)} AS part2_only_y${k}`).join(", ")},
            COUNT(*) FILTER (WHERE ${ys.map((k) => `amount_y${k} < 0`).join(" OR ")}) AS negative_rows,
            COALESCE(SUM(amount_y1) FILTER (WHERE amount_y1 < 0), 0) AS negative_y1,
            COUNT(*) FILTER (WHERE regexp_matches(trim(COALESCE(sponsor, '')), '^[Cc][Dd] *[0-9]+$')) AS vacant_rows
          FROM pdf_capital_sd b${w.sql()}`,
    params: w.params,
  };
}

/** The matching rows printed only in Part II, in book order (listed apart from the Part I total). */
export function bookPart2OnlyQuery(f) {
  const w = bookWhere(f);
  w.add("part = 'II'");
  w.add(`NOT ${IN_OTHER_PART("b", "I")}`);
  return {
    sql: `SELECT fiscal_year, status, part, sub_id, budget_line, boro, title, sponsor, amount_y1, amount_y2, amount_y3, amount_y4,
            pdf_page, row_in_page, bbox_pt, source_pdf, pdf_sha256, flags, review_id
          FROM pdf_capital_sd b${w.sql()}
          ORDER BY fiscal_year DESC, pdf_page, row_in_page
          ${OFFSET(0)}`,
    params: w.params,
  };
}

/**
 * The "MA" series (agency code, then MA: "PV MA0005"): rows the book prints only in Part II, with
 * one question about them sent to Council Finance in every year (#209: needs_info).
 */
export const isMaSeries = (subId) => /^[A-Z]{1,2} MA/.test(String(subId ?? "").trim());
export const PART2_ONLY_LABEL = "printed only in Part II";
export const MA_QUESTION_LABEL = "question sent to Council Finance";

/**
 * NYC Open Data rows for the book rows on screen (#205). The crosswalk keys a PDF capital record
 * on (report year, SUB ID, amount year), and, where the book prints one SUB ID on two rows, also
 * on the row's place, "p<page>r<row>". The query asks by year and SUB ID; odForBookRow() then keeps
 * only the crosswalk rows for this row's own place, so a reused ID never shows the other row's match.
 */
export function odForBookRowsQuery(rows) {
  const keys = [...new Map((rows ?? []).map((r) => [`${Number(r.fiscal_year)}|${r.sub_id}`, [Number(r.fiscal_year), String(r.sub_id)]])).values()];
  if (!keys.length) return null;
  return {
    sql: `SELECT x.fiscal_year, x.record_row, x.record_amount_fy, x.record_part, x.dataset_id, x.portal_row_id, x.candidates,
            x.match_status, r.match_rule, x.differing_fields, x.portal_value, d.name AS dataset_name, d.snapshot_date
          FROM open_data_crosswalk x
          LEFT JOIN open_data_rules r ON r.rule_id = x.rule_id
          LEFT JOIN open_data_datasets d ON d.dataset_id = x.dataset_id
          WHERE x.family = 'capital_award' AND x.record_pdf = 1 AND (${keys.map(() => "(x.fiscal_year = ? AND x.record_row = ?)").join(" OR ")})
          ORDER BY x.fiscal_year, x.record_row, x.record_amount_fy, x.dataset_id`,
    params: keys.flat(),
  };
}

/** A printed amount that is only a dash ("-", "–", "—"): the book prints no amount there. */
export const printedDash = (p) => /^\s*[-–—]\s*$/.test(String(p ?? ""));

/** A book row's place, as the crosswalk writes it. */
export const bookPlace = (r) => `p${Number(r.pdf_page)}r${Number(r.row_in_page)}`;

/**
 * The crosswalk rows for a book row, each with `exact`: true when the match is this row's own (its
 * place is recorded and is this row's, or the book prints the SUB ID on this row only), false when
 * the crosswalk records no place and the book prints the SUB ID on more than one row (`id_rows`),
 * so the match is to the SUB ID, not to this exact row. A crosswalk row recording another row's
 * place is dropped. The crosswalk records a place for 32 rows and never a part.
 */
export function odForBookRow(xs, r) {
  const place = bookPlace(r);
  const shared = Number(r.id_rows ?? 1) > 1;
  return (xs ?? [])
    .filter((x) => Number(x.fiscal_year) === Number(r.fiscal_year) && x.record_row === r.sub_id)
    .filter((x) => x.record_part == null || x.record_part === "" || x.record_part === place)
    .map((x) => ({ ...x, exact: x.record_part === place || !shared }));
}
export const OD_SUB_ID_ONLY = "matched on project ID only, not to this exact row";

/** The borough codes the book prints: the five boroughs, and A and C as printed (meaning not recorded). */
export const BOOK_BOROUGHS = [
  ["K", "Brooklyn (K)"],
  ["M", "Manhattan (M)"],
  ["Q", "Queens (Q)"],
  ["R", "Staten Island (R)"],
  ["X", "Bronx (X)"],
  ["A", "A (as printed)"],
  ["C", "C (as printed)"],
];
