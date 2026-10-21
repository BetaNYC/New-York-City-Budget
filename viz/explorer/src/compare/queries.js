/**
 * Queries for comparing two fiscal years, as pure functions returning { sql, params }.
 *
 * One entry per source in SOURCES: its table, the column that holds the fiscal year, the amount,
 * and which comparison dimensions it has. Structured sources (the disclosure spreadsheets, the
 * Council's capital list) are always in a build; PDF families (pdf_*) only when loaded, and their
 * rows carry `status` for the "checked, review in progress" label. Adding a PDF family to the
 * comparison is one more entry here.
 *
 * Keys are matched exactly (never substring), so a cell's drill-down lists exactly the rows that
 * were summed. A blank key is its own group, shown as such, never merged into another.
 */

// A marker for "printed blank", which no printed value is (it is not valid as a name, EIN or line).
export const BLANK = "~blank~";

export const SOURCES = {
  disclosure: {
    label: "Expense disclosure (Council spreadsheet)",
    table: "disclosure",
    fy: "fiscal_year",
    amount: "amount",
    dims: { agency: "agency", member: "council_member", org: "ein" },
    orgLabel: "legal_name",
    pdf: false,
  },
  schedule_c: {
    label: "Schedule C (adopted budget PDF)",
    table: "pdf_schedule_c",
    family: "schedule_c",
    fy: "fiscal_year",
    amount: "amount",
    dims: { agency: "agency", member: "member", org: "ein" },
    orgLabel: "org",
    pdf: true,
  },
  capital: {
    label: "Council capital (workbook / NYC Open Data)",
    table: "capital_council",
    fy: "report_year",
    // A list's designations: the amounts for its own year (out-year plans are not compared).
    where: "amount_fy = report_year",
    amount: "amount",
    dims: { line: "budget_line_norm", member: "sponsor" },
    pdf: false,
  },
  capital_sd: {
    label: "Capital §254 book, Part I (PDF)",
    table: "pdf_capital_sd",
    family: "capital_sd",
    fy: "fiscal_year",
    where: "part = 'I'",
    amount: "amount_y1",
    dims: { line: "budget_line", member: "sponsor", agency: "agency" },
    pdf: true,
  },
  transparency: {
    label: "Transparency resolutions (PDF), to organizations, net",
    table: "pdf_transparency",
    family: "transparency",
    // A year's resolutions (fiscal_year), organization rows only: agency-side offset rows are
    // left out, and rescissions (negative amounts) are netted in. Some rows designate another
    // budget year (budget_fiscal_year; DATA-ANOMALIES §6).
    fy: "fiscal_year",
    where: "agency_side = 0",
    amount: "amount",
    dims: { agency: "agency", member: "member", org: "ein" },
    orgLabel: "org",
    pdf: true,
  },
};

/** Which sources each comparison dimension can use, in order. */
export const DIM_SOURCES = {
  agency: ["disclosure", "schedule_c", "transparency", "capital_sd"],
  member: ["disclosure", "schedule_c", "transparency", "capital", "capital_sd"],
  org: ["disclosure", "schedule_c", "transparency"],
  line: ["capital", "capital_sd"],
};
export const DIM_LABEL = {
  agency: "By agency",
  member: "By Council member / sponsor",
  org: "By organization (EIN)",
  line: "Capital by budget line",
};

const keyExpr = (col) => `COALESCE(NULLIF(trim(CAST(${col} AS VARCHAR)), ''), '${BLANK}')`;
const whereOf = (s, extra = []) => {
  const c = [`${s.fy} = ?`, ...(s.where ? [s.where] : []), ...extra];
  return ` WHERE ${c.join(" AND ")}`;
};

/** Sums by key for one source, dimension and year. */
export function groupQuery(sourceId, dim, fy) {
  const s = SOURCES[sourceId];
  const col = s.dims[dim];
  if (!col) throw new Error(`${sourceId} has no ${dim}`);
  const label = dim === "org" && s.orgLabel ? `mode(${s.orgLabel})` : `ANY_VALUE(${col})`;
  return {
    sql: `SELECT ${keyExpr(col)} AS key, ${label} AS label, COALESCE(SUM(${s.amount}), 0) AS amount, COUNT(*) AS n
          ${s.pdf ? ", string_agg(DISTINCT status, ';') AS status" : ""}
          FROM ${s.table}${whereOf(s)} GROUP BY 1 ORDER BY 1`,
    params: [Number(fy)],
  };
}

/** The rows behind one cell: a source, a year, and a key of a dimension ("*" = every row). */
export function drillQuery(sourceId, dim, fy, key, limit = 200) {
  const s = SOURCES[sourceId];
  const extra = [];
  const params = [Number(fy)];
  if (key !== "*") {
    extra.push(`${keyExpr(s.dims[dim])} = ?`);
    params.push(key);
  }
  const cols = {
    disclosure: "fiscal_year, source_row, legal_name AS name, ein, council_member AS member, agency, source AS stream, status_norm AS state, amount",
    schedule_c: "fiscal_year, award_id, org AS name, ein, member, agency, section AS stream, status, amount, pdf_page, bbox_pt, source_pdf, flags, review_id",
    capital: "report_year AS fiscal_year, seq, title AS name, budget_line_norm AS line, sponsor AS member, borough, amount",
    capital_sd: "fiscal_year, sub_id, title AS name, budget_line AS line, sponsor AS member, agency, status, amount_y1 AS amount, pdf_page, bbox_pt, source_pdf, flags, review_id",
    transparency: "fiscal_year, row_id, org AS name, ein, member, agency, resolution_number || ' (' || resolution_date || ')' AS stream, status, amount, pdf_page, bbox_pt, source_pdf, flags, review_id",
  }[sourceId];
  return {
    sql: `SELECT ${cols} FROM ${s.table}${whereOf(s, extra)} ORDER BY amount DESC NULLS LAST LIMIT ${limit}`,
    params,
    countSql: `SELECT COUNT(*) AS n, COALESCE(SUM(${s.amount}), 0) AS amount FROM ${s.table}${whereOf(s, extra)}`,
  };
}

/** Year totals for every source (and the T&C condition count) for the two years. */
export function totalsQueries(fyA, fyB) {
  const ys = [Number(fyA), Number(fyB)];
  return {
    disclosure: {
      sql: `SELECT fiscal_year AS fy, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount,
              COALESCE(SUM(amount) FILTER (WHERE status_norm = 'cleared'), 0) AS cleared,
              COALESCE(SUM(amount) FILTER (WHERE status_norm = 'pending'), 0) AS pending
            FROM disclosure WHERE fiscal_year IN (?, ?) GROUP BY 1`,
      params: ys,
    },
    capital: {
      sql: `SELECT report_year AS fy, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount
            FROM capital_council WHERE report_year IN (?, ?) AND amount_fy = report_year GROUP BY 1`,
      params: ys,
    },
    schedule_c: {
      sql: `SELECT fiscal_year AS fy, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount, string_agg(DISTINCT status, ';') AS status
            FROM pdf_schedule_c WHERE fiscal_year IN (?, ?) GROUP BY 1`,
      params: ys,
    },
    capital_sd: {
      sql: `SELECT fiscal_year AS fy, COUNT(*) AS n, COALESCE(SUM(amount_y1), 0) AS amount, string_agg(DISTINCT status, ';') AS status
            FROM pdf_capital_sd WHERE fiscal_year IN (?, ?) AND part = 'I' GROUP BY 1`,
      params: ys,
    },
    transparency: {
      sql: `SELECT fiscal_year AS fy, COUNT(*) AS n, COALESCE(SUM(amount), 0) AS amount, string_agg(DISTINCT status, ';') AS status,
              COUNT(DISTINCT resolution_number) AS resolutions
            FROM pdf_transparency WHERE fiscal_year IN (?, ?) AND agency_side = 0 GROUP BY 1`,
      params: ys,
    },
    // Schedule C beside the disclosure, per year (pdf_sc_disclosure: the Schedule C review's rule).
    sc_pairs: {
      sql: `SELECT fiscal_year AS fy, side, COUNT(*) AS n,
              COALESCE(SUM(CASE WHEN side = 'disclosure_only' THEN disclosure_amount ELSE amount END), 0) AS amount,
              string_agg(DISTINCT status, ';') AS status
            FROM pdf_sc_disclosure WHERE fiscal_year IN (?, ?) GROUP BY 1, 2`,
      params: ys,
    },
    terms: {
      sql: `SELECT fiscal_year AS fy, COUNT(*) AS n, NULL AS amount, string_agg(DISTINCT status, ';') AS status
            FROM pdf_terms WHERE fiscal_year IN (?, ?) GROUP BY 1`,
      params: ys,
    },
  };
}

/** Both years' conditions, in printed order. */
export const termsQuery = (fy) => ({
  sql: `SELECT fiscal_year, status, item_number, agency_name, agency_code, units_of_appropriation, budget_lines, condition_text,
          pdf_page, bbox_pt, source_pdf, flags, review_id
        FROM pdf_terms WHERE fiscal_year = ? ORDER BY item_number`,
  params: [Number(fy)],
});

/** What a source has for a year: rows, or a gap with its reason. */
export function availability(sourceId, fy, ctx) {
  const y = Number(fy);
  if (sourceId === "disclosure") {
    const row = ctx.years.find((r) => r.fiscal_year === y);
    if (!row) return { ok: false, reason: `No Council disclosure workbook for FY${y} is in this repository.` };
    if (!row.loaded) return { ok: false, reason: row.note || `FY${y} is not loaded.` };
    return { ok: true, note: row.early_snapshot ? row.note : "" };
  }
  if (sourceId === "capital") {
    if (ctx.capitalYears.includes(y)) return { ok: true };
    const g = ctx.capitalGaps?.find((x) => x.year === y);
    return { ok: false, reason: g?.reason ?? `No Council capital list for FY${y} is in this repository.` };
  }
  const fam = SOURCES[sourceId]?.family ?? sourceId;
  const row = ctx.pdfYears.find((r) => r.family === fam && r.fiscal_year === y);
  if (!row) return { ok: false, reason: `No reviewed ${fam === "terms" ? "Terms and Conditions" : SOURCES[sourceId]?.label ?? fam} data for FY${y} in this build (not yet reviewed, or a public build, which shows closed years only).` };
  return { ok: true, status: row.status };
}
