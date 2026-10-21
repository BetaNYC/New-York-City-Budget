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

  test("the real README explains FY2018, and only FY2018 is a gap", () => {
    const readme = readFileSync(join(REPO, "data", "capital", "README.md"), "utf8");
    const published = [2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027];
    const g = capitalGaps(readme, published);
    expect(g.first).toBe(2015);
    expect(g.last).toBe(2027);
    expect(g.gaps.map((x) => x.year)).toEqual([2018]);
    expect(g.gaps[0].reason).toMatch(/No workbook was found/);
    expect(g.gaps[0].reason).not.toContain("**");
  });

  test("a gap year the README does not explain is a stop", () => {
    const readme = "## Which source each year comes from\n\n| Report year | Source | Why |\n|---|---|---|\n| FY2015 | workbook | ok |\n| FY2017 | workbook | ok |\n";
    expect(() => capitalGaps(readme, [2015, 2017])).toThrow(/FY2016/);
  });

  test("a README without the table is a stop", () => {
    expect(() => readSourceTable("# nothing here")).toThrow(/Which source each year/);
  });
});
