/**
 * verify-index.mjs — the last gate before a built index replaces data/budget.db.
 *
 * build-index.mjs calls verifyIndex() on the freshly built file and refuses to install it if any
 * problem is returned. A dataset that loads 0 rows, or a year the inputs declare that is absent
 * from the index, must stop the build: an empty table answers "covers (none)" to every question,
 * which reads as a fact about the city rather than a broken build.
 *
 * What each expectation is checked against (all of it independent of what the build inserted):
 *   disclosure      every data/disclosure_years.csv row with loaded=yes has exactly award_rows
 *                   (> 0) rows in `disclosure`; every year in the CSV is in `disclosure_years`
 *   capital         every year in CAPITAL_REPORT_YEARS (data/capital/README.md, "Which source
 *                   each year comes from") has rows in `capital_council` and one `capital_sources`
 *                   row; no other year appears; per-year counts equal the CSV's
 *   capital_vs_omb  > 0 rows; every report year it holds is a capital report year
 *   meta            built_at, inputs, counts present
 */

/**
 * The Council capital report years the repo publishes. FY2018 is a documented gap
 * (data/capital/README.md). Adding or dropping a year is a deliberate edit here AND there.
 */
export const CAPITAL_REPORT_YEARS = [2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027];

/**
 * @param {import("better-sqlite3").Database} db  the built index (read-only is fine)
 * @param {{ disclosureYears: Array<{fiscal_year: string|number, loaded: string, award_rows: string|number}>,
 *           capitalRowsByYear: Map<number, number>, capitalYears?: number[] }} expect
 * @returns {string[]} problems; empty means the index may ship
 */
export function verifyIndex(db, expect) {
  const problems = [];
  const capitalYears = expect.capitalYears ?? CAPITAL_REPORT_YEARS;
  const countBy = (sql) => new Map(db.prepare(sql).all().map((r) => [Number(r.y), Number(r.n)]));
  const total = (table) => Number(db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).get().n);

  // --- disclosure
  if (total("disclosure") === 0) problems.push("disclosure: 0 rows");
  const discByYear = countBy("SELECT fiscal_year AS y, COUNT(*) AS n FROM disclosure GROUP BY fiscal_year");
  const yearRows = new Set(db.prepare("SELECT fiscal_year AS y FROM disclosure_years").all().map((r) => Number(r.y)));
  const loaded = new Set();
  for (const y of expect.disclosureYears) {
    const year = Number(y.fiscal_year);
    if (!yearRows.has(year)) problems.push(`disclosure_years: FY${year} is in data/disclosure_years.csv but not in the index`);
    if (y.loaded !== "yes") continue;
    loaded.add(year);
    const want = Number(y.award_rows);
    const got = discByYear.get(year) ?? 0;
    if (!(want > 0)) problems.push(`disclosure: FY${year} is loaded=yes but declares award_rows ${JSON.stringify(y.award_rows)}`);
    if (got === 0) problems.push(`disclosure: FY${year} is missing (0 rows; data/disclosure_years.csv says ${want})`);
    else if (got !== want) problems.push(`disclosure: FY${year} has ${got} rows; data/disclosure_years.csv says ${want}`);
  }
  for (const year of discByYear.keys()) {
    if (!loaded.has(year)) problems.push(`disclosure: FY${year} has rows but is not a loaded year in data/disclosure_years.csv`);
  }

  // --- capital
  if (total("capital_council") === 0) problems.push("capital_council: 0 rows");
  const capByYear = countBy("SELECT report_year AS y, COUNT(*) AS n FROM capital_council GROUP BY report_year");
  const srcYears = new Set(db.prepare("SELECT report_year AS y FROM capital_sources").all().map((r) => Number(r.y)));
  for (const year of capitalYears) {
    const got = capByYear.get(year) ?? 0;
    const want = expect.capitalRowsByYear.get(year) ?? 0;
    if (want === 0) problems.push(`capital: FY${year} is a published report year but data/capital/council_capital_awards.csv has no rows for it`);
    if (got === 0) problems.push(`capital_council: FY${year} is missing (0 rows)`);
    else if (got !== want) problems.push(`capital_council: FY${year} has ${got} rows; the CSV has ${want}`);
    if (!srcYears.has(year)) problems.push(`capital_sources: FY${year} has no provenance row`);
  }
  for (const year of new Set([...capByYear.keys(), ...expect.capitalRowsByYear.keys()])) {
    if (!capitalYears.includes(year)) {
      problems.push(`capital: FY${year} is not a published report year (CAPITAL_REPORT_YEARS, data/capital/README.md)`);
    }
  }

  // --- Council vs OMB
  if (total("capital_vs_omb") === 0) problems.push("capital_vs_omb: 0 rows");
  for (const year of countBy("SELECT report_year AS y, COUNT(*) AS n FROM capital_vs_omb GROUP BY report_year").keys()) {
    if (!capitalYears.includes(year)) problems.push(`capital_vs_omb: FY${year} is not a capital report year`);
  }

  // --- meta
  const meta = new Set(db.prepare("SELECT key FROM meta").all().map((r) => r.key));
  for (const k of ["built_at", "inputs", "counts"]) if (!meta.has(k)) problems.push(`meta: no ${k}`);

  return problems;
}
