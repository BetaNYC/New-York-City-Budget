/**
 * Which data files each view needs, so a first visit downloads only the landing page's (about
 * 3.7 MB) and each PDF family's Parquet loads when a view that reads it first opens. Pure
 * functions of the URL state and manifest.json, shared by the app (App.jsx) and the tests
 * (test/unit/needs.test.js, test/lazy-load.test.mjs).
 *
 * A table is named here once, in a group; a view's list is the union of its groups. A table the
 * build did not write (a family with no reviewed year, the review build's extra tables) is dropped,
 * so a view never waits for a file that does not exist.
 */
import { DIM_SOURCES, SOURCES } from "../compare/queries.js";
import { AWARDS_FILTERS, CAPITAL_FILTERS } from "../state/hash.js";

/** The spreadsheet tables, written by every build (scripts/build-data.mjs TABLES). */
export const TABLES = ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta"];

/**
 * Loaded on every visit: the spreadsheet tables, and pdf_years (8 KB), the list of PDF family-years
 * the tabs and every view's year lists are built from. Not a family's rows.
 */
export const BASE = [...TABLES, "pdf_years"];

/** Review notes behind every PDF row's flag badge (src/components/pdf.jsx), for any family, and the
 * Council questions they join to (src/query/pdf.js). */
const REVIEW_NOTES = ["pdf_review", "pdf_council_questions"];

/** The NYC Open Data crosswalk (open_data_*), from the manifest's file list. */
export const openDataTables = (manifest) => fileTables(manifest).filter((t) => t.startsWith("open_data_"));

/**
 * One PDF family's tables (manifest.pdf_families[family].tables), plus its review notes. Schedule
 * C also brings pdf_sc_disclosure, its pairing with the spreadsheet rows, which every Schedule C
 * screen shows; the capital book brings pdf_capital_sd_series, the Part-II-only ID series its
 * question label reads (src/query/pdf.js part2SeriesQuery).
 */
export function familyTables(manifest, family) {
  const fam = manifest?.pdf_families?.[family];
  if (!fam) return [];
  const extra = { schedule_c: ["pdf_sc_disclosure"], capital_sd: ["pdf_capital_sd_series"] }[family] ?? [];
  return [...fam.tables, ...extra, ...REVIEW_NOTES];
}

/** The Schedule C pairing and the Open Data badges the expense list can add (Awards.jsx). */
export const awardsExtras = (manifest) => available(manifest, [...familyTables(manifest, "schedule_c"), ...openDataTables(manifest)]);

/** Every table the build wrote. */
const fileTables = (manifest) => Object.keys(manifest?.files ?? {}).filter((f) => f.endsWith(".parquet")).map((f) => f.slice(0, -".parquet".length));

/** The tables in `names` the build wrote, once each, in order. */
function available(manifest, names) {
  const have = new Set(fileTables(manifest));
  return [...new Set(names)].filter((t) => have.has(t));
}

/** The comparison's sources for its section (Compare.jsx SECTIONS) and drill-down. */
function compareFamilies(state) {
  const sec = state.csec || "totals";
  const ids = sec === "totals" ? Object.keys(SOURCES) : sec === "terms" ? ["terms"] : DIM_SOURCES[sec] ?? Object.keys(SOURCES);
  const fams = ids.map((id) => SOURCES[id]?.family ?? (id === "terms" ? "terms" : null));
  if (state.ckey && state.csrc) fams.push(SOURCES[state.csrc]?.family ?? null);
  // The totals also show Schedule C beside the disclosure (pdf_sc_disclosure) and the T&C count.
  if (sec === "totals") fams.push("terms");
  return fams.filter(Boolean);
}

/**
 * The tables the view in `state` reads, beyond what is already loaded. `extras` adds the Awards
 * list's optional columns (awardsExtras), once someone has asked for them.
 */
export function tablesForView(state, manifest, { extras = false } = {}) {
  const fam = (f) => familyTables(manifest, f);
  const od = openDataTables(manifest);
  let need;
  switch (state.view) {
    case "about":
      return [];
    case "agencies":
      // City agency budgets reads JSON, not DuckDB (#299; src/agency/data.js): no table at all.
      return [];
    case "award":
      need = [...fam("schedule_c"), ...od];
      break;
    case "capital":
    case "capital-row":
    case "book":
      need = [...fam("capital_sd"), ...od];
      break;
    case "orgs":
      need = fam("capital_sd");
      break;
    case "terms":
      need = [...fam("terms"), ...od];
      break;
    case "schedc":
      need = fam("schedule_c");
      break;
    case "transparency":
      need = fam("transparency");
      break;
    case "compare":
      need = compareFamilies(state).flatMap(fam);
      break;
    case "review":
      // The review screen reads every family and the suggestions, in a local review build only.
      // A public build has no review screen, so it reads nothing (#301).
      if (!manifest?.review_screen) return [];
      need = fileTables(manifest);
      break;
    case "years":
    case "omb":
    case "source":
      need = [];
      break;
    default:
      // The expense list (the landing page): its Schedule C filter needs the pairing; the optional
      // Schedule C and Open Data columns once asked for.
      need = [...(state.scside ? fam("schedule_c") : []), ...(extras ? awardsExtras(manifest) : [])];
  }
  return available(manifest, [...BASE, ...need]);
}

/**
 * Whether a view starts the query engine (DuckDB-WASM, about 8.6 MB over the wire and 34 MB
 * decoded, before any data; #301). City agency budgets reads its own JSON (#299), About the data
 * reads only manifest.json, and Years and Council vs OMB read the Council JSON files. Review needs it only in a review build: on the public site it
 * just says there is no queue. null: the answer depends on the manifest, which is not in yet.
 */
export function needsEngine(view, manifest, state = {}) {
  // Years and Council vs OMB read the Council JSON files (data/council/; #301), and so does one
  // award: its Schedule C and Open Data panels load the engine when asked for.
  if (view === "agencies" || view === "about" || view === "years" || view === "omb" || view === "award" || view === "capital-row") return false;
  if (view === "review") return manifest ? Boolean(manifest.review_screen) : null;
  if (view === undefined || view === "awards") {
    // The expense list: one fiscal year (any filter within it) reads that year's file, and the
    // unfiltered first page over all years reads awards/index.json. The Schedule C side, and any
    // other filter over all years, need the engine (state/hash.js awardsYear).
    if (state.scside) return true;
    const filtered = AWARDS_FILTERS.some((k) => state[k] !== null && state[k] !== undefined && state[k] !== "");
    if (state.fy > 0) return false;
    if (state.fy === 0) return filtered || (state.page ?? 0) > 0;
    return filtered;
  }
  if (view === "capital") {
    // The capital list, the same way: one report year reads its file (capital/fyYYYY.json).
    const filtered = CAPITAL_FILTERS.some((k) => state[k] !== null && state[k] !== undefined && state[k] !== "");
    if (state.cfy > 0) return false;
    return filtered || state.cfy === 0;
  }
  return true;
}

/** The download, in bytes, of a list of tables (manifest.files sizes). */
export const bytesOf = (manifest, tables) => tables.reduce((t, name) => t + (manifest?.files?.[`${name}.parquet`]?.bytes ?? 0), 0);

/** Bytes as "about N MB" (at least 1, so a small file never reads as nothing to download). */
export const aboutMb = (bytes) => `about ${Math.max(1, Math.round(bytes / 1e6))} MB`;
