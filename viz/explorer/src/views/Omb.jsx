import { useQueries } from "../duckdb/useDuckDB.js";
import { VERDICT_LABEL, count, money } from "../format.js";
import * as Q from "../query/sql.js";
import { ombFilters } from "../state/hash.js";
import { Matched, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";

/**
 * The Council's capital list against OMB's adopted capital budget, by budget line: this
 * repository's arithmetic (data/capital/council_vs_omb_by_budget_line.csv). A blank side means the
 * line is absent from it, never $0.
 */
export default function Omb({ state, set, ombYears }) {
  const f = ombFilters(state);
  const q = useQueries(true, JSON.stringify([f, state.opage]), () => ({ counts: Q.ombCountsQuery(f), rows: Q.ombRowsQuery(f, state.opage) }));
  return (
    <section>
      <h2>Council capital vs OMB</h2>
      <p className="lede">
        For each report year and budget line, the Council's capital rows against OMB's adopted Capital Budget (NYC Open Data 46m8-77gv; the release used
        is shown on each row), first and second year. The budget line is the only key the two share; nothing here is matched at project level. Years:{" "}
        {ombYears.map((y) => `FY${y}`).join(", ")}.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter
          label="Report year"
          value={state.ofy ?? ""}
          options={[["", "All years"], ...ombYears.map((y) => [String(y), `FY${y}`])]}
          onApply={(v) => set({ ofy: v === "" ? null : Number(v) })}
        />
        <SelectFilter
          label="Verdict"
          value={state.verdict}
          options={[["", "Any verdict"], ...Q.OMB_VERDICTS.map((v) => [v, VERDICT_LABEL[v]])]}
          onApply={(v) => set({ verdict: v })}
        />
        <TextFilter label="Budget line" value={state.oline} onApply={(v) => set({ oline: v })} placeholder="HL DN164" width="8rem" />
      </form>
      {state.ofy != null && !ombYears.includes(state.ofy) && <Notice tone="warn">FY{state.ofy} is not in the comparison.</Notice>}
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && <Results data={q.data} state={state} set={set} />}
      </Status>
    </section>
  );
}

function Results({ data, state, set }) {
  const verdicts = Object.fromEntries(Q.OMB_VERDICTS.map((v) => [v, 0]));
  let matched = 0;
  for (const r of data.counts) {
    verdicts[r.verdict] += Number(r.n);
    matched += Number(r.n);
  }
  const side = (v) => (v === null || v === undefined ? <span className="muted">not on this side</span> : money(v));
  return (
    <>
      <Matched matched={matched} what="line-year comparisons" />
      {matched > 0 && (
        <p>
          {Q.OMB_VERDICTS.map((v) => `${VERDICT_LABEL[v]}: ${count(verdicts[v])}`).join(" · ")}. Disagreements first, then the largest first-year difference.
        </p>
      )}
      {matched > 0 && (
        <>
          <div className="table-wrap">
            <table className="rows">
              <thead>
                <tr>
                  <th scope="col">Report year</th>
                  <th scope="col">Budget line</th>
                  <th scope="col">Verdict</th>
                  <th scope="col" className="num">
                    Council, year 1
                  </th>
                  <th scope="col" className="num">
                    OMB, year 1
                  </th>
                  <th scope="col" className="num">
                    Council, year 2
                  </th>
                  <th scope="col" className="num">
                    OMB, year 2
                  </th>
                  <th scope="col">OMB release</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={`${r.report_year}:${r.budget_line_norm}`}>
                    <td>{r.report_year}</td>
                    <td>
                      <button type="button" className="linkish" onClick={() => set({ view: "capital", cfy: r.report_year, line: r.budget_line_norm }, { push: true })}>
                        {r.budget_line_norm}
                      </button>
                    </td>
                    <td>{VERDICT_LABEL[r.verdict]}</td>
                    <td className="num">{side(r.council_y1)}</td>
                    <td className="num">{side(r.omb_y1)}</td>
                    <td className="num">{side(r.council_y2)}</td>
                    <td className="num">{side(r.omb_y2)}</td>
                    <td>{r.omb_pub_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={state.opage} matched={matched} onPage={(p) => set({ opage: p }, { keepPage: true })} />
        </>
      )}
    </>
  );
}
