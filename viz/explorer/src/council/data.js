/**
 * The Council explorer's JSON reader (#301): fetches data/council/ files (scripts/council-json.mjs
 * writes them, src/council/paths.js names them) and answers the queries that carry a `json` form,
 * so a fast view needs no query engine.
 *
 * A query object is { sql, params, json? }. `json` is { files: [path, ...], run(files) -> rows },
 * where `files` are the parsed files in the same order. run() must return exactly the rows the SQL
 * returns; test/council-parity.test.mjs runs both on the same filters and compares them.
 *
 * Each file is fetched once per visit, with its sha256 from manifest.json as the cache key, as the
 * Parquet files are.
 */
import { dataUrl } from "../paths.js";
import { getSnapshot } from "../duckdb/store.js";

const loads = new Map();

async function fetchJson(path) {
  const entry = getSnapshot().manifest?.council_json?.files?.[path];
  if (!entry) throw new Error(`manifest.json lists no ${path}`);
  const res = await fetch(dataUrl(path, entry.sha256.slice(0, 12)));
  if (!res.ok) throw new Error(`Could not load ${path} (HTTP ${res.status})`);
  return res.json();
}

/** One Council JSON file, parsed; fetched once per visit. A failed fetch is forgotten, so a retry fetches again. */
export function councilFile(path) {
  if (!loads.has(path)) {
    loads.set(
      path,
      fetchJson(path).catch((error) => {
        loads.delete(path);
        throw error;
      })
    );
  }
  return loads.get(path);
}

/** Whether the build wrote this file (a year that is not loaded has none). */
export const hasCouncilFile = (path) => Boolean(getSnapshot().manifest?.council_json?.files?.[path]);

/**
 * Run a query's JSON form. A file listed in `optional` that the build did not write is passed as
 * null (one award in a year that is not loaded: no such row).
 */
export async function runJson(q) {
  const optional = new Set(q.json.optional ?? []);
  const files = await Promise.all(q.json.files.map((p) => (optional.has(p) && !hasCouncilFile(p) ? null : councilFile(p))));
  return q.json.run(files);
}
