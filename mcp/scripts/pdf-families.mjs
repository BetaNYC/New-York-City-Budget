/**
 * pdf-families.mjs — the reviewed PDF tables (viz/explorer/INTEGRATION.md §1–3), loaded into the
 * index by build-index.mjs from the families data/pdf_years.csv lists.
 *
 * One config entry per PDF family. A family's files are data/fyNN/pdf/<family>/fyNN_<family>_<file>.csv
 * (written by code/build_pdf_promoted.py). Each table's columns are declared here, in order, with
 * their SQLite type and the CSV column they come from; a CSV whose header is not exactly that set is
 * a stop, so a promoted file cannot drift from the index unnoticed. `{y1}`..`{y4}` in a CSV name is
 * the row's fiscal year + 0..3 (the capital book prints FY2027–FY2030 as fy2027..fy2030; the table
 * stores them as amount_y1..amount_y4 so every year shares one schema).
 *
 * Which rows load (the gate, INTEGRATION.md §3):
 *   status = closed      always: the MCP's own index, the public explorer
 *   status = reviewed    only with --include-reviewed, which build-index.mjs refuses unless --out
 *                        points away from mcp/data/budget.db (the explorer's local or demo build)
 * Every pdf_* table exists in every index, empty when nothing is loaded, so the schema never
 * depends on the gate. No MCP tool reads a pdf_* table (test/pdf-families.test.js).
 *
 * To add a family (Schedule C next): one entry in PDF_FAMILIES, one row in data/pdf_years.csv.
 */

const T = "TEXT";
const I = "INTEGER";

/** The row contract (INTEGRATION.md §1), first on every table. */
const CONTRACT = [
  ["fiscal_year", I],
  ["source_pdf", T],
  ["pdf_sha256", T],
  ["pdf_page", I],
  ["bbox_pt", T],
  ["review_id", T],
  ["flags", T],
];

const years = (dbPrefix, csv, type, suffix = "") =>
  [1, 2, 3, 4].map((k) => [`${dbPrefix}_y${k}${suffix}`, type, csv.replace("{y}", `{y${k}}`)]);

/** The review queue, one table for every family. */
export const REVIEW_TABLE = {
  table: "pdf_review",
  file: "review",
  columns: [
    ["fiscal_year", I], ["family", T], ["source_pdf", T], ["pdf_sha256", T], ["review_id", T],
    ["check_id", T], ["severity", T], ["pdf_page", I], ["part", T], ["sub_id", T], ["budget_line", T],
    ["field", T], ["dollars", I], ["expected", T], ["observed", T], ["note", T],
  ],
};

export const PDF_FAMILIES = {
  capital_sd: {
    label: "Capital §254 supporting detail",
    main: "pdf_capital_sd",
    tables: [
      {
        table: "pdf_capital_sd",
        file: "projects",
        columns: [
          ...CONTRACT,
          ["part", T], ["agency", T], ["row_in_page", I], ["sub_id", T], ["budget_line", T], ["boro", T],
          ["title", T], ["building_code", T], ["school_code", T],
          ...years("amount", "fy{y}", I),
          ["sponsor", T], ["title_raw", T], ["sponsor_raw", T],
          ...years("amount", "fy{y}_printed", T, "_printed"),
        ],
      },
      {
        table: "pdf_capital_sd_orgs",
        file: "orgs",
        columns: [
          ...CONTRACT,
          ["organization", T], ["budget_line", T],
          ...years("amount", "fy{y}", I),
          ...years("org_printed", "org_printed_fy{y}", I),
          ["org_lines", I], ["org_line_in_org", I], ["org_status", T], ["org_pdf_page", I], ["org_bbox_pt", T],
        ],
      },
      {
        table: "pdf_capital_sd_totals",
        file: "totals",
        columns: [
          ...CONTRACT,
          ["kind", T], ["part", T], ["name", T], ["printed_count", I], ["rows", I],
          ...years("printed", "printed_fy{y}", I),
          ...years("sum", "sum_fy{y}", I),
          ["tie_status", T, "status"], ["printed_text", T],
        ],
      },
    ],
  },
  terms: {
    label: "Terms and Conditions",
    main: "pdf_terms",
    tables: [
      {
        table: "pdf_terms",
        file: "conditions",
        columns: [
          ...CONTRACT,
          ["item_number", I], ["page_start", I], ["page_end", I], ["page_boxes", T], ["kind", T],
          ["agency_name", T], ["agency_code", T], ["units_of_appropriation", T], ["num_units", I],
          ["budget_lines", T], ["dates_mentioned", T], ["report_deadlines", T], ["heading_raw", T],
          ["condition_text", T], ["condition_text_raw", T],
        ],
      },
      {
        table: "pdf_terms_units",
        file: "units",
        columns: [
          ...CONTRACT,
          ["item_number", I], ["agency_name", T], ["agency_code", T], ["unit_of_appropriation", T], ["budget_line", T],
        ],
      },
      {
        table: "pdf_terms_fsr",
        file: "fsr_table",
        columns: [
          ...CONTRACT,
          ["item_number", I], ["financial_status_report", T], ["report_content", T], ["issue_date", T],
          ["anticipated_meeting_date", T], ["report_content_raw", T],
        ],
      },
    ],
  },
};

export const PDF_YEARS_COLUMNS = ["fiscal_year", "family", "source_pdf", "pdf_sha256", "issue", "status", "rows",
  "flagged", "printed_totals_tied", "note"];
export const STATUSES = ["reviewed", "closed"];

/** Every pdf_* table, in a fixed order: pdf_years, each family's tables, pdf_review. */
export const PDF_TABLES = [
  "pdf_years",
  ...Object.values(PDF_FAMILIES).flatMap((f) => f.tables.map((t) => t.table)),
  REVIEW_TABLE.table,
];

const ident = (s) => `"${s}"`;

/** CREATE TABLE statements for every pdf_* table (rows carry `family` and `status`). */
export function pdfSchemaSql() {
  const out = [
    `CREATE TABLE pdf_years (fiscal_year INTEGER, family TEXT, source_pdf TEXT, pdf_sha256 TEXT, issue INTEGER,
       status TEXT, rows INTEGER, flagged INTEGER, printed_totals_tied TEXT, note TEXT)`,
  ];
  for (const fam of Object.values(PDF_FAMILIES)) {
    for (const t of fam.tables) {
      out.push(`CREATE TABLE ${t.table} (${[...t.columns.map(([n, ty]) => `${ident(n)} ${ty}`), '"family" TEXT', '"status" TEXT'].join(", ")})`);
    }
  }
  out.push(`CREATE TABLE ${REVIEW_TABLE.table} (${[...REVIEW_TABLE.columns.map(([n, ty]) => `${ident(n)} ${ty}`), '"status" TEXT'].join(", ")})`);
  return out.join(";\n") + ";";
}

/** `{y1}`..`{y4}` -> fiscal year + 0..3. */
const csvName = (name, fy) => name.replace(/\{y(\d)\}/g, (_, k) => String(fy + Number(k) - 1));

/** "" -> NULL; otherwise the value must be an integer. */
function intOf(v, at) {
  if (v === "" || v === undefined) return null;
  const n = Number(v);
  if (!Number.isSafeInteger(n) || !/^-?\d+$/.test(v)) throw new Error(`${at}: ${JSON.stringify(v)} is not an integer`);
  return n;
}

function insertAll(db, table, columns, rows, extra, at) {
  const names = [...columns.map(([n]) => n), ...Object.keys(extra)];
  const stmt = db.prepare(`INSERT INTO ${table} (${names.map(ident).join(", ")}) VALUES (${names.map(() => "?").join(", ")})`);
  db.transaction(() => {
    rows.forEach((r, i) => {
      const vals = columns.map(([n, ty, src]) => {
        const v = r[src ?? n];
        return ty === I ? intOf(v, `${at} row ${i + 2} ${src ?? n}`) : v ?? "";
      });
      stmt.run(...vals, ...Object.values(extra));
    });
  })();
}

/**
 * Load the families data/pdf_years.csv lists into `db` (whose schema pdfSchemaSql() created).
 *
 * @param db               better-sqlite3 database
 * @param io               { readCsv(rel), sha256Of(rel), exists(rel) } from build-index.mjs (they record inputs)
 * @param includeReviewed  load status = reviewed families too
 * @returns { counts, loaded: [{fiscal_year, family, status, rows}], expect } for verifyPdf()
 */
export function loadPdfFamilies(db, io, includeReviewed) {
  const yearsRel = "data/pdf_years.csv";
  const years = io.readCsv(yearsRel);
  if (years.length && Object.keys(years[0]).join(",") !== PDF_YEARS_COLUMNS.join(",")) {
    throw new Error(`${yearsRel}: columns ${Object.keys(years[0]).join(",")}; expected ${PDF_YEARS_COLUMNS.join(",")}`);
  }
  const counts = Object.fromEntries(PDF_TABLES.map((t) => [t, 0]));
  const loaded = [];
  const seen = new Set();
  for (const y of years) {
    const fy = intOf(y.fiscal_year, `${yearsRel} fiscal_year`);
    const at = `${yearsRel} FY${fy} ${y.family}`;
    const fam = PDF_FAMILIES[y.family];
    if (!fam) throw new Error(`${at}: unknown family (add it to mcp/scripts/pdf-families.mjs)`);
    if (!STATUSES.includes(y.status)) throw new Error(`${at}: status ${JSON.stringify(y.status)}; expected ${STATUSES.join(" or ")}`);
    if (seen.has(`${fy}/${y.family}`)) throw new Error(`${at}: listed twice`);
    seen.add(`${fy}/${y.family}`);
    const load = y.status === "closed" || (y.status === "reviewed" && includeReviewed);
    if (!load) continue;

    // The PDF the rows cite must be the bytes pdf_years.csv names.
    const sha = io.sha256Of(y.source_pdf);
    if (sha !== y.pdf_sha256) throw new Error(`${at}: ${y.source_pdf} sha256 ${sha} differs from pdf_years.csv (${y.pdf_sha256})`);

    const yy = String(fy).slice(2);
    const dir = `data/fy${yy}/pdf/${y.family}`;
    const extra = { family: y.family, status: y.status };
    let mainRows = null;
    for (const t of [...fam.tables, REVIEW_TABLE]) {
      const rel = `${dir}/fy${yy}_${y.family}_${t.file}.csv`;
      const rows = io.readCsv(rel);
      const want = t.columns.map(([n, , src]) => csvName(src ?? n, fy));
      const have = rows.length ? Object.keys(rows[0]) : want;
      if ([...have].sort().join(",") !== [...want].sort().join(",")) {
        throw new Error(`${rel}: columns differ from mcp/scripts/pdf-families.mjs\n  file:   ${have.join(",")}\n  config: ${want.join(",")}`);
      }
      for (const [i, r] of rows.entries()) {
        if (Number(r.fiscal_year) !== fy) throw new Error(`${rel} row ${i + 2}: fiscal_year ${r.fiscal_year}`);
        if (r.pdf_sha256 !== y.pdf_sha256 || r.source_pdf !== y.source_pdf) throw new Error(`${rel} row ${i + 2}: source_pdf/pdf_sha256 differ from pdf_years.csv`);
      }
      const cols = t.columns.map(([n, ty, src]) => [n, ty, csvName(src ?? n, fy)]);
      const ex = t === REVIEW_TABLE ? { status: y.status } : extra;
      insertAll(db, t.table, cols, rows, ex, rel);
      counts[t.table] += rows.length;
      if (t.table === fam.main) mainRows = rows.length;
    }
    if (mainRows !== intOf(y.rows, `${at} rows`)) throw new Error(`${at}: rows ${y.rows}, but ${fam.main} has ${mainRows}`);
    db.prepare(`INSERT INTO pdf_years VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
      fy, y.family, y.source_pdf, y.pdf_sha256, intOf(y.issue, `${at} issue`), y.status,
      mainRows, intOf(y.flagged, `${at} flagged`), y.printed_totals_tied, y.note
    );
    counts.pdf_years += 1;
    loaded.push({ fiscal_year: fy, family: y.family, status: y.status, rows: mainRows });
  }
  return { counts, loaded, includeReviewed };
}

/**
 * Problems with the pdf_* tables of a built index: rows of a status the gate did not allow, a
 * loaded family whose main table count is not pdf_years.rows, or rows of a family not loaded.
 */
export function verifyPdf(db, { loaded, includeReviewed }) {
  const problems = [];
  const allowed = includeReviewed ? ["closed", "reviewed"] : ["closed"];
  for (const t of PDF_TABLES) {
    for (const { status, n } of db.prepare(`SELECT status, COUNT(*) AS n FROM ${t} GROUP BY status`).all()) {
      if (!allowed.includes(status)) problems.push(`${t}: ${n} rows with status ${JSON.stringify(status)}, not allowed in this build`);
    }
  }
  const want = new Map(loaded.map((l) => [`${l.fiscal_year}/${l.family}`, l]));
  for (const [fam, cfg] of Object.entries(PDF_FAMILIES)) {
    for (const { y, n } of db.prepare(`SELECT fiscal_year AS y, COUNT(*) AS n FROM ${cfg.main} GROUP BY fiscal_year`).all()) {
      const l = want.get(`${y}/${fam}`);
      if (!l) problems.push(`${cfg.main}: FY${y} has ${n} rows but is not loaded`);
      else if (l.rows !== n) problems.push(`${cfg.main}: FY${y} has ${n} rows; pdf_years.csv says ${l.rows}`);
    }
  }
  return problems;
}
