import { describe, expect, test } from "vitest";

import { buildYears, headlineOk } from "../../src/data/years.js";

const disc = [
  { fiscal_year: 2009, loaded: 1, early_snapshot: 1, note: "early snapshot: ...", rows: 10, cleared_rows: 8, cleared_amount: 80, pending_rows: 2, pending_amount: 20, other_rows: 0, other_amount: 0 },
  { fiscal_year: 2010, loaded: 0, early_snapshot: 0, note: "not loaded: incomplete", rows: 0, cleared_rows: 0, cleared_amount: 0, pending_rows: 0, pending_amount: 0, other_rows: 0, other_amount: 0 },
  { fiscal_year: 2011, loaded: 1, early_snapshot: 0, note: "", rows: 5, cleared_rows: 3, cleared_amount: 30, pending_rows: 1, pending_amount: 1, other_rows: 1, other_amount: 9 },
  { fiscal_year: 2016, loaded: 1, early_snapshot: 0, note: "", rows: 4, cleared_rows: 4, cleared_amount: 40, pending_rows: 0, pending_amount: 0, other_rows: 0, other_amount: 0 },
];
const cap = [
  { report_year: 2015, report_year_amounts: { rows: 1, amount: 5 }, out_year_amounts: { rows: 0, amount: 0 }, amount_unknown: 0 },
  { report_year: 2017, report_year_amounts: { rows: 1, amount: 6 }, out_year_amounts: { rows: 0, amount: 0 }, amount_unknown: 0 },
];
const manifest = { first: 2015, last: 2017, gaps: [{ year: 2016, reason: "No workbook was found. A gap." }] };

describe("year overview model", () => {
  const years = buildYears(disc, cap, manifest);
  const at = (y) => years.find((r) => r.fiscal_year === y);

  test("covers every year from first to last, with no holes", () => {
    expect(years.map((y) => y.fiscal_year)).toEqual([2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017]);
  });

  test("a not-loaded expense year is a gap with the CSV's note, never zeros", () => {
    expect(at(2010).disclosure).toEqual({ kind: "gap", reason: "not loaded: incomplete" });
  });

  test("a year missing from disclosure_years is a gap with a reason", () => {
    expect(at(2012).disclosure.kind).toBe("gap");
    expect(at(2012).disclosure.reason).toMatch(/disclosure_years\.csv/);
  });

  test("a capital gap year carries the README's reason; years before the dataset say so", () => {
    expect(at(2016).capital).toEqual({ kind: "gap", reason: "No workbook was found. A gap." });
    expect(at(2009).capital.kind).toBe("gap");
    expect(at(2009).capital.reason).toMatch(/starts at FY2015/);
    expect(at(2015).capital.kind).toBe("data");
  });

  test("early snapshots and other-status years are never headline figures", () => {
    expect(headlineOk(at(2009).disclosure)).toBe(false);
    expect(headlineOk(at(2011).disclosure)).toBe(false);
    expect(headlineOk(at(2016).disclosure)).toBe(true);
    expect(headlineOk(at(2010).disclosure)).toBe(false);
  });
});
