/**
 * How current each source is, for about_data (#329): the `freshness` hooks DATA-SOURCES.json
 * names, by key. Every date is read at run time from the index this package ships (the day
 * BetaNYC downloaded each copy) or from the PDF tables download on this machine. None is typed
 * by hand. A hook that throws is reported by about_data as "could not read it".
 */
import { FRESHNESS_NOT_FETCHED, type FreshnessHook } from "./betanyc-tools.js";
import { getDb, getMeta } from "./db.js";
import { openPdfTables } from "./pdfdata.js";

/** The one value a query returns, or null when it is empty. */
function one(sql: string, ...params: unknown[]): string | null {
  const r = getDb().prepare(sql).get(...params) as { d: string | null } | undefined;
  return r?.d ? String(r.d) : null;
}

const planRetrieved = (id: string) => () => one("SELECT retrieved AS d FROM capital_plan_sources WHERE dataset_id = ?", id);

export const FRESHNESS_HOOKS: Record<string, FreshnessHook> = {
  // The Council's workbooks from its Research & Data site.
  expense_disclosure_retrieved: () => one("SELECT MAX(retrieved) AS d FROM disclosure_years WHERE loaded = 1 AND source_kind = 'council_rnd'"),
  capital_workbook_retrieved: () =>
    one("SELECT MAX(retrieved) AS d FROM capital_sources WHERE source_kind = 'council_workbook' AND COALESCE(wayback_timestamp, '') = ''"),
  // The Internet Archive copies: the disclosure years loaded from them, and the capital workbooks.
  wayback_retrieved: () =>
    one(`SELECT MAX(d) AS d FROM (
           SELECT retrieved AS d FROM disclosure_years WHERE loaded = 1 AND source_kind = 'internet_archive'
           UNION ALL SELECT retrieved FROM capital_sources WHERE COALESCE(wayback_timestamp, '') <> '')`),
  t474_retrieved: () => one("SELECT MAX(retrieved) AS d FROM capital_sources WHERE source_kind = 'open_data_t474'"),
  // The FY2018 book is a PDF read in this repo; the index records no download date for it.
  fy2018_book: () => one("SELECT retrieved AS d FROM capital_sources WHERE report_year = 2018"),
  agency_budget_retrieved: () => {
    const raw = getMeta("agency_budget");
    return raw ? (JSON.parse(raw) as { retrieved_at?: string }).retrieved_at ?? null : null;
  },
  omb_capital_budget_retrieved: () => one("SELECT snapshot_date AS d FROM open_data_datasets WHERE dataset_id = '46m8-77gv'"),
  capital_plan_retrieved: planRetrieved("2cmn-uidm"),
  cpdb_commitments_retrieved: planRetrieved("djxg-kcfi"),
  cpdb_projects_retrieved: planRetrieved("fi59-268w"),
  // When the Legistar index the member roster was extracted from was built.
  member_roster: () => {
    const raw = getMeta("member_roster");
    return raw ? (JSON.parse(raw) as { db_last_indexed_at?: string }).db_last_indexed_at ?? null : null;
  },
  // The optional download: when the installed tables were built; not fetched until installed.
  pdf_tables: () => {
    const { tables, problem } = openPdfTables();
    if (tables) return tables.meta.built_at || null;
    return problem ? null : FRESHNESS_NOT_FETCHED;
  },
};
