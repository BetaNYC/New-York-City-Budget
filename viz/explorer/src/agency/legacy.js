/**
 * Old /agencies/ links (#270, #286). The old Backbone app (viz/agencies/js/app.js) had three
 * routes, all in the URL fragment, which a server can't see, so only script can forward them:
 *
 *   #(?year=Y)                                          all agencies, year Y
 *   #fund-detail/<agency-slug>(/<unit-slug>)?year=Y     an agency, or one of its units
 *   #control-officer-detail/<agency-slug>(/...)?year=Y  removed in #266; same as fund-detail
 *
 * The forwarding page (/agencies/, #288) turns one into an explorer hash with legacyToExplorerHash;
 * the explorer then resolves the slug path against every agency and unit name ever published
 * (resolveLegacy), and replaces `legacy` with the agency and unit numbers.
 *
 * Pure functions: no DOM, no data loading.
 */
import { DEFAULT_STATE, writeHash } from "../state/hash.js";

/** The old app's slug rule (BudgetHelpers.convertToSlug), exactly. */
export function agencySlug(text) {
  if (text == undefined) return "";
  return String(text)
    .toLowerCase()
    .replace(/[^\w ]+/g, "")
    .replace(/ +/g, "-");
}

const ROUTE = /^(?:fund-detail|control-officer-detail)\/([^?]+)/;

/** An old fragment ("#fund-detail/police-department?year=2025") as an explorer hash. */
export function legacyToExplorerHash(hash) {
  const raw = String(hash ?? "").replace(/^#/, "");
  const q = raw.indexOf("?");
  const path = q === -1 ? raw : raw.slice(0, q);
  const query = q === -1 ? "" : raw.slice(q + 1);
  const year = Number.parseInt(new URLSearchParams(query).get("year") ?? "", 10);
  const m = ROUTE.exec(path);
  let legacy = "";
  if (m) {
    legacy = m[1]
      .split("/")
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => {
        try {
          return decodeURIComponent(s);
        } catch {
          return s;
        }
      })
      .join("/");
  }
  return writeHash({ ...DEFAULT_STATE, view: "agencies", abfy: Number.isFinite(year) ? year : null, legacy }) || "#view=agencies";
}

/**
 * An old slug path ("police-department/operations") -> { abag, abunit, candidates }, or null when
 * no agency matches. An agency slug matches any name the agency has had. A unit slug shared by
 * two or more units of that agency gives abunit "" and every one in `candidates`, so the page asks
 * instead of guessing; an unknown unit gives abunit "" and no candidates (the agency is shown).
 *
 * @param {string} legacy
 * @param {Array<{agency_number: string, agency_name: string, unit_number: string, unit_name: string}>} names
 */
export function resolveLegacy(legacy, names) {
  const [agencyPart = "", unitPart = ""] = String(legacy ?? "").split("/");
  if (!agencyPart) return null;
  const agencies = [...new Set(names.filter((n) => agencySlug(n.agency_name) === agencyPart).map((n) => n.agency_number))];
  if (agencies.length !== 1) return null;
  const abag = agencies[0];
  if (!unitPart) return { abag, abunit: "", candidates: [] };
  const units = new Map();
  for (const n of names) {
    if (n.agency_number !== abag || agencySlug(n.unit_name) !== unitPart) continue;
    if (!units.has(n.unit_number)) units.set(n.unit_number, { unit_number: n.unit_number, unit_name: n.unit_name });
  }
  const candidates = [...units.values()].sort((a, b) => a.unit_number.localeCompare(b.unit_number));
  if (candidates.length === 1) return { abag, abunit: candidates[0].unit_number, candidates: [] };
  return { abag, abunit: "", candidates };
}
