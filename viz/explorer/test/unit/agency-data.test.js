import { describe, expect, test } from "vitest";

import { agencyByYear, agencyJsonFiles, agencyList, agencyNames, agencyPath, agencyUnits, agenciesPath, citywidePath, fiscalYears, hasAgency, unitByYear, unitNames } from "../../src/agency/data.js";

/** Two agencies, two years: unit 002 is new in FY2027; FY2027's modified is not published yet. */
const row = (fiscal_year, agency_number, agency_name, unit_number, unit_name, adopted, modified) => ({
  fiscal_year, agency_number, agency_name, unit_number, unit_name, adopted, modified,
  adopted_release: adopted === null ? null : `${fiscal_year - 1}0630`,
  modified_release: modified === null ? null : `${fiscal_year}0630`,
});
const ROWS = [
  row(2026, "056", "POLICE DEPARTMENT", "001", "OPERATIONS", 100.1, 110.2),
  row(2026, "040", "DEPT OF EDUCATION", "401", "GE INSTR", 500, 520),
  row(2027, "056", "POLICE DEPARTMENT", "001", "OPERATIONS", 120.3, null),
  row(2027, "056", "POLICE DEPARTMENT", "002", "EXECUTIVE", 5, null),
  row(2027, "040", "DEPARTMENT OF EDUCATION", "401", "GE INSTR", 530, null),
];
const files = agencyJsonFiles(ROWS, { generated_at: "2026-11-12T00:00:00Z" });

describe("agency JSON (#299)", () => {
  test("one citywide file, one agency list, one file per agency", () => {
    expect(Object.keys(files).sort()).toEqual([agencyPath("040"), agencyPath("056"), agenciesPath(), citywidePath()].sort());
  });

  test("citywide sums are exact, and a year with no modified figure is null, never 0", () => {
    // FAILS if cents drift (100.1 + 500 in floating point) or an unpublished total becomes 0.
    const [fy26, fy27] = files[citywidePath()].years;
    expect(fy26).toMatchObject({ fiscal_year: 2026, adopted: 600.1, modified: 630.2, units: 2, units_no_modified: 0 });
    expect(fy27).toMatchObject({ fiscal_year: 2027, adopted: 655.3, modified: null, units: 3, units_no_modified: 3 });
    expect(fiscalYears(files[citywidePath()])).toEqual([
      { fiscal_year: 2027, has_modified: false },
      { fiscal_year: 2026, has_modified: true },
    ]);
  });

  test("the agency list is largest adopted first, with each year's own name", () => {
    const list = agencyList(files[agenciesPath()], 2027);
    expect(list.map((r) => [r.agency_number, r.agency_name, r.adopted])).toEqual([
      ["040", "DEPARTMENT OF EDUCATION", 530],
      ["056", "POLICE DEPARTMENT", 125.3],
    ]);
    expect(list[0]).not.toHaveProperty("fiscal_year");
    expect(hasAgency(files[agenciesPath()], "056")).toBe(true);
    expect(hasAgency(files[agenciesPath()], "999")).toBe(false);
  });

  test("a unit missing from a year is missing from that year, not shown as $0", () => {
    const nypd = files[agencyPath("056")];
    expect(agencyUnits(nypd, 2026).map((u) => u.unit_number)).toEqual(["001"]);
    expect(agencyUnits(nypd, 2027).map((u) => [u.unit_number, u.adopted, u.modified])).toEqual([
      ["001", 120.3, null],
      ["002", 5, null],
    ]);
    expect(unitByYear(nypd, "002").map((y) => y.fiscal_year)).toEqual([2027]);
    expect(agencyByYear(nypd).map((y) => [y.fiscal_year, y.adopted, y.modified])).toEqual([
      [2026, 100.1, 110.2],
      [2027, 125.3, null],
    ]);
  });

  test("old links can match any name an agency or unit has had", () => {
    expect(agencyNames(files[agenciesPath()]).filter((n) => n.agency_number === "040").map((n) => n.agency_name)).toEqual(["DEPARTMENT OF EDUCATION", "DEPT OF EDUCATION"]);
    expect(unitNames(files[agencyPath("056")]).map((n) => n.unit_name)).toEqual(["OPERATIONS", "OPERATIONS", "EXECUTIVE"]);
  });
});
