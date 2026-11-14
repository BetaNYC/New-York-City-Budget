/**
 * OMB's Capital Commitment Plan (NYC Open Data 2cmn-uidm) and DCP's Capital Projects Database
 * (CPDB: djxg-kcfi commitments, fi59-268w projects), from the index's capital_plan, cpdb_* and
 * capital_plan_sources tables (scripts/capital-plan.mjs, #250).
 *
 * Units are always said in words: the plan is in THOUSANDS of dollars, as OMB publishes it; CPDB
 * is in dollars, which DCP does not state (BetaNYC's check: CPDB = OMB's thousands x 1,000).
 * Figures from different sources are never added together.
 */
import { getDb } from "./db.js";

export interface CapitalPlanSource {
  dataset_id: string;
  title: string;
  publisher: string;
  file: string;
  rows: number;
  rows_updated_at: string;
  retrieved: string;
  sha256: string;
  unit: string;
  version: string;
  note: string;
}

/** YYYYMMDD -> YYYY-MM-DD. */
export const isoDate = (d: string) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;

export function capitalPlanSources(): Map<string, CapitalPlanSource> {
  const rows = getDb().prepare("SELECT * FROM capital_plan_sources").all() as CapitalPlanSource[];
  return new Map(rows.map((r) => [r.dataset_id, r]));
}

export function capitalPlanReleases(): string[] {
  return (getDb().prepare("SELECT DISTINCT pub_date FROM capital_plan ORDER BY pub_date").all() as { pub_date: string }[]).map(
    (r) => r.pub_date
  );
}

/** The year list's lines for the plan and CPDB (list_available_fiscal_years). */
export function capitalPlanYearsSection(): string[] {
  const src = capitalPlanSources();
  const plan = src.get("2cmn-uidm");
  const commits = src.get("djxg-kcfi");
  const projects = src.get("fi59-268w");
  if (!plan || !commits || !projects) return ["Capital Commitment Plan and CPDB: not in this index."];
  const rel = capitalPlanReleases();
  const n = (v: number) => v.toLocaleString("en-US");
  return [
    `OMB Capital Commitment Plan (NYC Open Data ${plan.dataset_id}): ${rel.length} releases, ${isoDate(rel[0])} to ${isoDate(rel[rel.length - 1])}; ${n(plan.rows)} release × budget line × funding rows, each with four or five planned fiscal years. In ${plan.unit.split(" (")[0]}, as OMB publishes it. Snapshot retrieved ${plan.retrieved}.`,
    `DCP Capital Projects Database (CPDB) version ${commits.version}, published ${commits.rows_updated_at}: ${n(commits.rows)} planned commitments (${commits.dataset_id}) and ${n(projects.rows)} projects (${projects.dataset_id}). One version only, so it cannot show change over time. In dollars: DCP does not state the unit; BetaNYC checked that CPDB's City totals equal OMB's (in thousands) times 1,000. Snapshots retrieved ${commits.retrieved} and ${projects.retrieved}.`,
    "  Both link to the Council's capital list by budget line only, never by project: one budget line holds many projects.",
  ];
}

// ===========================================================================
// search_capital_plan (#250, PR C)
// ===========================================================================

/** "P D018", "P-D018", "PD018" -> "PD018": the one key every source's budget line reduces to. */
const fmtN = (v: number) => v.toLocaleString("en-US");
const lineKey = (s: string) => s.replace(/[\s-]/g, "").toUpperCase();
const signed = (v: number, s: string) => (v < 0 ? `-$${s}` : `$${s}`);
/** CPDB dollars, shown to the dollar. */
export const dollars = (v: number | null) => (v == null ? "—" : signed(v, Math.abs(Math.round(v)).toLocaleString("en-US")));
/** OMB's figure as published, in thousands, said in words. */
export const thousands = (v: number | null) =>
  v == null ? "—" : `${signed(v, Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 2 }))} thousand`;

export const PLAN_FUNDING = ["CITY", "NON CITY"] as const;

export const PLAN_CAVEAT =
  "Caveat: these sources link to each other and to the Council's capital list by budget line only, never by project: Council project IDs appear in no OMB or DCP dataset, and one budget line holds many projects. Figures from different sources are never added together here. OMB's plan is in thousands of dollars, as published; CPDB is in dollars. CPDB is one version, so it cannot show change over time; the plan's releases can. A project's CPDB totals are the whole project's, across all its budget lines, and are never split or summed to one line. CPDB's spent and Checkbook figures are DCP's per project; for spending detail use @betanyc/nyc-checkbook-mcp.";

interface PlanRow {
  pub_date: string;
  budline: string;
  budget_line_norm: string | null;
  budline_desc: string;
  funding: string;
  yr1_fy: number;
  year1_amt_k: number | null;
  year2_amt_k: number | null;
  year3_amt_k: number | null;
  year4_amt_k: number | null;
  year5_amt_k: number | null;
}

interface ProjectRow {
  maprojid: string;
  magencyacro: string;
  magencyname: string;
  description: string;
  mindate: string | null;
  maxdate: string | null;
  totalplannedcommit: number | null;
  adopt_total: number | null;
  allocate_total: number | null;
  commit_total: number | null;
  spent_total: number | null;
  spent_total_checkbooknyc: number | null;
}

const planYears = (r: PlanRow) =>
  [r.year1_amt_k, r.year2_amt_k, r.year3_amt_k, r.year4_amt_k, r.year5_amt_k]
    .map((v, i) => (v == null ? null : `FY${r.yr1_fy + i} ${thousands(v)}`))
    .filter((x): x is string => x != null)
    .join(" · ");

/** Every release date, YYYYMMDD. */
export function allPlanReleases(): string[] {
  return capitalPlanReleases();
}

function projectLines(maprojid: string): string[] {
  return (
    getDb().prepare("SELECT DISTINCT budget_line_norm FROM cpdb_commitments WHERE maprojid = ? ORDER BY 1").all(maprojid) as { budget_line_norm: string }[]
  ).map((r) => r.budget_line_norm);
}

function projectTotals(p: ProjectRow): string {
  return `planned ${dollars(p.totalplannedcommit)} · adopted ${dollars(p.adopt_total)} · allocated ${dollars(p.allocate_total)} · committed ${dollars(p.commit_total)} · spent ${dollars(p.spent_total)} (DCP's figure) · Checkbook NYC checks ${dollars(p.spent_total_checkbooknyc)}`;
}

function sourcesFooter(version: string): string {
  const src = capitalPlanSources();
  const s = (id: string) => src.get(id);
  return [
    "---",
    `Source: NYC Open Data ${"2cmn-uidm"} (OMB's Capital Commitment Plan; snapshot retrieved ${s("2cmn-uidm")?.retrieved}), djxg-kcfi and fi59-268w (DCP's Capital Projects Database, version ${version}, published ${s("djxg-kcfi")?.rows_updated_at}; retrieved ${s("djxg-kcfi")?.retrieved} and ${s("fi59-268w")?.retrieved}), committed in the source repo with their manifests; the Council's rows from data/capital/council_capital_awards.csv.`,
  ].join("\n");
}

export interface CapitalPlanArgs {
  budget_line?: string;
  project_id?: string;
  /** YYYYMMDD, already checked against allPlanReleases(). */
  release?: string;
  funding?: (typeof PLAN_FUNDING)[number];
  limit: number;
}

/** The answer's text, without the server's own "Served by" line. */
export function searchCapitalPlanText(a: CapitalPlanArgs): string {
  const db = getDb();
  const version = capitalPlanSources().get("djxg-kcfi")?.version ?? "";
  const unitCpdb = "In dollars: DCP does not state the unit; BetaNYC checked that CPDB's City totals equal OMB's (in thousands) times 1,000.";
  const L: string[] = [];

  if (a.project_id != null) {
    const p = db.prepare("SELECT * FROM cpdb_projects WHERE UPPER(maprojid) = UPPER(?)").get(a.project_id.trim()) as ProjectRow | undefined;
    if (!p) return [`Project ${JSON.stringify(a.project_id)} is not in CPDB version ${version} (fi59-268w). project_id is DCP's maprojid: the managing agency's three digits, then the project ID, e.g. 850GKOH15-01.`, "", PLAN_CAVEAT, "", sourcesFooter(version)].join("\n");
    const lines = projectLines(p.maprojid);
    L.push(
      `CPDB project ${p.maprojid} · "${p.description}" · managed by ${p.magencyname} (${p.magencyacro}) · planned commitments ${p.mindate ?? "?"} to ${p.maxdate ?? "?"}`,
      `CPDB version ${version}. ${unitCpdb}`,
      "",
      `Project totals (fi59-268w; the whole project, all ${lines.length} of its budget lines): ${projectTotals(p)}`,
      "",
      `Planned commitments by budget line and fiscal year (djxg-kcfi), City / Non-City:`
    );
    for (const line of lines) {
      const fy = db
        .prepare(
          "SELECT plan_fy, SUM(totalcityplannedcommit) c, SUM(totalnoncityplannedcommit) nc FROM cpdb_commitments WHERE maprojid = ? AND budget_line_norm = ? GROUP BY plan_fy ORDER BY plan_fy"
        )
        .all(p.maprojid, line) as { plan_fy: number; c: number; nc: number }[];
      L.push(`  ${line}: ` + fy.map((r) => `FY${r.plan_fy} City ${dollars(r.c)} / Non-City ${dollars(r.nc)}`).join(" · "));
    }
    L.push("", "For a line's OMB plan and the Council's rows on it, call search_capital_plan with budget_line.", "", PLAN_CAVEAT, "", sourcesFooter(version));
    return L.join("\n");
  }

  const key = lineKey(a.budget_line ?? "");
  const shown = a.budget_line ?? "";
  // --- 1. OMB's plan ------------------------------------------------------------------------
  const plan = (
    db
      .prepare(
        "SELECT * FROM capital_plan WHERE REPLACE(REPLACE(budline, ' ', ''), '-', '') = ? ORDER BY pub_date DESC, funding"
      )
      .all(key) as PlanRow[]
  ).filter((r) => !a.funding || r.funding === a.funding);
  const cpdb = db
    .prepare("SELECT COUNT(*) n, COUNT(DISTINCT maprojid) p FROM cpdb_commitments WHERE REPLACE(budget_line_norm, ' ', '') = ?")
    .get(key) as { n: number; p: number };
  const council = db
    .prepare(
      "SELECT report_year, COUNT(*) n, SUM(amount) amt, SUM(amount IS NULL) unknown FROM capital_council WHERE REPLACE(budget_line_norm, ' ', '') = ? GROUP BY report_year ORDER BY report_year"
    )
    .all(key) as { report_year: number; n: number; amt: number | null; unknown: number }[];
  if (!plan.length && !cpdb.n && !council.length) {
    return [`Budget line ${shown} is not in OMB's Capital Commitment Plan (any release${a.funding ? `, ${a.funding} funding` : ""}), in CPDB version ${version}, or in the Council's capital list.`, "", PLAN_CAVEAT, "", sourcesFooter(version)].join("\n");
  }
  const releases = [...new Set(plan.map((r) => r.pub_date))];
  const rel = a.release ?? releases[0];
  const atRel = plan.filter((r) => r.pub_date === rel);
  const desc = (atRel[0] ?? plan[0])?.budline_desc;
  L.push(`Budget line ${atRel[0]?.budget_line_norm ?? plan[0]?.budget_line_norm ?? shown}${desc ? ` · "${desc}"` : ""}`, "");
  if (!plan.length) {
    L.push(`1. OMB Capital Commitment Plan (2cmn-uidm): this line is not in OMB's Capital Commitment Plan in any release${a.funding ? ` with ${a.funding} funding` : ""}.`);
  } else {
    L.push(`1. OMB Capital Commitment Plan (NYC Open Data 2cmn-uidm), release ${isoDate(rel)}. In THOUSANDS of dollars, as OMB publishes them.`);
    if (!atRel.length) L.push(`   This line is not in the ${isoDate(rel)} release. It is in: ${releases.map(isoDate).join(", ")}.`);
    for (const r of atRel) L.push(`   ${r.funding}: ${planYears(r)}`);
    L.push(`   How the plan moved, every release with this line (newest first; thousands of dollars):`);
    for (const r of plan) L.push(`   ${isoDate(r.pub_date)} · ${r.funding} · ${planYears(r)}`);
  }

  // --- 2. CPDB on this line ------------------------------------------------------------------
  L.push("");
  if (!cpdb.n) {
    L.push(`2. DCP Capital Projects Database (CPDB) version ${version}: no planned commitments on this line.`);
  } else {
    const byFy = db
      .prepare(
        "SELECT plan_fy, SUM(totalcityplannedcommit) c, SUM(totalnoncityplannedcommit) nc FROM cpdb_commitments WHERE REPLACE(budget_line_norm, ' ', '') = ? GROUP BY plan_fy ORDER BY plan_fy"
      )
      .all(key) as { plan_fy: number; c: number; nc: number }[];
    const projects = db
      .prepare(
        `SELECT c.maprojid, SUM(c.totalcityplannedcommit) c, SUM(c.totalnoncityplannedcommit) nc, MIN(c.plan_fy) f, MAX(c.plan_fy) l,
                SUM(COALESCE(c.totalplannedcommit, 0)) t
         FROM cpdb_commitments c WHERE REPLACE(c.budget_line_norm, ' ', '') = ? GROUP BY c.maprojid ORDER BY t DESC, c.maprojid LIMIT ?`
      )
      .all(key, a.limit) as { maprojid: string; c: number; nc: number; f: number; l: number }[];
    L.push(
      `2. DCP Capital Projects Database (CPDB) version ${version}, published ${capitalPlanSources().get("djxg-kcfi")?.rows_updated_at}: ${fmtN(cpdb.n)} planned commitment(s) on this line, ${fmtN(cpdb.p)} project(s). ${unitCpdb}`,
      "   On this line, by fiscal year (July to June): " + byFy.map((r) => `FY${r.plan_fy} City ${dollars(r.c)} / Non-City ${dollars(r.nc)}`).join(" · "),
      `   Projects on this line, largest planned total first (showing ${projects.length} of ${fmtN(cpdb.p)}):`
    );
    const getP = db.prepare("SELECT * FROM cpdb_projects WHERE maprojid = ?");
    for (const pr of projects) {
      const p = getP.get(pr.maprojid) as ProjectRow;
      const lines = projectLines(pr.maprojid);
      const span = pr.f === pr.l ? `FY${pr.f}` : `FY${pr.f}–FY${pr.l}`;
      L.push(
        "",
        `   ${pr.maprojid} · "${p.description}" · managed by ${p.magencyacro}`,
        `     On this line: City ${dollars(pr.c)} / Non-City ${dollars(pr.nc)}, ${span}.`,
        lines.length > 1
          ? `     CPDB project totals (fi59-268w; whole project, all ${lines.length} of its budget lines: ${lines.join(", ")}): ${projectTotals(p)}`
          : `     CPDB project totals (fi59-268w; whole project, on this budget line only): ${projectTotals(p)}`
      );
    }
  }

  // --- 3. The Council's own rows ---------------------------------------------------------------
  L.push("");
  if (!council.length) {
    L.push("3. The Council's capital list: no Council capital rows on this line.");
  } else {
    const rows = council.reduce((s, r) => s + r.n, 0);
    L.push(
      `3. The Council's capital list (search_council_capital): ${fmtN(rows)} Council capital row(s) on this line, shown apart, never added to OMB's or CPDB's figures. By report year: ` +
        council.map((r) => `FY${r.report_year} ${fmtN(r.n)} row(s) ${r.amt == null ? "amount unknown" : dollars(r.amt)}${r.unknown ? ` (${r.unknown} with no amount)` : ""}`).join(" · ")
    );
  }
  L.push("", PLAN_CAVEAT, "", sourcesFooter(version));
  return L.join("\n");
}
