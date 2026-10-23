import { useQueries } from "../duckdb/useDuckDB.js";
import { money, plural } from "../format.js";
import * as P from "../query/pdf.js";
import { FlagBadge, HiddenText, PageImageNote, ReviewedLabel, RowLinks } from "../components/pdf.jsx";
import { Matched, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";
import { YearStatus } from "./ScheduleCSearch.jsx";

/**
 * Transparency resolutions (#213): the changes the Council votes after the budget is adopted:
 * money added to an organization, taken back, or given a new purpose. Every row says when the
 * change was made (its resolution's number and date) and which budget year it changes (a year's
 * resolutions can change earlier years; each chart's own year is on its rows, #209).
 */
export default function Transparency(props) {
  if (!props.pdfYears.some((y) => y.family === "transparency")) {
    return <Notice>No transparency resolution data is in this build. It appears once a year's resolutions have been checked (data/pdf_years.csv).</Notice>;
  }
  return <Body {...props} />;
}

function Body({ state, set, go, manifest, pdfYears }) {
  const years = pdfYears.filter((y) => y.family === "transparency");
  const f = P.trFilters(state);
  const q = useQueries(true, JSON.stringify(["tr", f, state.trpage]), () => ({ t: P.trTotalsQuery(f), rows: P.trQuery(f, state.trpage) }));
  const rq = useQueries(true, "tr-resolutions", () => ({ r: P.trResolutionsQuery() }));
  const r = q.data ? P.rollupTr(q.data.t) : null;
  const yearOptions = [["", "All years"], ...years.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}`])];
  const resolutions = (rq.data?.r ?? []).filter((x) => state.trfy == null || Number(x.fiscal_year) === state.trfy);
  return (
    <section>
      <h2>Transparency resolutions: changes after the budget was adopted</h2>
      <p className="lede">
        After it adopts the budget, the Council changes its designations by resolution: money added to an organization, money taken back, or the same money
        given a new purpose. Each row is one line of one resolution's charts, as printed, with the date the Council adopted the resolution.
      </p>
      <YearStatus years={years.filter((y) => state.trfy == null || y.fiscal_year === state.trfy)} />
      <form className="filters" onSubmit={(e) => e.preventDefault()} aria-label="Search transparency resolutions">
        <SelectFilter label="Year of the resolutions" value={state.trfy ?? ""} options={yearOptions} onApply={(v) => set({ trfy: v === "" ? null : Number(v), trreso: "" })} />
        <TextFilter label="Budget year changed" type="number" value={state.trbfy ?? ""} onApply={(v) => set({ trbfy: v === "" ? null : Number(v) })} width="8rem" />
        <TextFilter label="Organization" value={state.trorg} onApply={(v) => set({ trorg: v })} placeholder="part of the name" />
        <TextFilter label="EIN (tax ID)" value={state.trein} onApply={(v) => set({ trein: v })} placeholder="13-2612524" width="9rem" />
        <TextFilter label="Council member" value={state.trmember} onApply={(v) => set({ trmember: v })} placeholder="surname or Speaker" />
        <label className="field">
          <span>Resolution number</span>
          <input
            list="tr-resolution-list"
            defaultValue={state.trreso}
            key={state.trreso}
            placeholder="e.g. 1013"
            aria-describedby="tr-reso-help"
            onBlur={(e) => e.target.value.trim() !== state.trreso && set({ trreso: e.target.value.trim() })}
            onKeyDown={(e) => e.key === "Enter" && e.currentTarget.value.trim() !== state.trreso && set({ trreso: e.currentTarget.value.trim() })}
          />
          <datalist id="tr-resolution-list">
            {resolutions.map((x) => (
              <option key={`${x.fiscal_year}|${x.resolution_seq}`} value={x.resolution_number}>
                {x.resolution_date} · FY{x.fiscal_year}
              </option>
            ))}
          </datalist>
          <span id="tr-reso-help" className="visually-hidden">
            Part of the number is enough; the list suggests the resolutions of the year chosen.
          </span>
        </label>
        <TextFilter label="Adopted on or after" type="date" value={state.trfrom} onApply={(v) => set({ trfrom: v })} width="10rem" />
        <TextFilter label="Adopted on or before" type="date" value={state.trto} onApply={(v) => set({ trto: v })} width="10rem" />
        <SelectFilter
          label="Kind of change"
          value={state.traction}
          options={[["", "Any"], ...P.TR_ACTIONS.map((a) => [a, P.TR_ACTION_LABEL[a]])]}
          onApply={(v) => set({ traction: v })}
        />
      </form>
      {P.einUnusable(state.trein) && <Notice tone="warn">"{state.trein}" is not an EIN: give its nine digits (e.g. 13-2612524). The EIN filter is not applied.</Notice>}
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && (
          <>
            <Matched matched={r.matched} what="resolution rows" />
            {r.matched > 0 && (
              <table className="totals">
                <caption>Over all {plural(r.matched, "matching row")}, by kind of change</caption>
                <tbody>
                  {P.TR_ACTIONS.filter((a) => r.byAction[a]).map((a) => (
                    <tr key={a}>
                      <th scope="row">{P.TR_ACTION_LABEL[a]}</th>
                      <td>{plural(r.byAction[a].n, "row")}</td>
                      <td className="num">{a === "listed" ? <span className="muted">{P.NO_AMOUNT_LABEL}</span> : money(r.byAction[a].amount)}</td>
                    </tr>
                  ))}
                  {Object.keys(r.agencyByAction).length > 0 ? (
                    <tr>
                      <th scope="rowgroup" colSpan={3} className="small">
                        Lines for a City agency itself, not money to or from an organization (some charts list them in their own section); kept out of the
                        lines above
                      </th>
                    </tr>
                  ) : null}
                  {P.TR_ACTIONS.filter((a) => r.agencyByAction[a]).map((a) => (
                    <tr key={`agency-${a}`}>
                      <th scope="row">City agency lines: {P.TR_ACTION_LABEL[a].toLowerCase()}</th>
                      <td>{plural(r.agencyByAction[a].n, "row")}</td>
                      <td className="num">{a === "listed" ? <span className="muted">{P.NO_AMOUNT_LABEL}</span> : money(r.agencyByAction[a].amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {r.matched > 0 && (
              <p className="muted small">
                Amounts are as printed: money taken back prints as a negative number, and a change of purpose prints the old purpose as a negative line and the new
                one as a positive line, so the two nearly cancel out. Rows that print no dollar amount are counted as rows, never as dollars.
              </p>
            )}
            {r.matched > 0 && (
              <div className="table-wrap">
                <table className="rows">
                  <caption className="visually-hidden">Resolution rows, newest resolution first</caption>
                  <thead>
                    <tr>
                      <th scope="col">Resolution</th>
                      <th scope="col">Change</th>
                      <th scope="col">Council member</th>
                      <th scope="col">Organization (as printed)</th>
                      <th scope="col">EIN (tax ID)</th>
                      <th scope="col">Agency</th>
                      <th scope="col">Purpose</th>
                      <th scope="col" className="num">
                        Amount
                      </th>
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.data.rows.map((x) => (
                      <TrRow key={`${x.fiscal_year}|${x.row_id}`} x={x} state={state} go={go} manifest={manifest} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Pager page={state.trpage} matched={r.matched} onPage={(p) => set({ trpage: p }, { keepPage: true })} />
          </>
        )}
      </Status>
    </section>
  );
}

const fmtEin = (e) => (/^\d{9}$/.test(String(e ?? "")) ? `${e.slice(0, 2)}-${e.slice(2)}` : e || "");

function TrRow({ x, state, go, manifest }) {
  const amount = x.amount == null ? P.NO_AMOUNT_LABEL : money(x.amount);
  return (
    <tr>
      <td className="small">
        <strong>{x.resolution_number}</strong>
        <div>
          adopted <time dateTime={x.resolution_date}>{x.resolution_date}</time>
        </div>
        <div className="muted">
          FY{x.fiscal_year} resolutions{Number(x.budget_fiscal_year) !== Number(x.fiscal_year) ? ` · changes the FY${x.budget_fiscal_year} budget` : ""}
        </div>
        <ReviewedLabel status={x.status} />
      </td>
      <td className="small">
        {P.TR_ACTION_LABEL[x.action] ?? x.action}
        <div className="muted">
          Chart {x.chart_number}: {x.chart_title}
        </div>
        {Number(x.agency_side) === 1 ? <div className="muted">a line for a City agency itself, not an organization</div> : null}
      </td>
      <td>{x.member}</td>
      <td>
        {x.org} <FlagBadge flags={x.flags} reviewId={x.review_id} />
        {x.fiscal_conduit ? (
          <div className="small">
            Fiscal conduit (receives the money for it): {x.fiscal_conduit}
            {x.fiscal_conduit_ein ? `, EIN ${fmtEin(x.fiscal_conduit_ein)}` : ""}
          </div>
        ) : null}
        <HiddenText text={x.hidden_text} />
        <PageImageNote fields={x.read_from_page_image} />
      </td>
      <td>{fmtEin(x.ein)}</td>
      <td>{x.agency}</td>
      <td className="small">{x.purpose}</td>
      <td className="num">{x.amount == null ? <span className="muted">{amount}</span> : amount}</td>
      <td>
        <RowLinks state={state} go={go} manifest={manifest} row={x} label={`${x.resolution_number} (${x.resolution_date}): ${x.org}, ${amount}`} />
      </td>
    </tr>
  );
}
