/**
 * agency-budget.mjs — City agency budgets (#270, built in #284): the `agency_budget` table, from
 * the committed NYC Open Data Expense Budget snapshot `mwzb-yiwb` (source/agency-budget-qa/).
 *
 * THE ONE PLACE THE YEAR RULE IS CODED for the MCP and the explorer (the explorer exports this
 * table to Parquet; it never reads a CSV). code/qa_agency_budget.py and
 * test/agency-budget.test.js check it with their own code, on purpose.
 *
 * The year rule (DATA-DICTIONARY.md, DATA-ANOMALIES.md §57, #268, #274):
 *
 *   The June release of tag Y is the tag's latest publication_date, when that date is in June of
 *   Y-1 (the Adopted budget). A tag whose latest release is not a June one (a Preliminary or
 *   Executive release of a budget not yet adopted) is not used.
 *   Adopted FY Y  = sum(financial_plan_amount)          in the June release tagged Y
 *   Modified FY Y = sum(current_modified_budget_amount) in the June release tagged Y+1
 *   adopted_budget_amount in the release tagged Y is FY Y-1 (#274's bug): never read here.
 *
 * One row per fiscal year x agency x unit of appropriation (FY2017 on) where the unit is in that
 * year's adopted release or the next year's. `adopted` is NULL when the unit is not in that
 * year's adopted release; `modified` is NULL when it is not in the next one, or the next one is
 * not out yet. Never 0 for "absent". Numbers are 3-character text ("040"): releases before 2023
 * serve them unpadded ("40"). Names are as published in that year's adopted release, or in the
 * modified release when the unit is only there. Releases are publication dates (YYYYMMDD).
 *
 * Gross: Open Data rows include intra-city transfers. OMB's headline totals are net.
 *
 * The year range comes from the data, never a hard-coded last year (plan risk 5): a new June
 * release adds a year on the next build.
 */

const SNAP = "source/agency-budget-qa";
/** The first fiscal year the explorer and the MCP show (the old /agencies/ app's first year). */
export const FIRST_YEAR = 2017;

export const AGENCY_BUDGET_SCHEMA = {
  agency_budget: [
    ["fiscal_year", "INTEGER"], ["agency_number", "TEXT"], ["agency_name", "TEXT"], ["unit_number", "TEXT"],
    ["unit_name", "TEXT"], ["adopted", "REAL"], ["modified", "REAL"], ["adopted_release", "TEXT"],
    ["modified_release", "TEXT"],
  ],
};
export const AGENCY_BUDGET_TABLES = Object.keys(AGENCY_BUDGET_SCHEMA);

export function agencyBudgetSchemaSql() {
  return Object.entries(AGENCY_BUDGET_SCHEMA)
    .map(([t, cols]) => `CREATE TABLE ${t} (${cols.map(([c, ty]) => `${c} ${ty}`).join(", ")});`)
    .join("\n");
}

/** "40" -> "040". Anything that is not 1-3 digits is a stop. */
function num3(v, where) {
  const s = String(v ?? "").trim();
  if (!/^\d{1,3}$/.test(s)) throw new Error(`${where}: ${JSON.stringify(v)} is not an agency or unit number`);
  return s.padStart(3, "0");
}

/** Whole cents as an integer, so sums are exact. Blank is a stop: the snapshot always has a value. */
function cents(v, where) {
  const s = String(v ?? "").trim();
  const n = Number(s);
  if (s === "" || !Number.isFinite(n)) throw new Error(`${where}: amount ${JSON.stringify(v)} is not a number`);
  return Math.round(n * 100);
}

/**
 * The June release of each tag: Map(tag -> publication_date).
 * @param {Array<{fiscal_year: string, publication_date: string}>} releases
 */
export function juneReleases(releases) {
  const latest = new Map();
  for (const r of releases) {
    const tag = Number(r.fiscal_year);
    if (!Number.isInteger(tag) || !/^\d{8}$/.test(r.publication_date)) {
      throw new Error(`${SNAP}/releases.csv: bad row ${JSON.stringify(r)}`);
    }
    if ((latest.get(tag) ?? "") < r.publication_date) latest.set(tag, r.publication_date);
  }
  return new Map([...latest].filter(([tag, d]) => d.slice(0, 6) === `${tag - 1}06`).sort((a, b) => a[0] - b[0]));
}

/**
 * The year rule, as rows. Pure: takes the two snapshot files' rows, returns the table's rows in
 * (fiscal_year, agency_number, unit_number) order.
 */
export function agencyBudgetRows(releases, byUnit) {
  const june = juneReleases(releases);
  /** `${tag}|${agency}|${unit}` -> { fp, cm, agency_name, unit_name } (cents) */
  const sums = new Map();
  for (const [i, r] of byUnit.entries()) {
    const where = `${SNAP}/by_unit.csv line ${i + 2}`;
    const tag = Number(r.fiscal_year);
    if (june.get(tag) !== r.publication_date) continue;
    const k = `${tag}|${num3(r.agency_number, where)}|${num3(r.unit_appropriation_number, where)}`;
    const s = sums.get(k) ?? { fp: 0, cm: 0 };
    s.fp += cents(r.financial_plan_amount, where);
    s.cm += cents(r.current_modified_budget_amount, where);
    s.agency_name = String(r.agency_name ?? "").trim();
    s.unit_name = String(r.unit_appropriation_name ?? "").trim();
    sums.set(k, s);
  }
  const years = [...june.keys()].filter((y) => y >= FIRST_YEAR);
  for (const y of years) {
    if (![...sums.keys()].some((k) => k.startsWith(`${y}|`))) throw new Error(`agency_budget: the June release tagged ${y} has no rows in ${SNAP}/by_unit.csv`);
  }
  const units = [...new Set([...sums.keys()].map((k) => k.slice(k.indexOf("|") + 1)))].sort();
  const out = [];
  for (const y of years) {
    for (const au of units) {
      const a = sums.get(`${y}|${au}`);
      const m = june.has(y + 1) ? sums.get(`${y + 1}|${au}`) : undefined;
      if (!a && !m) continue;
      const [agency_number, unit_number] = au.split("|");
      const named = a ?? m;
      out.push({
        fiscal_year: y,
        agency_number,
        agency_name: named.agency_name,
        unit_number,
        unit_name: named.unit_name,
        adopted: a ? a.fp / 100 : null,
        modified: m ? m.cm / 100 : null,
        adopted_release: a ? june.get(y) : null,
        modified_release: m ? june.get(y + 1) : null,
      });
    }
  }
  return out;
}

/**
 * Load the table. `io.readCsv(rel)` records each file in meta.inputs (build-index.mjs).
 * @returns {{ counts: { agency_budget: number }, years: number[] }}
 */
export function loadAgencyBudget(db, io) {
  const releases = io.readCsv(`${SNAP}/releases.csv`);
  const byUnit = io.readCsv(`${SNAP}/by_unit.csv`);
  for (const [rows, rel, cols] of [
    [releases, "releases.csv", ["fiscal_year", "publication_date"]],
    [byUnit, "by_unit.csv", ["fiscal_year", "publication_date", "agency_number", "agency_name", "unit_appropriation_number",
      "unit_appropriation_name", "current_modified_budget_amount", "financial_plan_amount"]],
  ]) {
    if (rows.length === 0) throw new Error(`${SNAP}/${rel}: no rows`);
    for (const c of cols) if (!(c in rows[0])) throw new Error(`${SNAP}/${rel}: no column ${c}`);
  }
  const rows = agencyBudgetRows(releases, byUnit);
  // When the snapshot was pulled: the latest request time in its manifest (UTC).
  const manifest = io.readCsv(`${SNAP}/MANIFEST.csv`);
  const retrieved = manifest.map((m) => m.retrieved_at ?? "").sort().at(-1) ?? "";
  if (!/^\d{4}-\d{2}-\d{2}T/.test(retrieved)) throw new Error(`${SNAP}/MANIFEST.csv: no retrieved_at`);
  const june = juneReleases(releases);
  const cols = AGENCY_BUDGET_SCHEMA.agency_budget.map(([c]) => c);
  const ins = db.prepare(`INSERT INTO agency_budget (${cols.join(", ")}) VALUES (${cols.map((c) => "@" + c).join(", ")})`);
  db.transaction(() => {
    for (const r of rows) ins.run(r);
  })();
  db.exec("CREATE INDEX idx_agency_budget ON agency_budget(fiscal_year, agency_number, unit_number)");
  const years = [...new Set(rows.map((r) => r.fiscal_year))];
  // What list_available_fiscal_years and the explorer say about the source (src/agency.ts).
  const meta = {
    dataset: "mwzb-yiwb",
    url: "https://data.cityofnewyork.us/d/mwzb-yiwb",
    snapshot: SNAP,
    retrieved_at: retrieved,
    first_year: years[0],
    last_year: years.at(-1),
    june_releases: Object.fromEntries([...june].map(([tag, d]) => [String(tag), d])),
  };
  return { counts: { agency_budget: rows.length }, years, meta };
}

/** Problems with the built table; empty means it may ship (verify-index.mjs's rule). */
export function verifyAgencyBudget(db, loaded) {
  const problems = [];
  const n = Number(db.prepare("SELECT COUNT(*) AS n FROM agency_budget").get().n);
  if (n === 0) problems.push("agency_budget: 0 rows");
  if (n !== loaded.counts.agency_budget) problems.push(`agency_budget: ${n} rows, loader made ${loaded.counts.agency_budget}`);
  const years = db.prepare("SELECT DISTINCT fiscal_year AS y FROM agency_budget ORDER BY y").all().map((r) => Number(r.y));
  if (years[0] !== FIRST_YEAR) problems.push(`agency_budget: first year ${years[0]}, want ${FIRST_YEAR}`);
  for (let i = 1; i < years.length; i++) if (years[i] !== years[i - 1] + 1) problems.push(`agency_budget: FY${years[i - 1] + 1} is missing`);
  const dup = db.prepare("SELECT COUNT(*) AS n FROM (SELECT 1 FROM agency_budget GROUP BY fiscal_year, agency_number, unit_number HAVING COUNT(*) > 1)").get().n;
  if (dup) problems.push(`agency_budget: ${dup} duplicate year x agency x unit keys`);
  const newest = years.at(-1);
  const pub = db.prepare("SELECT COUNT(*) AS n FROM agency_budget WHERE fiscal_year = ? AND modified IS NOT NULL").get(newest).n;
  if (pub) problems.push(`agency_budget: FY${newest} has ${pub} modified figures, but no newer June release exists`);
  return problems;
}
