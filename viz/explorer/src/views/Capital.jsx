import { useQueries } from "../duckdb/useDuckDB.js";
import { CAPITAL_BEFORE_FIRST } from "../data/years.js";
import { CAPITAL_FLAG_NOTE, count, flagNotes, money, plural } from "../format.js";
import { sourceLinks } from "../paths.js";
import * as Q from "../query/sql.js";
import { capitalFilters, writeHash } from "../state/hash.js";
import { HashLink, Matched, NoData, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";

/** Council capital designations: by report year, sponsor, borough, district, budget line. */
export default function Capital({ state, set, go, manifest, capitalYears }) {
  const f = capitalFilters(state);
  const gap = gapFor(state.cfy, manifest.capital, capitalYears);
  const q = useQueries(true, JSON.stringify([f, state.cpage]), () =>
    gap ? null : { totals: Q.capitalTotalsQuery(f), rows: Q.capitalRowsQuery(f, state.cpage) }
  );
  const first = manifest.capital.first;
  const last = manifest.capital.last;
  const yearOptions = [["", "All report years"]];
  for (let y = last; y >= first; y--) yearOptions.push([String(y), capitalYears.includes(y) ? `FY${y}` : `FY${y} (no data)`]);

  return (
    <section>
      <h2>Council capital</h2>
      <p className="lede">
        The Council's capital designations from its capital workbooks and NYC Open Data (t474-a92g). A list's designations are the rows whose amount is for the
        list's own year; out-year rows are plans for later years. Sums are this repository's arithmetic: only FY2015 and FY2016 print totals.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Report year" value={state.cfy ?? ""} options={yearOptions} onApply={(v) => set({ cfy: v === "" ? null : Number(v) })} />
        <TextFilter label="Amount for FY" type="number" value={state.afy ?? ""} onApply={(v) => set({ afy: v === "" ? null : Number(v) })} width="7rem" />
        <TextFilter label="Sponsor" value={state.sponsor} onApply={(v) => set({ sponsor: v })} placeholder="surname" />
        <SelectFilter
          label="Borough"
          value={state.borough}
          options={[["", "Any borough"], ...Object.entries(Q.BOROUGHS).map(([k, v]) => [k, `${v} (${k})`])]}
          onApply={(v) => set({ borough: v })}
        />
        <TextFilter label="Council district" type="number" value={state.district ?? ""} onApply={(v) => set({ district: v === "" ? null : Number(v) })} width="7rem" />
        <TextFilter label="Budget line" value={state.line} onApply={(v) => set({ line: v })} placeholder="P D018" width="8rem" />
        <TextFilter label="Title" value={state.title} onApply={(v) => set({ title: v })} />
        <TextFilter label="Description" value={state.description} onApply={(v) => set({ description: v })} />
        <TextFilter label="Min $" type="number" value={state.cmin ?? ""} onApply={(v) => set({ cmin: v === "" ? null : Number(v) })} width="7rem" />
        <TextFilter label="Max $" type="number" value={state.cmax ?? ""} onApply={(v) => set({ cmax: v === "" ? null : Number(v) })} width="7rem" />
      </form>
      {state.district != null && (
        <Notice>
          The district filter reads the Council workbooks only (FY2015–FY2017, FY2026, FY2027). NYC Open Data typed t474's district column as a number and
          collapsed every list into one integer, so FY2019–FY2025 rows cannot match a district; use the sponsor filter for those years.
        </Notice>
      )}
      {state.line && !Q.normBudgetLine(state.line) && (
        <Notice tone="warn">
          "{state.line}" is not a budget line: give an agency code of one or two letters, a space or "-", then the line (e.g. P D018).
        </Notice>
      )}
      {gap ? (
        <NoData year={state.cfy} what="capital" reason={gap} />
      ) : (
        <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
          {q.data && <Results data={q.data} state={state} set={set} go={go} />}
        </Status>
      )}
    </section>
  );
}

export function gapFor(year, cap, capitalYears) {
  if (year == null || capitalYears.includes(year)) return null;
  const g = cap.gaps.find((x) => x.year === year);
  if (g) return g.reason;
  if (year < cap.first) return CAPITAL_BEFORE_FIRST(cap.first);
  return "No Council capital list for this year is in this repository.";
}

function Results({ data, state, set, go }) {
  const r = Q.rollupCapital(data.totals);
  return (
    <>
      <Matched matched={r.matched} what="capital rows" />
      {r.matched > 0 && (
        <table className="totals">
          <caption>Totals over all {count(r.matched)} matching rows</caption>
          <tbody>
            <tr>
              <th scope="row">Amounts for the list's own year</th>
              <td>{plural(r.report_year_amounts.rows, "row")}</td>
              <td className="num">{money(r.report_year_amounts.amount)}</td>
            </tr>
            <tr>
              <th scope="row">Out-year amounts (plans for later years)</th>
              <td>{plural(r.out_year_amounts.rows, "row")}</td>
              <td className="num">{money(r.out_year_amounts.amount)}</td>
            </tr>
            {r.amount_unknown > 0 && (
              <tr>
                <th scope="row">Amount cannot be proven (not in totals)</th>
                <td>{plural(r.amount_unknown, "row")}</td>
                <td className="num">—</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
      {r.matched > 0 && (
        <>
          <div className="table-wrap">
            <table className="rows">
              <thead>
                <tr>
                  <th scope="col">Report year</th>
                  <th scope="col">For FY</th>
                  <th scope="col">Title</th>
                  <th scope="col">Sponsor</th>
                  <th scope="col">Budget line</th>
                  <th scope="col">Boro</th>
                  <th scope="col">District</th>
                  <th scope="col" className="num">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => {
                  const target = { view: "capital-row", seq: row.seq };
                  return (
                    <tr key={row.seq}>
                      <td>{row.report_year}</td>
                      <td>{row.amount_fy ?? "—"}</td>
                      <td>
                        <HashLink href={writeHash({ ...state, ...target })} onGo={() => go(target)}>
                          {row.title || "(no title)"}
                        </HashLink>
                        {row.description ? <div className="muted small">{row.description}</div> : null}
                      </td>
                      <td>{row.sponsor}</td>
                      <td>{row.budget_line}</td>
                      <td>{row.borough}</td>
                      <td>{row.source_kind === "open_data_t474" ? <span className="muted">unusable (t474)</span> : row.council_district}</td>
                      <td className="num">{row.amount === null ? <span className="muted">unknown</span> : money(row.amount)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Pager page={state.cpage} matched={r.matched} onPage={(p) => set({ cpage: p }, { keepPage: true })} />
        </>
      )}
    </>
  );
}

const CAPITAL_FIELDS = [
  ["report_year", "Report year", "The Council capital list the row comes from."],
  ["amount_fy", "Amount for fiscal year", "The report year, or an out-year."],
  ["amount", "Amount", "Dollars as printed; negative on some technical adjustments."],
  ["title", "Title"],
  ["description", "Description"],
  ["sponsor", "Sponsor"],
  ["project_id", "Council project ID", "Not linked to OMB's or the Financial Management System's IDs."],
  ["budget_line", "Budget line (as printed)"],
  ["budget_line_norm", "Budget line (normalized)", "The only key shared with OMB."],
  ["borough", "Borough"],
  ["council_district", "Council district (as printed)", "Unusable in NYC Open Data t474 rows (lists collapsed into one number)."],
  ["source_kind", "Source kind"],
  ["row_flag", "Row flag"],
];

export function CapitalRow({ state, back, manifest }) {
  const q = useQueries(true, String(state.seq), () => (state.seq != null ? { row: Q.capitalRowQuery(state.seq) } : null));
  const c = q.data?.row?.[0];
  const links = c ? sourceLinks(manifest.source_commit, c.source_file) : null;
  return (
    <section>
      <p>
        <button type="button" className="linkish" onClick={back}>
          ← Back to capital
        </button>
      </p>
      <Status loading={q.loading} error={q.error}>
        {!c ? (
          <Notice tone="warn">No capital row {state.seq ?? "?"}. The link may predate a data update.</Notice>
        ) : (
          <>
            <h2>
              {c.title || "(no title)"} <span className="muted">FY{c.report_year}</span>
            </h2>
            <p className="big">
              {c.amount === null ? "Amount unknown" : money(c.amount)} {c.amount_fy != null ? `for FY${c.amount_fy}` : ""}
            </p>
            {flagNotes(c.row_flag, CAPITAL_FLAG_NOTE).map((f) => (
              <Notice key={f.flag} tone="warn">
                <code>{f.flag}</code>: {f.note}
              </Notice>
            ))}
            <h3>Source</h3>
            <p>
              {c.source_kind === "open_data_t474" ? "NYC Open Data t474-a92g, row id " : "Row "}
              <strong>{c.source_row}</strong> of <code>{c.source_file}</code>, retrieved {c.retrieved}
              {c.wayback_timestamp ? `, from an Internet Archive capture (${c.wayback_timestamp})` : ""}.
            </p>
            <ul>
              {links && (
                <li>
                  <a href={links.raw}>Download the source file</a> (as committed at <code>{manifest.source_commit.slice(0, 7)}</code>) ·{" "}
                  <a href={links.page}>its page on GitHub</a>
                </li>
              )}
              {c.source_url && (
                <li>
                  Published at <a href={c.source_url}>{c.source_url}</a>
                </li>
              )}
              {c.sha256 && (
                <li>
                  sha256 <code>{c.sha256}</code>
                </li>
              )}
            </ul>
            <h3>Every column</h3>
            <dl className="fields">
              {CAPITAL_FIELDS.map(([k, label, note]) => (
                <div key={k}>
                  <dt>
                    {label} <code className="muted small">{k}</code>
                  </dt>
                  <dd>
                    {k === "amount" ? money(c[k]) : c[k] === null || c[k] === "" ? <span className="muted">blank</span> : String(c[k])}
                    {note ? <div className="muted small">{note}</div> : null}
                  </dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </Status>
    </section>
  );
}
