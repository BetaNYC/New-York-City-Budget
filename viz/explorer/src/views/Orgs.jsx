import { useQueries } from "../duckdb/useDuckDB.js";
import { count, money } from "../format.js";
import * as P from "../query/pdf.js";
import { FlagBadge, ReviewedLabel, SourcePageLink } from "../components/pdf.jsx";
import { Matched, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";

/**
 * Capital §254 Part III, "Capital project detail by non-city entity": each organization's printed
 * line and the budget-line rows under it. From the reviewed PDF tables (pdf_capital_sd_orgs).
 */
export default function Orgs({ state, set, go, pdfYears }) {
  const fams = pdfYears.filter((y) => y.family === "capital_sd");
  const f = P.orgFilters(state);
  const q = useQueries(true, JSON.stringify([f, state.gpage]), () => ({ totals: P.orgsTotalsQuery(f), rows: P.orgsQuery(f, state.gpage) }));
  const yearOptions = [["", "All years"], ...fams.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}`])];
  return (
    <section>
      <h2>Organizations (capital Part III)</h2>
      {fams.map((y) => (
        <ReviewedLabel key={y.fiscal_year} status={y.status} block />
      ))}
      <p className="lede">
        The §254 book's Part III lists every non-city organization the Council's capital changes fund, with its total and the budget lines it is funded on. The
        organization's line is printed in the PDF; "rows" are the budget-line rows printed under it.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Fiscal year" value={state.gfy ?? ""} options={yearOptions} onApply={(v) => set({ gfy: v === "" ? null : Number(v) })} />
        <TextFilter label="Organization" value={state.org} onApply={(v) => set({ org: v })} placeholder="name" />
        <TextFilter label="Budget line" value={state.gline} onApply={(v) => set({ gline: v })} placeholder="PV DN004" width="8rem" />
      </form>
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && <Results data={q.data} state={state} set={set} go={go} />}
      </Status>
    </section>
  );
}

function Results({ data, state, set, go }) {
  const t = data.totals[0];
  const n = Number(t?.orgs ?? 0);
  return (
    <>
      <Matched matched={n} what="organizations" />
      {n > 0 && (
        <p className="muted">
          {count(t.lines)} budget-line rows: {money(t.y1)} for the book's own year, {money(Number(t.y2) + Number(t.y3) + Number(t.y4))} for the three later years (sums of the
          matching rows)
        </p>
      )}
      {n > 0 && (
        <div className="table-wrap">
          <table className="rows">
            <thead>
              <tr>
                <th scope="col">FY</th>
                <th scope="col">Organization</th>
                <th scope="col">Budget lines</th>
                <th scope="col" className="num">
                  Printed total, first year
                </th>
                <th scope="col" className="num">
                  Later years
                </th>
                <th scope="col">Rows add up</th>
                <th scope="col">Source</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((o) => (
                <tr key={`${o.fiscal_year}|${o.organization}`}>
                  <td>{o.fiscal_year}</td>
                  <td>
                    {o.organization} <ReviewedLabel status={o.status} />
                    <FlagBadge flags={o.flags} reviewId={o.review_id} />
                  </td>
                  <td>
                    <ul className="plain">
                      {o.lines.map((l) => (
                        <li key={l.budget_line}>
                          <code>{l.budget_line}</code> {money(l.y1)}
                          {Number(l.y2) || Number(l.y3) || Number(l.y4) ? <span className="muted"> + {money(Number(l.y2) + Number(l.y3) + Number(l.y4))} later</span> : null}{" "}
                          <SourcePageLink state={state} go={go} pdf={o.source_pdf} page={l.pdf_page} bbox={l.bbox_pt} label={`${o.organization}, ${l.budget_line}`} />
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td className="num">{money(o.org_printed_y1)}</td>
                  <td className="num">{money(Number(o.org_printed_y2) + Number(o.org_printed_y3) + Number(o.org_printed_y4))}</td>
                  <td>{o.org_status === "OK" ? "yes" : <strong>no</strong>}</td>
                  <td>
                    <SourcePageLink state={state} go={go} pdf={o.source_pdf} page={o.org_pdf_page} bbox={o.org_bbox_pt} label={o.organization} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pager page={state.gpage} matched={n} onPage={(p) => set({ gpage: p }, { keepPage: true })} />
      {n === 0 && <Notice>No organization matches. Names are as printed in Part III (e.g. "ALI FORNAY CENTER, INC." is spelled so in the PDF).</Notice>}
    </>
  );
}
