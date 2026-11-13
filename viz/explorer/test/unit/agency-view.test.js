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
    expect(vsLastYearWords({ prevRow: { adopted: null }, row, year: 2026, first: 2017, noun: "unit", seenBefore: true })).toBe("No FY2025 adopted figure");
    // NYPD 011 has an FY2025 row with no adopted figure: it is new in FY2026.
    expect(vsLastYearWords({ prevRow: { adopted: null }, row, year: 2026, first: 2017, noun: "unit", seenBefore: false })).toBe("New unit in FY2026");
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

describe("short money, colored changes, sorting, split units (#307)", () => {
  test("short money: $117.8B, $767.0M, $562K", async () => {
    const { moneyShort } = await import("../../src/views/Agencies.jsx");
    expect(moneyShort(117791473676)).toBe("$117.8B");
    expect(moneyShort(766619276)).toBe("$766.6M");
    expect(moneyShort(767000000)).toBe("$767.0M");
    expect(moneyShort(562059)).toBe("$562K");
    expect(moneyShort(420)).toBe("$420");
    expect(moneyShort(-2500000)).toBe("−$2.5M");
    expect(moneyShort(null)).toBeNull();
  });

  test("a change keeps its sign and exact dollars; up is green, down red, zero neither", async () => {
    // FAILS if color becomes the only signal (WCAG 1.4.1) or the exact figure is lost.
    const { changeText } = await import("../../src/views/Agencies.jsx");
    expect(changeText({ dollars: 3406481844, pct: 2.978 })).toEqual({ short: "+3.0%", full: "+$3,406,481,844 (+3.0%)", tone: "up" });
    expect(changeText({ dollars: -10, pct: -10 })).toMatchObject({ short: "−10.0%", tone: "down" });
    expect(changeText({ dollars: 0, pct: 0 })).toMatchObject({ short: "0.0%", tone: undefined });
  });

  test("sorting: numbers low to high first then flip; names by number then A–Z; no figure last", async () => {
    const { SORT_DEFAULT, nextSort, sortRows, sortMessage } = await import("../../src/views/Agencies.jsx");
    const cols = [
      { key: "name", kind: "name", label: "Unit", number: (r) => r.n, name: (r) => r.name },
      { key: "adopted", kind: "num", label: "Adopted FY2026", value: (r) => r.a },
    ];
    const rows = [
      { n: "002", name: "B", a: 5 },
      { n: "001", name: "C", a: null },
      { n: "003", name: "A", a: 9 },
    ];
    const ids = (st) => sortRows(rows, cols, st).map((r) => r.n);
    expect(ids(SORT_DEFAULT)).toEqual(["003", "002", "001"]);
    let st = nextSort(SORT_DEFAULT, cols[0]);
    expect(ids(st)).toEqual(["001", "002", "003"]);
    expect(sortMessage(cols, st, "unit")).toBe("Sorted by unit number.");
    st = nextSort(st, cols[0]);
    expect(ids(st)).toEqual(["003", "002", "001"]);
    expect(sortMessage(cols, st, "unit")).toBe("Sorted by unit name, A to Z.");
    st = nextSort(st, cols[1]);
    expect(st.dir).toBe("ascending");
    expect(ids(st)).toEqual(["002", "003", "001"]);
    expect(sortMessage(cols, st, "unit")).toBe("Sorted by Adopted FY2026, low to high. Rows with no figure are last.");
    expect(ids(nextSort(st, cols[1]))).toEqual(["003", "002", "001"]);
  });

  test("split units: a big drop in a year the agency added units names the new ones", async () => {
    // NYPD FY2026: 001 Operations $1.51B -> $271M while 011 and 012 appear.
    const { splitHints } = await import("../../src/views/Agencies.jsx");
    const units = [
      { unit_number: "001", adopted: 270725018, prev: { adopted: 1506991264 }, seenBefore: true },
      { unit_number: "002", adopted: 367421058, prev: { adopted: 360865805 }, seenBefore: true },
      { unit_number: "011", adopted: 766619276, prev: { adopted: null }, seenBefore: false },
      { unit_number: "012", adopted: 659228617, prev: null, seenBefore: false },
    ];
    const h = splitHints(units, 2026, 2017);
    expect(h.added).toEqual(["011", "012"]);
    expect([...h.dropped]).toEqual(["001"]);
    expect(splitHints(units.slice(0, 2), 2026, 2017).dropped.size).toBe(0);
    expect(splitHints(units, 2017, 2017).added).toEqual([]);
  });
});
