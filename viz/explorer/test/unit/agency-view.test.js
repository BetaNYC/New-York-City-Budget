/**
 * Pure helpers of the Agency budgets view (#286): the "Download this table" CSV, and the chart's
 * text alternative and axis. Each test says what would make it FAIL.
 */
import { describe, expect, test } from "vitest";

import { csvCell, toCsv } from "../../src/agency/csv.js";
import { chartSummary, niceScale, shortMoney } from "../../src/components/YearChart.jsx";
import { change, pad3 } from "../../src/query/agency.js";

describe("Agency budgets view helpers", () => {
  test("CSV cells are quoted only when needed, and a missing figure is empty, not 0", () => {
    // FAILS if a name with a comma splits a row, or NULL is written as 0.
    expect(csvCell("DEPT OF CONSUMER & WORKER PROTECTION")).toBe("DEPT OF CONSUMER & WORKER PROTECTION");
    expect(csvCell('A, "B"')).toBe('"A, ""B"""');
    expect(csvCell(null)).toBe("");
    expect(csvCell(0)).toBe("0");
    const csv = toCsv([{ a: "056", n: "POLICE, NYC", v: null }], [["Agency", "a"], ["Name", "n"], ["Adopted", "v"], ["Year", () => 2025]]);
    expect(csv).toBe('Agency,Name,Adopted,Year\r\n056,"POLICE, NYC",,2025\r\n');
  });

  test("the chart's name sums it up from the numbers, and says what is not published", () => {
    // FAILS if the chart's text alternative drops the years, the words adopted / modified, or
    // calls an unpublished figure anything else.
    const s = chartSummary(
      [
        { year: 2017, adopted: 100, modified: 120 },
        { year: 2018, adopted: 300, modified: null },
      ],
      "TEST AGENCY",
      2018
    );
    expect(s).toMatch(/adopted and modified/i);
    expect(s).toMatch(/FY2017–FY2018/);
    expect(s).toMatch(/\$100 in FY2017 to \$300 in FY2018/);
    expect(s).toMatch(/FY2018 modified is not yet published/);
  });

  test("axis steps are round, and labels short", () => {
    expect(niceScale(117_791_473_676)).toEqual({ top: 120_000_000_000, step: 20_000_000_000 });
    expect(shortMoney(20_000_000_000)).toBe("$20B");
    expect(shortMoney(2_500_000)).toBe("$2.5M");
  });

  test("change is null when either figure is missing, and agency numbers keep three digits", () => {
    // FAILS if a missing figure is treated as $0 (a -100% change), or "56" is not "056".
    expect(change(null, 5)).toBeNull();
    expect(change(5, null)).toBeNull();
    expect(change(200, 150)).toEqual({ dollars: -50, pct: -25 });
    expect(pad3("56")).toBe("056");
    expect(pad3("police")).toBe("police");
  });
});

describe("citywide summary (#300)", () => {
  test("the change from the year before reads like the old app's summary", async () => {
    // FY2026 vs FY2025, as the old /agencies/ app showed them (Noel's QA, 2026-11-12).
    const { pctText } = await import("../../src/views/Agencies.jsx");
    expect(pctText(114384991832, 117791473676)).toBe("+3.0%");
    expect(pctText(123844584236, 129228819136)).toBe("+4.3%");
    expect(pctText(100, 90)).toBe("−10.0%");
    // FAILS if a missing figure (not yet published) turns into a change from or to $0.
    expect(pctText(123844584236, null)).toBeNull();
    expect(pctText(null, 5)).toBeNull();
  });
});

describe("change columns say which change, or why there is none (#306)", () => {
  test("adopted vs. the year before: a reason instead of a bare dash", async () => {
    // FAILS if a missing prior-year figure shows as "—", $0, or a -100% change.
    const { vsLastYearWords } = await import("../../src/views/Agencies.jsx");
    const row = { adopted: 5, modified: 6 };
    expect(vsLastYearWords({ prevRow: { adopted: 4 }, row, year: 2026, first: 2017, noun: "unit" })).toBeNull();
    expect(vsLastYearWords({ prevRow: null, row, year: 2026, first: 2017, noun: "unit", seenBefore: false })).toBe("New unit in FY2026");
    expect(vsLastYearWords({ prevRow: null, row, year: 2026, first: 2017, noun: "unit", seenBefore: true })).toBe("Not in the FY2025 budget");
    expect(vsLastYearWords({ prevRow: { adopted: null }, row, year: 2026, first: 2017, noun: "unit" })).toBe("No FY2025 adopted figure");
    expect(vsLastYearWords({ prevRow: null, row, year: 2017, first: 2017, noun: "agency" })).toBe("No FY2016 figure");
    expect(vsLastYearWords({ prevRow: { adopted: 4 }, row: { adopted: null }, year: 2026, first: 2017, noun: "unit" })).toBe("No FY2026 adopted figure");
  });

  test("modified vs. adopted: the newest year is not yet published, never $0", async () => {
    const { vsAdoptedWords, NOT_PUBLISHED, NOT_IN_BUDGET } = await import("../../src/views/Agencies.jsx");
    expect(vsAdoptedWords({ row: { adopted: 5, modified: 6 }, year: 2026, newest: 2027 })).toBeNull();
    expect(vsAdoptedWords({ row: { adopted: 5, modified: null }, year: 2027, newest: 2027 })).toBe(NOT_PUBLISHED);
    expect(vsAdoptedWords({ row: { adopted: 5, modified: null }, year: 2025, newest: 2027 })).toBe("No FY2025 modified figure");
    expect(vsAdoptedWords({ row: null, year: 2025, newest: 2027 })).toBe(NOT_IN_BUDGET);
  });
});
