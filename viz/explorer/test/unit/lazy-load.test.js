import { afterAll, beforeAll, beforeEach, describe, expect, test, vi } from "vitest";

import { BASE, awardsExtras, tablesForView } from "../../src/duckdb/needs.js";

/**
 * Lazy loading (the explorer's first visit downloads only the landing page's files): which files
 * each view asks for (src/duckdb/needs.js), and that the store fetches exactly those, each once
 * (src/duckdb/store.js, with DuckDB-WASM and fetch replaced by stand-ins that log the requests).
 * test/lazy-load.test.mjs checks the same lists against the real build: each view's queries run
 * with only its files loaded.
 */

const fam = (main, tables) => ({ label: main, main, tables, decisions: {} });
const MANIFEST = {
  source_commit: "0".repeat(40),
  pdf_families: {
    capital_sd: fam("pdf_capital_sd", ["pdf_capital_sd", "pdf_capital_sd_orgs", "pdf_capital_sd_totals"]),
    terms: fam("pdf_terms", ["pdf_terms", "pdf_terms_units", "pdf_terms_fsr"]),
    schedule_c: fam("pdf_schedule_c", ["pdf_schedule_c", "pdf_schedule_c_subawards", "pdf_schedule_c_categories", "pdf_schedule_c_initiatives"]),
    transparency: fam("pdf_transparency", ["pdf_transparency", "pdf_transparency_charts", "pdf_transparency_resolutions"]),
  },
  files: Object.fromEntries(
    [
      "disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta", "pdf_years",
      "pdf_capital_sd", "pdf_capital_sd_orgs", "pdf_capital_sd_totals", "pdf_terms", "pdf_terms_units", "pdf_terms_fsr",
      "pdf_schedule_c", "pdf_schedule_c_subawards", "pdf_schedule_c_categories", "pdf_schedule_c_initiatives",
      "pdf_transparency", "pdf_transparency_charts", "pdf_transparency_resolutions", "pdf_sc_disclosure", "pdf_review",
      "open_data_crosswalk", "open_data_rules", "open_data_coverage", "open_data_datasets",
    ].map((t, i) => [`${t}.parquet`, { bytes: 1000 + i, rows: 1, sha256: String(i).padStart(64, "a") }])
  ),
};

const pdfFamilyFiles = (ts) => ts.filter((t) => t.startsWith("pdf_") && t !== "pdf_years");
const extra = (view, more = {}) => tablesForView({ view, ...more }, MANIFEST).filter((t) => !BASE.includes(t)).sort();

describe("which files each view needs (needs.js)", () => {
  test("the landing page (expense awards) needs the spreadsheet tables and pdf_years only: no PDF family's file", () => {
    for (const view of [undefined, "awards"]) {
      const ts = tablesForView({ view }, MANIFEST);
      expect(ts.sort()).toEqual([...BASE].sort());
      expect(pdfFamilyFiles(ts)).toEqual([]);
      expect(ts.some((t) => t.startsWith("open_data_"))).toBe(false);
    }
  });

  test("each PDF view needs its own family's files (and the review notes), no other family's", () => {
    expect(extra("schedc")).toEqual(["pdf_review", "pdf_sc_disclosure", "pdf_schedule_c", "pdf_schedule_c_categories", "pdf_schedule_c_initiatives", "pdf_schedule_c_subawards"]);
    expect(extra("transparency")).toEqual(["pdf_review", "pdf_transparency", "pdf_transparency_charts", "pdf_transparency_resolutions"]);
    expect(extra("orgs")).toEqual(["pdf_capital_sd", "pdf_capital_sd_orgs", "pdf_capital_sd_totals", "pdf_review"]);
    const od = ["open_data_coverage", "open_data_crosswalk", "open_data_datasets", "open_data_rules"];
    expect(extra("book")).toEqual(["pdf_capital_sd", "pdf_capital_sd_orgs", "pdf_capital_sd_totals", "pdf_review", ...od].sort());
    expect(extra("capital")).toEqual(extra("book"));
    expect(extra("terms")).toEqual(["pdf_review", "pdf_terms", "pdf_terms_fsr", "pdf_terms_units", ...od].sort());
  });

  test("views over the spreadsheets only need nothing more; About the data needs nothing at all", () => {
    for (const view of ["years", "omb", "source"]) expect(extra(view)).toEqual([]);
    expect(tablesForView({ view: "about" }, MANIFEST)).toEqual([]);
  });

  test("a deep link into a filtered landing page or an award loads what it shows", () => {
    expect(extra("awards", { scside: "pdf_only" })).toEqual(extra("schedc"));
    expect(extra("award")).toEqual([...extra("schedc"), "open_data_coverage", "open_data_crosswalk", "open_data_datasets", "open_data_rules"].sort());
    expect(tablesForView({ view: "awards" }, MANIFEST, { extras: true }).sort()).toEqual([...BASE, ...awardsExtras(MANIFEST)].sort());
  });

  test("Compare loads the sources of its section only", () => {
    expect(extra("compare", { csec: "terms" })).toEqual(["pdf_review", "pdf_terms", "pdf_terms_fsr", "pdf_terms_units"]);
    expect(extra("compare", { csec: "line" })).toEqual(extra("orgs"));
    expect(pdfFamilyFiles(extra("compare", { csec: "org" }))).not.toContain("pdf_capital_sd");
    // The totals compare every source, the Schedule C pairing and the T&C count.
    expect(extra("compare")).toEqual(pdfFamilyFiles(Object.keys(MANIFEST.files).map((f) => f.replace(".parquet", ""))).sort());
  });

  test("a file the build did not write is never asked for", () => {
    const noTr = { ...MANIFEST, files: Object.fromEntries(Object.entries(MANIFEST.files).filter(([f]) => !f.startsWith("pdf_transparency"))) };
    expect(tablesForView({ view: "transparency" }, noTr).filter((t) => t.startsWith("pdf_transparency"))).toEqual([]);
  });
});

// ---------------------------------------------------------------- the store

const requested = [];
const created = [];

vi.mock("@duckdb/duckdb-wasm", () => {
  class AsyncDuckDB {
    async instantiate() {}
    async open() {}
    async registerFileBuffer() {}
    async connect() {
      return { query: async (sql) => (created.push(/CREATE TABLE "([^"]+)"/.exec(sql)?.[1]), { toArray: () => [] }) };
    }
  }
  return {
    AsyncDuckDB,
    ConsoleLogger: class {},
    LogLevel: { WARNING: 2 },
    getPlatformFeatures: async () => ({ wasmExceptions: true }),
    selectBundle: async (b) => b.eh,
  };
});

/** The data files fetched, by table name, without the cache-busting query. */
const fetched = () => requested.map((u) => new URL(u).pathname.split("/").at(-1)).filter((f) => f.endsWith(".parquet")).map((f) => f.slice(0, -".parquet".length));

describe("the store fetches only what is asked, once (store.js)", () => {
  let store;
  let firstVisit;
  beforeAll(async () => {
    vi.stubGlobal("window", { location: { href: "https://example.test/explorer/" } });
    vi.stubGlobal("Worker", class {});
    vi.stubGlobal("fetch", async (url) => {
      requested.push(String(url));
      const body = String(url).includes("manifest.json") ? JSON.stringify(MANIFEST) : "PAR1";
      return new Response(body, { status: 200 });
    });
    store = await import("../../src/duckdb/store.js");
    await store.ensureData();
    firstVisit = fetched();
  });
  afterAll(() => vi.unstubAllGlobals());
  beforeEach(() => {
    requested.length = 0;
    created.length = 0;
  });

  test("the first visit fetches the manifest's landing-page files and no PDF family's file", () => {
    expect(firstVisit.sort()).toEqual([...BASE].sort());
    expect(pdfFamilyFiles(firstVisit)).toEqual([]);
    const loaded = Object.entries(store.getSnapshot().tables).filter(([, s]) => s === "ready").map(([t]) => t);
    expect(loaded.sort()).toEqual([...BASE].sort());
    expect(store.getSnapshot().phase).toBe("ready");
  });

  test("two views asking for the same file at once share one download", async () => {
    await Promise.all([store.ensureTables(["pdf_review"]), store.ensureTables(["pdf_review", "pdf_years"])]);
    expect(fetched()).toEqual(["pdf_review"]);
  });

  test("opening each view fetches exactly its files, once; going back fetches nothing", async () => {
    const seen = new Set(Object.keys(store.getSnapshot().tables));
    for (const view of ["schedc", "transparency", "orgs", "book", "terms", "award", "compare"]) {
      requested.length = 0;
      const want = tablesForView({ view }, MANIFEST);
      await store.ensureTables(want);
      const fresh = want.filter((t) => !seen.has(t));
      expect(fetched().sort(), view).toEqual(fresh.sort());
      fresh.forEach((t) => seen.add(t));
    }
    requested.length = 0;
    await store.ensureTables(tablesForView({ view: "schedc" }, MANIFEST));
    expect(fetched()).toEqual([]);
  });

});

describe("the landing page's offer of more columns (Awards.jsx MoreColumns)", () => {
  const offer = async (manifest, props) => {
    const { createElement } = await import("react");
    const { renderToStaticMarkup } = await import("react-dom/server");
    const { MoreColumns } = await import("../../src/views/Awards.jsx");
    return renderToStaticMarkup(createElement(MoreColumns, { manifest, tables: {}, canSc: true, scIn: false, odIn: false, ...props }));
  };
  const noOd = { ...MANIFEST, files: Object.fromEntries(Object.entries(MANIFEST.files).filter(([f]) => !f.startsWith("open_data_"))) };

  test("names both columns when the build has both", async () => {
    const html = await offer(MANIFEST);
    expect(html).toContain("Schedule C");
    expect(html).toContain("NYC Open Data");
    expect(html).toContain("Show these columns");
  });

  test("a build without the Open Data tables never mentions them", async () => {
    const html = await offer(noOd);
    expect(html).toContain("Schedule C");
    expect(html).not.toContain("Open Data");
    expect(html).toContain("Show this column");
    expect(await offer(noOd, { scIn: true })).toBe("");
  });

  test("nothing to offer once the columns are in", async () => {
    expect(await offer(MANIFEST, { scIn: true, odIn: true })).toBe("");
    expect(await offer(MANIFEST, { canSc: false, odIn: true })).toBe("");
  });
});
