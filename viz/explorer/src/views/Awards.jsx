import { Fragment } from "react";

import { useQueries } from "../duckdb/useDuckDB.js";
import { DISCLOSURE_FLAG_NOTE, OTHER_STATUS_NOTE, STATUS_LABEL, count, money, plural } from "../format.js";
import * as Q from "../query/sql.js";
import { disclosureFilters, writeHash } from "../state/hash.js";
import { HashLink, Matched, NoData, Notice, Pager, SelectFilter, Status, TextFilter } from "../components/ui.jsx";
import { SC_SIDE_LABEL } from "../query/pdf.js";
import { ScCell, ScOnlyResults, ScPanel, scYearsOf, useScForRows } from "./ScheduleC.jsx";

/**
 * Browse and search the Council's expense funding disclosure. Totals cover every matching row;
 * the table shows one page, highest amount first (the MCP's order).
 */
export default function Awards({ state, set, go, years, pdfYears }) {
  const f = disclosureFilters(state);
  const scYears = scYearsOf(pdfYears);
  const scOnly = state.scside === "pdf_only" && scYears.length > 0;
  const yearRow = state.fy != null ? years.find((y) => y.fiscal_year === state.fy) : null;
  const notLoaded = yearRow && !yearRow.loaded;
  const key = JSON.stringify([f, state.page]);
  const q = useQueries(true, key, () =>
    notLoaded || scOnly
      ? null
      : {
          totals: Q.disclosureTotalsQuery(f),
          flags: Q.disclosureFlagsQuery(f),
          rows: Q.disclosureRowsQuery(f, state.page),
        }
  );

  const yearOptions = [
    ["", "All years"],
    ...years.map((y) => [String(y.fiscal_year), `FY${y.fiscal_year}${y.loaded ? (y.early_snapshot ? " (early snapshot)" : "") : " (not loaded)"}`]),
  ];

  return (
    <section>
      <h2>Expense awards</h2>
      <p className="lede">
        The Council's own expense funding disclosure: one row per designation it publishes, with the grantee, EIN, amount, clearance status and the
        Council member listed. <code>council_member</code> is the roster when the workbook was exported, not necessarily the sponsor at adoption.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Fiscal year" value={state.fy ?? ""} options={yearOptions} onApply={(v) => set({ fy: v === "" ? null : Number(v) })} />
        <SelectFilter
          label="Status"
          value={state.status}
          options={[["", "Any status"], ...Q.DISCLOSURE_STATUSES.map((s) => [s, STATUS_LABEL[s]])]}
          onApply={(v) => set({ status: v })}
        />
        <TextFilter label="Organization" value={state.legal_name} onApply={(v) => set({ legal_name: v })} placeholder="e.g. food bank" />
        <TextFilter label="EIN" value={state.ein} onApply={(v) => set({ ein: v })} placeholder="13-3179546" width="9rem" />
        <TextFilter label="Council member" value={state.council_member} onApply={(v) => set({ council_member: v })} placeholder="surname" />
        <TextFilter label="Agency" value={state.agency} onApply={(v) => set({ agency: v })} placeholder="DYCD" width="8rem" />
        <TextFilter label="Program" value={state.program_name} onApply={(v) => set({ program_name: v })} />
        <TextFilter label="Funding source" value={state.source} onApply={(v) => set({ source: v })} placeholder="Local, Youth, …" />
        <TextFilter label="Min $" type="number" value={state.min ?? ""} onApply={(v) => set({ min: v === "" ? null : Number(v) })} width="7rem" />
        <TextFilter label="Max $" type="number" value={state.max ?? ""} onApply={(v) => set({ max: v === "" ? null : Number(v) })} width="7rem" />
        {scYears.length > 0 && (
          <SelectFilter
            label="Schedule C (PDF)"
            value={state.scside}
            options={[["", "Any"], ...["matched", "disclosure_only", "pdf_only"].map((k) => [k, SC_SIDE_LABEL[k]])]}
            onApply={(v) => set({ scside: v })}
          />
        )}
      </form>
      <ScPanel fy={state.fy} scYears={scYears} set={set} />

      {scOnly ? (
        <ScOnlyResults f={f} state={state} set={set} go={go} />
      ) : notLoaded ? (
        <NoData year={state.fy} what="expense award" reason={yearRow.note} />
      ) : (
        <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
          {q.data && <Results data={q.data} state={state} set={set} go={go} years={years} scYears={scYears} />}
        </Status>
      )}
    </section>
  );
}

function Results({ data, state, set, go, years, scYears }) {
  const sc = useScForRows(data.rows, scYears);
  const r = Q.rollupDisclosure(data.totals);
  const matchedYears = r.by_year.map((y) => y.fiscal_year);
  const early = years.filter((y) => y.early_snapshot && matchedYears.includes(y.fiscal_year));
  const otherYears = r.by_year.filter((y) => y.totals.other.rows > 0).map((y) => y.fiscal_year);
  const noHeadline = early.length > 0 || otherYears.length > 0;
  return (
    <>
      <Matched matched={r.matched} what="awards" />
      {r.matched > 0 && (
        <table className="totals">
          <caption>Totals over all {count(r.matched)} matching rows</caption>
          <tbody>
            {Q.DISCLOSURE_STATUSES.filter((s) => s !== "other" || r.totals.other.rows > 0).map((s) => (
              <tr key={s}>
                <th scope="row">
                  {STATUS_LABEL[s]}
                  {s === "cleared" && noHeadline ? " (not a headline figure: see note)" : ""}
                </th>
                <td>{plural(r.totals[s].rows, "row")}</td>
                <td className="num">{money(r.totals[s].amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {early.length > 0 && (
        <Notice tone="warn">
          <strong>Early snapshot{early.length > 1 ? "s" : ""}:</strong>{" "}
          {early.map((y) => (
            <Fragment key={y.fiscal_year}>
              FY{y.fiscal_year}: {y.note || "frozen while many designations were still pending."}{" "}
            </Fragment>
          ))}
          Do not headline {early.length > 1 ? "their" : "its"} Cleared total.
        </Notice>
      )}
      {otherYears.length > 0 && <Notice tone="warn">{OTHER_STATUS_NOTE}</Notice>}
      {matchedYears.length > 1 && state.fy == null && r.matched > 0 && (
        <p className="muted">These totals add up {matchedYears.length} fiscal years. Each year is a separate Council workbook; see Years for the per-year view.</p>
      )}
      {data.flags.length > 0 && (
        <ul className="flags">
          {data.flags.map((fl) => (
            <li key={fl.row_flag}>
              {plural(fl.n, "matching row")} ({money(fl.amount)}) flagged <code>{fl.row_flag}</code>:{" "}
              {fl.row_flag
                .split(";")
                .map((x) => DISCLOSURE_FLAG_NOTE[x] ?? x)
                .join(" ")}{" "}
              Counted in the totals.
            </li>
          ))}
        </ul>
      )}
      {r.matched > 0 && (
        <>
          <div className="table-wrap">
            <table className="rows">
              <thead>
                <tr>
                  <th scope="col">FY</th>
                  <th scope="col">Organization</th>
                  <th scope="col">EIN</th>
                  <th scope="col">Council member</th>
                  <th scope="col">Funding source</th>
                  <th scope="col">Agency</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="num">
                    Amount
                  </th>
                  {sc ? <th scope="col">Schedule C (PDF)</th> : null}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => {
                  const target = { view: "award", ay: row.fiscal_year, row: row.source_row };
                  return (
                    <tr key={`${row.fiscal_year}:${row.source_row}`}>
                      <td>{row.fiscal_year}</td>
                      <td>
                        <HashLink href={writeHash({ ...state, ...target })} onGo={() => go(target)}>
                          {row.legal_name || "(no name printed)"}
                        </HashLink>
                        {row.program_name ? <div className="muted small">{row.program_name}</div> : null}
                      </td>
                      <td>{row.ein || <span className="muted">none printed</span>}</td>
                      <td>{row.council_member}</td>
                      <td>{row.source}</td>
                      <td>{row.agency}</td>
                      <td>{row.status}</td>
                      <td className="num">{money(row.amount)}</td>
                      {sc ? (
                        <ScCell
                          m={sc.get(`${Number(row.fiscal_year)}|${Number(row.source_row)}`)}
                          state={state}
                          go={go}
                          inYear={scYears.some((y) => y.fiscal_year === Number(row.fiscal_year))}
                        />
                      ) : null}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Pager page={state.page} matched={r.matched} onPage={(p) => set({ page: p }, { keepPage: true })} />
        </>
      )}
    </>
  );
}
