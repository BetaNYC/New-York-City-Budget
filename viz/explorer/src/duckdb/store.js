/**
 * The DuckDB engine, as a module-scope singleton, plus the data load.
 *
 * Adapted from nyc-eo-explorer's src/duckdb/store.js (MIT, BetaNYC): a module singleton rather
 * than a React effect, so StrictMode's double mount cannot start two engines; only the `eh`
 * bundle (GitHub Pages cannot send the COOP/COEP headers `coi` needs); BigInt cast to double.
 *
 * All six tables are small (about 3.7 MB of Parquet in total), so each file is fetched whole and
 * materialized as a table once, rather than read by HTTP range requests on every query.
 */
import * as duckdb from "@duckdb/duckdb-wasm";
import ehWasm from "@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url";
import ehWorker from "@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url";

import { dataUrl } from "../paths.js";

const BUNDLES = {
  mvp: { mainModule: ehWasm, mainWorker: ehWorker },
  eh: { mainModule: ehWasm, mainWorker: ehWorker },
};

/** The tables every build writes (scripts/build-data.mjs TABLES). The reviewed PDF tables (pdf_*)
 * and the NYC Open Data crosswalk (open_data_*) are read from the manifest's file list, so a table
 * added to mcp/scripts/pdf-families.mjs or open-data.mjs loads without a change here. */
export const TABLES = ["disclosure", "disclosure_years", "capital_council", "capital_sources", "capital_vs_omb", "meta"];
const tablesOf = (manifest) => [...TABLES, ...Object.keys(manifest.files).map((f) => f.replace(/\.parquet$/, "")).filter((t) => t.startsWith("pdf_") || t.startsWith("open_data_"))];

export const PHASES = { IDLE: "idle", MANIFEST: "manifest", ENGINE: "engine", DATA: "data", READY: "ready", ERROR: "error" };

let snapshot = { phase: PHASES.IDLE, progress: 0, error: null, manifest: null };
const listeners = new Set();
let conn = null;
let bootPromise = null;

function emit(patch) {
  snapshot = { ...snapshot, ...patch };
  listeners.forEach((l) => l());
}

export const subscribe = (l) => (listeners.add(l), () => listeners.delete(l));
export const getSnapshot = () => snapshot;

async function fetchOk(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (HTTP ${res.status})`);
  return res;
}

async function boot() {
  emit({ phase: PHASES.MANIFEST });
  const manifest = await (await fetchOk(dataUrl("manifest.json", String(Date.now())))).json();
  for (const t of TABLES) {
    if (!manifest.files?.[`${t}.parquet`]) throw new Error(`manifest.json lists no ${t}.parquet; the data build is incomplete`);
  }
  emit({ manifest });

  const features = await duckdb.getPlatformFeatures();
  if (!features.wasmExceptions) {
    throw new Error("This browser does not support WebAssembly exception handling, which the explorer needs. Try a browser released after mid-2022.");
  }
  emit({ phase: PHASES.ENGINE, progress: 0 });
  const bundle = await duckdb.selectBundle(BUNDLES);
  // A classic worker: duckdb-browser-eh.worker.js is an IIFE script, bundled same-origin.
  const worker = new Worker(bundle.mainWorker);
  const db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING), worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker, (p) => {
    if (p && p.bytesTotal > 0) emit({ progress: p.bytesLoaded / p.bytesTotal });
  });
  await db.open({ path: ":memory:", query: { castBigIntToDouble: true } });
  conn = await db.connect();

  emit({ phase: PHASES.DATA, progress: 0 });
  let done = 0;
  const tables = tablesOf(manifest);
  for (const t of tables) {
    const file = `${t}.parquet`;
    const bytes = new Uint8Array(await (await fetchOk(dataUrl(file, manifest.files[file].sha256.slice(0, 12)))).arrayBuffer());
    await db.registerFileBuffer(file, bytes);
    await conn.query(`CREATE TABLE "${t}" AS SELECT * FROM '${file}'`);
    emit({ progress: ++done / tables.length });
  }
  emit({ phase: PHASES.READY, progress: 1 });
}

export function ensureData() {
  if (!bootPromise) {
    bootPromise = boot().catch((error) => {
      emit({ phase: PHASES.ERROR, error });
      bootPromise = null;
      throw error;
    });
  }
  return bootPromise;
}

/** Run a { sql, params } query; plain JS row objects. */
export async function run({ sql, params = [] }) {
  if (!conn) throw new Error("The database is not ready yet.");
  if (!params.length) return (await conn.query(sql)).toArray().map((r) => r.toJSON());
  const stmt = await conn.prepare(sql);
  try {
    return (await stmt.query(...params)).toArray().map((r) => r.toJSON());
  } finally {
    await stmt.close();
  }
}
