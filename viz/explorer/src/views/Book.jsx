import { useQueries } from "../duckdb/useDuckDB.js";
import { money, plural } from "../format.js";
import * as P from "../query/pdf.js";
import * as Q from "../query/sql.js";
import { FlagBadge, ReviewedLabel, RowLinks } from "../components/pdf.jsx";
import { StateBadge } from "../components/OpenData.jsx";
import { Matched, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";
import { datasetUrl, rowUrl, stateOf, tooltipOf } from "../query/opendata.js";
import { YearStatus } from "./ScheduleCSearch.jsx";

/**
 * The capital book (#213): every row of each year's §254 supporting-detail PDF, the Council's
 * printed list of its capital changes, searchable by SUB ID, sponsor, borough, agency, title, budget
 * line and year. Amounts are as printed, negative ones (reductions) included; a sponsor cell may
 * name a district with no member ("CD 22", #206). FY2019's book also prints each row's Council
 * district and a description, shown where present. The Capital view shows the Council workbook's
 * rows beside the book; this one is the book itself.
 */
export default function Book(props) {
  if (!props.pdfYears.some((y) => y.family === "capital_sd")) {
    return <Notice>No capital book data is in this build. It appears once a year's book has been checked (data/pdf_years.csv).</Notice>;
  }
  return <Body {...props} />;
}

function Body({ state, set, go, manifest, pdfYears }) {
  const years = pdfYears.filter((y) => y.family === "capital_sd");
  const f = P.bookFilters(state);
  const q = useQueries(true, JSON.stringify(["book", f, state.bkpage]), () => ({ t: P.bookTotalsQuery(f), rows: P.bookQuery(f, state.bkpage) }));
  const rows = q.data?.rows ?? [];
  const oq = useQueries(true, `bookod|${rows.map((r) => `${r.fiscal_year}|${r.sub_id}`).join(",")}`, () => {
    const x = P.odForBookRowsQuery(rows);
    return x ? { x } : null;
  });
  const t = q.data?.t?.[0];
  const fy = state.bkfy;
  const yearOptions = [["", "All years"], ...years.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}`])];
  // The four year columns are the book's own year and the next three; with one year chosen they get its labels.
  const yl = (k) => (fy == null ? (k === 1 ? "Book's year" : `Year +${k - 1}`) : `FY${fy + k - 1}`);
  const fy19 = rows.some((r) => r.council_district || r.description);
  return (
    <section>
      <h2>The capital book: every row of the §254 supporting detail</h2>
      <p className="lede">
        Each year the Council prints the capital projects it funds in a supporting-detail book (under §254 of the City Charter). These rows were read from
        that PDF and checked against its printed totals. Amounts are as printed, for the book's own year and the next three; a negative amount is a reduction.
      </p>
      <YearStatus years={years.filter((y) => fy == null || y.fiscal_year === fy)} />
      <form className="filters" onSubmit={(e) => e.preventDefault()} aria-label="Search the capital book">
        <SelectFilter label="Fiscal year" value={fy ?? ""} options={yearOptions} onApply={(v) => set({ bkfy: v === "" ? null : Number(v) })} />
        <TextFilter label="Project ID (SUB ID)" value={state.bkid} onApply={(v) => set({ bkid: v })} placeholder="HR CC0168" width="9rem" />
        <TextFilter label="Sponsor" value={state.bksponsor} onApply={(v) => set({ bksponsor: v })} placeholder="surname, Speaker, CD 22" />
        <SelectFilter
          label="Borough"
          value={state.bkboro}
          options={[["", "Any borough"], ...Object.entries(Q.BOROUGHS).map(([k, v]) => [k, `${v} (${k})`])]}
          onApply={(v) => set({ bkboro: v })}
        />
        <TextFilter label="Agency" value={state.bkagency} onApply={(v) => set({ bkagency: v })} placeholder="e.g. parks" />
        <TextFilter label="Title or description" value={state.bktitle} onApply={(v) => set({ bktitle: v })} placeholder="e.g. library" />
        <TextFilter label="Budget line" value={state.bkline} onApply={(v) => set({ bkline: v })} placeholder="P D018" width="8rem" />
        <SelectFilter label="Part of the book" value={state.bkpart} options={[["", "Any"], ["I", "Part I"], ["II", "Part II"]]} onApply={(v) => set({ bkpart: v })} />
        <TextFilter label="Min $ (book's year)" type="number" value={state.bkmin ?? ""} onApply={(v) => set({ bkmin: v === "" ? null : Number(v) })} width="8rem" />
        <TextFilter label="Max $ (book's year)" type="number" value={state.bkmax ?? ""} onApply={(v) => set({ bkmax: v === "" ? null : Number(v) })} width="8rem" />
      </form>
      {state.bkline && !Q.normBudgetLine(state.bkline) && (
        <Notice tone="warn">"{state.bkline}" is not a budget line: give an agency code of one or two letters, a space or "-", then the line (e.g. P D018).</Notice>
      )}
      <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
        {q.data && (
          <>
            <Matched matched={Number(t.n)} what="book rows" />
            {Number(t.n) > 0 && (
              <table className="totals">
                <caption>
                  Totals over all {plural(t.n, "matching row")}
                  {Number(t.years) > 1 ? ` in ${t.years} books (each book's columns are its own years)` : ""}
                </caption>
                <tbody>
                  {[1, 2, 3, 4].map((k) => (
                    <tr key={k}>
                      <th scope="row">{yl(k)}</th>
                      <td className="num">{money(t[`y${k}`])}</td>
                    </tr>
                  ))}
                  {Number(t.negative_rows) > 0 && (
                    <tr>
                      <th scope="row">Reductions (negative amounts), already in the totals above</th>
                      <td className="num">
                        {plural(t.negative_rows, "row")} · {money(t.negative_y1)} in the book's year
                      </td>
                    </tr>
                  )}
                  {Number(t.vacant_rows) > 0 && (
                    <tr>
                      <th scope="row">Sponsor printed as a district with no member ("CD nn")</th>
                      <td className="num">{plural(t.vacant_rows, "row")}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
            {Number(t.n) > 0 && (
              <div className="table-wrap">
                <table className="rows">
                  <caption className="visually-hidden">Capital book rows, in book order</caption>
                  <thead>
                    <tr>
                      <th scope="col">FY</th>
                      <th scope="col">Project ID</th>
                      <th scope="col">Title (as printed)</th>
                      <th scope="col">Sponsor</th>
                      <th scope="col">Budget line</th>
                      <th scope="col">Boro</th>
                      <th scope="col">Agency</th>
                      {fy19 ? <th scope="col">Council district (FY2019 book)</th> : null}
                      {[1, 2, 3, 4].map((k) => (
                        <th key={k} scope="col" className="num">
                          {yl(k)}
                        </th>
                      ))}
                      <th scope="col">NYC Open Data</th>
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <BookRow
                        key={`${r.fiscal_year}|${r.part}|${r.pdf_page}|${r.row_in_page}`}
                        r={r}
                        fy19={fy19}
                        od={oq.data ? P.odForBookRow(oq.data.x, r) : null}
                        state={state}
                        go={go}
                        manifest={manifest}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <Pager page={state.bkpage} matched={Number(t.n)} onPage={(p) => set({ bkpage: p }, { keepPage: true })} />
          </>
        )}
      </Status>
    </section>
  );
}

const amountCell = (v) => (v == null ? <span className="muted">not printed</span> : Number(v) < 0 ? <span className="negative">{money(v)} (reduction)</span> : money(v));

function BookRow({ r, fy19, od, state, go, manifest }) {
  return (
    <tr>
      <td>
        {r.fiscal_year}
        <div className="muted small">Part {r.part}</div>
      </td>
      <td>
        <code>{r.sub_id}</code>
      </td>
      <td>
        {r.title} <ReviewedLabel status={r.status} /> <FlagBadge flags={r.flags} reviewId={r.review_id} />
        {r.description ? <div className="muted small">{r.description}</div> : null}
      </td>
      <td>
        {r.sponsor ? (
          P.isVacantDistrict(r.sponsor) ? (
            <>
              {r.sponsor} <div className="muted small">a district with no member when the book was printed</div>
            </>
          ) : (
            r.sponsor
          )
        ) : (
          <span className="muted">none printed</span>
        )}
      </td>
      <td>{r.budget_line}</td>
      <td>{r.boro}</td>
      <td className="small">{r.agency}</td>
      {fy19 ? <td>{r.council_district}</td> : null}
      <td className="num">{amountCell(r.amount_y1)}</td>
      <td className="num">{amountCell(r.amount_y2)}</td>
      <td className="num">{amountCell(r.amount_y3)}</td>
      <td className="num">{amountCell(r.amount_y4)}</td>
      <OdBookCell xs={od} />
      <td>
        <RowLinks state={state} go={go} manifest={manifest} row={r} label={`${r.sub_id} ${r.title}, FY${r.fiscal_year} ${money(r.amount_y1)}`} />
      </td>
    </tr>
  );
}

/** This row's own NYC Open Data matches (#205: keyed on the row's place where its ID is printed twice). */
function OdBookCell({ xs }) {
  if (!xs) return <td className="muted small">…</td>;
  if (!xs.length) {
    return (
      <td className="small">
        <StateBadge state="nocheck" title={tooltipOf(null)} />
      </td>
    );
  }
  return (
    <td className="small">
      {xs.map((x) => {
        const one = x.portal_row_id && !String(x.portal_row_id).includes(";");
        return (
          <div key={`${x.dataset_id}|${x.record_amount_fy}|${x.record_part ?? ""}`}>
            <StateBadge state={stateOf(x)} title={tooltipOf(x)} />{" "}
            <span className="muted">
              FY{x.record_amount_fy} · <a href={one ? rowUrl(x.dataset_id, x.portal_row_id) : datasetUrl(x.dataset_id)}>{one ? "see row" : x.dataset_id}</a>
            </span>
          </div>
        );
      })}
    </td>
  );
}
