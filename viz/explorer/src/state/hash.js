/**
 * URL-hash state, as pure functions, so every view and filter is a link someone can send.
 *
 * Adapted from nyc-eo-explorer's src/state/hash.js (MIT, BetaNYC): no router, a fixed key order
 * so the same state always serializes to the same string (read(write(s)) is stable), unknown keys
 * ignored so an old or hand-edited link degrades rather than breaks, numbers parsed rather than
 * passed through.
 */

export const VIEWS = ["awards", "award", "years", "capital", "capital-row", "omb", "orgs", "terms", "source", "review", "compare", "about"];

export const DEFAULT_STATE = {
  view: "awards",
  // Expense awards (the disclosure)
  fy: null,
  status: "",
  legal_name: "",
  council_member: "",
  agency: "",
  program_name: "",
  source: "",
  ein: "",
  min: null,
  max: null,
  page: 0,
  scside: "", // Schedule C as a second source: "" | matched | disclosure_only | pdf_only
  ay: null, // award detail: fiscal year
  row: null, // award detail: source_row within that year
  // Council capital
  cfy: null,
  afy: null,
  sponsor: "",
  borough: "",
  district: null,
  line: "",
  title: "",
  description: "",
  cmin: null,
  cmax: null,
  cpage: 0,
  seq: null, // capital row detail
  // Council vs OMB
  ofy: null,
  oline: "",
  verdict: "",
  opage: 0,
  // Reviewed PDF data (only in a build made with --include-reviewed, or once a year is closed)
  gfy: null, // organizations (capital Part III): fiscal year
  org: "",
  gline: "",
  gpage: 0,
  tfy: null, // Terms and Conditions
  tagency: "",
  tunit: "",
  tq: "",
  tkind: "",
  tpage: 0,
  rfam: "", // review queue: family, year, check, severity, open/decided, selected review_id
  rfy: null,
  rcheck: "",
  rsev: "",
  rstate: "",
  rid: "",
  cmpa: null, // compare two years: year A (default FY2026), year B (default FY2027), section,
  cmpb: null, //   source, status filter, and the drill-down: source dimension, year, key
  csec: "",
  csrc: "",
  cstat: "",
  cdim: "",
  cfyd: null,
  ckey: "",
  spdf: "", // source viewer: repo path of the PDF, page, row box (x0,top,x1,bottom), label
  spage: null,
  sbox: "",
  slabel: "",
};

const INT_KEYS = ["fy", "page", "ay", "row", "cfy", "afy", "district", "cpage", "seq", "ofy", "opage", "gfy", "gpage", "tfy", "tpage", "spage", "rfy", "cmpa", "cmpb", "cfyd"];
const NUM_KEYS = ["min", "max", "cmin", "cmax"];

export function readHash(hash = typeof window === "undefined" ? "" : window.location.hash) {
  const state = { ...DEFAULT_STATE };
  const raw = String(hash || "").replace(/^#/, "");
  if (!raw) return state;
  let params;
  try {
    params = new URLSearchParams(raw);
  } catch {
    return state;
  }
  for (const [key, value] of params.entries()) {
    if (!(key in DEFAULT_STATE)) continue;
    if (INT_KEYS.includes(key)) {
      const n = Number.parseInt(value, 10);
      state[key] = Number.isFinite(n) ? n : DEFAULT_STATE[key];
    } else if (NUM_KEYS.includes(key)) {
      const n = Number.parseFloat(value);
      state[key] = Number.isFinite(n) ? n : null;
    } else if (key === "view") {
      state.view = VIEWS.includes(value) ? value : DEFAULT_STATE.view;
    } else {
      state[key] = value;
    }
  }
  return state;
}

export function writeHash(state) {
  const params = new URLSearchParams();
  for (const key of Object.keys(DEFAULT_STATE)) {
    const value = state[key];
    if (value === null || value === undefined || value === "" || value === DEFAULT_STATE[key]) continue;
    params.set(key, String(value));
  }
  const s = params.toString();
  return s ? `#${s}` : "";
}

/** How many entries this app has pushed behind the current one (0 on arrival). */
export function historyDepth() {
  const d = window.history.state?.budgetNav;
  return Number.isInteger(d) && d >= 0 ? d : 0;
}

/**
 * "push" for moving to another view or record, "replace" for filter edits. Each pushed entry
 * carries its depth, so "Back" can tell a step the app made from the page the visitor arrived on.
 */
export function pushHash(state, mode = "replace") {
  const hash = writeHash(state);
  const url = hash || window.location.pathname + window.location.search;
  const depth = historyDepth();
  if (mode === "push" && hash !== window.location.hash) {
    window.history.pushState({ budgetNav: depth + 1 }, "", url);
  } else if (hash !== window.location.hash) {
    window.history.replaceState({ budgetNav: depth }, "", url);
  }
}

// ---------------------------------------------------------------- state -> query filters

export const disclosureFilters = (s) => ({
  fiscal_year: s.fy,
  status: s.status,
  legal_name: s.legal_name,
  council_member: s.council_member,
  agency: s.agency,
  program_name: s.program_name,
  source: s.source,
  ein: s.ein,
  min_amount: s.min,
  max_amount: s.max,
  sc_side: s.scside,
});

export const capitalFilters = (s) => ({
  fiscal_year: s.cfy,
  amount_fy: s.afy,
  sponsor: s.sponsor,
  borough: s.borough,
  council_district: s.district,
  budget_line: s.line,
  title: s.title,
  description: s.description,
  min_amount: s.cmin,
  max_amount: s.cmax,
});

export const ombFilters = (s) => ({ report_year: s.ofy, budget_line: s.oline, verdict: s.verdict });

/** The keys of each view's filters, for "clear filters" and for resetting the page on a change. */
export const FILTER_KEYS = {
  awards: ["fy", "status", "legal_name", "council_member", "agency", "program_name", "source", "ein", "min", "max", "scside"],
  capital: ["cfy", "afy", "sponsor", "borough", "district", "line", "title", "description", "cmin", "cmax"],
  omb: ["ofy", "oline", "verdict"],
  orgs: ["gfy", "org", "gline"],
  terms: ["tfy", "tagency", "tunit", "tq", "tkind"],
};
export const PAGE_KEY = { awards: "page", capital: "cpage", omb: "opage", orgs: "gpage", terms: "tpage" };
