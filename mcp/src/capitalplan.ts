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
