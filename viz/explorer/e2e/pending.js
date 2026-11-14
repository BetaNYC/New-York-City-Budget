/**
 * Whether each part of #270 exists yet, so the specs run the day it lands and are skipped, with
 * the issue that builds it, until then. No spec here edits the app or its data.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
export const APP = resolve(HERE, "..");
export const REPO = resolve(APP, "..", "..");

/**
 * The assembled site, served under /New-York-City-Budget/ like GitHub Pages, so a link that starts
 * with "/" (and leaves the site) fails here too. Built by `npm run e2e:site`.
 */
export const SITE_ROOT = join(HERE, ".site");
export const SITE = join(SITE_ROOT, "New-York-City-Budget");
export const PORT = Number(process.env.E2E_PORT ?? 4327);
export const BASE_URL = `http://127.0.0.1:${PORT}/New-York-City-Budget/`;

const read = (p) => (existsSync(p) ? readFileSync(p, "utf8") : "");
const siteBuilt = existsSync(join(SITE, "explorer", "index.html"));
const viewInSource = /export const VIEWS = \[[^\]]*"agencies"/.test(read(join(APP, "src", "state", "hash.js")));
const dataInSite = Boolean(JSON.parse(read(join(SITE, "explorer", "data", "manifest.json")) || "{}").files?.["agency_budget.parquet"]);

/** Skip reason for the Agency budgets view's specs, or false. */
export const VIEW_PENDING = !viewInSource
  ? "PENDING #286: the explorer has no Agency budgets view yet (src/state/hash.js VIEWS)"
  : !siteBuilt
    ? "e2e site not built: run `npm run e2e:site` first"
    : !dataInSite
      ? "PENDING #284: the built site has no agency_budget.parquet"
      : false;

/** Skip reason for the retirement specs (the old Backbone app forwards to the explorer), or false. */
export const RETIRED_PENDING = /backbone/i.test(read(join(REPO, "viz", "agencies", "index.html")))
  ? "PENDING #288: viz/agencies/index.html is still the Backbone app"
  : !siteBuilt
    ? "e2e site not built: run `npm run e2e:site` first"
    : false;

export const SITE_BUILT = siteBuilt;
