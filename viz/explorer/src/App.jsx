import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useDuckDB, useQueries } from "./duckdb/useDuckDB.js";
import { PHASES, ensureData } from "./duckdb/store.js";
import { FILTER_KEYS, PAGE_KEY, historyDepth, pushHash, readHash, writeHash } from "./state/hash.js";
import { HashLink, Notice } from "./components/ui.jsx";
import { ReviewScreenContext } from "./components/pdf.jsx";
import About from "./views/About.jsx";
import Award from "./views/Award.jsx";
import Awards from "./views/Awards.jsx";
import Capital, { CapitalRow } from "./views/Capital.jsx";
import Compare from "./views/Compare.jsx";
import Omb from "./views/Omb.jsx";
import Orgs from "./views/Orgs.jsx";
import Source from "./views/Source.jsx";
import Terms from "./views/Terms.jsx";
import ScheduleCSearch from "./views/ScheduleCSearch.jsx";
import Transparency from "./views/Transparency.jsx";
import Book from "./views/Book.jsx";
import { CLOSED_LABEL, pdfYearsQuery, REVIEWED_LABEL } from "./query/pdf.js";
import Years from "./views/Years.jsx";

// The review screen is only in a review build: load its code only when it is opened.
const Review = lazy(() => import("./views/Review.jsx"));

const TABS = [
  ["awards", "Expense awards"],
  ["years", "Years"],
  ["compare", "Compare years"],
  ["capital", "Capital"],
  ["omb", "Capital vs OMB"],
  // Shown only when a PDF family is loaded (data/pdf_years.csv: reviewed or closed; #190).
  ["schedc", "Schedule C", "schedule_c"],
  ["transparency", "Transparency resolutions", "transparency"],
  ["book", "Capital book", "capital_sd"],
  ["orgs", "Organizations", "capital_sd"],
  ["terms", "Terms & Conditions", "terms"],
  // The review screen: only in a local review build (npm run data -- --include-reviewed), never public.
  ["review", "Review", "review"],
  ["about", "About the data"],
];
const PARENT = { award: "awards", "capital-row": "capital" };

export default function App() {
  const db = useDuckDB();
  const [state, setState] = useState(() => readHash());
  const current = useRef(state);
  current.current = state;

  useEffect(() => {
    ensureData().catch(() => {});
    const sync = () => setState(readHash());
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, []);

  /** Edit filters: a changed filter returns its view to page 1. `push` makes a history entry. */
  const set = useCallback((patch, opts = {}) => {
    const prev = current.current;
    const next = { ...prev, ...patch };
    if (!opts.keepPage) {
      for (const [view, keys] of Object.entries(FILTER_KEYS)) {
        if (keys.some((k) => k in patch && patch[k] !== prev[k])) next[PAGE_KEY[view]] = 0;
      }
    }
    pushHash(next, opts.push ? "push" : "replace");
    current.current = next;
    setState(next);
  }, []);
  const go = useCallback((patch) => set(patch, { push: true }), [set]);
  const back = useCallback(() => {
    if (historyDepth() > 0) window.history.back();
    else go({ view: PARENT[state.view] ?? "awards" });
  }, [go, state.view]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [state.view]);

  const ready = db.phase === PHASES.READY;
  const tab = PARENT[state.view] ?? state.view;

  return (
    <>
      <header className="site">
        <div className="wrap">
          <p className="kicker">
            <a href="../">BetaNYC · New York City Budget</a>
          </p>
          <h1>NYC Council budget explorer</h1>
          <nav className="tabs" aria-label="Views">
            {TABS.filter(([, , fam]) => !fam || (fam === "review" ? Boolean(db.manifest?.review_screen) && (db.manifest?.files?.["pdf_review.parquet"]?.rows ?? 0) > 0 : (db.manifest?.files?.[`${db.manifest?.pdf_families?.[fam]?.main}.parquet`]?.rows ?? 0) > 0)).map(([v, label]) => (
              <HashLink key={v} href={writeHash({ ...state, view: v })} onGo={() => go({ view: v })} className={tab === v ? "active" : undefined} current={tab === v}>
                {label}
              </HashLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="wrap">
        {db.manifest?.review_screen ? (
          <Notice tone="warn">
            <strong>Local review build.</strong> This build has the Review tab, where a person decides the flagged rows; the public site does not. Rows marked{" "}
            <span className="reviewed">{REVIEWED_LABEL}</span> come from PDFs re-read for the PDF review (<a href="https://github.com/BetaNYC/New-York-City-Budget/issues/101">GitHub epic #101</a>; each fiscal year has its own issue,
            e.g. #102 for FY2027, #103 for FY2026): every printed total was checked and the doubts are listed, but a person has not signed them off.
          </Notice>
        ) : null}
        {db.phase === PHASES.ERROR ? (
          <Notice tone="error">
            The data could not be loaded: {String(db.error?.message ?? db.error)}.{" "}
            <button type="button" className="linkish" onClick={() => ensureData().catch(() => {})}>
              Try again
            </button>
          </Notice>
        ) : !ready ? (
          state.view === "about" ? (
            <About manifest={db.manifest} />
          ) : (
            <Loading phase={db.phase} progress={db.progress} manifest={db.manifest} />
          )
        ) : (
          <ReviewScreenContext.Provider value={Boolean(db.manifest?.review_screen)}>
            <Ready state={state} set={set} go={go} back={back} manifest={db.manifest} />
          </ReviewScreenContext.Provider>
        )}
      </main>
      <footer className="site">
        <div className="wrap">
          <p>
            Built by <a href="https://beta.nyc">BetaNYC</a> from the NYC Council's own spreadsheets and NYC Open Data, the same data as the{" "}
            <a href="https://www.npmjs.com/package/@betanyc/nyc-budget-mcp">@betanyc/nyc-budget-mcp</a> server
            {db.manifest?.include_reviewed ? (
              <>
                , plus the tables read from the Council's budget PDFs and checked against every printed total (each row says "{REVIEWED_LABEL}" or "{CLOSED_LABEL}")
              </>
            ) : null}
            .{" "}
            {db.manifest ? (
              <>
                Data build of {db.manifest.generated_at.slice(0, 10)} from commit{" "}
                <a href={`https://github.com/${db.manifest.source_repo}/commit/${db.manifest.source_commit}`}>
                  <code>{db.manifest.source_commit.slice(0, 7)}</code>
                </a>
                .{" "}
              </>
            ) : null}
            Something wrong? <a href="https://github.com/BetaNYC/New-York-City-Budget/issues">Open an issue</a>.
          </p>
        </div>
      </footer>
    </>
  );
}

/** The data download, in whole MB, from the manifest's file sizes. */
export const dataMb = (manifest) => Math.max(1, Math.round(Object.values(manifest?.files ?? {}).reduce((t, f) => t + (f.bytes ?? 0), 0) / 1e6));

function Loading({ phase, progress, manifest }) {
  const what = { idle: "Starting", manifest: "Reading the data manifest", engine: "Loading the query engine", data: "Loading the data" }[phase] ?? "Loading";
  return (
    <div className="loading" role="status" aria-live="polite">
      <p>
        {what}… {phase === "engine" || phase === "data" ? `${Math.round(progress * 100)}%` : ""}
      </p>
      <progress value={progress} max={1} />
      <p className="muted small">The explorer runs in your browser: it downloads the query engine (about 33 MB, cached after the first visit) and about {dataMb(manifest)} MB of data.</p>
    </div>
  );
}

/** Lookups every view needs, read once the data is in. */
function Ready({ state, set, go, back, manifest }) {
  const q = useQueries(true, "lookups", () => ({
    years: { sql: "SELECT fiscal_year, loaded, early_snapshot, note FROM disclosure_years ORDER BY fiscal_year DESC", params: [] },
    capYears: { sql: "SELECT report_year FROM capital_sources ORDER BY report_year", params: [] },
    ombYears: { sql: "SELECT DISTINCT report_year FROM capital_vs_omb ORDER BY report_year", params: [] },
    pdfYears: pdfYearsQuery(),
  }));
  const lookups = useMemo(() => {
    if (!q.data) return null;
    return {
      years: q.data.years.map((y) => ({ ...y, fiscal_year: Number(y.fiscal_year), loaded: Boolean(Number(y.loaded)), early_snapshot: Boolean(Number(y.early_snapshot)) })),
      capitalYears: q.data.capYears.map((r) => Number(r.report_year)),
      ombYears: q.data.ombYears.map((r) => Number(r.report_year)),
      pdfYears: q.data.pdfYears.map((y) => ({ ...y, fiscal_year: Number(y.fiscal_year) })),
    };
  }, [q.data]);
  if (q.error) return <Notice tone="error">{String(q.error.message ?? q.error)}</Notice>;
  if (!lookups) return <p className="muted">Loading…</p>;
  const props = { state, set, go, back, manifest, ...lookups };
  switch (state.view) {
    case "award":
      return <Award {...props} />;
    case "years":
      return <Years {...props} />;
    case "capital":
      return <Capital {...props} />;
    case "capital-row":
      return <CapitalRow {...props} />;
    case "omb":
      return <Omb {...props} />;
    case "orgs":
      return <Orgs {...props} />;
    case "terms":
      return <Terms {...props} />;
    case "schedc":
      return <ScheduleCSearch {...props} />;
    case "transparency":
      return <Transparency {...props} />;
    case "book":
      return <Book {...props} />;
    case "source":
      return <Source {...props} />;
    case "review":
      return manifest.review_screen ? (
        <Suspense fallback={<p className="muted">Loading the review screen…</p>}>
          <Review {...props} />
        </Suspense>
      ) : (
        <Notice>
          No review queue in this build. It appears in a local build made with <code>npm run data -- --include-reviewed</code>.
        </Notice>
      );
    case "compare":
      return <Compare {...props} />;
    case "about":
      return <About manifest={manifest} />;
    default:
      return <Awards {...props} />;
  }
}
