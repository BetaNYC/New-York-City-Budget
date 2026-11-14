/**
 * The Agency budgets view's URL state (#270, built in #286).
 *
 * PENDING #286: skipped until src/state/hash.js lists the "agencies" view. Then these run as is.
 *
 * Contract (docs/plans/2026-11-12-270-agency-budgets.md, "Explorer view"):
 *   view=agencies   the view
 *   abfy            fiscal year (integer); null = the newest year with an adopted budget
 *   abag            agency number, TEXT ("056"; never parsed to 56)
 *   abunit          unit of appropriation number, TEXT ("001")
 *   legacy          an old /agencies/ route ("police-department/operations"), resolved once
 */
import { describe, expect, test } from "vitest";

import { DEFAULT_STATE, VIEWS, readHash, writeHash } from "../../src/state/hash.js";
import { BASE, tablesForView } from "../../src/duckdb/needs.js";

const PENDING = !VIEWS.includes("agencies");

describe.skipIf(PENDING)("Agency budgets: URL state (PENDING #286 until VIEWS has 'agencies')", () => {
  test("the view and its keys are in the state, with blank defaults", () => {
    // FAILS if a key is missing (a link someone sent would lose it) or defaults to a value.
    for (const k of ["abfy", "abag", "abunit", "legacy"]) expect(k in DEFAULT_STATE).toBe(true);
    expect(DEFAULT_STATE.abfy).toBeNull();
    expect(DEFAULT_STATE.abag).toBe("");
    expect(DEFAULT_STATE.abunit).toBe("");
  });

  test("agency and unit numbers stay text with their zeros; the year is a number", () => {
    // FAILS if "056" comes back as 56 (it would match no row) or the year as a string.
    const s = readHash("#view=agencies&abfy=2025&abag=056&abunit=001");
    expect(s.view).toBe("agencies");
    expect(s.abfy).toBe(2025);
    expect(s.abag).toBe("056");
    expect(s.abunit).toBe("001");
  });

  test("round-trips, and write(read(write(s))) is stable", () => {
    // FAILS if a shared link changes when the page rewrites it.
    const s = { ...DEFAULT_STATE, view: "agencies", abfy: 2019, abag: "341", abunit: "002" };
    const h = writeHash(s);
    expect(readHash(h)).toEqual(s);
    expect(writeHash(readHash(h))).toBe(h);
  });

  test("a bad year degrades to the default instead of breaking the page", () => {
    // FAILS if "#view=agencies&abfy=abc" throws or keeps "abc".
    expect(readHash("#view=agencies&abfy=abc").abfy).toBeNull();
  });

  test("the agency view asks DuckDB for nothing, and the Council views never load agency_budget", () => {
    // FAILS if agency_budget is added to the first-visit download (BASE), or the agency view asks
    // for any table: it reads JSON (src/agency/data.js, #299), never the 33 MB query engine.
    const manifest = { files: { "agency_budget.parquet": { rows: 1, bytes: 1 }, "disclosure.parquet": { rows: 1, bytes: 1 } } };
    expect(BASE).not.toContain("agency_budget");
    expect(tablesForView({ ...DEFAULT_STATE, view: "agencies" }, manifest)).toEqual([]);
    expect(tablesForView({ ...DEFAULT_STATE, view: "awards" }, manifest)).not.toContain("agency_budget");
  });
});
