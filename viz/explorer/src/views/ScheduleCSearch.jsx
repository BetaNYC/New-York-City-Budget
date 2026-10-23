import { useQueries } from "../duckdb/useDuckDB.js";
import { count, money, plural } from "../format.js";
import * as P from "../query/pdf.js";
import { writeHash } from "../state/hash.js";
import { FlagBadge, PageImageNote, ReviewedLabel, RowLinks } from "../components/pdf.jsx";
import { HashLink, Matched, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";
import { scYearsOf } from "./ScheduleC.jsx";

/**
 * Schedule C, every row (#213): the designations printed in each adopted budget, searchable by
 * organization, EIN, sponsor, category, initiative, agency, year and amount. Each row says where it
 * stands against the Council's disclosure spreadsheet (the pairing the Expense awards view shows
 * from the spreadsheet's side). Sub-awards (a partner list printed under one award) are shown
 * under that award and never added to a total.
 */
export default function ScheduleCSearch(props) {
  if (!scYearsOf(props.pdfYears).length) {
    return <Notice>No Schedule C data is in this build. It appears once a year's Schedule C has been checked (data/pdf_years.csv).</Notice>;
  }
  return <Body {...props} />;
}

function Body({ state, set, go, manifest, pdfYears }) {
  const years = scYearsOf(pdfYears);
  const f = P.scSearchFilters(state);
  const q = useQueries(true, JSON.stringify(["scsearch", f, state.scpage]), () => ({ t: P.scSearchTotalsQuery(f), rows: P.scSearchQuery(f, state.scpage) }));
  const subq = useQueries(true, `scsub|${(q.data?.rows ?? []).filter((r) => Number(r.subawards) > 0).map((r) => r.award_id).join(",")}`, () => {
    const sq = P.scSubawardsQuery(q.data?.rows);
    return sq ? { s: sq } : null;
  });
  const subs = new Map();
  for (const s of subq.data?.s ?? []) {
    const k = `${Number(s.fiscal_year)}|${s.parent_award_id}`;
    if (!subs.has(k)) subs.set(k, []);
    subs.get(k).push(s);
  }
  const t = q.data?.t?.[0];
  const yearOptions = [["", "All years"], ...years.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}`])];
  const filtered = years.filter((y) => state.scfy == null || y.fiscal_year === state.scfy);
  return (
    <section>
      <h2>Schedule C: every designation printed in the adopted budget</h2>
      <p className="lede">
        Schedule C is the Council's list of the money it designated to organizations, printed with each adopted budget. These rows were read from the PDF and
        checked against every printed total. Search every row here; the <a href={writeHash({ ...state, view: "awards" })}>Expense awards</a> view shows the
        Council's later spreadsheet, with each spreadsheet row's Schedule C partner.
      </p>
      <YearStatus years={filtered} />
      <form className="filters" onSubmit={(e) => e.preventDefault()} aria-label="Search Schedule C">
        <SelectFilter label="Fiscal year" value={state.scfy ?? ""} options={yearOptions} onApply={(v) => set({ scfy: v === "" ? null : Number(v) })} />
        <TextFilter label="Organization" value={state.scorg} onApply={(v) => set({ scorg: v })} placeholder="part of the name" />
        <TextFilter label="EIN" value={state.scein} onApply={(v) => set({ scein: v })} placeholder="13-2612524" width="9rem" />
        <TextFilter label="Sponsor" value={state.scspon} onApply={(v) => set({ scspon: v })} placeholder="member, Speaker, delegation" />
        <TextFilter label="Category" value={state.sccat} onApply={(v) => set({ sccat: v })} placeholder="e.g. Local" />
        <TextFilter label="Initiative" value={state.scinit} onApply={(v) => set({ scinit: v })} placeholder="e.g. senior" />
        <TextFilter label="Agency" value={state.scagency} onApply={(v) => set({ scagency: v })} placeholder="e.g. DYCD" width="8rem" />
        <TextFilter label="Min $" type="number" value={state.scmin ?? ""} onApply={(v) => set({ scmin: v === "" ? null : Number(v) })} width="7rem" />
        <TextFilter label="Max $" type="number" value={state.scmax ?? ""} onApply={(v) => set({ scmax: v === "" ? null : Number(v) })} width="7rem" />
        <SelectFilter
          label="In the disclosure spreadsheet"
          value={state.scdisc}
          options={[["", "Any"], ...Object.entries(P.SC_DISCLOSURE_LABEL).map(([k, v]) => [k, v.replace("In the spreadsheet: ", "")])]}
          onApply={(v) => set({ scdisc: v })}
        />
      </form>
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && (
          <>
            <Matched matched={Number(t.n)} what="Schedule C rows" />
            {Number(t.n) > 0 && (
              <p>
                <strong>{money(t.amount)}</strong> printed across {plural(t.n, "row")} in {plural(t.years, "year")}.
                {Number(t.no_amount) > 0 ? ` ${plural(t.no_amount, "row")} print no dollar amount and are not in the total.` : ""} Sub-awards (a partner list printed
                under one award) are shown under their award and are not added: they are that award's money passed on.
              </p>
            )}
            {Number(t.n) > 0 && (
              <div className="table-wrap">
                <table className="rows">
                  <caption className="visually-hidden">Schedule C rows, highest amount first</caption>
                  <thead>
                    <tr>
                      <th scope="col">FY</th>
                      <th scope="col">Organization (as printed)</th>
                      <th scope="col">EIN</th>
                      <th scope="col">Sponsor</th>
                      <th scope="col">Category and initiative</th>
                      <th scope="col">Agency</th>
                      <th scope="col">Purpose</th>
                      <th scope="col" className="num">
                        Amount
                      </th>
                      <th scope="col">Disclosure spreadsheet</th>
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.data.rows.map((r) => (
                      <ScRow key={r.award_id} r={r} subs={subs.get(`${Number(r.fiscal_year)}|${r.award_id}`)} state={state} go={go} manifest={manifest} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Pager page={state.scpage} matched={Number(t.n)} onPage={(p) => set({ scpage: p }, { keepPage: true })} />
          </>
        )}
      </Status>
    </section>
  );
}

/** One line per year in view: its status, in words. */
export function YearStatus({ years }) {
  if (!years.length) return null;
  const by = new Map();
  for (const y of years) {
    if (!by.has(y.status)) by.set(y.status, []);
    by.get(y.status).push(y.fiscal_year);
  }
  return (
    <ul className="year-status small">
      {[...by.entries()].map(([status, ys]) => (
        <li key={status}>
          <ReviewedLabel status={status} />: {ys.sort((a, b) => a - b).map((y) => `FY${y}`).join(", ")}
        </li>
      ))}
    </ul>
  );
}

const sponsorOf = (r) => [r.member, r.sponsor, r.delegation].filter(Boolean).join(" · ");
const fmtEin = (e) => (/^\d{9}$/.test(String(e ?? "")) ? `${e.slice(0, 2)}-${e.slice(2)}` : e || "");

function ScRow({ r, subs, state, go, manifest }) {
  const label = `Schedule C FY${r.fiscal_year}: ${r.org}, ${money(r.amount)}`;
  const award = r.disclosure_row != null ? { view: "award", ay: Number(r.fiscal_year), row: Number(r.disclosure_row) } : null;
  return (
    <>
      <tr>
        <td>{r.fiscal_year}</td>
        <td>
          {r.org} <ReviewedLabel status={r.status} /> <FlagBadge flags={r.flags} reviewId={r.review_id} />
          {Number(r.review_not_completed) === 1 ? (
            <div className="small">
              <span className="mark-label">{P.REVIEW_NOT_COMPLETED_LABEL}</span> <span className="muted">{P.REVIEW_NOT_COMPLETED_NOTE}</span>
            </div>
          ) : null}
          {r.fiscal_conduit ? (
            <div className="small">
              Fiscal conduit (receives the money for it): {r.fiscal_conduit}
              {r.fiscal_conduit_ein ? `, EIN ${fmtEin(r.fiscal_conduit_ein)}` : ""}
            </div>
          ) : null}
          <PageImageNote fields={r.read_from_page_image} />
        </td>
        <td>{fmtEin(r.ein)}</td>
        <td>{sponsorOf(r)}</td>
        <td className="small">
          {r.category}
          {r.initiative ? <div className="muted">{r.initiative}</div> : null}
        </td>
        <td>{r.agency}</td>
        <td className="small">
          {r.program_or_subheading ? <div className="muted">Program or sub-heading: {r.program_or_subheading}</div> : null}
          {r.purpose}
        </td>
        <td className="num">{r.amount == null ? <span className="muted">{P.NO_AMOUNT_LABEL}</span> : money(r.amount)}</td>
        <td className="small">
          {award ? (
            <HashLink href={writeHash({ ...state, ...award })} onGo={() => go(award)}>
              {P.SC_DISCLOSURE_LABEL[r.disclosure_status] ?? r.disclosure_status}
            </HashLink>
          ) : (
            <>
              {P.SC_DISCLOSURE_LABEL[r.disclosure_status] ?? r.disclosure_status}
              {r.disclosure_reason ? <div className="muted">{P.SC_REASON[r.disclosure_reason] ?? r.disclosure_reason}</div> : null}
            </>
          )}
        </td>
        <td>
          <RowLinks state={state} go={go} manifest={manifest} row={r} label={label} />
        </td>
      </tr>
      {Number(r.subawards) > 0 ? (
        <tr className="subawards">
          <td />
          <td colSpan={9}>
            <table className="rows small">
              <caption>
                Sub-awards printed under this award: {plural(r.subawards, "organization")} it passes the money to. Not added to any total.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Organization (as printed)</th>
                  <th scope="col">EIN</th>
                  <th scope="col">Service</th>
                  <th scope="col" className="num">
                    Amount
                  </th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {(subs ?? []).map((s) => (
                  <tr key={s.subaward_id}>
                    <td>
                      {s.org} <FlagBadge flags={s.flags} reviewId={s.review_id} />
                    </td>
                    <td>{fmtEin(s.ein)}</td>
                    <td>{s.service_type}</td>
                    <td className="num">{money(s.amount)}</td>
                    <td>
                      <RowLinks state={state} go={go} manifest={manifest} row={s} label={`Sub-award FY${s.fiscal_year}: ${s.org}, ${money(s.amount)}`} />
                    </td>
                  </tr>
                ))}
                {!subs ? (
                  <tr>
                    <td colSpan={5} className="muted">
                      Loading {count(r.subawards)} rows…
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </td>
        </tr>
      ) : null}
    </>
  );
}
