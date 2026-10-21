import { useQueries } from "../duckdb/useDuckDB.js";
import { count, money, plural } from "../format.js";
import * as P from "../query/pdf.js";
import { FlagBadge, ReviewedLabel, SourcePageLink } from "../components/pdf.jsx";
import { Matched, Pager, Status } from "../components/ui.jsx";

/**
 * Schedule C (the adopted budget's PDF) as a second source beside the disclosure spreadsheet
 * (INTEGRATION.md §4), shown only when a Schedule C family is loaded. The pairing is the Schedule C
 * review's own rule (code/schedc/disclosure.py, ported in mcp/scripts/pdf-families.mjs): (EIN,
 * amount) as a multiset, and the City's own EIN only with a matching name. Report only: neither
 * source changes the other.
 */

export const scYearsOf = (pdfYears) => (pdfYears ?? []).filter((y) => y.family === "schedule_c");

/** Whole-year counts: in both, spreadsheet only, Schedule C only. */
export function ScPanel({ fy, scYears, set }) {
  const years = scYears.filter((y) => fy == null || y.fiscal_year === fy);
  const q = useQueries(true, `scsum${fy}`, () => (years.length ? { s: P.scSummaryQuery(fy) } : null));
  if (!years.length) return null;
  const rows = q.data?.s ?? [];
  return (
    <div className="book">
      {years.map((y) => {
        const by = Object.fromEntries(rows.filter((r) => Number(r.fiscal_year) === y.fiscal_year).map((r) => [r.side, r]));
        return (
          <div key={y.fiscal_year}>
            <h3>
              FY{y.fiscal_year} Schedule C beside this spreadsheet <ReviewedLabel status={y.status} />
            </h3>
            <p className="small">
              Schedule C is the list of designations printed in the adopted budget; this spreadsheet is the Council's later disclosure. Rows pair on EIN and
              amount (the City's own EIN also needs a matching name). Whole year, before the filters below:
            </p>
            <table className="totals">
              <tbody>
                {["matched", "disclosure_only", "pdf_only"].map((side) => (
                  <tr key={side}>
                    <th scope="row">
                      <button type="button" className="linkish" onClick={() => set({ fy: y.fiscal_year, scside: side })}>
                        {P.SC_SIDE_LABEL[side]}
                      </button>
                    </th>
                    <td>{plural(by[side]?.n ?? 0, "row")}</td>
                    <td className="num">{money(by[side]?.amount ?? 0)}</td>
                    <td className="muted small">
                      {side === "matched" ? "Schedule C's amounts" : side === "pdf_only" ? "printed in Schedule C, no spreadsheet partner" : "spreadsheet amounts"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {Number(by.matched?.ambiguous ?? 0) + Number(by.disclosure_only?.ambiguous ?? 0) > 0 && (
              <p className="muted small">
                {count(Number(by.matched?.ambiguous ?? 0) + Number(by.disclosure_only?.ambiguous ?? 0))} spreadsheet rows share an EIN and amount with others in
                another stream or status, so which of them pairs is a choice (body rows prefer the Speaker's and initiative streams, appendix rows their own
                stream, then Cleared, then sheet order), not a fact.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** For the spreadsheet rows on screen: Map "fy|source_row" -> their Schedule C side. */
export function useScForRows(rows, scYears) {
  const years = new Set(scYears.map((y) => y.fiscal_year));
  const mine = (rows ?? []).filter((r) => years.has(Number(r.fiscal_year)));
  const key = mine.map((r) => P.scKey(r.fiscal_year, r.source_row)).join(",");
  const q = useQueries(true, `scrows|${key}`, () => {
    const sq = P.scForDisclosureRowsQuery(mine);
    return sq ? { m: sq } : null;
  });
  if (!years.size) return null;
  return new Map((q.data?.m ?? []).map((r) => [P.scKey(r.fiscal_year, r.disclosure_row), r]));
}

/** The Schedule C cell of a spreadsheet row. */
export function ScCell({ m, state, go, inYear }) {
  if (!inYear) return <td className="muted small">no Schedule C loaded for this year</td>;
  if (!m) return <td className="muted small">…</td>;
  if (m.side === "disclosure_only") {
    return (
      <td className="small">
        <span className="muted">not in Schedule C</span>
        <div className="muted">{P.SC_REASON[m.reason] ?? m.reason}</div>
      </td>
    );
  }
  return (
    <td className="small">
      <div>
        {money(m.amount)} · <SourcePageLink state={state} go={go} pdf={m.source_pdf} page={m.pdf_page} bbox={m.bbox_pt} label={`Schedule C: ${m.org}`} />{" "}
        <ReviewedLabel status={m.status} /> <FlagBadge flags={m.flags} reviewId={m.review_id} />
      </div>
      {m.ambiguous ? <div className="muted">one of several rows with this EIN and amount</div> : null}
    </td>
  );
}

/** Schedule C rows with no spreadsheet partner, under the Awards filters that map to them. */
export function ScOnlyResults({ f, state, set, go }) {
  const q = useQueries(true, JSON.stringify(["sconly", f, state.page]), () => ({ t: P.scOnlyTotalsQuery(f), rows: P.scOnlyQuery(f, state.page) }));
  const t = q.data?.t?.[0];
  return (
    <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
      {q.data && (
        <>
          <Matched matched={Number(t.n)} what="Schedule C rows with no spreadsheet partner" />
          {Number(t.n) > 0 && <p className="muted">{money(t.amount)} printed in Schedule C. Status and funding-source filters do not apply to PDF rows.</p>}
          {Number(t.n) > 0 && (
            <div className="table-wrap">
              <table className="rows">
                <thead>
                  <tr>
                    <th scope="col">FY</th>
                    <th scope="col">Organization (as printed)</th>
                    <th scope="col">EIN</th>
                    <th scope="col">Council member</th>
                    <th scope="col">Section</th>
                    <th scope="col">Why no partner</th>
                    <th scope="col" className="num">
                      Amount
                    </th>
                    <th scope="col">Page</th>
                  </tr>
                </thead>
                <tbody>
                  {q.data.rows.map((r) => (
                    <tr key={r.award_id}>
                      <td>{r.fiscal_year}</td>
                      <td>
                        {r.org} <ReviewedLabel status={r.status} /> <FlagBadge flags={r.flags} reviewId={r.review_id} />
                        {r.initiative ? <div className="muted small">{r.initiative}</div> : null}
                      </td>
                      <td>{r.ein}</td>
                      <td>{r.member}</td>
                      <td>{r.section.replace("_", " ")}</td>
                      <td className="small">
                        {P.SC_REASON[r.reason] ?? r.reason}
                        {r.reason === "amount_differs" && r.nearest_amount != null ? <div className="muted">nearest spreadsheet amount {money(r.nearest_amount)}</div> : null}
                      </td>
                      <td className="num">{money(r.amount)}</td>
                      <td>
                        <SourcePageLink state={state} go={go} pdf={r.source_pdf} page={r.pdf_page} bbox={r.bbox_pt} label={`Schedule C: ${r.org}`} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Pager page={state.page} matched={Number(t.n)} onPage={(p) => set({ page: p }, { keepPage: true })} />
        </>
      )}
    </Status>
  );
}

/** On an award's page: its Schedule C partner, or why it has none. */
export function ScForAward({ a, scYears, state, go }) {
  const inYear = scYears.some((y) => y.fiscal_year === Number(a.fiscal_year));
  const q = useQueries(true, `scaward|${a.fiscal_year}|${a.source_row}`, () => (inYear ? { m: P.scForDisclosureRowsQuery([a]) } : null));
  if (!inYear) return null;
  const m = q.data?.m?.[0];
  return (
    <>
      <h3>
        In Schedule C (the adopted budget's PDF) {m ? <ReviewedLabel status={m.status ?? scYears[0].status} /> : null}
      </h3>
      {!m ? (
        <p className="muted">Loading…</p>
      ) : m.side === "disclosure_only" ? (
        <p>
          Not paired with a Schedule C row. {P.SC_REASON[m.reason] ?? m.reason}
        </p>
      ) : (
        <p>
          Printed as <strong>{m.org}</strong>, {money(m.amount)}
          {m.member ? `, ${m.member}` : ""}, in the {m.section.replace("_", " ")}.{" "}
          <SourcePageLink state={state} go={go} pdf={m.source_pdf} page={m.pdf_page} bbox={m.bbox_pt} label={`Schedule C: ${m.org}`}>
            See it on p.{m.pdf_page}
          </SourcePageLink>{" "}
          <FlagBadge flags={m.flags} reviewId={m.review_id} />
          {m.ambiguous ? <span className="muted small"> (one of several rows with this EIN and amount: the pairing is a choice)</span> : null}
        </p>
      )}
    </>
  );
}
