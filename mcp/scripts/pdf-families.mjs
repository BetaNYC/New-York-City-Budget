/**
 * pdf-families.mjs — the reviewed PDF tables (viz/explorer/INTEGRATION.md §1–3), loaded into the
 * index by build-index.mjs from the families data/pdf_years.csv lists.
 *
 * One config entry per PDF family. A family's files are data/fyNN/pdf/<family>/fyNN_<prefix>_<file>.csv
 * (written by code/build_pdf_promoted.py; <prefix> is the family name unless the entry sets one:
 * Schedule C's files are fyNN_sc_*). Each table's columns are declared here, in order, with
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
 * Every family's review CSV goes into one table, pdf_review: the columns all families share are
 * mapped by name (`review.map`), and the family's other review columns are kept, verbatim, as JSON
 * in `detail`. A family may also `derive` tables from what is loaded (Schedule C: its disclosure
 * alignment, pdf_sc_disclosure, below).
 *
 * To add a family: one entry in PDF_FAMILIES, one row in data/pdf_years.csv.
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

/** The review queue, one table for every family: shared columns, plus `detail` (JSON). */
export const REVIEW_TABLE = {
  table: "pdf_review",
  columns: [
    ["fiscal_year", I], ["family", T], ["source_pdf", T], ["pdf_sha256", T], ["review_id", T],
    ["check_id", T], ["severity", T], ["pdf_page", I], ["field", T], ["dollars", I], ["expected", T],
    ["observed", T], ["note", T], ["detail", T],
  ],
};

/** Capital and T&C review CSVs (code/review_capital_sd.py, code/review_terms.py). */
const REVIEW_PY = {
  file: "review",
  map: Object.fromEntries(["fiscal_year", "family", "source_pdf", "pdf_sha256", "review_id", "check_id", "severity",
    "pdf_page", "field", "dollars", "expected", "observed", "note"].map((c) => [c, c])),
  detail: ["part", "sub_id", "budget_line"],
};

export const PDF_FAMILIES = {
  capital_sd: {
    label: "Capital §254 supporting detail",
    main: "pdf_capital_sd",
    decisions: { 2027: "research/2026-10-20-fy27-capital-terms-review/data/fy27_capital_sd_review_decisions.csv" },
    review: REVIEW_PY,
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
    decisions: { 2027: "research/2026-10-20-fy27-capital-terms-review/data/fy27_terms_review_decisions.csv" },
    review: REVIEW_PY,
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

/** Schedule C (code/parse_schedule_c_v2.py, code/schedc/; PR #125, #126). */
PDF_FAMILIES.schedule_c = {
  label: "Schedule C",
  main: "pdf_schedule_c",
  decisions: { 2027: "research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv" },
  prefix: "sc",
  review: {
    file: "review",
    map: {
      fiscal_year: "fiscal_year", family: "family", source_pdf: "source_pdf", pdf_sha256: "pdf_sha256",
      review_id: "review_id", check_id: "check_id", severity: "severity", pdf_page: "pdf_page", field: "field",
      dollars: "dollar_impact", expected: "expected", observed: "observed", note: "what_to_check",
    },
    detail: ["table_index", "row_index", "award_id", "value_vector", "value_image", "value_other", "overlay",
      "decision", "note"],
  },
  tables: [
    {
      table: "pdf_schedule_c",
      file: "awards",
      columns: [
        ...CONTRACT,
        ["award_id", T], ["section", T], ["category", T], ["initiative", T], ["initiative_id", I], ["member", T],
        ["sponsor", T], ["delegation", T], ["org", T], ["ein", T], ["amount", I], ["agency", T], ["purpose", T],
        ["ein_printed", T], ["amount_printed", T], ["member_raw", T], ["sponsor_raw", T], ["delegation_raw", T],
        ["org_raw", T], ["agency_raw", T], ["purpose_raw", T], ["clean_rules_applied", T], ["row_flags", T],
        ["image_check", T], ["disclosure_status", T], ["disclosure_reason", T], ["table_index", I], ["row_index", I],
        ["lattice", T],
      ],
    },
    {
      table: "pdf_schedule_c_categories",
      file: "categories",
      columns: [
        ...CONTRACT,
        ["category", T], ["line", T], ["agency", T], ["initiative", T], ["amount", I], ["amount_printed", T],
        ["table_index", I], ["row_index", I],
      ],
    },
    {
      table: "pdf_schedule_c_initiatives",
      file: "initiatives",
      columns: [
        ...CONTRACT,
        ["initiative_id", I], ["category", T], ["initiative", T], ["amount", I], ["amount_printed", T],
        ["statement_kind", T], ["reserve", I], ["designated", I], ["n_rows", I], ["rows_sum", I], ["statement", T],
        ["table_index", I],
      ],
    },
  ],
  derive: deriveScDisclosure,
};

/** Tables a family derives (not read from a CSV): name -> CREATE columns. */
/**
 * The suggested decision for each review row (data/pdf_review_suggestions.csv, written by
 * code/build_review_suggestions.py from the families' REVIEW.md files). Loaded for loaded
 * families only, and read only when at least one family loads.
 */
export const SUGGESTIONS = {
  table: "pdf_review_suggestions",
  file: "data/pdf_review_suggestions.csv",
  columns: [["fiscal_year", I], ["family", T], ["review_id", T], ["check_id", T], ["suggested_decision", T], ["suggested_note", T], ["source", T]],
};

export const DERIVED = {
  pdf_sc_disclosure: [
    ["fiscal_year", I], ["side", T], ["award_id", T], ["ein", T], ["amount", I], ["disclosure_row", I],
    ["disclosure_status", T], ["disclosure_name", T], ["disclosure_source", T], ["disclosure_amount", "REAL"],
    ["reason", T], ["ambiguous", I],
  ],
};

export const PDF_YEARS_COLUMNS = ["fiscal_year", "family", "source_pdf", "pdf_sha256", "issue", "status", "rows",
  "flagged", "printed_totals_tied", "note"];
export const STATUSES = ["reviewed", "closed"];

/** Every pdf_* table, in a fixed order: pdf_years, each family's tables, pdf_review. */
export const PDF_TABLES = [
  "pdf_years",
  ...Object.values(PDF_FAMILIES).flatMap((f) => f.tables.map((t) => t.table)),
  ...Object.keys(DERIVED),
  REVIEW_TABLE.table,
  SUGGESTIONS.table,
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
  for (const [t, cols] of Object.entries(DERIVED)) {
    out.push(`CREATE TABLE ${t} (${[...cols.map(([n, ty]) => `${ident(n)} ${ty}`), '"family" TEXT', '"status" TEXT'].join(", ")})`);
  }
  out.push(`CREATE TABLE ${SUGGESTIONS.table} (${[...SUGGESTIONS.columns.map(([n, ty]) => `${ident(n)} ${ty}`), '"status" TEXT'].join(", ")})`);
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
    const prefix = fam.prefix ?? y.family;
    for (const t of fam.tables) {
      const rel = `${dir}/fy${yy}_${prefix}_${t.file}.csv`;
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
      insertAll(db, t.table, cols, rows, extra, rel);
      counts[t.table] += rows.length;
      if (t.table === fam.main) mainRows = rows.length;
    }
    counts[REVIEW_TABLE.table] += loadReview(db, io, `${dir}/fy${yy}_${prefix}_${fam.review.file}.csv`, fam.review, y);
    for (const [t, n] of Object.entries(fam.derive ? fam.derive(db, fy, y) : {})) counts[t] += n;
    if (mainRows !== intOf(y.rows, `${at} rows`)) throw new Error(`${at}: rows ${y.rows}, but ${fam.main} has ${mainRows}`);
    db.prepare(`INSERT INTO pdf_years VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
      fy, y.family, y.source_pdf, y.pdf_sha256, intOf(y.issue, `${at} issue`), y.status,
      mainRows, intOf(y.flagged, `${at} flagged`), y.printed_totals_tied, y.note
    );
    counts.pdf_years += 1;
    loaded.push({ fiscal_year: fy, family: y.family, status: y.status, rows: mainRows });
  }
  if (loaded.length) counts[SUGGESTIONS.table] = loadSuggestions(db, io, loaded);
  return { counts, loaded, includeReviewed };
}

/** Suggestions for the loaded families; every loaded review row must have exactly one. */
function loadSuggestions(db, io, loaded) {
  const rows = io.readCsv(SUGGESTIONS.file);
  const want = SUGGESTIONS.columns.map(([n]) => n);
  if (rows.length && Object.keys(rows[0]).join(",") !== want.join(",")) throw new Error(`${SUGGESTIONS.file}: columns ${Object.keys(rows[0]).join(",")}; expected ${want.join(",")}`);
  const status = new Map(loaded.map((l) => [`${l.fiscal_year}/${l.family}`, l.status]));
  const mine = rows.filter((r) => status.has(`${r.fiscal_year}/${r.family}`));
  const ins = db.prepare(`INSERT INTO ${SUGGESTIONS.table} VALUES (?, ?, ?, ?, ?, ?, ?, ?)`);
  db.transaction(() => {
    for (const r of mine) ins.run(Number(r.fiscal_year), r.family, r.review_id, r.check_id, r.suggested_decision, r.suggested_note, r.source, status.get(`${r.fiscal_year}/${r.family}`));
  })();
  const missing = db.prepare(`SELECT COUNT(*) AS n FROM ${REVIEW_TABLE.table} r WHERE NOT EXISTS (SELECT 1 FROM ${SUGGESTIONS.table} s
    WHERE s.fiscal_year = r.fiscal_year AND s.family = r.family AND s.review_id = r.review_id)`).get().n;
  const extra = db.prepare(`SELECT COUNT(*) AS n FROM ${SUGGESTIONS.table} s WHERE NOT EXISTS (SELECT 1 FROM ${REVIEW_TABLE.table} r
    WHERE s.fiscal_year = r.fiscal_year AND s.family = r.family AND s.review_id = r.review_id)`).get().n;
  if (missing || extra) throw new Error(`${SUGGESTIONS.file}: ${missing} review rows have no suggestion row, ${extra} suggestion rows match no review row (run code/build_review_suggestions.py --write)`);
  return mine.length;
}

/** One family's review CSV into pdf_review: mapped columns, the rest as JSON in `detail`. */
function loadReview(db, io, rel, cfg, y) {
  const rows = io.readCsv(rel);
  const want = new Set([...Object.values(cfg.map), ...cfg.detail]);
  const have = rows.length ? Object.keys(rows[0]) : [...want];
  if ([...have].sort().join(",") !== [...want].sort().join(",")) {
    throw new Error(`${rel}: columns differ from mcp/scripts/pdf-families.mjs (review)\n  file:   ${have.join(",")}\n  config: ${[...want].join(",")}`);
  }
  const names = REVIEW_TABLE.columns.map(([n]) => n);
  const stmt = db.prepare(`INSERT INTO ${REVIEW_TABLE.table} (${[...names, "status"].map(ident).join(", ")}) VALUES (${[...names, "status"].map(() => "?").join(", ")})`);
  db.transaction(() => {
    rows.forEach((r, i) => {
      if (r.family !== y.family || r.pdf_sha256 !== y.pdf_sha256) throw new Error(`${rel} row ${i + 2}: family or pdf_sha256 differs from pdf_years.csv`);
      const detail = Object.fromEntries(cfg.detail.filter((c) => r[c] !== "").map((c) => [c, r[c]]));
      const vals = REVIEW_TABLE.columns.map(([n, ty]) => {
        if (n === "detail") return Object.keys(detail).length ? JSON.stringify(detail) : "";
        const v = r[cfg.map[n]];
        return ty === I ? intOf(v, `${rel} row ${i + 2} ${cfg.map[n]}`) : v ?? "";
      });
      stmt.run(...vals, y.status);
    });
  })();
  return rows.length;
}

// ---------------------------------------------------------------- Schedule C x disclosure

const CITY_EIN = "136400434";
const SC_ORDER = ["body", "appendix_a", "appendix_b", "appendix_c"];
const SC_PREFERS = { body: ["speaker", "initiative"], appendix_a: ["aging"], appendix_b: ["local"], appendix_c: ["youth"] };
const STATUS_RANK = { cleared: 0, pending: 1, other: 2 };

/** Disclosure `source` -> stream (code/reconcile_disclosure_schedule_c.py stream_of). */
export function streamOf(source) {
  const s = String(source ?? "").trim().toLowerCase();
  if (s === "local" || s === "aging" || s === "youth") return s;
  return s.startsWith("speaker") ? "speaker" : "initiative";
}

const normName = (s) => String(s ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");

/**
 * The Schedule C session's disclosure alignment (code/schedc/disclosure.py `align`, PR #125),
 * ported line for line: (EIN, amount) as a multiset; the City's own EIN 13-6400434 also needs the
 * disclosure's legal name to be a prefix of the PDF's organization text (normalized). Allocation:
 * sections in order body, A, B, C; within a section by award_id; a row claims, among the free
 * candidates of its key, its section's preferred stream first, then Cleared before Pending, then
 * sheet order. Every unmatched row gets one waterfall reason. Report only: it never changes a value.
 *
 * awards: [{award_id, section, ein, amount, org}]; disc: [{row, ein, amount, status, name, source}]
 * in the workbook's order. Returns { pairs, pdfOnly, discOnly, ambiguous }.
 */
export function alignScheduleC(awards, disc) {
  const key = (ein, amount) => `${ein}|${Number(amount)}`;
  const byKey = new Map();
  disc.forEach((d, i) => {
    const k = key(d.ein, d.amount);
    if (!byKey.has(k)) byKey.set(k, []);
    byKey.get(k).push(i);
  });
  const stream = disc.map((d) => streamOf(d.source));
  const nameOk = (ein, dname, org) => {
    if (ein !== CITY_EIN) return true;
    const d = normName(dname);
    return d !== "" && normName(org).startsWith(d);
  };
  const taken = new Map();
  const pairs = new Map();
  const unmatched = [];
  for (const sec of SC_ORDER) {
    const rows = awards.filter((a) => a.section === sec).sort((a, b) => (a.award_id < b.award_id ? -1 : a.award_id > b.award_id ? 1 : 0));
    for (const a of rows) {
      if (!a.ein || a.amount === null || a.amount === undefined) {
        unmatched.push(a);
        continue;
      }
      const cands = (byKey.get(key(a.ein, a.amount)) ?? []).filter((i) => !taken.has(i) && nameOk(a.ein, disc[i].name, a.org));
      if (!cands.length) {
        unmatched.push(a);
        continue;
      }
      const pref = SC_PREFERS[sec];
      cands.sort((i, j) => {
        const pi = pref.includes(stream[i]) ? 0 : 1;
        const pj = pref.includes(stream[j]) ? 0 : 1;
        if (pi !== pj) return pi - pj;
        const ri = STATUS_RANK[disc[i].status] ?? 3;
        const rj = STATUS_RANK[disc[j].status] ?? 3;
        if (ri !== rj) return ri - rj;
        return disc[i].row - disc[j].row;
      });
      taken.set(cands[0], a.award_id);
      pairs.set(a.award_id, cands[0]);
    }
  }
  const ambiguous = new Set();
  for (const idxs of byKey.values()) {
    const claimed = idxs.filter((i) => taken.has(i));
    if (claimed.length && claimed.length < idxs.length && new Set(idxs.map((i) => `${stream[i]}|${disc[i].status}`)).size > 1) {
      idxs.forEach((i) => ambiguous.add(i));
    }
  }
  const free = disc.map((_, i) => i).filter((i) => !taken.has(i));
  const freeByEin = new Map();
  for (const i of free) {
    if (!freeByEin.has(disc[i].ein)) freeByEin.set(disc[i].ein, []);
    freeByEin.get(disc[i].ein).push(i);
  }
  const anyKey = new Set(byKey.keys());
  const discEins = new Set(disc.map((d) => d.ein));
  const pdfOnly = unmatched.map((a) => {
    let reason;
    let near = null;
    if (!a.ein || a.amount === null || a.amount === undefined) reason = "pdf_value_unreadable";
    else if (anyKey.has(key(a.ein, a.amount))) {
      reason = a.ein === CITY_EIN && byKey.get(key(a.ein, a.amount)).some((i) => !taken.has(i)) ? "city_ein_name_mismatch" : "key_already_claimed";
    } else if (freeByEin.get(a.ein)?.length) {
      reason = "amount_differs";
      near = freeByEin.get(a.ein).map((i) => disc[i].amount).sort((x, y) => Math.abs(x - a.amount) - Math.abs(y - a.amount))[0];
    } else reason = discEins.has(a.ein) ? "ein_fully_claimed" : "ein_not_in_disclosure";
    return { award: a, reason, near };
  });
  const scEins = new Set(awards.filter((a) => a.ein).map((a) => a.ein));
  const discOnly = free.map((i) => {
    const d = disc[i];
    const reason = d.ein === CITY_EIN && d.status === "pending" ? "city_ein_pending" : !scEins.has(d.ein) ? "ein_not_in_pdf" : "amount_or_count_differs";
    return { i, reason };
  });
  return { pairs, pdfOnly, discOnly, ambiguous };
}

/**
 * Build pdf_sc_disclosure for one loaded Schedule C year from the index's own disclosure table,
 * and stop if the port disagrees with the promoted file's disclosure_status / disclosure_reason on
 * any row (the Schedule C session's own result).
 */
function deriveScDisclosure(db, fy, y) {
  const awards = db.prepare("SELECT award_id, section, ein, amount, org, disclosure_status, disclosure_reason FROM pdf_schedule_c WHERE fiscal_year = ? AND family = 'schedule_c' AND status = ?").all(fy, y.status);
  const disc = db.prepare("SELECT source_row AS row, ein, amount, status_norm AS status, legal_name AS name, source FROM disclosure WHERE fiscal_year = ? ORDER BY rowid").all(fy);
  const r = alignScheduleC(awards, disc);
  const bad = [];
  const reasonOf = new Map(r.pdfOnly.map((u) => [u.award.award_id, u.reason]));
  for (const a of awards) {
    const i = r.pairs.get(a.award_id);
    const status = i === undefined ? "unmatched" : disc[i].status;
    const reason = i === undefined ? reasonOf.get(a.award_id) : "";
    if (status !== a.disclosure_status || reason !== (a.disclosure_reason ?? "")) bad.push(`${a.award_id}: ${status}/${reason} vs file ${a.disclosure_status}/${a.disclosure_reason}`);
  }
  if (bad.length) throw new Error(`pdf_sc_disclosure FY${fy}: the port of code/schedc/disclosure.py disagrees with the promoted file on ${bad.length} rows:\n  ${bad.slice(0, 10).join("\n  ")}`);
  const ins = db.prepare(`INSERT INTO pdf_sc_disclosure VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'schedule_c', ?)`);
  let n = 0;
  db.transaction(() => {
    const amb = (i) => (r.ambiguous.has(i) ? 1 : 0);
    for (const a of awards) {
      const i = r.pairs.get(a.award_id);
      if (i === undefined) continue;
      const d = disc[i];
      ins.run(fy, "matched", a.award_id, a.ein, a.amount, d.row, d.status, d.name, d.source, d.amount, "matched", amb(i), y.status);
      n++;
    }
    for (const u of r.pdfOnly) {
      ins.run(fy, "pdf_only", u.award.award_id, u.award.ein, u.award.amount, null, null, null, null, u.near, u.reason, 0, y.status);
      n++;
    }
    for (const { i, reason } of r.discOnly) {
      const d = disc[i];
      ins.run(fy, "disclosure_only", null, d.ein, null, d.row, d.status, d.name, d.source, d.amount, reason, amb(i), y.status);
      n++;
    }
  })();
  return { pdf_sc_disclosure: n };
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
