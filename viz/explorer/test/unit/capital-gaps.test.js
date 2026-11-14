import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, test } from "vitest";

import { capitalGaps, readSourceTable, yearsOf } from "../../scripts/lib/capital-gaps.mjs";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");

describe("capital gap reasons from data/capital/README.md", () => {
  test("yearsOf reads single years, lists and en-dash ranges", () => {
    expect(yearsOf("FY2015, FY2016, FY2017")).toEqual([2015, 2016, 2017]);
    expect(yearsOf("FY2019–FY2025")).toEqual([2019, 2020, 2021, 2022, 2023, 2024, 2025]);
    expect(yearsOf("FY2018")).toEqual([2018]);
  });

  test("the real README: no gap since FY2018 is published, PDF-derived (#202)", async () => {
    const readme = readFileSync(join(REPO, "data", "capital", "README.md"), "utf8");
    const { CAPITAL_REPORT_YEARS } = await import("../../../../mcp/scripts/verify-index.mjs");
    expect(CAPITAL_REPORT_YEARS).toContain(2018);
    const g = capitalGaps(readme, CAPITAL_REPORT_YEARS);
    expect(g.first).toBe(2015);
    expect(g.last).toBe(2027);
    expect(g.gaps).toEqual([]);
    // Without FY2018, the README's table would not explain the gap: FY2018's row is no longer "none".
    expect(() => capitalGaps(readme, CAPITAL_REPORT_YEARS.filter((y) => y !== 2018))).toThrow(/FY2018/);
  });

  test("a gap year the README does not explain is a stop", () => {
    const readme = "## Which source each year comes from\n\n| Report year | Source | Why |\n|---|---|---|\n| FY2015 | workbook | ok |\n| FY2017 | workbook | ok |\n";
    expect(() => capitalGaps(readme, [2015, 2017])).toThrow(/FY2016/);
  });

  test("a README without the table is a stop", () => {
    expect(() => readSourceTable("# nothing here")).toThrow(/Which source each year/);
  });
});
