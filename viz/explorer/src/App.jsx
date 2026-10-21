import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useDuckDB, useQueries } from "./duckdb/useDuckDB.js";
import { PHASES, ensureData } from "./duckdb/store.js";
import { FILTER_KEYS, PAGE_KEY, historyDepth, pushHash, readHash, writeHash } from "./state/hash.js";
import { HashLink, Notice } from "./components/ui.jsx";
import About from "./views/About.jsx";
import Award from "./views/Award.jsx";
import Awards from "./views/Awards.jsx";
import Capital, { CapitalRow } from "./views/Capital.jsx";
import Omb from "./views/Omb.jsx";
import Orgs from "./views/Orgs.jsx";
import Review from "./views/Review.jsx";
import Source from "./views/Source.jsx";
import Terms from "./views/Terms.jsx";
import { pdfYearsQuery, REVIEWED_LABEL } from "./query/pdf.js";
import Years from "./views/Years.jsx";

const TABS = [
  ["awards", "Expense awards"],
  ["years", "Years"],
  ["capital", "Capital"],
  ["omb", "Capital vs OMB"],
  // Shown only when a PDF family is loaded (data/pdf_years.csv; closed, or reviewed in a
  // --include-reviewed build).
  ["orgs", "Organizations", "capital_sd"],
  ["terms", "Terms & Conditions", "terms"],
  // The review screen: only when a family is loaded with status = reviewed (a --include-reviewed build).
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
            {TABS.filter(([, , fam]) => !fam || (fam === "review" ? Boolean(db.manifest?.include_reviewed) && (db.manifest?.files?.["pdf_review.parquet"]?.rows ?? 0) > 0 : (db.manifest?.files?.[`${db.manifest?.pdf_families?.[fam]?.main}.parquet`]?.rows ?? 0) > 0)).map(([v, label]) => (
              <HashLink key={v} href={writeHash({ ...state, view: v })} onGo={() => go({ view: v })} className={tab === v ? "active" : undefined}>
                {label}
              </HashLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="wrap">
        {db.manifest?.include_reviewed ? (
          <Notice tone="warn">
            <strong>Demo build with PDF data still in review.</strong> Rows marked <span className="reviewed">{REVIEWED_LABEL}</span> come from PDFs re-read for
            GitHub issue #102: every printed total was checked and the doubts are listed, but a person has not signed them off. The public site does not show them.
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
            <Loading phase={db.phase} progress={db.progress} />
          )
        ) : (
          <Ready state={state} set={set} go={go} back={back} manifest={db.manifest} />
        )}
      </main>
      <footer className="site">
        <div className="wrap">
          <p>
            Built by <a href="https://beta.nyc">BetaNYC</a> from the NYC Council's own spreadsheets and NYC Open Data, the same data as the{" "}
            <a href="https://www.npmjs.com/package/@betanyc/nyc-budget-mcp">@betanyc/nyc-budget-mcp</a> server
            {db.manifest?.include_reviewed ? <>, plus reviewed PDF tables the server does not serve ({REVIEWED_LABEL})</> : null}.{" "}
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

function Loading({ phase, progress }) {
  const what = { idle: "Starting", manifest: "Reading the data manifest", engine: "Loading the query engine", data: "Loading the data" }[phase] ?? "Loading";
  return (
    <div className="loading" role="status" aria-live="polite">
      <p>
        {what}… {phase === "engine" || phase === "data" ? `${Math.round(progress * 100)}%` : ""}
      </p>
      <progress value={progress} max={1} />
      <p className="muted small">The explorer runs in your browser: it downloads the query engine (about 33 MB, cached after the first visit) and about 4 MB of data.</p>
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
    case "source":
      return <Source {...props} />;
    case "review":
      return <Review {...props} />;
    case "about":
      return <About manifest={manifest} />;
    default:
      return <Awards {...props} />;
  }
}
