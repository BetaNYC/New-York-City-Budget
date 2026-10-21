import { describe, expect, test } from "vitest";

import { HOW_WE_CHECK, STATES, coveredRange, stateOf, stripShares, tooltipOf } from "../../src/query/opendata.js";

// Four states (Noel, 2026-10-21): text carries the meaning, every searched state names its date.
describe("Open Data states", () => {
  const base = { dataset_id: "4d7f-74pe", dataset_name: "City Council Discretionary Funding", snapshot_date: "2026-10-14" };
  const rule = (n, m) => `fy_ein_amount: bucket holds ${n} of ours and ${m} on the portal; presence uncertain`;

  test("labels", () => {
    expect(STATES.found.label).toBe("On NYC Open Data");
    expect(STATES.maybe.label).toBe("Maybe on NYC Open Data");
    expect(STATES.notfound.label).toBe("Not found on NYC Open Data");
    expect(STATES.nocheck.label).toBe("No Open Data to check");
  });

  test("a one-to-one match is found, with its row and date", () => {
    for (const s of ["same", "differs"]) {
      const x = { ...base, match_status: s, portal_row_id: "row-abc" };
      expect(stateOf(x)).toBe("found");
      expect(tooltipOf(x)).toBe("Matches row row-abc in City Council Discretionary Funding (4d7f-74pe), as of 2026-10-14.");
    }
  });

  test("any look-alike bucket is maybe, never found, whatever the counts", () => {
    for (const [n, m] of [[2, 1], [2, 3], [2, 2]]) {
      const x = { ...base, match_status: "ambiguous", match_rule: rule(n, m), candidates: m };
      expect(stateOf(x)).toBe("maybe");
      expect(tooltipOf(x)).toMatch(new RegExp(`^${n} of our records and ${m} portal rows share this year and amount; we can't tell which\\.`));
      expect(tooltipOf(x)).toContain("2026-10-14");
    }
  });

  test("not found names the dataset, its years and the date; no dataset means nothing to check", () => {
    const x = { ...base, match_status: "absent" };
    expect(stateOf(x)).toBe("notfound");
    expect(tooltipOf(x, [2009, 2021])).toBe("Searched City Council Discretionary Funding (covers FY2009–FY2021) as of 2026-10-14; no match.");
    expect(stateOf(undefined)).toBe("nocheck");
    expect(tooltipOf(null)).toBe("No NYC Open Data dataset covers this year, so we couldn't check.");
  });

  test("the strip counts only found as found, and maybe separately", () => {
    const c = { records: 100, same: 80, differs: 2, context: 0, ambiguous: 6 };
    expect(stripShares(c)).toMatchObject({ foundPct: 82, maybePct: 6 });
    const cov = [{ dataset_id: "d", fiscal_year: 2026, covered: 1 }, { dataset_id: "d", fiscal_year: 2027, covered: 1 }, { dataset_id: "d", fiscal_year: 2015, covered: 0 }];
    expect(coveredRange(cov, "d")).toEqual([2026, 2027]);
  });

  test("the note says what a match is and is not", () => {
    expect(HOW_WE_CHECK).toMatch(/^How we check\./);
    expect(HOW_WE_CHECK).toContain("A match is our best effort, not an official link.");
    expect(HOW_WE_CHECK).toContain("If you spot a wrong match, tell us.");
  });
});
