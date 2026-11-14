/**
 * capital-plan.mjs — OMB's Capital Commitment Plan and DCP's Capital Projects Database (CPDB) in
 * the index (#250, PR B; docs/plans/2026-11-13-250-capital-plan-and-cpdb.md).
 *
 *   capital_plan          NYC Open Data 2cmn-uidm (OMB), every release (pub_date). One row per
 *                         release x budget line x funding (CITY / NON CITY): four or five planned
 *                         years from yr1_fy. THOUSANDS of dollars, as published; the columns say
 *                         so (year1_amt_k ... year5_amt_k). A year OMB did not publish is NULL.
 *   cpdb_commitments      NYC Open Data djxg-kcfi (DCP): one planned commitment per project x
 *                         budget line x date. Dollars. The project's description, agency and ID
 *                         are the same on every row as in cpdb_projects (checked), and are read
 *                         from there by maprojid; the version is in capital_plan_sources.
 *   cpdb_codes            the names behind djxg-kcfi's codes: sponsor agency (sagencyacro ->
 *                         sagencyname) and commitment (commitmentcode -> commitmentdescription).
 *                         One name per code, or the build stops. typcname stays on each row: DCP
 *                         gives one type code several names ("REC").
 *   cpdb_projects         NYC Open Data fi59-268w (DCP): one row per FMS project (maprojid), its
 *                         planned, adopted, allocated, committed and spent totals. Dollars. NO
 *                         budget line: a project reaches a line only through cpdb_commitments, and
 *                         its totals are never split or summed to a line.
 *   capital_plan_sources  one row per dataset: file, sha256, rows, rowsUpdatedAt, retrieved, unit,
 *                         version.
 *
 * Read from the committed snapshots (source/open-data-<id>/<id>.csv.gz), each checked against its
 * MANIFEST (sha256 and row count) before a row is read. A mismatch, an unknown value, or a row that
 * does not fit is a stop. Values are as published; the only changes are the budget line's normal
 * form (the one code/build_capital_council.py norm_line writes, "AG D001"), dates as YYYY-MM-DD,
 * and a planned commitment's fiscal year (July to June).
 *
 * The 2cmn-uidm row with no release, line or year (amounts that look like grand totals) is not a
 * line; it is left out and named in its source row's note, as code/build_capital_council.py does.
 *
 * CPDB's unit: DCP never states it in writing (its data dictionary's unit column says only "double
 * precision"). BetaNYC checked that CPDB's City totals per budget line and fiscal year equal OMB's
 * (published in thousands) times 1,000. verifyCapitalPlan() repeats that check on every build, so
 * a CPDB published in thousands stops the build instead of serving figures 1,000 times too small.
 */
import { gunzipSync } from "zlib";
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { parse } from "csv-parse/sync";

const PLAN_UNIT = 'thousands of dollars (OMB\'s data dictionary, Capital_Commitment_Plan.xlsx: "The dollar values are in thousands.")';
const CPDB_UNIT =
  "dollars, not thousands (DCP does not state the unit; BetaNYC checked that CPDB's City totals equal OMB's, published in thousands, times 1,000)";

const AMT = "REAL";
const PLAN_AMTS = [1, 2, 3, 4, 5].map((i) => `year${i}_amt_k`);
const COMMIT_AMTS = ["ccnonexempt", "ccexempt", "totalcityplannedcommit", "nccstate", "nccfederal", "nccother",
  "totalnoncityplannedcommit", "totalplannedcommit"];
const STAGES = ["ccnonexempt", "ccexempt", "citycost", "nccstate", "nccfederal", "nccother", "noncitycost", "total"];
const PROJECT_AMTS = ["plannedcommit_ccnonexempt", "ccexempt", "totalcityplannedcommit", "nccstate", "nccfederal", "nccother",
  "totalnoncityplannedcommit", "totalplannedcommit",
  ...["adopt", "allocate", "commit", "spent"].flatMap((s) => STAGES.map((c) => `${s}_${c}`)), "spent_total_checkbooknyc"];

export const CAPITAL_PLAN_SCHEMA = {
  capital_plan: [
    ["pub_date", "TEXT"], ["projtype", "TEXT"], ["projtype_desc", "TEXT"], ["budline", "TEXT"],
    ["budget_line_norm", "TEXT"], ["budline_desc", "TEXT"], ["funding", "TEXT"], ["num_yrs", "INTEGER"],
    ["yr1_fy", "INTEGER"], ...PLAN_AMTS.map((c) => [c, AMT]), ["source_row", "TEXT"],
  ],
  cpdb_commitments: [
    ["maprojid", "TEXT"], ["sagencyacro", "TEXT"], ["budgetline", "TEXT"], ["budget_line_norm", "TEXT"],
    ["projecttype", "TEXT"], ["plancommdate", "TEXT"], ["plan_fy", "INTEGER"], ["commitmentcode", "TEXT"],
    ["typc", "TEXT"], ["typcname", "TEXT"], ...COMMIT_AMTS.map((c) => [c, AMT]), ["source_row", "TEXT"],
  ],
  cpdb_codes: [["kind", "TEXT"], ["code", "TEXT"], ["name", "TEXT"]],
  cpdb_projects: [
    ["ccpversion", "TEXT"], ["maprojid", "TEXT"], ["magencyacro", "TEXT"], ["magency", "TEXT"],
    ["magencyname", "TEXT"], ["description", "TEXT"], ["projectid", "TEXT"], ["mindate", "TEXT"],
    ["maxdate", "TEXT"], ["typecategory", "TEXT"], ...PROJECT_AMTS.map((c) => [c, AMT]), ["source_row", "TEXT"],
  ],
  capital_plan_sources: [
    ["dataset_id", "TEXT PRIMARY KEY"], ["title", "TEXT"], ["publisher", "TEXT"], ["file", "TEXT"], ["rows", "INTEGER"],
    ["rows_updated_at", "TEXT"], ["retrieved", "TEXT"], ["sha256", "TEXT"], ["unit", "TEXT"], ["version", "TEXT"],
    ["note", "TEXT"],
  ],
};
export const CAPITAL_PLAN_TABLES = Object.keys(CAPITAL_PLAN_SCHEMA);

export function capitalPlanSchemaSql() {
  return [
    ...Object.entries(CAPITAL_PLAN_SCHEMA).map(([t, cols]) => `CREATE TABLE ${t} (${cols.map(([c, ty]) => `${c} ${ty}`).join(", ")});`),
    "CREATE INDEX idx_plan_line ON capital_plan(budget_line_norm);",
    "CREATE INDEX idx_cpdb_line ON cpdb_commitments(budget_line_norm);",
    "CREATE INDEX idx_cpdb_proj ON cpdb_projects(maprojid);",
    "CREATE UNIQUE INDEX idx_cpdb_codes ON cpdb_codes(kind, code);",
  ].join("\n");
}

const DATASETS = {
  "2cmn-uidm": { title: "Capital Commitment Plan", publisher: "Mayor's Office of Management & Budget (OMB)", unit: PLAN_UNIT },
  "djxg-kcfi": { title: "Capital Projects Database (CPDB) - Commitments", publisher: "Department of City Planning (DCP)", unit: CPDB_UNIT },
  "fi59-268w": { title: "Capital Projects Database (CPDB) - Projects", publisher: "Department of City Planning (DCP)", unit: CPDB_UNIT },
};

/** One line, as code/parse_expense_disclosure.py _clean does for these fields: whitespace runs to one space. */
const clean = (v) => String(v ?? "").replace(/\s+/g, " ").trim();

/**
 * Budget line -> "AG D001", the normal form of code/build_capital_council.py norm_line. With OMB's
 * own project type the agency code is split off by it ("AGD001", "PVDN132"); otherwise the line
 * needs a space or hyphen after a one- or two-letter code ("AG-DN04L"). Anything else is "".
 */
export function normLine(raw, projtype) {
  const s = clean(raw).toUpperCase();
  if (!s) return "";
  const pt = clean(projtype).toUpperCase();
  if (pt && s.startsWith(pt)) {
    const rest = s.slice(pt.length).replace(/[\s-]+/g, "");
    return rest ? `${pt} ${rest}` : "";
  }
  const m = /^([A-Z]{1,2})[\s-]+([A-Z0-9]+)$/.exec(s);
  return m ? `${m[1]} ${m[2]}` : "";
}

/** A planned commitment date's fiscal year: July to June (2026-07-01 is FY2027). */
export function planFy(date) {
  return Number(date.slice(0, 4)) + (Number(date.slice(5, 7)) >= 7 ? 1 : 0);
}

function ymd(v, where) {
  const s = String(v ?? "");
  if (s === "") return null;
  if (!/^\d{4}-\d{2}-\d{2}(T|$)/.test(s)) throw new Error(`${where}: date ${JSON.stringify(s)}`);
  return s.slice(0, 10);
}

function amount(v, where) {
  if (v === "" || v == null) return null;
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error(`${where}: amount ${JSON.stringify(v)}`);
  return n;
}

function int(v, where) {
  const n = Number(v);
  if (v === "" || !Number.isInteger(n)) throw new Error(`${where}: ${JSON.stringify(v)} is not a whole number`);
  return n;
}

/** The snapshot's rows, after its bytes and row count are checked against its MANIFEST. */
function snapshot(io, id) {
  const rel = `source/open-data-${id}/${id}.csv.gz`;
  const man = io.readCsv(`source/open-data-${id}/MANIFEST.csv`).find((m) => m.file === `${id}.csv.gz`);
  if (!man) throw new Error(`${rel}: no row in its MANIFEST.csv`);
  const bytes = io.readBytes(rel);
  const sha = createHash("sha256").update(bytes).digest("hex");
  if (sha !== man.sha256) throw new Error(`${rel}: sha256 ${sha} differs from its MANIFEST (${man.sha256})`);
  const rows = parse(gunzipSync(bytes).toString("utf8"), { columns: true, skip_empty_lines: true, bom: true });
  if (rows.length !== Number(man.rows)) throw new Error(`${rel}: ${rows.length} rows, MANIFEST says ${man.rows}`);
  const rua = /rowsUpdatedAt (\d+)/.exec(man.note ?? "");
  if (!rua) throw new Error(`${rel}: its MANIFEST note has no rowsUpdatedAt`);
  const retrieved = (man.retrieved_at ?? "").slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(retrieved)) throw new Error(`${rel}: no retrieval date in its MANIFEST`);
  return {
    rows,
    source: {
      dataset_id: id, ...DATASETS[id], file: rel, sha256: sha,
      rows_updated_at: new Date(Number(rua[1]) * 1000).toISOString().slice(0, 10), retrieved,
    },
  };
}

function insertAll(db, table, rows) {
  const cols = CAPITAL_PLAN_SCHEMA[table].map(([c]) => c);
  const ins = db.prepare(`INSERT INTO ${table} (${cols.join(", ")}) VALUES (${cols.map((c) => "@" + c).join(", ")})`);
  db.transaction(() => {
    for (const r of rows) ins.run(r);
  })();
  return rows.length;
}

/** The one CPDB version a snapshot carries; two versions in one file is a stop. */
function oneVersion(rows, id) {
  const v = [...new Set(rows.map((r) => r.ccpversion))];
  if (v.length !== 1 || !v[0]) throw new Error(`${id}: ccpversion ${JSON.stringify(v)}; expected exactly one`);
  return v[0];
}

/** io: { readCsv(rel), readBytes(rel) }, both recording the file as an input. */
export function loadCapitalPlan(db, io) {
  const counts = {};
  const sources = [];

  // --- 2cmn-uidm: the commitment plan, every release ------------------------------------------
  {
    const { rows, source } = snapshot(io, "2cmn-uidm");
    const out = [];
    const stripped = [];
    let unnormed = 0;
    for (const r of rows) {
      const at = `2cmn-uidm ${r[":id"]}`;
      if (r.pub_date === "" && r.budline === "") {
        stripped.push(r[":id"]);
        continue;
      }
      if (!/^\d{8}$/.test(r.pub_date)) throw new Error(`${at}: pub_date ${JSON.stringify(r.pub_date)}`);
      if (!["CITY", "NON CITY"].includes(r.funding)) throw new Error(`${at}: funding ${JSON.stringify(r.funding)}`);
      const n = int(r.num_yrs_prsnt, `${at} num_yrs_prsnt`);
      if (n !== 4 && n !== 5) throw new Error(`${at}: num_yrs_prsnt ${n}`);
      // A line whose project type is not its prefix ("ED0408" under EP) has no normal form, as in
      // code/build_capital_council.py: kept, with budget_line_norm NULL, and counted in the note.
      const norm = normLine(r.budline, r.projtype) || null;
      if (!norm) unnormed++;
      const amts = Object.fromEntries(PLAN_AMTS.map((c, i) => [c, amount(r[`year${i + 1}_amt`], `${at} year${i + 1}_amt`)]));
      if (n === 4 && amts.year5_amt_k !== null) throw new Error(`${at}: a 4-year release with a fifth year`);
      out.push({
        pub_date: r.pub_date, projtype: r.projtype, projtype_desc: r.projtype_desc, budline: r.budline,
        budget_line_norm: norm, budline_desc: clean(r.budline_desc), funding: r.funding, num_yrs: n,
        yr1_fy: int(r.yr1_fy, `${at} yr1_fy`), ...amts, source_row: r[":id"],
      });
    }
    if (stripped.length !== 1) throw new Error(`2cmn-uidm: ${stripped.length} rows with no release or line; expected the one total row`);
    counts.capital_plan = insertAll(db, "capital_plan", out);
    sources.push({
      ...source, rows: out.length, version: "",
      note: `every release (pub_date); the row ${stripped[0]}, with no release, line or year (amounts that look like grand totals), is not loaded; ${unnormed} rows whose budline does not start with their projtype have no budget_line_norm (found by budline only)`,
    });
  }

  // --- fi59-268w: CPDB projects (first: the commitments read their project fields from here) ----
  const projects = new Map();
  {
    const { rows, source } = snapshot(io, "fi59-268w");
    const version = oneVersion(rows, "fi59-268w");
    const out = rows.map((r) => {
      const at = `fi59-268w ${r[":id"]}`;
      return {
        ccpversion: r.ccpversion, maprojid: r.maprojid, magencyacro: r.magencyacro, magency: r.magency,
        magencyname: r.magencyname, description: clean(r.description), projectid: r.projectid,
        mindate: ymd(r.mindate, `${at} mindate`), maxdate: ymd(r.maxdate, `${at} maxdate`), typecategory: r.typecategory,
        ...Object.fromEntries(PROJECT_AMTS.map((c) => [c, amount(r[c], `${at} ${c}`)])), source_row: r[":id"],
      };
    });
    for (const p of out) {
      if (projects.has(p.maprojid)) throw new Error(`fi59-268w: maprojid ${p.maprojid} appears twice`);
      projects.set(p.maprojid, p);
    }
    counts.cpdb_projects = insertAll(db, "cpdb_projects", out);
    sources.push({ ...source, rows: out.length, version, note: "one row per FMS project (maprojid); no budget line" });
  }

  // --- djxg-kcfi: CPDB planned commitments ----------------------------------------------------
  {
    const { rows, source } = snapshot(io, "djxg-kcfi");
    const version = oneVersion(rows, "djxg-kcfi");
    if (version !== sources.at(-1).version) throw new Error(`djxg-kcfi is CPDB ${version}, fi59-268w is ${sources.at(-1).version}`);
    const codes = new Map();
    const code = (kind, c, name, at) => {
      const k = `${kind}\t${c}`;
      if (codes.has(k) && codes.get(k).name !== name) throw new Error(`${at}: ${kind} ${c} is named both ${JSON.stringify(codes.get(k).name)} and ${JSON.stringify(name)}`);
      codes.set(k, { kind, code: c, name });
    };
    const out = rows.map((r) => {
      const at = `djxg-kcfi ${r[":id"]}`;
      const norm = normLine(r.budgetline);
      if (!norm) throw new Error(`${at}: budgetline ${JSON.stringify(r.budgetline)} has no normal form`);
      const d = ymd(r.plancommdate, `${at} plancommdate`);
      if (!d) throw new Error(`${at}: no plancommdate`);
      const p = projects.get(r.maprojid);
      if (!p) throw new Error(`${at}: maprojid ${r.maprojid} is not in fi59-268w`);
      if (p.magency !== r.magency || p.projectid !== r.projectid || p.description !== clean(r.projectdescription)) {
        throw new Error(`${at}: magency, projectid or description differs from fi59-268w's ${r.maprojid}`);
      }
      code("sponsor_agency", r.sagencyacro, r.sagencyname, at);
      code("commitment", r.commitmentcode, r.commitmentdescription, at);
      return {
        maprojid: r.maprojid, sagencyacro: r.sagencyacro, budgetline: r.budgetline, budget_line_norm: norm,
        projecttype: r.projecttype, plancommdate: d, plan_fy: planFy(d), commitmentcode: r.commitmentcode, typc: r.typc,
        typcname: r.typcname,
        ...Object.fromEntries(COMMIT_AMTS.map((c) => [c, amount(r[c], `${at} ${c}`)])), source_row: r[":id"],
      };
    });
    counts.cpdb_commitments = insertAll(db, "cpdb_commitments", out);
    counts.cpdb_codes = insertAll(db, "cpdb_codes", [...codes.values()]);
    sources.push({ ...source, rows: out.length, version, note: "one CPDB version; a planned commitment's fiscal year runs July to June; project fields from fi59-268w, code names in cpdb_codes" });
  }

  insertAll(db, "capital_plan_sources", sources);
  return { counts, sources };
}

/** Problems, or []: empty tables, two CPDB versions, a project with no commitments, or a CPDB unit that is not dollars. */
export function verifyCapitalPlan(db) {
  const problems = [];
  for (const t of ["capital_plan", "cpdb_commitments", "cpdb_projects"]) {
    if (db.prepare(`SELECT COUNT(*) n FROM ${t}`).get().n === 0) problems.push(`${t}: 0 rows`);
  }
  const v = db.prepare("SELECT COUNT(DISTINCT version) n FROM capital_plan_sources WHERE dataset_id IN ('djxg-kcfi', 'fi59-268w')").get().n;
  if (v !== 1) problems.push("CPDB: commitments and projects are not one version");
  const orphans = db.prepare("SELECT COUNT(*) n FROM cpdb_projects p WHERE NOT EXISTS (SELECT 1 FROM cpdb_commitments c WHERE c.maprojid = p.maprojid)").get().n;
  if (orphans) problems.push(`CPDB: ${orphans} project(s) with no planned commitment, so no budget line`);
  // The unit check (plan §1): CPDB's City total per line and fiscal year / OMB's newest release's
  // City amount (thousands), over every line-year both have; the median must be 1,000.
  const newest = db.prepare("SELECT MAX(pub_date) d FROM capital_plan").get().d;
  const ratios = db
    .prepare(
      `WITH omb AS (
         SELECT budget_line_norm l, yr1_fy + k.i fy,
                SUM(CASE k.i WHEN 0 THEN year1_amt_k WHEN 1 THEN year2_amt_k WHEN 2 THEN year3_amt_k WHEN 3 THEN year4_amt_k ELSE year5_amt_k END) amt
         FROM capital_plan, (SELECT 0 i UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) k
         WHERE pub_date = ? AND funding = 'CITY' GROUP BY 1, 2),
       cp AS (SELECT budget_line_norm l, plan_fy fy, SUM(totalcityplannedcommit) amt FROM cpdb_commitments GROUP BY 1, 2)
       SELECT cp.amt / omb.amt r FROM omb JOIN cp USING (l, fy) WHERE omb.amt IS NOT NULL AND omb.amt <> 0 ORDER BY r`
    )
    .all(newest)
    .map((x) => x.r);
  const median = ratios[Math.floor(ratios.length / 2)];
  if (ratios.length < 100 || median !== 1000) {
    problems.push(`CPDB unit check: median CPDB/OMB ratio ${median} over ${ratios.length} line-years against ${newest}; expected 1000 (CPDB in dollars, OMB in thousands)`);
  }
  return problems;
}

/** For build-index's io: the file's bytes, recorded as an input. */
export function bytesReader(repoPath) {
  return (rel) => readFileSync(repoPath(rel));
}
