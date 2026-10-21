import { describe, expect, test } from "vitest";

import * as Q from "../../src/query/sql.js";

describe("disclosure query building", () => {
  test("no filters: no WHERE, and the MCP's sort", () => {
    const q = Q.disclosureRowsQuery({}, 0);
    expect(q.sql).not.toMatch(/WHERE/);
    expect(q.sql).toMatch(/ORDER BY amount DESC, fiscal_year, source_row LIMIT 50 OFFSET 0/);
    expect(q.params).toEqual([]);
  });

  test("text filters match the folded twin with the MCP's fold rule, as a parameter", () => {
    const q = Q.disclosureTotalsQuery({ legal_name: "  Jewish Émigré’s  " });
    expect(q.sql).toContain("contains(lower(COALESCE(legal_name_fold, legal_name)), ?)");
    expect(q.params).toEqual(["jewish emigre's"]);
  });

  test("user text never reaches the SQL string (quotes, wildcards, SQL)", () => {
    const evil = "x'); DROP TABLE disclosure; --%_";
    const q = Q.disclosureRowsQuery({ legal_name: evil, council_member: evil }, 0);
    expect(q.sql).not.toContain("DROP");
    expect(q.params.length).toBe(2);
  });

  test("blank and whitespace-only filters are no filter", () => {
    expect(Q.disclosureWhere({ legal_name: "   ", ein: "", status: "", fiscal_year: null }).sql).toBe("");
  });

  test("EIN compares digits only; status only from the known set; amounts as numbers", () => {
    const w = Q.disclosureWhere({ ein: "13-3179546", status: "bogus", min_amount: "100", max_amount: 200, fiscal_year: "2027" });
    expect(w.sql).toBe("WHERE fiscal_year = ? AND ein = ? AND amount >= ? AND amount <= ?");
    expect(w.params).toEqual([2027, "133179546", 100, 200]);
  });

  test("pages offset by PAGE_SIZE; a bad page is page 0", () => {
    expect(Q.disclosureRowsQuery({}, 2).sql).toContain(`OFFSET ${2 * Q.PAGE_SIZE}`);
    expect(Q.disclosureRowsQuery({}, -4).sql).toContain("OFFSET 0");
    expect(Q.disclosureRowsQuery({}, "x").sql).toContain("OFFSET 0");
  });

  test("rollupDisclosure totals by status and by year, and counts every row", () => {
    const r = Q.rollupDisclosure([
      { fiscal_year: 2026, status_norm: "cleared", n: 2, amount: 10 },
      { fiscal_year: 2027, status_norm: "cleared", n: 3, amount: 5.5 },
      { fiscal_year: 2027, status_norm: "pending", n: 1, amount: 1 },
      { fiscal_year: 2027, status_norm: "weird", n: 1, amount: 2 },
    ]);
    expect(r.matched).toBe(7);
    expect(r.totals.cleared).toEqual({ rows: 5, amount: 15.5 });
    expect(r.totals.other).toEqual({ rows: 1, amount: 2 });
    expect(r.by_year.map((y) => y.fiscal_year)).toEqual([2026, 2027]);
  });
});

describe("capital and OMB query building", () => {
  test("district filter matches a token in the workbook district list", () => {
    const w = Q.capitalWhere({ council_district: "08" });
    expect(w.sql).toBe("WHERE contains(district_tokens, ?)");
    expect(w.params).toEqual([",8,"]);
  });

  test("budget line is normalized; an unreadable one matches nothing rather than everything", () => {
    expect(Q.capitalWhere({ budget_line: "p-d018" }).params).toEqual(["P D018"]);
    const bad = Q.capitalWhere({ budget_line: "PD018" });
    expect(bad.sql).toBe("WHERE budget_line_norm = ?");
    expect(bad.params[0]).not.toMatch(/^[A-Z]{1,2} /);
  });

  test("normBudgetLine", () => {
    expect(Q.normBudgetLine("  pw   dn846 ")).toBe("PW DN846");
    expect(Q.normBudgetLine("AG-D001")).toBe("AG D001");
    expect(Q.normBudgetLine("PD018")).toBeNull();
  });

  test("capital rows sort unknown amounts last, then by amount", () => {
    expect(Q.capitalRowsQuery({}, 0).sql).toMatch(/ORDER BY amount IS NULL, amount DESC, report_year, source_file, seq/);
  });

  test("rollupCapital separates report-year, out-year and unknown amounts", () => {
    const r = Q.rollupCapital([
      { report_year: 2020, kind: "report", n: 2, amount: 100 },
      { report_year: 2020, kind: "out", n: 1, amount: 50 },
      { report_year: 2020, kind: "unknown", n: 1, amount: 0 },
      { report_year: 2021, kind: "report", n: 1, amount: 7 },
    ]);
    expect(r.matched).toBe(5);
    expect(r.report_year_amounts).toEqual({ rows: 3, amount: 107 });
    expect(r.out_year_amounts).toEqual({ rows: 1, amount: 50 });
    expect(r.amount_unknown).toBe(1);
    expect(r.by_report_year).toHaveLength(2);
  });

  test("OMB verdict filter accepts only known verdicts", () => {
    expect(Q.ombWhere({ verdict: "differ", report_year: 2024 }).params).toEqual([2024, "differ"]);
    expect(Q.ombWhere({ verdict: "nope" }).sql).toBe("");
  });
});
