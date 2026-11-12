/**
 * City agency budgets (#270, tools in #285): queries over the index's `agency_budget` table, which
 * scripts/agency-budget.mjs builds from NYC Open Data `mwzb-yiwb` under the year rule.
 *
 * Every figure keeps its NULLs: `adopted` is NULL when a unit is not in that year's adopted
 * budget, `modified` when it is not in the next year's release or that release is not out yet.
 * Totals are SUMs over the units that have a figure, and say how many units had none.
 *
 * `agency` and `unit` take a number ("056", "56", "1") or words from the name ("police"). Words
 * match every name the agency or unit has had in any year, folded the way every other text filter
 * here is (src/fold.ts), each word anywhere in the name.
 */
import { getDb, getMeta } from "./db.js";
import { fold } from "./fold.js";

export interface AgencyBudgetRow {
  fiscal_year: number;
  agency_number: string;
  agency_name: string;
  unit_number: string;
  unit_name: string;
  adopted: number | null;
  modified: number | null;
  adopted_release: string | null;
  modified_release: string | null;
}

export interface AgencyBudgetMeta {
  dataset: string;
  url: string;
  snapshot: string;
  retrieved_at: string;
  first_year: number;
  last_year: number;
  june_releases: Record<string, string>;
}

export function agencyBudgetMeta(): AgencyBudgetMeta {
  const raw = getMeta("agency_budget");
  if (!raw) throw new Error("This index has no agency budget data (meta.agency_budget). Rebuild it with npm run build-index.");
  return JSON.parse(raw) as AgencyBudgetMeta;
}

export function agencyBudgetYears(): number[] {
  return (getDb().prepare("SELECT DISTINCT fiscal_year FROM agency_budget ORDER BY fiscal_year").all() as { fiscal_year: number }[]).map(
    (r) => r.fiscal_year
  );
}

/** A number argument, padded to 3 characters; null when the argument is words. */
export function numberArg(v: string): string | null {
  const s = v.trim();
  return /^\d{1,3}$/.test(s) ? s.padStart(3, "0") : null;
}

const words = (v: string) => fold(v).split(/[^a-z0-9#&']+/).filter(Boolean);
const hasAll = (name: string, ws: string[]) => {
  const f = fold(name);
  return ws.every((w) => f.includes(w));
};

/** Agency numbers an `agency` argument names, in number order. */
export function matchAgencies(agency: string): string[] {
  const num = numberArg(agency);
  const db = getDb();
  if (num) return (db.prepare("SELECT DISTINCT agency_number FROM agency_budget WHERE agency_number = ?").all(num) as { agency_number: string }[]).map((r) => r.agency_number);
  const ws = words(agency);
  if (ws.length === 0) return [];
  const names = db.prepare("SELECT DISTINCT agency_number, agency_name FROM agency_budget ORDER BY agency_number").all() as { agency_number: string; agency_name: string }[];
  return [...new Set(names.filter((r) => hasAll(r.agency_name, ws)).map((r) => r.agency_number))];
}

/** (agency, unit) keys a `unit` argument names, within `agencies` when given. */
export function matchUnits(unit: string, agencies: string[] | null): Set<string> {
  const num = numberArg(unit);
  const db = getDb();
  const all = db.prepare("SELECT DISTINCT agency_number, unit_number, unit_name FROM agency_budget").all() as { agency_number: string; unit_number: string; unit_name: string }[];
  const inAgency = agencies ? new Set(agencies) : null;
  const ws = num ? [] : words(unit);
  const keys = new Set<string>();
  for (const r of all) {
    if (inAgency && !inAgency.has(r.agency_number)) continue;
    if (num ? r.unit_number === num : ws.length > 0 && hasAll(r.unit_name, ws)) keys.add(`${r.agency_number}|${r.unit_number}`);
  }
  return keys;
}

export interface AgencyGroup {
  agency_number: string;
  agency_name: string;
  units: AgencyBudgetRow[];
  adopted: number | null;
  modified: number | null;
  /** Units with no adopted / no modified figure this year. */
  no_adopted: number;
  no_modified: number;
}

/** Whole cents, summed exactly; null when no unit has a figure. */
function total(rows: AgencyBudgetRow[], col: "adopted" | "modified"): number | null {
  const have = rows.filter((r) => r[col] != null);
  return have.length ? have.reduce((s, r) => s + Math.round((r[col] as number) * 100), 0) / 100 : null;
}

export function groupByAgency(rows: AgencyBudgetRow[]): AgencyGroup[] {
  const by = new Map<string, AgencyBudgetRow[]>();
  for (const r of rows) by.set(r.agency_number, [...(by.get(r.agency_number) ?? []), r]);
  return [...by].map(([agency_number, units]) => ({
    agency_number,
    // The name in this year's release (the units of one agency share it within a release).
    agency_name: units.find((u) => u.adopted_release)?.agency_name ?? units[0].agency_name,
    units,
    adopted: total(units, "adopted"),
    modified: total(units, "modified"),
    no_adopted: units.filter((u) => u.adopted == null).length,
    no_modified: units.filter((u) => u.modified == null).length,
  }));
}

export interface AgencyBudgetQuery {
  agency?: string;
  unit?: string;
  fiscal_year: number;
}

export interface AgencyBudgetResult {
  fiscal_year: number;
  /** The matching rows of that year, by agency then unit number. */
  rows: AgencyBudgetRow[];
  agencies: AgencyGroup[];
  adopted: number | null;
  modified: number | null;
  /** True when the agency or unit filter named something that exists in another year only. */
  other_years: number[];
}

/** The rows of one fiscal year an agency and unit filter select. */
export function queryAgencyBudget(q: AgencyBudgetQuery): AgencyBudgetResult {
  const db = getDb();
  const agencies = q.agency != null ? matchAgencies(q.agency) : null;
  const units = q.unit != null ? matchUnits(q.unit, agencies) : null;
  const keep = (r: AgencyBudgetRow) =>
    (agencies == null || agencies.includes(r.agency_number)) && (units == null || units.has(`${r.agency_number}|${r.unit_number}`));
  const all = (db.prepare("SELECT * FROM agency_budget WHERE fiscal_year = ? ORDER BY agency_number, unit_number").all(q.fiscal_year) as AgencyBudgetRow[]).filter(keep);
  let other_years: number[] = [];
  if (all.length === 0 && (agencies?.length || units?.size)) {
    other_years = (db.prepare("SELECT DISTINCT fiscal_year, agency_number, unit_number FROM agency_budget ORDER BY fiscal_year").all() as AgencyBudgetRow[])
      .filter(keep)
      .map((r) => r.fiscal_year)
      .filter((y, i, a) => a.indexOf(y) === i);
  }
  return {
    fiscal_year: q.fiscal_year,
    rows: all,
    agencies: groupByAgency(all),
    adopted: total(all, "adopted"),
    modified: total(all, "modified"),
    other_years,
  };
}

// ---------------------------------------------------------------- answers (server.ts tools)

const usd = (v: number): string => {
  const c = Math.round(v * 100) / 100;
  const s = Math.abs(c).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return c < 0 ? `-$${s}` : `$${s}`;
};
const plural = (n: number, one: string, many = `${one}s`) => `${n.toLocaleString("en-US")} ${n === 1 ? one : many}`;

export const CHECKBOOK_NOTE =
  "Budget, not spending: these are what the City budgeted. For what it actually spent, paid or put under contract, use Checkbook NYC or @betanyc/nyc-checkbook-mcp.";
export const GROSS_NOTE =
  "Amounts are gross: they include intra-city transfers (money one City agency pays another), so they add up to more than OMB's headline net budget.";

/** A user error: the server returns it as an error result. */
export class AgencyArgError extends Error {}

export function checkYear(fiscal_year: number | undefined): number {
  const years = agencyBudgetYears();
  if (years.length === 0) throw new AgencyArgError("This index has no agency budget rows.");
  if (fiscal_year == null) return years[years.length - 1];
  if (!years.includes(fiscal_year)) {
    throw new AgencyArgError(`fiscal_year ${fiscal_year} is not in the City agency budgets, which cover FY${years[0]}–FY${years[years.length - 1]}.`);
  }
  return fiscal_year;
}

function absentWords(kind: "adopted" | "modified", year: number, newest: number): string {
  if (kind === "modified" && year === newest) return `not yet published (it comes with the FY${year + 1} June release)`;
  return kind === "adopted" ? `not in the FY${year} adopted budget` : `not in that year's modified budget (the unit is not in the FY${year + 1} release)`;
}

function fig(v: number | null, kind: "adopted" | "modified", year: number, newest: number): string {
  return v == null ? absentWords(kind, year, newest) : usd(v);
}

function releaseLines(rows: AgencyBudgetRow[], year: number, newest: number, meta: AgencyBudgetMeta): string[] {
  const adopted = [...new Set(rows.map((r) => r.adopted_release).filter(Boolean))].join(", ") || meta.june_releases[String(year)] || "none";
  const modified = [...new Set(rows.map((r) => r.modified_release).filter(Boolean))].join(", ");
  return [
    `Source: NYC Open Data ${meta.dataset} (Expense Budget, OMB), ${meta.url}; snapshot retrieved ${meta.retrieved_at}.`,
    `Adopted FY${year}: financial_plan_amount in the June release tagged ${year} (publication_date ${adopted}).`,
    year === newest
      ? `Modified FY${year}: not yet published; it comes from the June release tagged ${year + 1}, which is not out yet.`
      : `Modified FY${year}: current_modified_budget_amount in the June release tagged ${year + 1} (publication_date ${modified || meta.june_releases[String(year + 1)] || "none"}).`,
  ];
}

function filterError(agency?: string, unit?: string): string | null {
  for (const [k, v] of [["agency", agency], ["unit", unit]] as const) {
    if (v == null) continue;
    if (v.length > 200) return `${k} is ${v.length} characters; the limit is 200.`;
    if (v.trim() === "" || fold(v) === "") return `${k} is empty; omit it, or give a number ('056') or words from the name ('police').`;
  }
  return null;
}

function noMatch(q: AgencyBudgetQuery, res: AgencyBudgetResult): string {
  const what = [q.agency != null ? `agency ${JSON.stringify(q.agency)}` : null, q.unit != null ? `unit ${JSON.stringify(q.unit)}` : null].filter(Boolean).join(" and ");
  if (res.other_years.length) {
    return `No City agency budget row matches ${what} in FY${q.fiscal_year}: ${q.unit != null ? "that unit is" : "it is"} not in that year's budget. It is in FY${res.other_years.join(", FY")}.`;
  }
  return `No City agency or unit matches ${what}. agency takes an agency number ('056', '56') or words from its name ('police'); unit takes a unit of appropriation number ('001') or words from its name.`;
}

export interface SearchAgencyArgs {
  agency?: string;
  unit?: string;
  fiscal_year?: number;
  limit?: number;
}

/** search_agency_budget's answer. */
export function searchAgencyBudgetText(a: SearchAgencyArgs): string {
  const err = filterError(a.agency, a.unit);
  if (err) throw new AgencyArgError(err);
  if (a.limit != null && a.limit < 1) throw new AgencyArgError(`limit must be at least 1 (got ${a.limit}); totals always cover every match.`);
  const limit = Math.min(a.limit ?? 50, 500);
  const year = checkYear(a.fiscal_year);
  const meta = agencyBudgetMeta();
  const newest = meta.last_year;
  const q = { agency: a.agency, unit: a.unit, fiscal_year: year };
  const res = queryAgencyBudget(q);
  if (res.rows.length === 0) {
    if (a.agency == null && a.unit == null) throw new AgencyArgError(`No agency budget rows for FY${year}.`);
    return [noMatch(q, res), "", CHECKBOOK_NOTE].join("\n");
  }
  const L: string[] = [];
  const filtered = a.agency != null || a.unit != null;
  L.push(`City agency budgets, FY${year}: ${plural(res.agencies.length, "agency", "agencies")}, ${plural(res.rows.length, "unit of appropriation", "units of appropriation")}.`);
  L.push(`Total: adopted ${fig(res.adopted, "adopted", year, newest)}; modified ${fig(res.modified, "modified", year, newest)}.`);
  L.push(GROSS_NOTE);
  L.push("");
  if (!filtered) {
    // The whole city: agencies with their totals, largest adopted first.
    const sorted = [...res.agencies].sort((x, y) => (y.adopted ?? -Infinity) - (x.adopted ?? -Infinity) || x.agency_number.localeCompare(y.agency_number));
    L.push(`Agencies, largest adopted first${sorted.length > limit ? ` (first ${limit} of ${sorted.length}; give agency to see one)` : ""}:`);
    for (const g of sorted.slice(0, limit)) {
      L.push(`  ${g.agency_number} ${g.agency_name}: adopted ${fig(g.adopted, "adopted", year, newest)} · modified ${fig(g.modified, "modified", year, newest)} (${plural(g.units.length, "unit")})`);
    }
  } else {
    let shown = 0;
    for (const g of res.agencies) {
      L.push(`${g.agency_number} ${g.agency_name}: adopted ${fig(g.adopted, "adopted", year, newest)} · modified ${fig(g.modified, "modified", year, newest)} (${plural(g.units.length, "unit")}${g.no_adopted ? `; ${g.no_adopted} not in the FY${year} adopted budget` : ""})`);
      for (const u of g.units) {
        if (shown >= limit) break;
        L.push(`  ${u.unit_number} ${u.unit_name}: adopted ${fig(u.adopted, "adopted", year, newest)} · modified ${fig(u.modified, "modified", year, newest)}`);
        shown++;
      }
    }
    if (shown < res.rows.length) L.push(`  … ${res.rows.length - shown} more units not listed (limit ${limit}); the totals above cover all of them.`);
  }
  L.push("");
  L.push(...releaseLines(res.rows, year, newest, meta));
  L.push(CHECKBOOK_NOTE);
  return L.join("\n");
}

export interface CompareArgs {
  agency?: string;
  unit?: string;
  fiscal_year: number;
}

/** compare_adopted_modified's answer. */
export function compareAdoptedModifiedText(a: CompareArgs): string {
  if (a.agency == null && a.unit == null) {
    throw new AgencyArgError("compare_adopted_modified needs agency or unit (or both), so it never answers for the whole city by accident. For citywide totals, use search_agency_budget.");
  }
  const err = filterError(a.agency, a.unit);
  if (err) throw new AgencyArgError(err);
  const year = checkYear(a.fiscal_year);
  const meta = agencyBudgetMeta();
  const newest = meta.last_year;
  const q = { agency: a.agency, unit: a.unit, fiscal_year: year };
  const res = queryAgencyBudget(q);
  if (res.rows.length === 0) return [noMatch(q, res), "", CHECKBOOK_NOTE].join("\n");
  const L: string[] = [];
  const names = res.agencies.map((g) => `${g.agency_number} ${g.agency_name}`).join("; ");
  const scope = a.unit != null && res.rows.length <= 3 ? res.rows.map((u) => `${u.agency_number}/${u.unit_number} ${u.unit_name}`).join("; ") : names;
  L.push(`Adopted vs modified, FY${year}: ${scope}`);
  L.push(`Adopted:  ${fig(res.adopted, "adopted", year, newest)}`);
  L.push(`Modified: ${fig(res.modified, "modified", year, newest)}`);
  if (res.modified == null || res.adopted == null) {
    L.push(year === newest && res.modified == null
      ? `Change: none to report. The FY${year} modified budget is not yet published.`
      : "Change: none to report, because one of the two figures is missing.");
  } else {
    const d = Math.round((res.modified - res.adopted) * 100) / 100;
    const pct = res.adopted === 0 ? null : (d / res.adopted) * 100;
    const word = d > 0 ? "increase" : d < 0 ? "decrease" : "no change";
    L.push(`Change: ${word} of ${usd(Math.abs(d))}${pct == null ? "" : ` (${d >= 0 ? "+" : "-"}${Math.abs(pct).toFixed(1)}%)`} from adopted to modified.`);
  }
  const noA = res.rows.filter((r) => r.adopted == null).length;
  const noM = res.rows.filter((r) => r.modified == null).length;
  if (noA) L.push(`${plural(noA, "unit")} not in the FY${year} adopted budget (counted only in modified).`);
  if (noM && year !== newest) L.push(`${plural(noM, "unit")} not in the modified budget (counted only in adopted).`);
  if (res.rows.length > 1) {
    L.push("");
    L.push("By unit, largest change first:");
    const by = [...res.rows].sort((x, y) => Math.abs((y.modified ?? 0) - (y.adopted ?? 0)) - Math.abs((x.modified ?? 0) - (x.adopted ?? 0)));
    for (const u of by.slice(0, 50)) {
      const c = u.adopted != null && u.modified != null ? ` · change ${u.modified - u.adopted >= 0 ? "+" : "-"}${usd(Math.abs(u.modified - u.adopted))}` : "";
      L.push(`  ${u.agency_number}/${u.unit_number} ${u.unit_name}: adopted ${fig(u.adopted, "adopted", year, newest)} · modified ${fig(u.modified, "modified", year, newest)}${c}`);
    }
    if (by.length > 50) L.push(`  … ${by.length - 50} more units; the totals above cover all of them.`);
  }
  L.push("");
  L.push(GROSS_NOTE);
  L.push(...releaseLines(res.rows, year, newest, meta));
  L.push(CHECKBOOK_NOTE);
  return L.join("\n");
}

/** list_available_fiscal_years's agency budget section. */
export function agencyYearsSection(): string[] {
  const meta = agencyBudgetMeta();
  const count = Number((getDb().prepare("SELECT COUNT(*) AS n FROM agency_budget").get() as { n: number }).n);
  return [
    `City agency budgets (search_agency_budget, compare_adopted_modified): adopted FY${meta.first_year}–FY${meta.last_year}, modified FY${meta.first_year}–FY${meta.last_year - 1} (FY${meta.last_year} modified not yet published); ${count.toLocaleString("en-US")} agency × unit × year rows.`,
    `  From NYC Open Data ${meta.dataset} (Expense Budget), June releases ${Object.entries(meta.june_releases).map(([t, d]) => `${t}: ${d}`).join(", ")}; snapshot retrieved ${meta.retrieved_at}. Gross (includes intra-city transfers).`,
  ];
}
