/**
 * URLs: the app's own data files, and the source spreadsheets each row came from.
 *
 * Adapted from nyc-eo-explorer's src/paths.js (MIT, BetaNYC). DuckDB's HTTP filesystem runs in a
 * Web Worker whose `location` is the worker script, so every URL handed to it must be absolute;
 * and the base is "./" (vite.config.js), so it is resolved against the page at first use, not at
 * import time — the unit tests import this module in Node, where there is no `window`.
 */
let originBase = null;
const base = () => (originBase ??= new URL(import.meta.env.BASE_URL, window.location.href));

export const assetUrl = (path) => new URL(path, base()).href;

/** public/ files get no content hash; cache-busting rides on the file's sha256 from the manifest. */
export const dataUrl = (name, version) => assetUrl(`data/${name}`) + (version ? `?v=${encodeURIComponent(version)}` : "");

export const REPO = "BetaNYC/New-York-City-Budget";
export const REPO_URL = `https://github.com/${REPO}`;

const encodePath = (p) => String(p).split("/").map(encodeURIComponent).join("/");

/**
 * The committed source file a row came from, pinned to the commit the site was built from.
 *
 * The spreadsheets are not copied into the site: they are read from GitHub, at the exact commit
 * the data build ran on (manifest.json `source_commit`), so the file a row cites is the file
 * that produced it, even after the repository moves on. Two links: `raw` downloads the file
 * (raw.githubusercontent.com; no file in source/ is in git LFS), `page` is GitHub's page for it,
 * with its history. Neither is fetched by the app, so cross-origin rules do not apply.
 */
export function sourceLinks(commit, path) {
  if (!commit || !path) return null;
  return {
    raw: `https://raw.githubusercontent.com/${REPO}/${encodeURIComponent(commit)}/${encodePath(path)}`,
    page: `${REPO_URL}/blob/${encodeURIComponent(commit)}/${encodePath(path)}`,
  };
}

/** A repo document (README, data dictionary) at the build's commit. */
export const docUrl = (commit, path) => `${REPO_URL}/blob/${encodeURIComponent(commit || "main")}/${encodePath(path)}`;
