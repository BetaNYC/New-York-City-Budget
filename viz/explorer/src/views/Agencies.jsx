import { useEffect, useMemo, useRef } from "react";

import { money, plural } from "../format.js";
import { change, pad3 } from "../query/agency.js";
import { agencyByYear, agencyList, agencyNames, agencyPath, agencyUnits, agenciesPath, cityByYear, citywidePath, fiscalYears, hasAgency, unitByYear, unitNames } from "../agency/data.js";
import { useAgencyJson } from "../agency/useAgencyJson.js";
import { resolveLegacy } from "../agency/legacy.js";
import { writeHash } from "../state/hash.js";
import { HashLink, Notice } from "../components/ui.jsx";
import { YearChart } from "../components/YearChart.jsx";
import { csvHref } from "../agency/csv.js";

/**
 * City agency budgets (#270, #286): every City agency's adopted and modified budget, by unit of
 * appropriation, FY2017 on, from NYC Open Data mwzb-yiwb (mcp/scripts/agency-budget.mjs).
 *
 * Read from small JSON files built from the same table (src/agency/data.js, #299), never DuckDB:
 * a first visit is well under 1 MB, where the query engine alone is about 33 MB.
 *
 * Three screens, one view: all agencies for a year (abfy), one agency's units (abag), one unit
 * across every year (abag + abunit). A figure that does not exist is words, never $0:
 * "Not yet published" for the newest year's modified budget, "Not in this year's budget" for a
 * unit the year's release does not have.
 *
 * The test contract (e2e/agencies.*.spec.js): root [data-view="agencies"], data-ready="true" once
 * the numbers are on screen; a <select> labeled "Fiscal year"; one polite live region; focus moves
 * to the new screen's heading after a move (not on first load, so Tab still reaches the skip link).
 */
export const NOT_PUBLISHED = "Not yet published";
export const NOT_IN_BUDGET = "Not in this year's budget";

export default function Agencies({ state, set, go }) {
  const yq = useAgencyJson([citywidePath()]);
  const city = yq.data?.[citywidePath()] ?? null;
  const years = useMemo(() => fiscalYears(city), [city]);
  // The build stamp, for the source note.
  const manifest = city ? { generated_at: city.generated_at } : null;
  const newest = years[0]?.fiscal_year ?? null;
  const fy = state.abfy && years.some((y) => y.fiscal_year === state.abfy) ? state.abfy : newest;
  const abag = state.abag ? pad3(state.abag) : "";
  const abunit = abag && state.abunit ? pad3(state.abunit) : "";

  useEffect(() => {
    document.title = "City agency budgets · NYC budget data · BetaNYC";
  }, []);

  if (yq.error) return <LoadError q={yq} />;
  if (!years.length) return <Root ready={false}><p className="muted">Loading…</p></Root>;
  if (state.legacy) return <Legacy state={state} set={set} go={go} fy={fy} />;
  const props = { state, set, go, fy, years, newest, abag, abunit, manifest };
  if (abag && abunit) return <UnitScreen {...props} />;
  if (abag) return <AgencyScreen {...props} />;
  return <ListScreen {...props} />;
}

/** A file that would not load, with a way to try again. */
function LoadError({ q }) {
  return (
    <Notice tone="error">
      The agency budgets could not be loaded: {String(q.error.message ?? q.error)}.{" "}
      <button type="button" className="linkish" onClick={q.retry}>
        Try again
      </button>
    </Notice>
  );
}

function Root({ ready, children }) {
  return (
    <section className="agencies" data-view="agencies" data-ready={ready ? "true" : "false"} aria-busy={ready ? undefined : "true"}>
      {children}
    </section>
  );
}

/** Words for a figure that does not exist; money otherwise. */
export function figure(v, { kind, year, newest }) {
  if (v !== null && v !== undefined) return money(v);
  if (kind === "modified" && year === newest) return NOT_PUBLISHED;
  return NOT_IN_BUDGET;
}

function Fig({ v, kind, year, newest }) {
  const text = figure(v, { kind, year, newest });
  return v === null || v === undefined ? <span className="words">{text}</span> : text;
}

function Change({ c }) {
  if (!c) return <span className="muted">—</span>;
  const sign = c.dollars > 0 ? "+" : c.dollars < 0 ? "−" : "";
  return (
    <span className={c.dollars < 0 ? "negative" : undefined}>
      {sign}
      {money(Math.abs(c.dollars))}
      {c.pct != null ? ` (${sign}${Math.abs(c.pct).toFixed(1)}%)` : ""}
    </span>
  );
}

/**
 * The screen last shown, across screens (each screen is its own component, so a per-component
 * "first render" can't tell a move from a first load). null until the first screen renders.
 */
let shownScreen = null;

/** The heading a screen opens with: focused after a move, not on the first load. */
function useFocusOnChange(key) {
  const ref = useRef(null);
  useEffect(() => {
    if (shownScreen !== null && shownScreen !== key) ref.current?.focus();
    shownScreen = key;
  }, [key]);
  return ref;
}

/** What screen readers hear after a change ("Showing FY2024, Police Department, 18 units"). */
function Live({ text }) {
  return (
    <p className="visually-hidden" aria-live="polite" aria-atomic="true">
      {text}
    </p>
  );
}

function YearPicker({ fy, years, set }) {
  return (
    <div className="filters agency-filters">
      <label className="field">
        <span>Fiscal year</span>
        <select value={fy} onChange={(e) => set({ abfy: Number(e.target.value) })}>
          {years.map((y) => (
            <option key={y.fiscal_year} value={y.fiscal_year}>
              FY{y.fiscal_year}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

function Crumbs({ items }) {
  return (
    <nav className="crumbs" aria-label="Where you are">
      <ol>
        {items.map(([label, href, onGo], i) => (
          <li key={i}>{href ? <HashLink href={href} onGo={onGo}>{label}</HashLink> : <span aria-current="page">{label}</span>}</li>
        ))}
      </ol>
    </nav>
  );
}

function SourceNote({ manifest }) {
  return (
    <p className="muted small source-note">
      Source: NYC Open Data, <a href="https://data.cityofnewyork.us/d/mwzb-yiwb">Expense Budget (mwzb-yiwb)</a>, published by the Mayor's Office of Management and
      Budget. Adopted is the budget the City adopted in June for that fiscal year. Modified is the same budget as of the end of the year, from the next June's
      release. Amounts are gross: they include money one City agency pays another (intra-city transfers), so they add up to more than the City's headline net
      budget. This is the budget, not spending: for what was paid, see <a href="https://www.checkbooknyc.com/">Checkbook NYC</a>. The same figures are in the{" "}
      <a href="../mcp.html">budget MCP server</a>.{manifest?.generated_at ? ` Data built ${manifest.generated_at.slice(0, 10)}.` : ""}
      {/* TODO(#270): link the cross-repo "What's changed" log here when that standard lands. */}
    </p>
  );
}

function Downloads({ rows, columns, name }) {
  return (
    <p className="downloads">
      <a className="button-link" href={csvHref(rows, columns)} download={name}>
        Download this table (CSV)
      </a>{" "}
      <a className="button-link" href="../agencies/data/nyc_budget.csv" download>
        Download every agency and year (CSV)
      </a>
    </p>
  );
}

// ---------------------------------------------------------------- all agencies

function ListScreen({ state, set, go, fy, years, newest, manifest }) {
  const q = useAgencyJson([agenciesPath()]);
  const heading = useFocusOnChange("list");
  const ready = !q.loading && !q.error && Boolean(q.data);
  const first = years.at(-1)?.fiscal_year;
  const rows = useMemo(() => {
    if (!q.data) return [];
    const all = q.data[agenciesPath()];
    const prev = new Map(agencyList(all, fy - 1).map((r) => [r.agency_number, r]));
    const earlier = new Set(years.filter((y) => y.fiscal_year < fy).flatMap((y) => agencyList(all, y.fiscal_year).map((r) => r.agency_number)));
    return agencyList(all, fy).map((r) => ({ ...r, prev: prev.get(r.agency_number) ?? null, seenBefore: earlier.has(r.agency_number) }));
  }, [q.data, fy, years]);
  const cityRows = cityByYear(q.data?.[citywidePath()]);
  return (
    <Root ready={ready}>
      <h2 ref={heading} tabIndex={-1}>
        All City agencies
      </h2>
      <p className="lede">
        How much each City agency was given in the budget the City adopted, and how that budget stood a year later. Pick an agency to see its units of
        appropriation, the lines the Council votes on.
      </p>
      <Explainer />
      {q.error ? <LoadError q={q} /> : null}
      {ready ? (
        <section className="trend" aria-labelledby="trend-h">
          <h3 id="trend-h">The whole city, over time</h3>
          <CitySummary rows={cityRows} newest={newest} />
          <ByYear
            rows={cityRows}
            years={years}
            newest={newest}
            title="New York City budget"
            noun="figure"
            caption={`New York City budget, all agencies: adopted and modified by fiscal year, FY${first}–FY${newest}`}
          />
        </section>
      ) : null}
      <section className="one-year" aria-labelledby="one-year-h">
        <h3 id="one-year-h">Agencies in FY{fy}</h3>
        <YearPicker fy={fy} years={years} set={set} />
        <Live text={ready ? `Showing FY${fy}, all agencies, ${plural(rows.length, "agency", "agencies")}.` : ""} />
        {ready ? (
          <>
            <table className="rows stack agency-table">
              <caption>
                Adopted and modified budgets by agency, FY{fy} ({plural(rows.length, "agency", "agencies")}, largest adopted first)
              </caption>
              <thead>
                <tr>
                  <th scope="col">Agency</th>
                  <th scope="col" className="num">Adopted FY{fy}</th>
                  <th scope="col" className="num">Adopted vs. FY{fy - 1} adopted</th>
                  <th scope="col" className="num">Modified FY{fy}</th>
                  <th scope="col" className="num">Modified vs. adopted</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.agency_number}>
                    <th scope="row">
                      <HashLink href={writeHash({ ...state, abfy: fy, abag: r.agency_number, abunit: "" })} onGo={() => go({ abfy: fy, abag: r.agency_number, abunit: "" })}>
                        {r.agency_name}
                      </HashLink>{" "}
                      <span className="muted small">{r.agency_number}</span>
                    </th>
                    <td className="num" data-label={`Adopted FY${fy}`}>
                      <Fig v={r.adopted} kind="adopted" year={fy} newest={newest} />
                    </td>
                    <td className="num" data-label={`Adopted vs. FY${fy - 1} adopted`}>
                      <VsLastYear prevRow={r.prev} row={r} year={fy} first={first} noun="agency" seenBefore={r.seenBefore} />
                    </td>
                    <td className="num" data-label={`Modified FY${fy}`}>
                      <Fig v={r.modified} kind="modified" year={fy} newest={newest} />
                    </td>
                    <td className="num" data-label="Modified vs. adopted">
                      <VsAdopted row={r} year={fy} newest={newest} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Downloads
              rows={rows}
              name={`nyc-agency-budgets-fy${fy}.csv`}
              columns={[["Fiscal year", () => fy], ["Agency number", "agency_number"], ["Agency", "agency_name"], ["Adopted", "adopted"], ["Modified", "modified"]]}
            />
          </>
        ) : !q.error ? (
          <p className="muted" role="status">Loading FY{fy}…</p>
        ) : null}
      </section>
      <SourceNote manifest={manifest} />
    </Root>
  );
}

/** What adopted and modified mean (#306): the full box on the list page. */
export const EXPLAINER_ID = "adopted-modified";
function Explainer() {
  return (
    <section className="explainer" id={EXPLAINER_ID} aria-labelledby={`${EXPLAINER_ID}-h`}>
      <h3 id={`${EXPLAINER_ID}-h`}>What adopted and modified mean</h3>
      <dl>
        <dt>Adopted</dt>
        <dd>The budget the Mayor and City Council agree on in June, before the fiscal year starts. The plan.</dd>
        <dt>Modified</dt>
        <dd>The same budget as it stood the next June, near the end of the year, after the City moved money around. Closer to what happened.</dd>
      </dl>
      <p>
        The gap between the two lines shows where plans changed during the year. NYC's fiscal year runs July 1 to June 30, so FY2026 is July 2025 to June
        2026.
      </p>
    </section>
  );
}

/** The one-line version on an agency page, with a link to the full box. */
function ExplainerNote({ state, go }) {
  return (
    <p className="explainer-note">
      Adopted is the plan agreed in June; modified is that budget a year later, after the City moved money around.{" "}
      <HashLink href={writeHash({ ...state, abag: "", abunit: "" })} onGo={() => go({ abag: "", abunit: "" })}>
        What adopted and modified mean
      </HashLink>
    </p>
  );
}

/**
 * The citywide trend in one line (#306): first year to newest adopted, and the newest modified
 * figure against its own adopted. Not tied to the year picker, which only changes Section 2.
 */
function CitySummary({ rows, newest }) {
  const a = rows.filter((r) => r.adopted != null);
  const m = rows.filter((r) => r.modified != null).at(-1);
  if (!a.length) return null;
  const [lo, hi] = [a[0], a.at(-1)];
  const pct = pctText(lo.adopted, hi.adopted);
  return (
    <p className="big citywide-summary">
      Adopted: <strong>{money(lo.adopted)}</strong> in FY{lo.fiscal_year}, <strong>{money(hi.adopted)}</strong> in FY{hi.fiscal_year}
      {pct ? ` (${pct})` : ""}.
      {m ? (
        <>
          {" "}
          Modified: <strong>{money(m.modified)}</strong> in FY{m.fiscal_year}
          {pctText(m.adopted, m.modified) ? ` (${pctText(m.adopted, m.modified)} vs. FY${m.fiscal_year} adopted)` : ""}.
        </>
      ) : null}
      {hi.fiscal_year === newest && hi.modified == null ? ` FY${newest} modified: ${NOT_PUBLISHED.toLowerCase()}.` : ""}
    </p>
  );
}

/** "+3.0%" / "−1.2%" from one figure to the next, or null when either is missing. */
export function pctText(from, to) {
  const c = change(from, to);
  if (!c || c.pct == null) return null;
  const sign = c.pct > 0 ? "+" : c.pct < 0 ? "−" : "";
  return `${sign}${Math.abs(c.pct).toFixed(1)}%`;
}

// ---------------------------------------------------------------- one agency

/**
 * The chart, then a table of the same numbers, open (#306). The trend table (list and agency
 * pages) has Year · Adopted · vs. year before · Modified · Modified vs. adopted; `simple` (the
 * unit page, unchanged by #306) keeps Year · Adopted · Modified · Modified minus adopted.
 */
function ByYear({ rows, years, newest, title, caption, noun, simple = false }) {
  const byYear = new Map(rows.map((r) => [Number(r.fiscal_year), r]));
  const all = [...years].map((y) => y.fiscal_year).sort((a, b) => a - b);
  const series = all.map((y) => {
    const r = byYear.get(y);
    return { year: y, row: r ?? null, adopted: r?.adopted ?? null, modified: r?.modified ?? null };
  });
  const first = all[0];
  return (
    <>
      <YearChart series={series} title={title} newest={newest} />
      <table className="rows stack agency-years">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Fiscal year</th>
            <th scope="col" className="num">Adopted</th>
            {simple ? null : <th scope="col" className="num">Adopted vs. year before</th>}
            <th scope="col" className="num">Modified</th>
            <th scope="col" className="num">{simple ? "Modified minus adopted" : "Modified vs. adopted"}</th>
          </tr>
        </thead>
        <tbody>
          {series.map((s, i) => (
            <tr key={s.year}>
              <th scope="row">FY{s.year}</th>
              <td className="num" data-label="Adopted">
                <Fig v={s.adopted} kind="adopted" year={s.year} newest={newest} />
              </td>
              {simple ? null : (
                <td className="num" data-label={`Adopted vs. FY${s.year - 1} adopted`}>
                  <VsLastYear prevRow={series[i - 1]?.row ?? null} row={s.row} year={s.year} first={first} noun={noun} seenBefore={series.slice(0, i).some((p) => p.row)} />
                </td>
              )}
              <td className="num" data-label="Modified">
                <Fig v={s.modified} kind="modified" year={s.year} newest={newest} />
              </td>
              <td className="num" data-label={simple ? "Modified minus adopted" : "Modified vs. adopted"}>
                {simple ? <Change c={change(s.adopted, s.modified)} /> : <VsAdopted row={s.row} year={s.year} newest={newest} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/**
 * Adopted against the year before's adopted, or why there is no change to show (#306): never a
 * bare dash. `noun` names what is new ("agency", "unit"); `seenBefore` is false when nothing came
 * before (a row missing from an earlier year then present is "Not in the FY… budget", not new).
 */
export function vsLastYearWords({ prevRow, row, year, first, noun, seenBefore = Boolean(prevRow) }) {
  if (!row || row.adopted == null) return `No FY${year} adopted figure`;
  if (year === first) return `No FY${year - 1} figure`;
  if (!prevRow && noun && noun !== "figure" && !seenBefore) return `New ${noun} in FY${year}`;
  if (!prevRow) return `Not in the FY${year - 1} budget`;
  if (prevRow.adopted == null) return `No FY${year - 1} adopted figure`;
  return null;
}

function VsLastYear(props) {
  const words = vsLastYearWords(props);
  if (words) return <span className="words">{words}</span>;
  return <Change c={change(props.prevRow.adopted, props.row.adopted)} />;
}

/** Modified against the same year's adopted, or why not: the newest year is not published yet. */
export function vsAdoptedWords({ row, year, newest }) {
  if (!row) return NOT_IN_BUDGET;
  if (row.modified == null) return year === newest ? NOT_PUBLISHED : `No FY${year} modified figure`;
  if (row.adopted == null) return `No FY${year} adopted figure`;
  return null;
}

function VsAdopted(props) {
  const words = vsAdoptedWords(props);
  if (words) return <span className="words">{words}</span>;
  return <Change c={change(props.row.adopted, props.row.modified)} />;
}

/**
 * One agency's file, once agencies.json says the agency exists (an unknown number shows "No
 * agency" without asking the server for a file that is not there). data is { path: object }; an
 * unknown agency gives data with no file in it.
 */
function useAgencyFile(abag) {
  const list = useAgencyJson([agenciesPath()]);
  const known = list.data ? hasAgency(list.data[agenciesPath()], abag) : undefined;
  const one = useAgencyJson([known ? agencyPath(abag) : null]);
  if (list.loading || list.error || known === undefined) return list;
  return known ? one : { ...list, data: {} };
}

function AgencyScreen({ state, set, go, fy, years, newest, abag, manifest }) {
  const q = useAgencyFile(abag);
  const heading = useFocusOnChange(`agency|${abag}`);
  const ready = !q.loading && !q.error && Boolean(q.data);
  const file = q.data?.[agencyPath(abag)];
  const first = years.at(-1)?.fiscal_year;
  const units = useMemo(() => {
    const prev = new Map(agencyUnits(file, fy - 1).map((u) => [u.unit_number, u]));
    const all = file?.units ?? [];
    return agencyUnits(file, fy).map((u) => {
      const yrs = all.find((x) => x.unit_number === u.unit_number)?.years ?? [];
      return { ...u, prev: prev.get(u.unit_number) ?? null, seenBefore: yrs.some((y) => y.fiscal_year < fy) };
    });
  }, [file, fy]);
  const byYear = agencyByYear(file);
  const name = byYear.find((r) => Number(r.fiscal_year) === fy)?.agency_name ?? byYear.at(-1)?.agency_name ?? `Agency ${abag}`;
  const listHref = writeHash({ ...state, abfy: fy, abag: "", abunit: "" });
  if (ready && byYear.length === 0) {
    return (
      <Root ready>
        <h2 ref={heading} tabIndex={-1}>No agency {abag}</h2>
        <Notice>No City agency has the number {abag} in these budgets. <HashLink href={listHref} onGo={() => go({ abag: "", abunit: "" })}>See all agencies</HashLink>.</Notice>
      </Root>
    );
  }
  return (
    <Root ready={ready}>
      <Crumbs items={[["All agencies", listHref, () => go({ abag: "", abunit: "" })], [name]]} />
      <h2 ref={heading} tabIndex={-1}>
        {name} <span className="muted small">agency {abag}</span>
      </h2>
      <ExplainerNote state={{ ...state, abfy: fy }} go={go} />
      {q.error ? <LoadError q={q} /> : null}
      {ready ? (
        <section className="trend" aria-labelledby="trend-h">
          <h3 id="trend-h">{name}, over time</h3>
          <ByYear rows={byYear} years={years} newest={newest} title={name} noun="agency" caption={`${name}: adopted and modified by fiscal year, FY${first}–FY${newest}`} />
        </section>
      ) : null}
      <section className="one-year" aria-labelledby="one-year-h">
        <h3 id="one-year-h">Its units in FY{fy}</h3>
        <YearPicker fy={fy} years={years} set={set} />
        <Live text={ready ? `Showing FY${fy}, ${name}, ${plural(units.length, "unit")}.` : ""} />
        {ready ? (
          <>
            {units.length === 0 ? (
              <Notice>{name} has no unit in the FY{fy} budget.</Notice>
            ) : (
              <table className="rows stack agency-table">
                <caption>
                  {name}: adopted and modified budget by unit of appropriation, FY{fy} ({plural(units.length, "unit")})
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Unit of appropriation</th>
                    <th scope="col" className="num">Adopted FY{fy}</th>
                    <th scope="col" className="num">Adopted vs. FY{fy - 1} adopted</th>
                    <th scope="col" className="num">Modified FY{fy}</th>
                    <th scope="col" className="num">Modified vs. adopted</th>
                  </tr>
                </thead>
                <tbody>
                  {units.map((u) => (
                    <tr key={u.unit_number}>
                      <th scope="row">
                        <HashLink href={writeHash({ ...state, abfy: fy, abag, abunit: u.unit_number })} onGo={() => go({ abfy: fy, abag, abunit: u.unit_number })}>
                          {u.unit_number} {u.unit_name}
                        </HashLink>
                      </th>
                      <td className="num" data-label={`Adopted FY${fy}`}>
                        <Fig v={u.adopted} kind="adopted" year={fy} newest={newest} />
                      </td>
                      <td className="num" data-label={`Adopted vs. FY${fy - 1} adopted`}>
                        <VsLastYear prevRow={u.prev} row={u} year={fy} first={first} noun="unit" seenBefore={u.seenBefore} />
                      </td>
                      <td className="num" data-label={`Modified FY${fy}`}>
                        <Fig v={u.modified} kind="modified" year={fy} newest={newest} />
                      </td>
                      <td className="num" data-label="Modified vs. adopted">
                        <VsAdopted row={u} year={fy} newest={newest} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <Downloads
              rows={units}
              name={`nyc-agency-${abag}-fy${fy}.csv`}
              columns={[["Fiscal year", () => fy], ["Agency number", () => abag], ["Agency", "agency_name"], ["Unit number", "unit_number"], ["Unit", "unit_name"], ["Adopted", "adopted"], ["Modified", "modified"], ["Adopted release", "adopted_release"], ["Modified release", "modified_release"]]}
            />
          </>
        ) : !q.error ? (
          <p className="muted" role="status">Loading…</p>
        ) : null}
      </section>
      <SourceNote manifest={manifest} />
    </Root>
  );
}

// ---------------------------------------------------------------- one unit

function UnitScreen({ state, set, go, fy, years, newest, abag, abunit, manifest }) {
  const q = useAgencyFile(abag);
  const heading = useFocusOnChange(`unit|${abag}|${abunit}`);
  const ready = !q.loading && !q.error && Boolean(q.data);
  const byYear = unitByYear(q.data?.[agencyPath(abag)], abunit);
  const latest = byYear.at(-1);
  const agencyName = latest?.agency_name ?? `Agency ${abag}`;
  const unitName = latest?.unit_name ?? "";
  const listHref = writeHash({ ...state, abfy: fy, abag: "", abunit: "" });
  const agencyHref = writeHash({ ...state, abfy: fy, abag, abunit: "" });
  if (ready && byYear.length === 0) {
    return (
      <Root ready>
        <h2 ref={heading} tabIndex={-1}>No unit {abunit} in agency {abag}</h2>
        <Notice>
          These budgets have no unit {abunit} in agency {abag}. <HashLink href={agencyHref} onGo={() => go({ abunit: "" })}>See agency {abag}</HashLink>.
        </Notice>
      </Root>
    );
  }
  return (
    <Root ready={ready}>
      <Crumbs items={[["All agencies", listHref, () => go({ abag: "", abunit: "" })], [agencyName, agencyHref, () => go({ abunit: "" })], [`${abunit} ${unitName}`]]} />
      <h2 ref={heading} tabIndex={-1}>
        {abunit} {unitName} <span className="muted small">{agencyName}</span>
      </h2>
      <p className="lede">One unit of appropriation, every year: the budget adopted for it, and the modified budget a year later.</p>
      <Live text={ready ? `Showing ${agencyName}, unit ${abunit} ${unitName}, every year.` : ""} />
      {q.error ? <LoadError q={q} /> : null}
      {ready ? (
        <>
          <ByYear simple rows={byYear} years={years} newest={newest} title={`${agencyName}, ${abunit} ${unitName}`} caption={`${agencyName}, unit ${abunit} ${unitName}: adopted and modified by fiscal year`} />
          <Downloads
            rows={byYear}
            name={`nyc-agency-${abag}-unit-${abunit}.csv`}
            columns={[["Fiscal year", "fiscal_year"], ["Agency number", () => abag], ["Agency", "agency_name"], ["Unit number", () => abunit], ["Unit", "unit_name"], ["Adopted", "adopted"], ["Modified", "modified"], ["Adopted release", "adopted_release"], ["Modified release", "modified_release"]]}
          />
        </>
      ) : !q.error ? (
        <p className="muted" role="status">Loading…</p>
      ) : null}
      <SourceNote manifest={manifest} />
    </Root>
  );
}

// ---------------------------------------------------------------- old /agencies/ links

function Legacy({ state, set, go, fy }) {
  // The agency first, from every name in agencies.json; then, for a unit, that agency's file.
  const [agencyPart = "", unitPart = ""] = String(state.legacy ?? "").split("/");
  const aq = useAgencyJson([agenciesPath()]);
  const found = useMemo(() => (aq.data ? resolveLegacy(agencyPart, agencyNames(aq.data[agenciesPath()])) : undefined), [aq.data, agencyPart]);
  const fq = useAgencyJson([found && unitPart ? agencyPath(found.abag) : null]);
  const q = aq.error ? aq : fq;
  const r = useMemo(() => {
    if (found === undefined) return undefined;
    if (found === null || !unitPart) return found;
    const file = fq.data?.[agencyPath(found.abag)];
    return file ? resolveLegacy(state.legacy, unitNames(file)) ?? found : undefined;
  }, [found, unitPart, fq.data, state.legacy]);
  const resolved = r && r.candidates.length === 0;
  useEffect(() => {
    // Replace, not push: the old link becomes the new address, and Back leaves the page.
    if (resolved) set({ legacy: "", abfy: state.abfy, abag: r.abag, abunit: r.abunit });
  }, [resolved]); // eslint-disable-line react-hooks/exhaustive-deps
  if (q.error) return <LoadError q={q} />;
  if (r === undefined || resolved) return <Root ready={false}><p className="muted" role="status">Opening your link…</p></Root>;
  const listHref = writeHash({ ...state, legacy: "", abag: "", abunit: "" });
  if (r === null) {
    return (
      <Root ready>
        <h2>We could not find that agency</h2>
        <Notice>
          This link is from the old City agency budgets page, and no agency in these budgets has the name in it (<code>{state.legacy}</code>).{" "}
          <HashLink href={listHref} onGo={() => set({ legacy: "", abag: "", abunit: "" })}>See all agencies for FY{fy}</HashLink>.
        </Notice>
      </Root>
    );
  }
  return (
    <Root ready>
      <h2>Which unit did you mean?</h2>
      <p>The old page gave these units of appropriation the same link. Pick one:</p>
      <ul>
        {r.candidates.map((c) => (
          <li key={c.unit_number}>
            <HashLink href={writeHash({ ...state, legacy: "", abag: r.abag, abunit: c.unit_number })} onGo={() => set({ legacy: "", abag: r.abag, abunit: c.unit_number })}>
              Unit {c.unit_number}: {c.unit_name}
            </HashLink>
          </li>
        ))}
      </ul>
      <p>
        <HashLink href={writeHash({ ...state, legacy: "", abag: r.abag, abunit: "" })} onGo={() => set({ legacy: "", abag: r.abag, abunit: "" })}>
          Or see the whole agency
        </HashLink>
        .
      </p>
    </Root>
  );
}

