import { useEffect, useMemo, useRef } from "react";

import { useQueries } from "../duckdb/useDuckDB.js";
import { money, plural } from "../format.js";
import { agencyFiscalYearsQuery, agencyListQuery, agencyNamesQuery, agencyUnitsQuery, agencyYearsQuery, change, pad3 } from "../query/agency.js";
import { resolveLegacy } from "../agency/legacy.js";
import { writeHash } from "../state/hash.js";
import { HashLink, Notice } from "../components/ui.jsx";
import { YearChart } from "../components/YearChart.jsx";
import { csvHref } from "../agency/csv.js";

/**
 * City agency budgets (#270, #286): every City agency's adopted and modified budget, by unit of
 * appropriation, FY2017 on, from NYC Open Data mwzb-yiwb (mcp/scripts/agency-budget.mjs).
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

export default function Agencies({ state, set, go, manifest }) {
  const yq = useQueries(true, "agency-years", () => ({ years: agencyFiscalYearsQuery() }));
  const years = useMemo(() => (yq.data?.years ?? []).map((r) => ({ fiscal_year: Number(r.fiscal_year), has_modified: Boolean(r.has_modified) })), [yq.data]);
  const newest = years[0]?.fiscal_year ?? null;
  const fy = state.abfy && years.some((y) => y.fiscal_year === state.abfy) ? state.abfy : newest;
  const abag = state.abag ? pad3(state.abag) : "";
  const abunit = abag && state.abunit ? pad3(state.abunit) : "";

  useEffect(() => {
    document.title = "City agency budgets · NYC budget data · BetaNYC";
  }, []);

  if (yq.error) return <Notice tone="error">{String(yq.error.message ?? yq.error)}</Notice>;
  if (!years.length) return <Root ready={false}><p className="muted">Loading…</p></Root>;
  if (state.legacy) return <Legacy state={state} set={set} go={go} fy={fy} />;
  const props = { state, set, go, fy, years, newest, abag, abunit, manifest };
  if (abag && abunit) return <UnitScreen {...props} />;
  if (abag) return <AgencyScreen {...props} />;
  return <ListScreen {...props} />;
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
  const q = useQueries(true, `agency-list|${fy}`, () => ({
    now: agencyListQuery({ abfy: fy }),
    prev: years.some((y) => y.fiscal_year === fy - 1) ? agencyListQuery({ abfy: fy - 1 }) : null,
    city: agencyYearsQuery({ abag: "", abunit: "" }),
  }));
  const heading = useFocusOnChange("list");
  const ready = !q.loading && !q.error && Boolean(q.data);
  const rows = useMemo(() => {
    if (!q.data) return [];
    const prev = new Map((q.data.prev ?? []).map((r) => [r.agency_number, r]));
    return q.data.now.map((r) => ({ ...r, prevAdopted: prev.get(r.agency_number)?.adopted ?? null }));
  }, [q.data]);
  const city = q.data?.city?.find((r) => Number(r.fiscal_year) === fy);
  return (
    <Root ready={ready}>
      <h2 ref={heading} tabIndex={-1}>
        All City agencies, FY{fy}
      </h2>
      <p className="lede">
        How much each City agency was given in the budget the City adopted, and how that budget stood a year later (the modified budget). Pick an agency to see its
        units of appropriation, the lines the Council votes on.
      </p>
      <YearPicker fy={fy} years={years} set={set} />
      <Live text={ready ? `Showing FY${fy}, all agencies, ${plural(rows.length, "agency", "agencies")}.` : ""} />
      {q.error ? <Notice tone="error">{String(q.error.message ?? q.error)}</Notice> : null}
      {ready ? (
        <>
          {city ? (
            <p className="big">
              Citywide, FY{fy}: adopted <strong>{money(city.adopted)}</strong>; modified <strong><Fig v={city.modified} kind="modified" year={fy} newest={newest} /></strong>.
            </p>
          ) : null}
          <table className="rows stack agency-table">
            <caption>
              Adopted and modified budgets by agency, FY{fy} ({plural(rows.length, "agency", "agencies")}, largest adopted first)
            </caption>
            <thead>
              <tr>
                <th scope="col">Agency</th>
                <th scope="col" className="num">Adopted FY{fy}</th>
                <th scope="col" className="num">Modified FY{fy}</th>
                <th scope="col" className="num">Adopted change from FY{fy - 1}</th>
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
                  <td className="num" data-label={`Modified FY${fy}`}>
                    <Fig v={r.modified} kind="modified" year={fy} newest={newest} />
                  </td>
                  <td className="num" data-label={`Adopted change from FY${fy - 1}`}>
                    <Change c={change(r.prevAdopted, r.adopted)} />
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
      <SourceNote manifest={manifest} />
    </Root>
  );
}

// ---------------------------------------------------------------- one agency

function ByYear({ rows, years, newest, title, caption }) {
  const byYear = new Map(rows.map((r) => [Number(r.fiscal_year), r]));
  const all = [...years].map((y) => y.fiscal_year).sort((a, b) => a - b);
  const series = all.map((y) => {
    const r = byYear.get(y);
    return { year: y, adopted: r?.adopted ?? null, modified: r?.modified ?? null };
  });
  return (
    <>
      <YearChart series={series} title={title} newest={newest} />
      <table className="rows stack agency-years">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Fiscal year</th>
            <th scope="col" className="num">Adopted</th>
            <th scope="col" className="num">Modified</th>
            <th scope="col" className="num">Modified minus adopted</th>
          </tr>
        </thead>
        <tbody>
          {series.map((s) => (
            <tr key={s.year}>
              <th scope="row">FY{s.year}</th>
              <td className="num" data-label="Adopted">
                <Fig v={s.adopted} kind="adopted" year={s.year} newest={newest} />
              </td>
              <td className="num" data-label="Modified">
                <Fig v={s.modified} kind="modified" year={s.year} newest={newest} />
              </td>
              <td className="num" data-label="Modified minus adopted">
                <Change c={change(s.adopted, s.modified)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function AgencyScreen({ state, set, go, fy, years, newest, abag, manifest }) {
  const q = useQueries(true, `agency|${abag}|${fy}`, () => ({
    units: agencyUnitsQuery({ abfy: fy, abag }),
    byYear: agencyYearsQuery({ abag, abunit: "" }),
  }));
  const heading = useFocusOnChange(`agency|${abag}`);
  const ready = !q.loading && !q.error && Boolean(q.data);
  const units = q.data?.units ?? [];
  const byYear = q.data?.byYear ?? [];
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
      <YearPicker fy={fy} years={years} set={set} />
      <Live text={ready ? `Showing FY${fy}, ${name}, ${plural(units.length, "unit")}.` : ""} />
      {q.error ? <Notice tone="error">{String(q.error.message ?? q.error)}</Notice> : null}
      {ready ? (
        <>
          <h3>Units of appropriation, FY{fy}</h3>
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
                  <th scope="col" className="num">Modified FY{fy}</th>
                  <th scope="col" className="num">Modified minus adopted</th>
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
                    <td className="num" data-label={`Modified FY${fy}`}>
                      <Fig v={u.modified} kind="modified" year={fy} newest={newest} />
                    </td>
                    <td className="num" data-label="Modified minus adopted">
                      <Change c={change(u.adopted, u.modified)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <h3>{name}, every year</h3>
          <ByYear rows={byYear} years={years} newest={newest} title={name} caption={`${name}: adopted and modified by fiscal year, FY${years.at(-1).fiscal_year}–FY${newest}`} />
          <Downloads
            rows={units}
            name={`nyc-agency-${abag}-fy${fy}.csv`}
            columns={[["Fiscal year", () => fy], ["Agency number", () => abag], ["Agency", "agency_name"], ["Unit number", "unit_number"], ["Unit", "unit_name"], ["Adopted", "adopted"], ["Modified", "modified"], ["Adopted release", "adopted_release"], ["Modified release", "modified_release"]]}
          />
        </>
      ) : !q.error ? (
        <p className="muted" role="status">Loading…</p>
      ) : null}
      <SourceNote manifest={manifest} />
    </Root>
  );
}

// ---------------------------------------------------------------- one unit

function UnitScreen({ state, set, go, fy, years, newest, abag, abunit, manifest }) {
  const q = useQueries(true, `unit|${abag}|${abunit}`, () => ({ byYear: agencyYearsQuery({ abag, abunit }) }));
  const heading = useFocusOnChange(`unit|${abag}|${abunit}`);
  const ready = !q.loading && !q.error && Boolean(q.data);
  const byYear = q.data?.byYear ?? [];
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
      {q.error ? <Notice tone="error">{String(q.error.message ?? q.error)}</Notice> : null}
      {ready ? (
        <>
          <ByYear rows={byYear} years={years} newest={newest} title={`${agencyName}, ${abunit} ${unitName}`} caption={`${agencyName}, unit ${abunit} ${unitName}: adopted and modified by fiscal year`} />
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
  const q = useQueries(true, "agency-names", () => ({ names: agencyNamesQuery() }));
  const r = useMemo(() => (q.data ? resolveLegacy(state.legacy, q.data.names) : undefined), [q.data, state.legacy]);
  const resolved = r && r.candidates.length === 0;
  useEffect(() => {
    // Replace, not push: the old link becomes the new address, and Back leaves the page.
    if (resolved) set({ legacy: "", abfy: state.abfy, abag: r.abag, abunit: r.abunit });
  }, [resolved]); // eslint-disable-line react-hooks/exhaustive-deps
  if (q.error) return <Notice tone="error">{String(q.error.message ?? q.error)}</Notice>;
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

