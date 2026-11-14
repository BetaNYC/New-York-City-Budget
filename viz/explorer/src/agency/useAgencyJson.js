import { useEffect, useState } from "react";

import { dataUrl } from "../paths.js";
import { citywidePath } from "./data.js";

/**
 * Fetch the agency view's JSON files (src/agency/data.js), once per visit each. No DuckDB (#299).
 *
 * citywide.json is fetched first and as is (it is about 3 KB, and carries the build stamp); every
 * other file is fetched with that stamp as its cache key, so a new build is never mixed with an
 * old one from the browser's cache.
 */
const loads = new Map();

function fetchJson(path, version) {
  const url = dataUrl(path, version);
  if (!loads.has(url)) {
    const p = fetch(url).then(async (res) => {
      if (!res.ok) throw new Error(`Could not load ${path} (HTTP ${res.status})`);
      return res.json();
    });
    // A failed fetch is forgotten, so the next render tries again.
    p.catch(() => loads.delete(url));
    loads.set(url, p);
  }
  return loads.get(url);
}

/** citywide.json, then the other files: { path: object }. */
async function loadAll(paths) {
  const city = await fetchJson(citywidePath());
  const version = city.generated_at ?? undefined;
  const out = { [citywidePath()]: city };
  await Promise.all(paths.filter((p) => p && p !== citywidePath()).map(async (p) => (out[p] = await fetchJson(p, version))));
  return out;
}

/**
 * The files in `paths` (null entries skipped), always with citywide.json:
 * { loading, error, data: { path: object } | null }, like useQueries: `loading` is true until the
 * files for these paths are in, and an answer for other paths is never shown as this one's.
 */
export function useAgencyJson(paths) {
  const key = paths.filter(Boolean).join("|");
  const [st, setSt] = useState({ key: null, data: null, error: null });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    loadAll(paths)
      .then((data) => live && setSt({ key, data, error: null }))
      .catch((error) => live && setSt({ key, data: null, error }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt]);
  const loading = st.key !== key;
  return { loading, error: loading ? null : st.error, data: loading ? null : st.data, retry: () => setAttempt((n) => n + 1) };
}
