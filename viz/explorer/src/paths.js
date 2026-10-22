/**
 * URLs: the app's own data files, and the source spreadsheets each row came from.
 *
 * Adapted from nyc-eo-explorer's src/paths.js (MIT, BetaNYC). DuckDB's HTTP filesystem runs in a
 * Web Worker whose `location` is the worker script, so every URL handed to it must be absolute;
 * and the base is "./" (vite.config.js), so it is resolved against the page at first use, not at
 * import time — the unit tests import this module in Node, where there is no `window`.
 */

// REPO, REPO_URL and the GitHub links come from the MCP's row-link builder (mcp/src/rowlinks.ts),
// imported, not copied, so the explorer and the MCP's answers link a file the same way (#210).
import { REPO, REPO_URL, githubLinks } from "../../../mcp/dist/rowlinks.js";

let originBase = null;
const base = () => (originBase ??= new URL(import.meta.env.BASE_URL, window.location.href));

export const assetUrl = (path) => new URL(path, base()).href;

/** public/ files get no content hash; cache-busting rides on the file's sha256 from the manifest. */
export const dataUrl = (name, version) => assetUrl(`data/${name}`) + (version ? `?v=${encodeURIComponent(version)}` : "");

export { REPO, REPO_URL };

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
export const sourceLinks = (commit, path) => githubLinks(commit, path);

/** A repo document (README, data dictionary) at the build's commit. */
export const docUrl = (commit, path) => `${REPO_URL}/blob/${encodeURIComponent(commit || "main")}/${encodePath(path)}`;
