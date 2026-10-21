#!/usr/bin/env node
/**
 * build-index.mjs — read the New-York-City-Budget repo's structured datasets and build the local
 * SQLite index (mcp/data/budget.db) that the MCP server queries.
 *
 * 2.0.0: STRUCTURED SOURCES ONLY. Every input is a spreadsheet the NYC Council published, a
 * dataset on NYC Open Data, or this repo's own manifest of those downloads:
 *
 *   data/disclosure_years.csv                          per-year workbook provenance (disclosure)
 *   data/fyNN/expense_disclosure/fyNN_expense_awards.csv   Council expense funding disclosure
 *   data/capital/council_capital_awards.csv            Council capital designations
 *   data/capital/council_vs_omb_by_budget_line.csv     the repo's Council-vs-OMB arithmetic
 *   source/{wayback-council,expense-funding-disclosure,open-data-t474-a92g}/MANIFEST.csv
 *   the capital source files themselves, read only to hash them
 *
 * The retired PDF extracts are never read: not data/fyNN/schedule_c/, its appendices or recovered
 * sidecars, data/fyNN/terms/, data/fyNN/capital/ (§254), transparency resolutions, data/combined/
 * or data/recovered/. The reviewed PDF tables (data/pdf_years.csv, data/fyNN/pdf/) have their own
 * gate: data/pdf_years.csv is always read, and a family's files only when its status is closed, or
 * reviewed under --include-reviewed --out <other file> (scripts/pdf-families.mjs).
 * Every file read is recorded in meta.inputs, and test/no-pdf-data.test.js fails if one of them
 * is not on the structured allowlist.
 *
 * Idempotent and atomic: the index is built into a sibling temp file, checked by
 * scripts/verify-index.mjs (a dataset with 0 rows, or a declared year that is missing, is a stop),
 * and only then renamed over data/budget.db. A failed build leaves the previous index in place,
 * and a reader that opens data/budget.db during a rebuild sees the old file or the new one, never
 * a half-built or empty one (#95: on npm 10, `npm pack --ignore-scripts` still runs `prepare`, and
 * the test suite's rebuild emptied the index under the test files reading it in parallel).
 * CSV parsing uses csv-parse (RFC 4180): names contain quoted commas.
 */
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { createHash } from "crypto";
import { readFileSync, existsSync, rmSync, mkdirSync, renameSync } from "fs";
import { join, dirname, basename, resolve } from "path";
import { fileURLToPath } from "url";
import { verifyIndex } from "./verify-index.mjs";
import { loadPdfFamilies, pdfSchemaSql, verifyPdf } from "./pdf-families.mjs";
// The folding rule db.ts applies to queries (src/fold.ts); `npm run build` always runs first.
import { fold } from "../dist/fold.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const MCP_ROOT = join(__dirname, "..");
const REPO = join(MCP_ROOT, "..");
const DEFAULT_DB_PATH = join(MCP_ROOT, "data", "budget.db");

/**
 * Reviewed PDF tables (scripts/pdf-families.mjs). Off by default: the MCP's own index, and the
 * npm package built from it, carry status = closed rows only. --include-reviewed also loads
 * status = reviewed families, and is refused unless --out names another file, so a reviewed
 * build can never replace data/budget.db (the explorer's local or demo build uses it).
 */
const ARGS = process.argv.slice(2);
const INCLUDE_REVIEWED = ARGS.includes("--include-reviewed");
const OUT_AT = ARGS.indexOf("--out");
const DB_PATH = OUT_AT >= 0 ? resolve(ARGS[OUT_AT + 1] ?? "") : DEFAULT_DB_PATH;
if (OUT_AT >= 0 && !ARGS[OUT_AT + 1]) throw new Error("build-index: --out needs a path");
if (INCLUDE_REVIEWED && DB_PATH === DEFAULT_DB_PATH) {
  throw new Error("build-index: --include-reviewed must not write data/budget.db; give --out <path>");
}
/** Built here, verified, then renamed over DB_PATH. Same directory, so the rename is atomic. */
const TMP_PATH = `${DB_PATH}.building-${process.pid}`;

/** Every repo-relative file this build reads, in order (meta.inputs). */
const INPUTS = [];

function log(event, detail) {
  console.error(JSON.stringify({ script: "build-index", event, ...detail, ts: new Date().toISOString() }));
}

function repoPath(rel) {
  const p = join(REPO, rel);
  if (!existsSync(p)) throw new Error(`Missing input (rebuild cannot proceed): ${rel}`);
  INPUTS.push(rel);
  return p;
}

function readCsv(rel) {
  return parse(readFileSync(repoPath(rel), "utf8"), {
    columns: true,
    skip_empty_lines: true,
    bom: true,
    trim: true,
  });
}

function sha256Of(rel) {
  return createHash("sha256").update(readFileSync(repoPath(rel))).digest("hex");
}

/** Digits-only EIN so "13-2612524" and "132612524" match. */
function normEin(v) {
  return (v ?? "").replace(/\D/g, "");
}

/** A required column; a CSV without it is a stop, never a silent blank. */
function need(rows, cols, what) {
  if (rows.length === 0) return;
  for (const c of cols) if (!(c in rows[0])) throw new Error(`${what}: no column ${c}`);
}

// ---------------------------------------------------------------- disclosure

// #72: every disclosure row carries a council_member_type; exactly the two member types carry a
// numeric Legistar person ID. A missing column or an inconsistent pair is a stop.
const MEMBER_TYPES = new Set(["member", "member_outside_fy", "ambiguous", "unresolved", "speaker",
  "delegation", "citywide", "district_label", "blank"]);
function memberId(r, year) {
  const t = r.council_member_type;
  if (!MEMBER_TYPES.has(t)) throw new Error(`FY${year} row ${r.source_row}: council_member_type ${JSON.stringify(t)}`);
  const id = r.council_member_id ?? "";
  if ((t === "member" || t === "member_outside_fy") !== /^\d+$/.test(id)) {
    throw new Error(`FY${year} row ${r.source_row}: council_member_id ${JSON.stringify(id)} does not fit type ${t}`);
  }
  return id;
}

// #69: duplicate_group is blank for a unique row, else a positive row number.
function dupGroup(r, year) {
  if (r.duplicate_group === "") return null;
  const g = Number(r.duplicate_group);
  if (!Number.isInteger(g) || g < 1) {
    throw new Error(`FY${year} row ${r.source_row}: duplicate_group ${JSON.stringify(r.duplicate_group)} is not a row number`);
  }
  return g;
}

// Excel error values, as the disclosure CSVs carry them verbatim (code/validate_data.py EXCEL_ERROR).
const EXCEL_ERROR = /^#(?:N\/A|REF!|VALUE!|DIV\/0!|NAME\?|NUM!|NULL!|SPILL!|CALC!|GETTING_DATA)$/;

// #70: zip_status vocabulary, and which statuses carry a 5-digit zip.
const ZIP_STATUSES = new Set(["valid", "padded", "trimmed", "repaired_extra_digit", "ambiguous_extra_digit",
  "not_a_zcta", "state_mismatch", "invalid", "blank"]);
const ZIP_HAS_VALUE = new Set(["valid", "padded", "trimmed", "repaired_extra_digit", "not_a_zcta", "state_mismatch"]);
function zipOf(r, year) {
  if (!ZIP_STATUSES.has(r.zip_status)) {
    throw new Error(`FY${year} row ${r.source_row}: zip_status ${JSON.stringify(r.zip_status)}`);
  }
  if (/^\d{5}$/.test(r.zip) !== ZIP_HAS_VALUE.has(r.zip_status)) {
    throw new Error(`FY${year} row ${r.source_row}: zip ${JSON.stringify(r.zip)} does not fit zip_status ${r.zip_status}`);
  }
  const ambiguous = r.zip_status === "ambiguous_extra_digit";
  if (ambiguous !== /^\d{5}(;\d{5})+$/.test(r.zip_candidates) || (!ambiguous && r.zip_candidates !== "")) {
    throw new Error(`FY${year} row ${r.source_row}: zip_candidates ${JSON.stringify(r.zip_candidates)} does not fit zip_status ${r.zip_status}`);
  }
  return r.zip;
}

// #89 A4 / B13: the cross-reference and flag vocabularies. Anything else is a stop.
const OD_MATCH = new Set(["", "exact", "rounded_cents", "rounded_dollars"]);
// row_flag joins one or more flags with ";" (no_grantee_ein is a rule: a blank or "NA" EIN).
const DISCLOSURE_ROW_FLAG_VALUES = new Set(["not_an_award", "no_grantee_ein"]);
const DISCLOSURE_ROW_FLAGS = {
  has: (v) => v === "" || v.split(";").every((x) => DISCLOSURE_ROW_FLAG_VALUES.has(x)),
};

// Substring-filtered text columns get a folded twin (<column>_fold) that queries match against
// as COALESCE(<column>_fold, <column>) ... COLLATE NOCASE. The twin is NULL only where folding
// changes nothing but ASCII letter case, which NOCASE already covers; that keeps the index from
// carrying a second copy of every name (a full copy added 15 MB to the package). The comparison
// is against an ASCII-only lower-casing on purpose: a full toLowerCase() would call "OssΘ"
// (t474 mojibake) unchanged by folding, store no twin, and the folded query "ossθ" would then
// miss the raw "OssΘ" under NOCASE, which folds ASCII only (review S2, 2026-10-17).
const DISCLOSURE_FOLD = ["legal_name", "council_member", "source", "agency", "program_name"];
const CAPITAL_FOLD = ["sponsor", "title", "description"];
const asciiLower = (s) => s.replace(/[A-Z]/g, (c) => c.toLowerCase());
const folded = (r, cols) =>
  Object.fromEntries(cols.map((c) => {
    const v = r[c] ?? "";
    const f = fold(v);
    return [`${c}_fold`, f === asciiLower(v) ? null : f];
  }));

const DISCLOSURE_COLUMNS = ["fiscal_year", "mocs_id", "od_mocs_id", "od_match", "source", "council_member",
  "council_member_id", "council_member_type", "legal_name", "ein", "status", "status_norm", "amount",
  "agency", "program_name", "address1", "address2", "city", "state", "postal_code", "zip", "zip_status",
  "zip_candidates", "fiscal_conduit", "fiscal_conduit_ein", "source_row", "duplicate_group", "row_flag"];

// ---------------------------------------------------------------- capital

const CAPITAL_COLUMNS = ["report_year", "amount_fy", "project_id", "borough", "budget_line", "budget_line_norm",
  "council_district", "sponsor", "title", "description", "amount", "source_kind", "source_file", "source_row",
  "row_flag"];
const CAPITAL_SOURCE_KINDS = new Set(["council_workbook", "open_data_t474"]);
const CAPITAL_ROW_FLAGS = new Set(["", "split_record_amount_unknown"]);
const BUDGET_LINE_NORM = /^[A-Z]{1,2} [A-Z0-9]+$/;

/**
 * council_district as searchable tokens: ",8,22," (numbers unpadded) for a Council workbook row;
 * NULL for a t474 row, because NYC Open Data typed that column as a number and collapsed every
 * comma list into one integer ("22, 25, 29" became 222529), so no t474 value can be trusted to be
 * one district. Tokens that are not one or two digits (FY2015 "1696") are kept as printed.
 */
function districtTokens(r) {
  if (r.source_kind !== "council_workbook") return null;
  const toks = r.council_district
    .split(",")
    .map((t) => t.trim())
    .filter((t) => t !== "")
    .map((t) => (/^\d{1,2}$/.test(t) ? String(Number(t)) : t));
  return toks.length ? `,${toks.join(",")},` : "";
}

// The Council RnD manifest has no url column; the folder's README records the capital file's URL
// ("Capital file URL", source/expense-funding-disclosure/README.md).
const RND_URLS = {
  "source/expense-funding-disclosure/Capital-Database.xlsx": "https://rnd.council.nyc.gov/src/assets/Capital-Database.xlsx",
};

/**
 * The manifest row that records a capital source file: its URL, capture timestamp, retrieval
 * time and sha256. A file with no manifest row is a stop.
 */
function manifestFor(rel, manifests) {
  for (const [prefix, man, keyOf] of manifests) {
    if (rel.startsWith(prefix)) {
      const key = keyOf(rel.slice(prefix.length));
      const row = man.find((m) => m.file === key);
      if (!row) throw new Error(`${rel}: no row for ${key} in ${prefix}MANIFEST.csv`);
      return row;
    }
  }
  throw new Error(`${rel}: not under a known source folder`);
}

function main() {
  mkdirSync(dirname(DB_PATH), { recursive: true });
  removeDb(TMP_PATH);
  try {
    build();
  } catch (err) {
    removeDb(TMP_PATH);
    throw err;
  }
}

/** A db file AND its WAL sidecars (a stale -wal makes the next open fail with
 * SQLITE_IOERR_SHORT_READ on network volumes). */
function removeDb(path) {
  for (const suffix of ["", "-wal", "-shm"]) {
    const f = path + suffix;
    if (existsSync(f)) rmSync(f);
  }
}

function build() {
  const db = new Database(TMP_PATH);
  db.pragma("journal_mode = WAL");
  db.exec(`
    CREATE TABLE disclosure (
      fiscal_year INTEGER, mocs_id TEXT, od_mocs_id TEXT, od_match TEXT, source TEXT,
      council_member TEXT, council_member_id TEXT, council_member_type TEXT, legal_name TEXT,
      ein TEXT, status TEXT, status_norm TEXT, amount REAL, agency TEXT, program_name TEXT,
      address1 TEXT, address2 TEXT, city TEXT, state TEXT, postal_code TEXT, zip TEXT,
      zip_status TEXT, zip_candidates TEXT,
      fiscal_conduit TEXT, fiscal_conduit_ein TEXT, source_row INTEGER,
      duplicate_group INTEGER, row_flag TEXT,
      legal_name_fold TEXT, council_member_fold TEXT, source_fold TEXT, agency_fold TEXT,
      program_name_fold TEXT
    );
    CREATE INDEX idx_disc_ein ON disclosure(ein);

    CREATE TABLE disclosure_years (
      fiscal_year INTEGER PRIMARY KEY, loaded INTEGER, source_kind TEXT, file TEXT, source_path TEXT,
      url TEXT, wayback_timestamp TEXT, sheet TEXT, retrieved TEXT, sha256 TEXT, award_rows INTEGER,
      early_snapshot INTEGER, note TEXT
    );

    CREATE TABLE capital_council (
      seq INTEGER, report_year INTEGER, amount_fy INTEGER, project_id TEXT, project_id_norm TEXT,
      borough TEXT, budget_line TEXT, budget_line_norm TEXT, council_district TEXT,
      district_tokens TEXT, sponsor TEXT, title TEXT, description TEXT, amount REAL,
      source_kind TEXT, source_file TEXT, source_row TEXT, row_flag TEXT,
      sponsor_fold TEXT, title_fold TEXT, description_fold TEXT
    );
    CREATE INDEX idx_cap_line ON capital_council(budget_line_norm);

    CREATE TABLE capital_sources (
      report_year INTEGER PRIMARY KEY, source_kind TEXT, source_file TEXT, url TEXT,
      wayback_timestamp TEXT, retrieved TEXT, sha256 TEXT, rows INTEGER, note TEXT
    );

    CREATE TABLE capital_vs_omb (
      report_year INTEGER, budget_line_norm TEXT, omb_pub_date TEXT, council_rows INTEGER,
      council_y1 INTEGER, omb_y1 INTEGER, council_y2 INTEGER, omb_y2 INTEGER, verdict TEXT
    );

    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
  `);
  db.exec(pdfSchemaSql());

  const counts = {};

  // --- disclosure: data/disclosure_years.csv drives which years load and what each cites -------
  // A loaded year's CSV row count must equal its award_rows, so the index can never serve a year
  // from a different snapshot than the one it names. FY2010 (loaded=no) is recorded, not loaded.
  const years = readCsv("data/disclosure_years.csv");
  need(years, ["fiscal_year", "loaded", "source_kind", "source_path", "url", "wayback_timestamp", "retrieved",
    "sha256", "sheet", "award_rows", "early_snapshot", "note"], "data/disclosure_years.csv");
  const insYear = db.prepare(
    `INSERT INTO disclosure_years VALUES (@fiscal_year, @loaded, @source_kind, @file, @source_path, @url,
       @wayback_timestamp, @sheet, @retrieved, @sha256, @award_rows, @early_snapshot, @note)`
  );
  const insDisc = db.prepare(
    `INSERT INTO disclosure (${[...DISCLOSURE_COLUMNS, ...DISCLOSURE_FOLD.map((c) => c + "_fold")].join(", ")})
     VALUES (${[...DISCLOSURE_COLUMNS, ...DISCLOSURE_FOLD.map((c) => c + "_fold")].map((c) => "@" + c).join(", ")})`
  );
  counts.disclosure = db.transaction(() => {
    let n = 0;
    for (const y of years) {
      const year = Number(y.fiscal_year);
      if (!["yes", "no"].includes(y.loaded)) throw new Error(`FY${year}: loaded ${JSON.stringify(y.loaded)}`);
      if (!["yes", ""].includes(y.early_snapshot)) throw new Error(`FY${year}: early_snapshot ${JSON.stringify(y.early_snapshot)}`);
      if (y.loaded === "no" && y.note.trim() === "") throw new Error(`FY${year}: not loaded and no note says why`);
      insYear.run({
        fiscal_year: year,
        loaded: y.loaded === "yes" ? 1 : 0,
        source_kind: y.source_kind,
        file: basename(y.source_path),
        source_path: y.source_path,
        url: y.url,
        wayback_timestamp: y.wayback_timestamp,
        sheet: y.sheet,
        retrieved: y.retrieved,
        sha256: y.sha256,
        award_rows: Number(y.award_rows),
        early_snapshot: y.early_snapshot === "yes" ? 1 : 0,
        note: y.note,
      });
      if (y.loaded !== "yes") continue;
      const key = `fy${String(year % 100).padStart(2, "0")}`;
      const rel = `data/${key}/expense_disclosure/${key}_expense_awards.csv`;
      const rows = readCsv(rel);
      need(rows, DISCLOSURE_COLUMNS, rel);
      if (rows.length !== Number(y.award_rows)) {
        throw new Error(`FY${year}: ${rows.length} rows in ${rel} but data/disclosure_years.csv says ${y.award_rows}`);
      }
      for (const r of rows) {
        if (Number(r.fiscal_year) !== year) throw new Error(`${rel} row ${r.source_row}: fiscal_year ${r.fiscal_year}`);
        for (const col of ["ein", "fiscal_conduit_ein"]) {
          if (EXCEL_ERROR.test(r[col] ?? "")) {
            throw new Error(`FY${year} row ${r.source_row}: ${col} is the Excel error ${r[col]}, not an EIN`);
          }
        }
        const amount = Number(r.amount);
        if (r.amount === "" || !Number.isFinite(amount)) {
          throw new Error(`FY${year} row ${r.source_row}: amount ${JSON.stringify(r.amount)} is not a number`);
        }
        if (!OD_MATCH.has(r.od_match) || (r.od_match === "") !== (r.od_mocs_id === "")) {
          throw new Error(`FY${year} row ${r.source_row}: od_mocs_id ${JSON.stringify(r.od_mocs_id)} / od_match ${JSON.stringify(r.od_match)}`);
        }
        if (!DISCLOSURE_ROW_FLAGS.has(r.row_flag)) {
          throw new Error(`FY${year} row ${r.source_row}: row_flag ${JSON.stringify(r.row_flag)}`);
        }
        insDisc.run({
          ...Object.fromEntries(DISCLOSURE_COLUMNS.map((c) => [c, r[c] ?? ""])),
          ...folded(r, DISCLOSURE_FOLD),
          fiscal_year: year,
          council_member_id: memberId(r, year),
          ein: normEin(r.ein),
          fiscal_conduit_ein: normEin(r.fiscal_conduit_ein),
          amount,
          zip: zipOf(r, year),
          source_row: Number.parseInt(r.source_row, 10),
          duplicate_group: dupGroup(r, year),
        });
        n++;
      }
    }
    return n;
  })();

  // --- capital: data/capital/council_capital_awards.csv ----------------------------------------
  const capRel = "data/capital/council_capital_awards.csv";
  const cap = readCsv(capRel);
  need(cap, CAPITAL_COLUMNS, capRel);
  const insCap = db.prepare(
    `INSERT INTO capital_council VALUES (@seq, @report_year, @amount_fy, @project_id, @project_id_norm,
       @borough, @budget_line, @budget_line_norm, @council_district, @district_tokens, @sponsor, @title,
       @description, @amount, @source_kind, @source_file, @source_row, @row_flag,
       @sponsor_fold, @title_fold, @description_fold)`
  );
  const filesByYear = new Map();
  counts.capital = db.transaction(() => {
    let seq = 0;
    for (const r of cap) {
      seq++;
      const at = `${capRel} line ${seq + 1}`;
      if (!CAPITAL_SOURCE_KINDS.has(r.source_kind)) throw new Error(`${at}: source_kind ${JSON.stringify(r.source_kind)}`);
      if (!CAPITAL_ROW_FLAGS.has(r.row_flag)) throw new Error(`${at}: row_flag ${JSON.stringify(r.row_flag)}`);
      if (r.budget_line_norm !== "" && !BUDGET_LINE_NORM.test(r.budget_line_norm)) {
        throw new Error(`${at}: budget_line_norm ${JSON.stringify(r.budget_line_norm)}`);
      }
      // An amount is blank exactly on a split record whose amount the Council's files cannot prove.
      const unknown = r.row_flag === "split_record_amount_unknown";
      if ((r.amount === "") !== unknown || (r.amount_fy === "") !== unknown) {
        throw new Error(`${at}: amount ${JSON.stringify(r.amount)} / amount_fy ${JSON.stringify(r.amount_fy)} vs row_flag ${JSON.stringify(r.row_flag)}`);
      }
      const amount = unknown ? null : Number(r.amount);
      if (amount !== null && !Number.isFinite(amount)) throw new Error(`${at}: amount ${JSON.stringify(r.amount)}`);
      const year = Number(r.report_year);
      if (!Number.isInteger(year)) throw new Error(`${at}: report_year ${JSON.stringify(r.report_year)}`);
      const seen = filesByYear.get(year) ?? new Map();
      const k = `${r.source_kind}\t${r.source_file}`;
      seen.set(k, (seen.get(k) ?? 0) + 1);
      filesByYear.set(year, seen);
      insCap.run({
        ...r,
        seq,
        report_year: year,
        amount_fy: unknown ? null : Number(r.amount_fy),
        project_id_norm: r.project_id.replace(/\s+/g, " ").toUpperCase(),
        district_tokens: districtTokens(r),
        amount,
        ...folded(r, CAPITAL_FOLD),
      });
    }
    return seq;
  })();

  // --- capital provenance: one source per report year, hashed here and checked ---------------
  const manifests = [
    ["source/wayback-council/", readCsv("source/wayback-council/MANIFEST.csv"), (k) => k],
    ["source/expense-funding-disclosure/", readCsv("source/expense-funding-disclosure/MANIFEST.csv"), (k) => k],
    ["source/open-data-t474-a92g/", readCsv("source/open-data-t474-a92g/MANIFEST.csv"), (k) => k],
  ];
  const insSrc = db.prepare(
    `INSERT INTO capital_sources VALUES (@report_year, @source_kind, @source_file, @url, @wayback_timestamp,
       @retrieved, @sha256, @rows, @note)`
  );
  db.transaction(() => {
    for (const [year, files] of [...filesByYear.entries()].sort((a, b) => a[0] - b[0])) {
      if (files.size !== 1) throw new Error(`capital report year ${year}: ${files.size} source files; expected one`);
      const [[k, rows]] = [...files.entries()];
      const [source_kind, source_file] = k.split("\t");
      const m = manifestFor(source_file, manifests);
      const sha = sha256Of(source_file);
      if (sha !== m.sha256) throw new Error(`${source_file}: sha256 ${sha} differs from its manifest (${m.sha256})`);
      // retrieved: the manifest's date. The wayback and Open Data manifests carry an ISO
      // timestamp (retrieved_at); the Council RnD manifest a date (retrieved).
      const retrieved = (m.retrieved_at ?? m.retrieved ?? "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(retrieved)) throw new Error(`${source_file}: no retrieval date in its manifest`);
      insSrc.run({
        report_year: year,
        source_kind,
        source_file,
        url: m.url ?? RND_URLS[source_file] ?? "",
        wayback_timestamp: m.wayback_timestamp ?? "",
        retrieved,
        sha256: sha,
        rows,
        note: m.note ?? "",
      });
    }
  })();

  // --- Council vs OMB by budget line (the repo's arithmetic, data/capital/RECONCILIATION.md §3) --
  const cmpRel = "data/capital/council_vs_omb_by_budget_line.csv";
  const cmp = readCsv(cmpRel);
  need(cmp, ["report_year", "budget_line_norm", "omb_pub_date", "council_rows", "council_y1", "omb_y1",
    "council_y2", "omb_y2", "verdict"], cmpRel);
  const VERDICTS = new Set(["match", "differ", "council_only", "omb_only"]);
  const insCmp = db.prepare(
    `INSERT INTO capital_vs_omb VALUES (@report_year, @budget_line_norm, @omb_pub_date, @council_rows,
       @council_y1, @omb_y1, @council_y2, @omb_y2, @verdict)`
  );
  counts.capital_vs_omb = db.transaction(() => {
    for (const r of cmp) {
      if (!VERDICTS.has(r.verdict)) throw new Error(`${cmpRel}: verdict ${JSON.stringify(r.verdict)}`);
      // One side is blank exactly when the line is absent from it: council_y1/y2 on omb_only,
      // omb_y1/y2 on council_only. Blank stays NULL (absent), never 0 (present with no money).
      const blankOk = (c) =>
        (r.verdict === "omb_only" && c.startsWith("council_y")) || (r.verdict === "council_only" && c.startsWith("omb_y"));
      const int = (c) => {
        if (r[c] === "" && blankOk(c)) return null;
        const v = Number(r[c]);
        if (r[c] === "" || !Number.isInteger(v)) throw new Error(`${cmpRel} ${r.report_year} ${r.budget_line_norm}: ${c} ${JSON.stringify(r[c])}`);
        return v;
      };
      insCmp.run({
        report_year: int("report_year"),
        budget_line_norm: r.budget_line_norm,
        omb_pub_date: r.omb_pub_date,
        council_rows: int("council_rows"),
        council_y1: int("council_y1"),
        omb_y1: int("omb_y1"),
        council_y2: int("council_y2"),
        omb_y2: int("omb_y2"),
        verdict: r.verdict,
      });
    }
    return cmp.length;
  })();

  // --- reviewed PDF tables, gated by status (scripts/pdf-families.mjs) ------------------------
  const pdf = loadPdfFamilies(db, { readCsv, sha256Of }, INCLUDE_REVIEWED);
  Object.assign(counts, pdf.counts);

  const setMeta = db.prepare("INSERT INTO meta (key, value) VALUES (?, ?)");
  setMeta.run("include_reviewed", INCLUDE_REVIEWED ? "yes" : "no");
  setMeta.run("built_at", new Date().toISOString());
  setMeta.run("source", "BetaNYC/New-York-City-Budget (committed structured datasets only)");
  setMeta.run("inputs", JSON.stringify(INPUTS));
  setMeta.run("counts", JSON.stringify(counts));

  // Rewrite the file without the free and part-filled pages row-by-row inserts leave behind.
  db.exec("VACUUM");

  // Fail loud before the index can ship: 0 rows, or a declared year missing, is a stop.
  const capitalRowsByYear = new Map();
  for (const r of cap) capitalRowsByYear.set(Number(r.report_year), (capitalRowsByYear.get(Number(r.report_year)) ?? 0) + 1);
  const problems = [...verifyIndex(db, { disclosureYears: years, capitalRowsByYear }), ...verifyPdf(db, pdf)];
  db.close();
  if (problems.length) {
    log("verify_failed", { problems });
    throw new Error(`build-index: the built index failed verification; data/budget.db was not replaced:\n  - ${problems.join("\n  - ")}`);
  }

  // Install: drop the old file's sidecars, then atomically replace it.
  for (const suffix of ["-wal", "-shm"]) if (existsSync(DB_PATH + suffix)) rmSync(DB_PATH + suffix);
  renameSync(TMP_PATH, DB_PATH);
  log("built", { db: DB_PATH, counts, inputs: INPUTS.length });
}

main();
