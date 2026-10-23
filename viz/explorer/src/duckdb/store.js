/**
 * The DuckDB engine, as a module-scope singleton, plus the data load.
 *
 * Adapted from nyc-eo-explorer's src/duckdb/store.js (MIT, BetaNYC): a module singleton rather
 * than a React effect, so StrictMode's double mount cannot start two engines; only the `eh`
 * bundle (GitHub Pages cannot send the COOP/COEP headers `coi` needs); BigInt cast to double.
 *
 * Each Parquet file is small enough to fetch whole and materialize as a table once, rather than
 * read by HTTP range requests on every query. Only the landing page's files load at start
 * (needs.js BASE, about 3.7 MB); a PDF family's files load when a view that reads them first opens
 * (ensureTables), once per visit. Every file is fetched with its sha256 as the cache key, so the
 * browser's cache works as before.
 */
import * as duckdb from "@duckdb/duckdb-wasm";
import ehWasm from "@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url";
import ehWorker from "@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url";

import { dataUrl } from "../paths.js";
import { BASE, TABLES } from "./needs.js";

const BUNDLES = {
  mvp: { mainModule: ehWasm, mainWorker: ehWorker },
  eh: { mainModule: ehWasm, mainWorker: ehWorker },
};

export { TABLES };

export const PHASES = { IDLE: "idle", MANIFEST: "manifest", ENGINE: "engine", DATA: "data", READY: "ready", ERROR: "error" };

/**
 * `tables`: what each table is doing: "loading", "ready" or "error" (absent: not asked for yet).
 * `tableError`: the last table load that failed, for a "Try again".
 */
let snapshot = { phase: PHASES.IDLE, progress: 0, error: null, manifest: null, tables: {}, tableError: null };
const listeners = new Set();
let db = null;
let conn = null;
let bootPromise = null;
/** One load per table: table -> promise, kept once it succeeds so a table is never fetched twice. */
const tableLoads = new Map();

function emit(patch) {
  snapshot = { ...snapshot, ...patch };
  listeners.forEach((l) => l());
}

const setTable = (t, state, patch = {}) => emit({ tables: { ...snapshot.tables, [t]: state }, ...patch });

export const subscribe = (l) => (listeners.add(l), () => listeners.delete(l));
export const getSnapshot = () => snapshot;

async function fetchOk(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (HTTP ${res.status})`);
  return res;
}

/** Fetch one Parquet file and materialize it as a table. */
async function loadTable(manifest, t) {
  const file = `${t}.parquet`;
  const entry = manifest.files?.[file];
  if (!entry) throw new Error(`manifest.json lists no ${file}`);
  const bytes = new Uint8Array(await (await fetchOk(dataUrl(file, entry.sha256.slice(0, 12)))).arrayBuffer());
  await db.registerFileBuffer(file, bytes);
  await conn.query(`CREATE TABLE "${t}" AS SELECT * FROM '${file}'`);
}

/**
 * Load these tables if they are not loaded yet; resolves when all are. Tables already loading are
 * waited for, not fetched again. A failed table is forgotten, so asking again retries it.
 */
export function ensureTables(names) {
  return Promise.all(
    names.map((t) => {
      if (!tableLoads.has(t)) {
        setTable(t, "loading");
        const p = (async () => {
          await ensureData();
          await loadTable(snapshot.manifest, t);
        })().then(
          () => setTable(t, "ready"),
          (error) => {
            tableLoads.delete(t);
            setTable(t, "error", { tableError: error });
            throw error;
          }
        );
        tableLoads.set(t, p);
      }
      return tableLoads.get(t);
    })
  );
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
  db = new duckdb.AsyncDuckDB(new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING), worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker, (p) => {
    if (p && p.bytesTotal > 0) emit({ progress: p.bytesLoaded / p.bytesTotal });
  });
  await db.open({ path: ":memory:", query: { castBigIntToDouble: true } });
  conn = await db.connect();

  // The landing page's tables only (needs.js BASE); the rest load with the view that reads them.
  emit({ phase: PHASES.DATA, progress: 0 });
  let done = 0;
  const base = BASE.filter((t) => manifest.files[`${t}.parquet`]);
  for (const t of base) {
    setTable(t, "loading");
    const p = loadTable(manifest, t);
    tableLoads.set(t, p);
    await p;
    setTable(t, "ready", { progress: ++done / base.length });
  }
  emit({ phase: PHASES.READY, progress: 1 });
}

export function ensureData() {
  if (!bootPromise) {
    bootPromise = boot().catch((error) => {
      // Start over cleanly on "Try again": the half-loaded engine and its tables are dropped.
      tableLoads.clear();
      emit({ phase: PHASES.ERROR, error, tables: {} });
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
