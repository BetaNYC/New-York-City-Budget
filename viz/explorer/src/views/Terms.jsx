import { useQueries } from "../duckdb/useDuckDB.js";
import { count } from "../format.js";
import * as P from "../query/pdf.js";
import { FlagBadge, ReviewedLabel, SourcePageLink } from "../components/pdf.jsx";
import { Matched, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";

/**
 * Terms and Conditions: the reports the Council requires as a condition of funds, by agency and
 * unit of appropriation (pdf_terms). Text only, no dollars.
 */
export default function Terms({ state, set, go, pdfYears }) {
  const fams = pdfYears.filter((y) => y.family === "terms");
  const f = P.termsFilters(state);
  const q = useQueries(true, JSON.stringify([f, state.tpage]), () => ({ n: P.termsCountQuery(f), rows: P.termsQuery(f, state.tpage) }));
  const yearOptions = [["", "All years"], ...fams.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}`])];
  return (
    <section>
      <h2>Terms and Conditions</h2>
      {fams.map((y) => (
        <ReviewedLabel key={y.fiscal_year} status={y.status} block />
      ))}
      <p className="lede">
        Each condition names the agencies and units of appropriation (or capital budget lines) whose funds it applies to, and the reports the agency must send
        the Council. Deadlines are the dates the text gives after "no later than"; read the condition for the full schedule.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Fiscal year" value={state.tfy ?? ""} options={yearOptions} onApply={(v) => set({ tfy: v === "" ? null : Number(v) })} />
        <TextFilter label="Agency" value={state.tagency} onApply={(v) => set({ tagency: v })} placeholder="name or code" />
        <TextFilter label="Unit or budget line" value={state.tunit} onApply={(v) => set({ tunit: v })} placeholder="001 or HD-0009" width="9rem" />
        <TextFilter label="Text" value={state.tq} onApply={(v) => set({ tq: v })} placeholder="e.g. shelter" />
        <SelectFilter
          label="Kind"
          value={state.tkind}
          options={[["", "Any"], ["expense", "Expense"], ["capital", "Capital"], ["capital+expense", "Both"]]}
          onApply={(v) => set({ tkind: v })}
        />
      </form>
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && (
          <>
            <Matched matched={Number(q.data.n[0].n)} what="conditions" />
            {Number(q.data.n[0].n) > 0 && <p className="muted">{count(q.data.n[0].agencies)} agency names among them.</p>}
            <ol className="conditions">
              {q.data.rows.map((c) => (
                <li key={`${c.fiscal_year}|${c.item_number}`} value={c.item_number}>
                  <Condition c={c} state={state} go={go} />
                </li>
              ))}
            </ol>
            <Pager page={state.tpage} matched={Number(q.data.n[0].n)} onPage={(p) => set({ tpage: p }, { keepPage: true })} />
          </>
        )}
      </Status>
    </section>
  );
}

function Condition({ c, state, go }) {
  const pages = c.page_start === c.page_end ? `p.${c.page_start}` : `pp.${c.page_start}–${c.page_end}`;
  return (
    <article className="condition">
      <h3>
        {c.agency_name} <span className="muted small">FY{c.fiscal_year} · {c.kind}</span> <ReviewedLabel status={c.status} />{" "}
        <FlagBadge flags={c.flags} reviewId={c.review_id} />
      </h3>
      <p className="small">
        {c.units_of_appropriation ? (
          <>
            Units of appropriation: <code>{c.units_of_appropriation.replaceAll("; ", ", ")}</code>
          </>
        ) : null}
        {c.budget_lines ? (
          <>
            {" "}
            Budget lines: <code>{c.budget_lines}</code>
          </>
        ) : null}
        {c.report_deadlines ? <> · Deadlines: {c.report_deadlines}</> : null} ·{" "}
        <SourcePageLink state={state} go={go} pdf={c.source_pdf} page={c.pdf_page} bbox={c.bbox_pt} label={`Condition ${c.item_number}: ${c.agency_name}`}>
          {pages}
        </SourcePageLink>
      </p>
      <details>
        <summary>Text</summary>
        <p className="condition-text">{c.condition_text}</p>
        {Number(c.item_number) === 15 ? <FsrTable fy={c.fiscal_year} /> : null}
      </details>
    </article>
  );
}

/** The DOE Financial Status Report schedule printed inside condition 15 (FY2027). */
function FsrTable({ fy }) {
  const q = useQueries(true, `fsr${fy}`, () => ({ rows: P.termsFsrQuery(fy) }));
  const rows = q.data?.rows ?? [];
  if (!rows.length) return null;
  return (
    <table className="rows small">
      <caption>The table printed in this condition</caption>
      <thead>
        <tr>
          <th>Financial status report</th>
          <th>Report content</th>
          <th>Issue date</th>
          <th>Anticipated meeting date</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.financial_status_report}>
            <td>{r.financial_status_report}</td>
            <td>
              {r.report_content} <FlagBadge flags={r.flags} reviewId={r.review_id} />
            </td>
            <td>{r.issue_date}</td>
            <td>{r.anticipated_meeting_date}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
