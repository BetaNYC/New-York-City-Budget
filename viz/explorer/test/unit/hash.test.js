import { describe, expect, test } from "vitest";

import { DEFAULT_STATE, FILTER_KEYS, capitalFilters, disclosureFilters, ombFilters, readHash, writeHash } from "../../src/state/hash.js";

describe("URL hash state", () => {
  test("the default state writes an empty hash and reads back", () => {
    expect(writeHash(DEFAULT_STATE)).toBe("");
    expect(readHash("")).toEqual(DEFAULT_STATE);
  });

  test("round-trips every kind of key, and write(read(write(s))) is stable", () => {
    const s = { ...DEFAULT_STATE, view: "capital", fy: 2027, status: "pending", legal_name: "Women’s & kids", min: 1000.5, page: 3, cfy: 2019, district: 8, line: "P D018", verdict: "differ" };
    const h = writeHash(s);
    expect(readHash(h)).toEqual(s);
    expect(writeHash(readHash(h))).toBe(h);
  });

  test("keys serialize in a fixed order whatever order they were set in", () => {
    expect(writeHash({ ...DEFAULT_STATE, ein: "1", fy: 2020 })).toBe(writeHash({ ...DEFAULT_STATE, fy: 2020, ein: "1" }));
  });

  test("unknown keys, bad numbers and unknown views degrade to defaults", () => {
    const s = readHash("#bogus=1&fy=abc&view=nope&min=x&page=2");
    expect(s.fy).toBeNull();
    expect(s.view).toBe("awards");
    expect(s.min).toBeNull();
    expect(s.page).toBe(2);
    expect("bogus" in s).toBe(false);
  });

  test("state maps onto the query layer's filter names", () => {
    const s = { ...DEFAULT_STATE, fy: 2027, ein: "13-3179546", min: 5, cfy: 2026, district: 3, oline: "HL DN164", ofy: 2024 };
    expect(disclosureFilters(s)).toMatchObject({ fiscal_year: 2027, ein: "13-3179546", min_amount: 5 });
    expect(capitalFilters(s)).toMatchObject({ fiscal_year: 2026, council_district: 3 });
    expect(ombFilters(s)).toEqual({ report_year: 2024, budget_line: "HL DN164", verdict: "" });
  });

  test("every filter key is a state key", () => {
    for (const keys of Object.values(FILTER_KEYS)) for (const k of keys) expect(k in DEFAULT_STATE).toBe(true);
  });
});
