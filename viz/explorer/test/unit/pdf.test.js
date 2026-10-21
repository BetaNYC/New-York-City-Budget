import { describe, expect, test } from "vitest";

import * as P from "../../src/query/pdf.js";
import { readHash, writeHash } from "../../src/state/hash.js";

describe("row boxes to the page", () => {
  test("bbox_pt (unrotated, top-left origin) -> PDF user space (bottom-left origin)", () => {
    // HR CC0168 on p.47 of the capital book: a 612 x 792 MediaBox shown with /Rotate 90.
    expect(P.bboxToPdfRect("489.30,176.03,506.46,769.62", [0, 0, 612, 792])).toEqual([489.3, 792 - 769.62, 506.46, 792 - 176.03]);
    expect(P.bboxToPdfRect("1,2,3,4", [10, 20, 110, 220])).toEqual([11, 216, 13, 218]);
    expect(P.bboxToPdfRect("", [0, 0, 1, 1])).toBeNull();
    expect(P.parseBbox("a,b,c,d")).toBeNull();
  });
  test("a viewport rectangle in either corner order becomes a CSS box", () => {
    expect(P.viewportBox([30, 40, 10, 5])).toEqual({ left: 10, top: 5, width: 20, height: 35 });
  });
});

describe("matching the §254 book to the Council workbook", () => {
  const idx = P.indexPdfMatches([{ fiscal_year: 2027, sub_id: "HR CC0168", budget_line: "HR DN917", sponsor: "ABREU" }]);
  test("on report year, the ID without its agency code, and the budget line", () => {
    expect(P.pdfMatchFor(idx, { report_year: 2027, project_id: "CC0168", budget_line_norm: "HR DN917" })?.sponsor).toBe("ABREU");
    expect(P.pdfMatchFor(idx, { report_year: 2027, project_id: "CC0168", budget_line: "hr-dn917" })?.sponsor).toBe("ABREU");
    expect(P.pdfMatchFor(idx, { report_year: 2026, project_id: "CC0168", budget_line_norm: "HR DN917" })).toBeUndefined();
    expect(P.pdfMatchFor(idx, { report_year: 2027, project_id: "CC0168", budget_line_norm: "HR DN918" })).toBeUndefined();
  });
  test("no query without a year", () => {
    expect(P.capitalPdfMatchesQuery([])).toBeNull();
    expect(P.capitalPdfMatchesQuery([2027, 2027]).params).toEqual([2027]);
  });
});

describe("filters", () => {
  test("text filters fold case and accents on both sides", () => {
    expect(P.textKey("  Avilés ")).toBe("aviles");
    const q = P.orgsTotalsQuery({ organization: "Fornay" });
    expect(q.sql).toContain("strip_accents(lower(");
    expect(q.params).toEqual(["fornay"]);
  });
  test("a budget-line filter uses the normal form", () => {
    expect(P.orgsQuery({ budget_line: "pv-dn004" }, 0).params).toEqual(["PV DN004"]);
  });
  test("review notes: no query for a row with no review id", () => {
    expect(P.reviewNotesQuery("")).toBeNull();
    expect(P.reviewNotesQuery("a;b;a").params).toEqual(["a", "b"]);
  });
});

describe("hash state for the new views", () => {
  test("round trip", () => {
    const s = { ...readHash(""), view: "source", spdf: "source/FY27/x.pdf", spage: 47, sbox: "1,2,3,4", slabel: "HR CC0168" };
    expect(readHash(writeHash(s))).toEqual(s);
    const t = { ...readHash(""), view: "terms", tfy: 2027, tagency: "education", tunit: "001", tpage: 1 };
    expect(readHash(writeHash(t))).toEqual(t);
  });
});
