import { afterAll, beforeAll, describe, expect, test, vi } from "vitest";

import { needsEngine, tablesForView } from "../../src/duckdb/needs.js";

/**
 * Which views start the query engine (#301, first PR). The engine is DuckDB-WASM: about 8.6 MB
 * over the wire and 34 MB decoded, before any data. A view that can answer without it must not
 * start it:
 *
 *   - City agency budgets reads its own JSON (#299).
 *   - About the data reads only manifest.json.
 *   - Review, on a public build (no review_screen in the manifest), only says "No review queue in
 *     this build". Before this fix it downloaded all 29 tables (22 MB) first (#301 triage, point 3).
 *
 * needsEngine returns null while the manifest is not in yet and the answer depends on it, so the
 * app waits instead of guessing. Each test says what result would make it FAIL.
 */

const PUBLIC = {
  files: Object.fromEntries(
    ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta"].map((t) => [t + ".parquet", { bytes: 1, rows: 1, sha256: "a".repeat(64) }])
  ),
};
const REVIEW_BUILD = { ...PUBLIC, review_screen: true };

describe("needsEngine (needs.js)", () => {
  test("City agency budgets, About the data, Years and Council vs OMB never start the engine", () => {
    // FAILS if one of them starts DuckDB, with or without a manifest.
    for (const view of ["agencies", "about", "years", "omb"]) {
      for (const m of [null, PUBLIC, REVIEW_BUILD]) expect(needsEngine(view, m), `${view} ${m ? "manifest" : "no manifest"}`).toBe(false);
    }
  });

  test("Review starts the engine only in a review build, and waits for the manifest to know", () => {
    // FAILS if a public build's #view=review starts DuckDB (the 22 MB bug), or a review build's does not.
    expect(needsEngine("review", PUBLIC)).toBe(false);
    expect(needsEngine("review", REVIEW_BUILD)).toBe(true);
    expect(needsEngine("review", null)).toBe(null);
  });

  test("every other Council view still starts the engine", () => {
    // FAILS if this fix stops a view that reads DuckDB from loading it.
    for (const view of [undefined, "awards", "award", "compare", "capital", "capital-row", "schedc", "transparency", "book", "orgs", "terms", "source"]) {
      expect(needsEngine(view, PUBLIC), String(view)).toBe(true);
    }
  });

  test("on a public build, Review asks for no table at all", () => {
    // FAILS if tablesForView still lists every file for a review screen that does not exist.
    expect(tablesForView({ view: "review" }, PUBLIC)).toEqual([]);
  });
});

// ---------------------------------------------------------------- the manifest, alone

const requested = [];
let engineImported = false;
vi.mock("@duckdb/duckdb-wasm", () => {
  engineImported = true;
  return {};
});

describe("ensureManifest (store.js)", () => {
  let store;
  beforeAll(async () => {
    vi.stubGlobal("window", { location: { href: "https://example.test/explorer/" } });
    vi.stubGlobal("fetch", async (url) => {
      requested.push(String(url));
      return new Response(JSON.stringify(PUBLIC), { status: 200 });
    });
    store = await import("../../src/duckdb/store.js");
  });
  afterAll(() => vi.unstubAllGlobals());

  test("reads manifest.json once, and nothing else: no engine, no table", async () => {
    // FAILS if reading the manifest imports DuckDB or fetches a data file, or fetches twice.
    await Promise.all([store.ensureManifest(), store.ensureManifest()]);
    await store.ensureManifest();
    expect(requested.map((u) => new URL(u).pathname.split("/").at(-1))).toEqual(["manifest.json"]);
    expect(store.getSnapshot().manifest).toEqual(PUBLIC);
    expect(engineImported).toBe(false);
    expect(store.getSnapshot().phase).not.toBe("engine");
  });
});
