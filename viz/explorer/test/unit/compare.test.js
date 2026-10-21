import { describe, expect, test } from "vitest";

import * as D from "../../src/compare/diff.js";
import * as Q from "../../src/compare/queries.js";

describe("diffKeyed", () => {
  const a = [
    { key: "1", label: "A Org", amount: 100, n: 1 },
    { key: "2", label: "B Org", amount: 50, n: 2 },
    { key: "3", label: "C Org", amount: 10.1, n: 1 },
    { key: "4", label: "D Org", amount: 7, n: 1 },
  ];
  const b = [
    { key: "2", label: "B Org", amount: 80, n: 3 },
    { key: "3", label: "C Org", amount: 10.099999999, n: 1 },
    { key: "4", label: "D Org", amount: 5, n: 1 },
    { key: "5", label: "E Org", amount: 30, n: 1 },
  ];
  const { rows, summary } = D.diffKeyed(a, b);
  const by = Object.fromEntries(rows.map((r) => [r.key, r]));
  test("each status", () => {
    expect([by[1].status, by[2].status, by[3].status, by[4].status, by[5].status]).toEqual(["dropped", "increased", "same", "decreased", "new"]);
    expect(by[1]).toMatchObject({ a: 100, b: null, delta: -100 });
    expect(by[5]).toMatchObject({ a: null, b: 30, delta: 30 });
  });
  test("cents decide 'same', so a float's last digit does not", () => {
    expect(by[3].status).toBe("same");
  });
  test("summary counts and sums by status", () => {
    expect(summary.new).toEqual({ count: 1, a: 0, b: 30 });
    expect(summary.dropped).toEqual({ count: 1, a: 100, b: 0 });
    expect(summary.increased.count + summary.decreased.count + summary.same.count).toBe(3);
  });
  test("largest change first; a status filter", () => {
    expect(D.sortDiff(rows).map((r) => r.key)).toEqual(["1", "2", "5", "4", "3"]);
    expect(D.sortDiff(rows, "new").map((r) => r.key)).toEqual(["5"]);
  });
});

describe("diffTerms", () => {
  const A = [
    { item_number: 1, units_of_appropriation: "042:001", condition_text: "Report by June 1, 2026 on bias." },
    { item_number: 2, units_of_appropriation: "125:003; 125:007", condition_text: "List older adult centers." },
    { item_number: 3, units_of_appropriation: "040:401", condition_text: "Gone next year." },
  ];
  const B = [
    { item_number: 1, units_of_appropriation: "042:001", condition_text: "Report by June 1, 2027 on bias." },
    { item_number: 2, units_of_appropriation: "125:007; 125:003", condition_text: "List older adult centers, with air conditioning." },
    { item_number: 3, units_of_appropriation: "071:100", condition_text: "Brand new." },
  ];
  const out = D.diffTerms(A, B);
  test("same text once years are ignored; changed by the same units; added; removed", () => {
    expect(out.map((o) => [o.status, o.a?.item_number ?? null, o.b?.item_number ?? null])).toEqual([
      ["same", 1, 1],
      ["changed", 2, 2],
      ["added", null, 3],
      ["removed", 3, null],
    ]);
  });
  test("normText and unitKey", () => {
    expect(D.normText("By June 1, 2027!")).toBe(D.normText("by june 1, 2026"));
    expect(D.unitKey({ units_of_appropriation: "125:007; 125:003" })).toBe("125:003;125:007");
  });
});

describe("queries", () => {
  test("group by an exact key; blanks are their own group", () => {
    const q = Q.groupQuery("disclosure", "org", 2027);
    expect(q.sql).toContain("mode(legal_name)");
    expect(q.sql).toContain(Q.BLANK);
    expect(q.params).toEqual([2027]);
    expect(Q.groupQuery("capital", "line", 2026).sql).toContain("amount_fy = report_year");
    expect(Q.groupQuery("capital_sd", "line", 2027).sql).toContain("part = 'I'");
    expect(() => Q.groupQuery("capital", "org", 2027)).toThrow();
  });
  test("a drill-down filters on the same key expression the sum used", () => {
    const d = Q.drillQuery("schedule_c", "member", 2027, "Speaker");
    expect(d.params).toEqual([2027, "Speaker"]);
    expect(d.sql).toContain("= ?");
    expect(Q.drillQuery("disclosure", "agency", 2026, "*").params).toEqual([2026]);
  });
  test("gaps say why, never zero", () => {
    const ctx = {
      years: [{ fiscal_year: 2010, loaded: false, note: "not loaded: incomplete" }, { fiscal_year: 2027, loaded: true }],
      capitalYears: [2027],
      capitalGaps: [{ year: 2018, reason: "FY2018 has no structured source" }],
      pdfYears: [{ family: "schedule_c", fiscal_year: 2027, status: "reviewed" }],
    };
    expect(Q.availability("disclosure", 2010, ctx)).toEqual({ ok: false, reason: "not loaded: incomplete" });
    expect(Q.availability("capital", 2018, ctx).reason).toMatch(/FY2018/);
    expect(Q.availability("schedule_c", 2027, ctx)).toEqual({ ok: true, status: "reviewed" });
    expect(Q.availability("schedule_c", 2026, ctx).ok).toBe(false);
  });
});
