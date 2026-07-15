#!/usr/bin/env node
/**
 * build-index.mjs — read the New-York-City-Budget repo's own CSVs (../data/**)
 * and build a local SQLite index (mcp/data/budget.db) that the MCP server queries.
 *
 * Idempotent: the .db is deleted and rebuilt from scratch on every run, so
 * re-running never duplicates rows.
 *
 * Data source: this MCP lives inside the New-York-City-Budget repo (mcp/) and
 * reads the repo's real data/ tree directly (../data, one level up from mcp/) —
 * data/{fy25,fy26,fy27}/… + data/combined/legistar_crosswalk.csv. There is no
 * copied snapshot to keep in sync: data and query layer move together. Every
 * dollar figure was extracted deterministically from the NYC Council's
 * adopted-budget PDFs and reconciled against printed totals in this repo — this
 * script only loads those CSVs verbatim; it does not re-interpret any number.
 *
 * CSV parsing uses csv-parse (RFC 4180 aware) — a naive comma split corrupts
 * rows because organization names contain quoted commas (e.g.
 * "El Puente de Williamsburg, Inc.").
 */
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { readFileSync, existsSync, rmSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const MCP_ROOT = join(__dirname, ".."); // .../New-York-City-Budget/mcp
// Read the parent repo's real data/ tree directly — no vendored snapshot to drift.
const SRC = join(MCP_ROOT, "..", "data");
// Built index stays inside mcp/ (git-ignored), out of the repo's tracked data/.
const DB_PATH = join(MCP_ROOT, "data", "budget.db");

// Per-dataset year coverage. Each list is the set of fiscal years that actually have a parsed,
// QA-cleared CSV of that document type in ../data/ (see code/PARSING.md + data/QA-REPORT.md).
// These differ by dataset — e.g. Terms has no FY19/FY20 document, Capital has no FY21 detail
// book — so each ingest loop is driven by its own list, and list_available_fiscal_years reports
// exactly these back. Award-bearing years start at FY2015 (first EIN-level Schedule C); FY2009–
// FY2014 are initiatives-only (no EIN) and are DELIBERATELY excluded from the award tools.
const yr = (n) => ({ key: `fy${n}`, year: 2000 + n });
const AWARD_YEARS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27].map(yr);
const TERMS_YEARS = [15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27].map(yr); // no FY19/FY20 T&C doc
const CAPITAL_YEARS = [20, 22, 23, 24, 25, 26, 27].map(yr); // no FY21 detail book
// Transparency: every parsed resolution-document year. FY2010–FY2013 are LOW org/program text
// confidence (financial columns reliable); surfaced downstream so callers join on EIN.
const TRANSPARENCY_YEARS = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26].map(yr);
const TRANSPARENCY_LOW_TEXT_CONFIDENCE = new Set([2010, 2011, 2012, 2013]);

function log(event, detail) {
  console.error(
    JSON.stringify({ script: "build-index", event, ...detail, ts: new Date().toISOString() })
  );
}

/** Digits-only EIN so "13-2612524" and "132612524" match. */
function normEin(v) {
  return (v ?? "").replace(/\D/g, "");
}

/** Parse an integer dollar amount; tolerate commas/$/whitespace and leading "-". Empty → null. */
function parseAmount(v) {
  if (v == null) return null;
  const s = String(v).replace(/[$,\s]/g, "");
  if (s === "" || s === "-") return null;
  const n = Number.parseInt(s, 10);
  return Number.isNaN(n) ? null : n;
}

function readCsv(path) {
  if (!existsSync(path)) {
    throw new Error(`Missing source CSV (rebuild cannot proceed): ${path}`);
  }
  return parse(readFileSync(path, "utf8"), {
    columns: true,
    skip_empty_lines: true,
    bom: true,
    trim: true,
  });
}

function main() {
  if (!existsSync(SRC)) {
    log("fatal", { reason: "repo data/ tree missing (expected ../data relative to mcp/)", path: SRC });
    process.exit(1);
  }
  mkdirSync(dirname(DB_PATH), { recursive: true });
  // Idempotent rebuild: drop the db AND its WAL sidecars. Removing only budget.db but leaving a
  // stale budget.db-wal / -shm behind makes the next open fail with SQLITE_IOERR_SHORT_READ
  // (observed on network volumes), so clear all three.
  for (const suffix of ["", "-wal", "-shm"]) {
    const f = DB_PATH + suffix;
    if (existsSync(f)) rmSync(f);
  }

  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");

  db.exec(`
    CREATE TABLE awards (
      fiscal_year INTEGER, category TEXT, initiative TEXT, award_type TEXT,
      member TEXT, organization TEXT, program TEXT, ein TEXT,
      amount INTEGER, agency TEXT, purpose TEXT
    );
    CREATE INDEX idx_awards_ein ON awards(ein);
    CREATE INDEX idx_awards_member ON awards(member);
    CREATE INDEX idx_awards_fy ON awards(fiscal_year);

    CREATE TABLE transparency (
      source_fy INTEGER, resolution TEXT, date TEXT, chart TEXT, fiscal_year INTEGER, action TEXT,
      source TEXT, council_member TEXT, organization TEXT, program TEXT,
      ein TEXT, amount INTEGER, agency TEXT, agy_num TEXT, ua TEXT,
      purpose TEXT, flags TEXT, low_text_confidence INTEGER
    );
    CREATE INDEX idx_tr_ein ON transparency(ein);
    CREATE INDEX idx_tr_member ON transparency(council_member);
    CREATE INDEX idx_tr_source_fy ON transparency(source_fy);
    CREATE INDEX idx_tr_fy ON transparency(fiscal_year);

    CREATE TABLE capital (
      fiscal_year INTEGER, part TEXT, agency TEXT, budget_line TEXT, sub_id TEXT,
      boro TEXT, fy1 INTEGER, fy2 INTEGER, fy3 INTEGER, fy4 INTEGER,
      sponsor TEXT, title TEXT, building_code TEXT, school_code TEXT, action TEXT
    );
    CREATE INDEX idx_cap_sponsor ON capital(sponsor);
    CREATE INDEX idx_cap_agency ON capital(agency);
    CREATE INDEX idx_cap_fy ON capital(fiscal_year);

    CREATE TABLE terms (
      fiscal_year INTEGER, item_number TEXT, agency_name TEXT, agency_code TEXT,
      units_of_appropriation TEXT, num_units TEXT, report_deadlines TEXT,
      coverage_period TEXT, condition_text TEXT
    );
    CREATE INDEX idx_terms_fy ON terms(fiscal_year);
    CREATE INDEX idx_terms_agency ON terms(agency_name);

    CREATE TABLE crosswalk (
      fiscal_year INTEGER, document_type TEXT, local_file TEXT,
      legistar_matter_number TEXT, legistar_url TEXT, adoption_date TEXT,
      status TEXT, notes TEXT
    );
    CREATE INDEX idx_cw_fy ON crosswalk(fiscal_year);
    CREATE INDEX idx_cw_type ON crosswalk(document_type);

    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
  `);

  const counts = {};

  // --- awards (per-year Schedule C; fiscal_year injected from the folder) ---
  const insAward = db.prepare(
    `INSERT INTO awards (fiscal_year, category, initiative, award_type, member,
       organization, program, ein, amount, agency, purpose)
     VALUES (@fiscal_year, @category, @initiative, @award_type, @member,
       @organization, @program, @ein, @amount, @agency, @purpose)`
  );
  counts.awards = db.transaction(() => {
    let n = 0;
    for (const { key, year } of AWARD_YEARS) {
      const rows = readCsv(join(SRC, key, "schedule_c", `${key}_schedule_c_awards.csv`));
      for (const r of rows) {
        insAward.run({
          fiscal_year: year,
          category: r.category ?? "",
          initiative: r.initiative ?? "",
          award_type: r.award_type ?? "",
          member: r.member ?? "",
          organization: r.organization ?? "",
          program: r.program ?? "",
          ein: normEin(r.ein),
          amount: parseAmount(r.amount),
          agency: r.agency ?? "",
          purpose: r.purpose ?? "",
        });
        n++;
      }
    }
    return n;
  })();

  // --- terms & conditions (per-year) ---
  const insTerm = db.prepare(
    `INSERT INTO terms (fiscal_year, item_number, agency_name, agency_code,
       units_of_appropriation, num_units, report_deadlines, coverage_period, condition_text)
     VALUES (@fiscal_year, @item_number, @agency_name, @agency_code,
       @units_of_appropriation, @num_units, @report_deadlines, @coverage_period, @condition_text)`
  );
  counts.terms = db.transaction(() => {
    let n = 0;
    for (const { key, year } of TERMS_YEARS) {
      const rows = readCsv(join(SRC, key, "terms", `${key}_terms_and_conditions.csv`));
      for (const r of rows) {
        insTerm.run({
          fiscal_year: year,
          item_number: r.item_number ?? "",
          agency_name: r.agency_name ?? "",
          agency_code: r.agency_code ?? "",
          units_of_appropriation: r.units_of_appropriation ?? "",
          num_units: r.num_units ?? "",
          report_deadlines: r.report_deadlines ?? "",
          coverage_period: r.coverage_period ?? "",
          condition_text: r.condition_text ?? "",
        });
        n++;
      }
    }
    return n;
  })();

  // --- capital (§254; every year loads its `${key}_capital_projects.csv`) ---
  // Each year's file is the reconciled Council-additions Capital Project Detail in the shared
  // 13-column schema (part, agency, budget_line, sub_id, boro, fy1..fy4, sponsor, title,
  // building_code, school_code). FY2025 was reparsed from the FY2025 Supporting Detail Book
  // (PR #21) into this same schema, so it loads exactly like FY2026/FY2027. Loading is by
  // explicit filename — the renamed provenance file (fy25_capital_changes_appropriation.csv,
  // which carries the legacy `action` column) and the Part III sidecar
  // (fy25_capital_noncity_by_entity.csv) are intentionally NOT indexed. The `action` column is
  // retained in the schema for back-compat but is empty for every currently-loaded row.
  const insCap = db.prepare(
    `INSERT INTO capital (fiscal_year, part, agency, budget_line, sub_id, boro,
       fy1, fy2, fy3, fy4, sponsor, title, building_code, school_code, action)
     VALUES (@fiscal_year, @part, @agency, @budget_line, @sub_id, @boro,
       @fy1, @fy2, @fy3, @fy4, @sponsor, @title, @building_code, @school_code, @action)`
  );
  counts.capital = db.transaction(() => {
    let n = 0;
    for (const { key, year } of CAPITAL_YEARS) {
      const rows = readCsv(join(SRC, key, "capital", `${key}_capital_projects.csv`));
      for (const r of rows) {
        insCap.run({
          fiscal_year: year,
          part: r.part ?? "",
          agency: r.agency ?? "",
          budget_line: r.budget_line ?? "",
          sub_id: r.sub_id ?? "",
          boro: r.boro ?? "",
          fy1: parseAmount(r.fy1),
          fy2: parseAmount(r.fy2),
          fy3: parseAmount(r.fy3),
          fy4: parseAmount(r.fy4),
          sponsor: r.sponsor ?? "",
          title: r.title ?? "",
          building_code: r.building_code ?? "",
          school_code: r.school_code ?? "",
          action: r.action ?? "",
        });
        n++;
      }
    }
    return n;
  })();

  // --- transparency resolutions (FY2010–FY2024 + FY2026) ---
  // `source_fy` = the resolution document's fiscal year (the folder), which is the reliable,
  // always-present per-year axis; the row-level `fiscal_year` is the embedded *designation* year,
  // which is often blank in FY2010–FY2013 (DATA-ANOMALIES #11). `low_text_confidence` flags the
  // FY2010–FY2013 years whose org/program TEXT is garbled (financials reliable; join on EIN).
  const insTr = db.prepare(
    `INSERT INTO transparency (source_fy, resolution, date, chart, fiscal_year, action, source,
       council_member, organization, program, ein, amount, agency, agy_num, ua, purpose, flags,
       low_text_confidence)
     VALUES (@source_fy, @resolution, @date, @chart, @fiscal_year, @action, @source,
       @council_member, @organization, @program, @ein, @amount, @agency, @agy_num, @ua, @purpose,
       @flags, @low_text_confidence)`
  );
  counts.transparency = db.transaction(() => {
    let n = 0;
    for (const { key, year } of TRANSPARENCY_YEARS) {
      const lowConf = TRANSPARENCY_LOW_TEXT_CONFIDENCE.has(year) ? 1 : 0;
      const rows = readCsv(join(SRC, key, "transparency-resolutions", `${key}_transparency_all.csv`));
      for (const r of rows) {
        const fy = Number.parseInt(r.fiscal_year, 10);
        insTr.run({
          source_fy: year,
          resolution: r.resolution ?? "",
          date: r.date ?? "",
          chart: r.chart ?? "",
          fiscal_year: Number.isNaN(fy) ? null : fy,
          action: r.action ?? "",
          source: r.source ?? "",
          council_member: r.council_member ?? "",
          organization: r.organization ?? "",
          program: r.program ?? "",
          ein: normEin(r.ein),
          amount: parseAmount(r.amount),
          agency: r.agency ?? "",
          agy_num: r.agy_num ?? "",
          ua: r.ua ?? "",
          purpose: r.purpose ?? "",
          flags: r.flags ?? "",
          low_text_confidence: lowConf,
        });
        n++;
      }
    }
    return n;
  })();

  // --- legistar crosswalk (FY2008–FY2027; provenance index, not parsed data) ---
  const insCw = db.prepare(
    `INSERT INTO crosswalk (fiscal_year, document_type, local_file,
       legistar_matter_number, legistar_url, adoption_date, status, notes)
     VALUES (@fiscal_year, @document_type, @local_file,
       @legistar_matter_number, @legistar_url, @adoption_date, @status, @notes)`
  );
  counts.crosswalk = db.transaction(() => {
    let n = 0;
    const rows = readCsv(join(SRC, "combined", "legistar_crosswalk.csv"));
    for (const r of rows) {
      const fy = Number.parseInt(r.fiscal_year, 10);
      insCw.run({
        fiscal_year: Number.isNaN(fy) ? null : fy,
        document_type: r.document_type ?? "",
        local_file: r.local_file ?? "",
        legistar_matter_number: r.legistar_matter_number ?? "",
        legistar_url: r.legistar_url ?? "",
        adoption_date: r.adoption_date ?? "",
        status: r.status ?? "",
        notes: r.notes ?? "",
      });
      n++;
    }
    return n;
  })();

  const setMeta = db.prepare("INSERT INTO meta (key, value) VALUES (?, ?)");
  setMeta.run("built_at", new Date().toISOString());
  setMeta.run("source", "BetaNYC/New-York-City-Budget (committed snapshot)");
  setMeta.run(
    "parsed_fiscal_years",
    JSON.stringify({
      awards: AWARD_YEARS.map((y) => y.year),
      terms: TERMS_YEARS.map((y) => y.year),
      capital: CAPITAL_YEARS.map((y) => y.year),
      transparency: TRANSPARENCY_YEARS.map((y) => y.year),
    })
  );
  setMeta.run("counts", JSON.stringify(counts));

  db.close();
  log("built", { db: DB_PATH, counts });
}

main();
