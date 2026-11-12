/**
 * Old /agencies/ links keep working (#270; built in #286, used by the forwarding page in #288).
 *
 * PENDING #286: skipped until src/agency/legacy.js exists. Then these run as is.
 *
 * The old Backbone app (viz/agencies/js/app.js) has three routes:
 *   #(?year=Y)                                   all agencies, year Y
 *   #fund-detail/<agency-slug>(/<unit-slug>)?year=Y
 *   #control-officer-detail/<agency-slug>(/<unit-slug>)?year=Y   (removed in #266; forwards to fund-detail)
 * Slugs come from names with BudgetHelpers.convertToSlug (viz/agencies/js/budget_helpers.js).
 *
 * Contract of src/agency/legacy.js:
 *   agencySlug(text)              the old slug rule, exactly
 *   legacyToExplorerHash(hash)    old fragment -> explorer hash: view=agencies, abfy=Y, legacy=<path>
 *   resolveLegacy(legacy, names)  <path> -> { abag, abunit, candidates }, or null when no agency matches.
 *     A known agency with an unknown unit gives { abag, abunit: "", candidates: [] }.
 *     names: rows { agency_number, agency_name, unit_number, unit_name }, every name ever published.
 *     An agency slug matches any name the agency has had (866 was DEPARTMENT OF CONSUMER AFFAIRS).
 *     A unit slug shared by two unit numbers (39 cases, e.g. City Council committees 600 and 800)
 *     returns abunit "" and both in `candidates`, so the page can ask, never guess.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

import { describe, expect, test } from "vitest";

import { readHash } from "../../src/state/hash.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..", "..");
const REPO = resolve(APP, "..", "..");
const MODULE = join(APP, "src", "agency", "legacy.js");
const L = existsSync(MODULE) ? await import(MODULE) : null;

/** The old app's own slug function, run from its own file, so the comparison is with the real thing. */
function oldSlug() {
  const ctx = {};
  vm.runInNewContext(readFileSync(join(REPO, "viz", "agencies", "js", "budget_helpers.js"), "utf8") + "\n;this.BudgetHelpers = BudgetHelpers;", ctx);
  return ctx.BudgetHelpers.convertToSlug;
}

/** Simple CSV for the committed files read here (no quoted fields in these columns). */
function csvRows(rel) {
  const [head, ...lines] = readFileSync(join(REPO, rel), "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((l) => {
    // Names may contain commas inside quotes; split on commas outside quotes.
    const cells = l.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map((c) => c.replace(/,$/, "").replace(/^"|"$/g, "").replace(/""/g, '"'));
    return Object.fromEntries(cols.map((c, i) => [c, cells[i] ?? ""]));
  });
}
const pad = (s) => (/^\d+$/.test(s) ? s.padStart(3, "0") : s);
/** Every agency and unit name in the Open Data snapshot, every year. */
const NAMES = csvRows("source/agency-budget-qa/by_unit.csv").map((r) => ({
  agency_number: pad(r.agency_number),
  agency_name: r.agency_name.trim(),
  unit_number: pad(r.unit_appropriation_number),
  unit_name: r.unit_appropriation_name.trim(),
}));
/** What the old app links to: its CSV's agency (Fund) and unit (Department) names. */
const OLD = csvRows("viz/agencies/data/nyc_budget.csv");

describe.skipIf(!L)("Agency budgets: old /agencies/ links (PENDING #286 until src/agency/legacy.js exists)", () => {
  test("agencySlug equals the old app's convertToSlug on every agency and unit name it shows", () => {
    // FAILS if any old link would resolve to nothing because the slug rule drifted.
    const slug = oldSlug();
    for (const r of OLD) {
      expect(L.agencySlug(r.Fund)).toBe(slug(r.Fund));
      expect(L.agencySlug(r.Department)).toBe(slug(r.Department));
    }
  });

  test.each([
    ["", { abfy: null, legacy: "" }],
    ["#", { abfy: null, legacy: "" }],
    ["#?year=2019", { abfy: 2019, legacy: "" }],
    ["#fund-detail/police-department?year=2025", { abfy: 2025, legacy: "police-department" }],
    ["#fund-detail/police-department/operations?year=2024", { abfy: 2024, legacy: "police-department/operations" }],
    ["#fund-detail/police-department", { abfy: null, legacy: "police-department" }],
    ["#control-officer-detail/police-department?year=2023", { abfy: 2023, legacy: "police-department" }],
    ["#control-officer-detail/manhattan-community-board-1/personal-services?year=2025", { abfy: 2025, legacy: "manhattan-community-board-1/personal-services" }],
    ["#something-else/entirely", { abfy: null, legacy: "" }],
  ])("legacyToExplorerHash(%j) lands on the agencies view with the right year and path", (old, want) => {
    // FAILS if an old link lands on the Council view, drops its year, or keeps junk.
    const s = readHash(L.legacyToExplorerHash(old));
    expect(s.view).toBe("agencies");
    expect(s.abfy).toBe(want.abfy);
    expect(s.legacy).toBe(want.legacy);
  });

  test("every agency link the old app can make resolves to exactly one agency number", () => {
    // FAILS if an old agency link resolves to nothing, or to the wrong agency.
    const slug = oldSlug();
    const byName = new Map(NAMES.map((n) => [n.agency_name, n.agency_number]));
    for (const fund of new Set(OLD.map((r) => r.Fund))) {
      const r = L.resolveLegacy(slug(fund), NAMES);
      expect(r, fund).not.toBeNull();
      expect(r.abag, fund).toBe(byName.get(fund));
      expect(r.abunit).toBe("");
    }
  });

  test("the old name of agency 866 still resolves (DEPARTMENT OF CONSUMER AFFAIRS)", () => {
    // FAILS if only the newest name is matched: the old app shows 866 under both names.
    expect(L.resolveLegacy("department-of-consumer-affairs", NAMES)?.abag).toBe("866");
    expect(L.resolveLegacy("dept-of-consumer-worker-protection", NAMES)?.abag).toBe("866");
  });

  test("a unit link resolves to its unit, or to every unit that shares its slug", () => {
    // FAILS if a shared slug silently picks one unit (the old app's findWhere took the first).
    const slug = oldSlug();
    const groups = new Map();
    for (const r of OLD) {
      const k = `${slug(r.Fund)}/${slug(r.Department)}`;
      groups.set(k, [...(groups.get(k) ?? []), r["Department ID"]]);
    }
    let shared = 0;
    for (const [path, ids] of groups) {
      const r = L.resolveLegacy(path, NAMES);
      expect(r, path).not.toBeNull();
      if (ids.length === 1) {
        expect(r.abunit, path).toBe(ids[0]);
      } else {
        shared++;
        expect(r.abunit, path).toBe("");
        expect(r.candidates.map((c) => c.unit_number).sort(), path).toEqual([...ids].sort());
      }
    }
    expect(shared).toBe(39);
  });

  test("an unknown agency returns null; a known agency with an unknown unit lands on the agency", () => {
    // FAILS if a mistyped link quietly shows a different agency, or a stale unit link loses the
    // agency it named.
    expect(L.resolveLegacy("no-such-agency", NAMES)).toBeNull();
    const r = L.resolveLegacy("police-department/no-such-unit", NAMES);
    expect(r?.abag).toBe("056");
    expect(r?.abunit).toBe("");
    expect(r?.candidates).toEqual([]);
  });
});
