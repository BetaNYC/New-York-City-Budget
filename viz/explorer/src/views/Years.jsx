import { useQueries } from "../duckdb/useDuckDB.js";
import { buildYears, headlineOk } from "../data/years.js";
import { count, money } from "../format.js";
import * as Q from "../query/sql.js";
import { Status } from "../components/ui.jsx";

/**
 * Totals by fiscal year, both datasets side by side. A year with no data says so, with the
 * recorded reason; an early-snapshot year is labeled and its Cleared total is not drawn as a bar,
 * so it is never read as comparable with the others.
 */
export default function Years({ manifest, go }) {
  const q = useQueries(true, "years", () => ({ disc: Q.YEAR_DISCLOSURE_QUERY, cap: Q.YEAR_CAPITAL_QUERY }));
  return (
    <section>
      <h2>Year overview</h2>
      <p className="lede">
        Each fiscal year is a separate Council file, downloaded on a recorded date. Cleared is the expense headline figure, except where a year is an early
        snapshot or prints statuses beyond Cleared and Pending. Capital figures are the amounts for the list's own year; out-year amounts are plans for later
        years.
      </p>
      <Status loading={q.loading} error={q.error}>
        {q.data && <Table rows={buildYears(q.data.disc, Q.rollupCapital(q.data.cap).by_report_year, manifest.capital)} go={go} />}
      </Status>
    </section>
  );
}

function Table({ rows, go }) {
  const maxCleared = Math.max(1, ...rows.filter((r) => headlineOk(r.disclosure)).map((r) => r.disclosure.cleared.amount));
  return (
    <div className="table-wrap">
      <table className="rows years">
        <thead>
          <tr>
            <th scope="col">FY</th>
            <th scope="col">Expense awards: Cleared</th>
            <th scope="col" className="num">
              Pending
            </th>
            <th scope="col" className="num">
              Rows
            </th>
            <th scope="col">Capital: report-year amounts</th>
            <th scope="col" className="num">
              Out-year amounts
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ fiscal_year: y, disclosure: d, capital: c }) => (
            <tr key={y}>
              <th scope="row">
                <button type="button" className="linkish" onClick={() => go({ view: "awards", fy: y })} disabled={d.kind !== "data"}>
                  FY{y}
                </button>
              </th>
              {d.kind === "data" ? (
                <>
                  <td>
                    <div className="amount-cell">
                      <span>{money(d.cleared.amount)}</span>
                      {headlineOk(d) ? (
                        <span className="bar" style={{ width: `${(100 * d.cleared.amount) / maxCleared}%` }} aria-hidden="true" />
                      ) : null}
                    </div>
                    {d.early_snapshot ? (
                      <div className="tag">Early snapshot: not a headline figure. {d.note}</div>
                    ) : d.other_rows > 0 ? (
                      <div className="tag">
                        Also {count(d.other.rows)} rows ({money(d.other.amount)}) with other statuses; not comparable with other years' Cleared totals.
                      </div>
                    ) : null}
                  </td>
                  <td className="num">{money(d.pending.amount)}</td>
                  <td className="num">{count(d.rows)}</td>
                </>
              ) : (
                <td colSpan={3} className="gap">
                  <strong>No expense award data for this year.</strong> {d.reason}
                </td>
              )}
              {c.kind === "data" ? (
                <>
                  <td>
                    <button type="button" className="linkish" onClick={() => go({ view: "capital", cfy: y })}>
                      {money(c.report_year_amounts.amount)}
                    </button>{" "}
                    <span className="muted small">({count(c.report_year_amounts.rows)} rows)</span>
                    {c.amount_unknown > 0 ? <div className="tag">{count(c.amount_unknown)} row(s) with an amount that cannot be proven, not in the total.</div> : null}
                  </td>
                  <td className="num">{money(c.out_year_amounts.amount)}</td>
                </>
              ) : (
                <td colSpan={2} className="gap">
                  <strong>No capital data for this year.</strong> {c.reason}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
