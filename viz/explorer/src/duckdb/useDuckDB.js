import { useEffect, useState, useSyncExternalStore } from "react";

import { getSnapshot, run, subscribe } from "./store.js";

/** Engine and data status (nyc-eo-explorer's hook, MIT). */
export function useDuckDB() {
  return useSyncExternalStore(subscribe, getSnapshot);
}

/**
 * Run queries whenever `key` changes and the data is ready. `make` returns an object of
 * { name: {sql, params} } (or null for nothing to run); the result is
 * { loading, error, data: { name: rows } }. `loading` is true whenever the data on hand belongs to
 * another key, including the render between a key change and the effect that starts the new
 * queries, so a view never shows an old answer as if it were the new one. `data` keeps the last
 * answer meanwhile, for a dimmed "Updating…" display. A stale answer is dropped.
 */
export function useQueries(ready, key, make) {
  const [st, setSt] = useState({ key: null, data: null, error: null });
  useEffect(() => {
    if (!ready) return undefined;
    let live = true;
    const queries = make();
    if (!queries) {
      setSt({ key, data: null, error: null });
      return undefined;
    }
    // One after another: they share one connection, and the worker serializes them anyway.
    (async () => {
      const data = {};
      for (const [name, q] of Object.entries(queries)) data[name] = await run(q);
      return data;
    })()
      .then((data) => live && setSt({ key, data, error: null }))
      .catch((error) => live && setSt({ key, data: null, error }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, key]);
  const loading = st.key !== key;
  return { loading, error: loading ? null : st.error, data: st.data };
}
