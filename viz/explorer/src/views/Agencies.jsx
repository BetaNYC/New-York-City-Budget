import { useEffect, useMemo, useRef, useState } from "react";

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

/** "$117.8B", "$767.0M", "$562K", "$420" (#307): short money for the tables and summary lines. */
export function moneyShort(v) {
  if (v === null || v === undefined) return null;
  const n = Number(v);
  const a = Math.abs(n);
  const sign = n < 0 ? "−" : "";
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${sign}$${Math.round(a / 1e3)}K`;
  return `${sign}$${Math.round(a)}`;
}

/**
 * Short on screen, exact for everyone else (#307): sighted readers see "$117.8B" and get the full
 * figure on hover (title); screen readers hear only "$117,791,473,676". The CSV downloads and the
 * chart's text alternative keep full dollars.
 */
function Short({ short, full, className }) {
  return (
    <span className={className} title={full}>
      <span aria-hidden="true">{short}</span>
      <span className="visually-hidden">{full}</span>
    </span>
  );
}

function Money({ v }) {
  return <Short short={moneyShort(v)} full={money(v)} className="money" />;
}

function Fig({ v, kind, year, newest }) {
  if (v === null || v === undefined) return <span className="words">{figure(v, { kind, year, newest })}</span>;
  return <Money v={v} />;
}

/**
 * A change as "+3.0%" (or short dollars when there is no percent), with its exact dollars, and its
 * tone: "up" green #0a7a3d, "down" red #b3261e, zero none (body gray). The + and − signs stay, so
 * color is never the only signal (WCAG 1.4.1).
 */
export function changeText(c) {
  const sign = c.dollars > 0 ? "+" : c.dollars < 0 ? "−" : "";
  const pct = c.pct != null ? `${sign}${Math.abs(c.pct).toFixed(1)}%` : null;
  return {
    short: pct ?? `${sign}${moneyShort(Math.abs(c.dollars))}`,
    full: `${sign}${money(Math.abs(c.dollars))}${pct ? ` (${pct})` : ""}`,
    tone: c.dollars > 0 ? "up" : c.dollars < 0 ? "down" : undefined,
  };
}

function Change({ c }) {
  if (!c) return <span className="muted">—</span>;
  const t = changeText(c);
  return <Short short={t.short} full={t.full} className={t.tone} />;
}

/** A percent in running text, green or red, with its sign. */
function Pct({ from, to }) {
  const c = change(from, to);
  if (!c || c.pct == null) return null;
  const t = changeText(c);
  return <span className={t.tone}>{t.short}</span>;
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

/**
 * Sortable one-year tables (#307, as /tmp/mock-gen/sort-colors.html): each header is a button in
 * its th, aria-sort on the active column, a ▲/▼ arrow, and a polite "Sorted by …" message.
 * Number columns: the first click sorts low to high, the next flips it. The name column: the first
 * click sorts by number, the next by name A–Z. Rows with no figure always go last.
 * Default: adopted, high to low.
 */
export const SORT_DEFAULT = { key: "adopted", dir: "descending", nameMode: null };

export function nextSort(cur, col) {
  if (col.kind === "name") return { key: col.key, dir: "ascending", nameMode: cur.key === col.key && cur.nameMode === "number" ? "name" : "number" };
  if (cur.key === col.key) return { ...cur, dir: cur.dir === "ascending" ? "descending" : "ascending" };
  return { key: col.key, dir: "ascending", nameMode: null };
}

export function sortRows(rows, cols, st) {
  const col = cols.find((c) => c.key === st.key);
  const name = cols.find((c) => c.kind === "name");
  const out = [...rows];
  if (!col) return out;
  if (col.kind === "name") {
    if (st.nameMode === "name") out.sort((a, b) => col.name(a).localeCompare(col.name(b)) || col.number(a).localeCompare(col.number(b)));
    else out.sort((a, b) => col.number(a).localeCompare(col.number(b)));
    return out;
  }
  const s = st.dir === "ascending" ? 1 : -1;
  out.sort((a, b) => {
    const x = col.value(a);
    const y = col.value(b);
    const nx = x === null || x === undefined;
    const ny = y === null || y === undefined;
    if (nx || ny) return nx - ny || name.number(a).localeCompare(name.number(b));
    return s * (x - y) || name.number(a).localeCompare(name.number(b));
  });
  return out;
}

export function sortMessage(cols, st, noun) {
  const col = cols.find((c) => c.key === st.key);
  if (!col) return "";
  if (col.kind === "name") return st.nameMode === "name" ? `Sorted by ${noun} name, A to Z.` : `Sorted by ${noun} number.`;
  return `Sorted by ${col.label}, ${st.dir === "ascending" ? "low to high" : "high to low"}. Rows with no figure are last.`;
}

function useSort(rows, cols, noun) {
  const [st, setSt] = useState(SORT_DEFAULT);
  const [msg, setMsg] = useState("");
  const sorted = useMemo(() => sortRows(rows, cols, st), [rows, cols, st]);
  const click = (col) => {
    const next = nextSort(st, col);
    setSt(next);
    setMsg(sortMessage(cols, next, noun));
  };
  return { st, sorted, msg, click };
}

function SortHeads({ cols, sort }) {
  return (
    <tr>
      {cols.map((c) => {
        const on = sort.st.key === c.key;
        const arrow = !on ? "" : c.kind === "name" ? (sort.st.nameMode === "name" ? "A–Z" : "#") : sort.st.dir === "ascending" ? "▲" : "▼";
        return (
          <th key={c.key} scope="col" className={c.kind === "name" ? "sortable" : "sortable num"} aria-sort={on ? (c.kind === "name" ? "ascending" : sort.st.dir) : undefined}>
            <button type="button" onClick={() => sort.click(c)}>
              {c.label}
              <span className="arrow" aria-hidden="true">
                {arrow}
              </span>
            </button>
          </th>
        );
      })}
    </tr>
  );
}

function SortStatus({ text }) {
  return (
    <p className="sort-status" aria-live="polite" aria-atomic="true">
      {text}
    </p>
  );
}

/** The value a change column sorts by: its percent, or nothing when the cell is words. */
const lastYearPct = (r, ctx) => (vsLastYearWords({ ...ctx, prevRow: r.prev, row: r, seenBefore: r.seenBefore }) ? null : change(r.prev.adopted, r.adopted)?.pct ?? null);
const vsAdoptedPct = (r, ctx) => (vsAdoptedWords({ ...ctx, row: r }) ? null : change(r.adopted, r.modified)?.pct ?? null);

function oneYearCols({ fy, first, newest, noun, number, name }) {
  const ctx = { year: fy, first, newest, noun };
  return [
    { key: "name", kind: "name", label: noun === "unit" ? "Unit" : "Agency", number, name },
    { key: "adopted", kind: "num", label: `Adopted FY${fy}`, value: (r) => r.adopted },
    { key: "vsLast", kind: "num", label: `vs. FY${fy - 1} adopted`, value: (r) => lastYearPct(r, ctx) },
    { key: "modified", kind: "num", label: `Modified FY${fy}`, value: (r) => r.modified },
    { key: "vsAdopted", kind: "num", label: "Modified vs. adopted", value: (r) => vsAdoptedPct(r, ctx) },
  ];
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

/** A section heading with its numbered step circle (1: over time, 2: one year). */
function StepHeading({ n, id, children }) {
  return (
    <h3 id={id} className="step-heading">
      <span className="step" aria-hidden="true">
        {n}
      </span>{" "}
      {children}
    </h3>
  );
}

/** Rows of one year's table: the year's figures, last year's row, and whether it is new. */
function OneYearTable({ caption, rows, cols, sort, noun, renderName, fy, first, newest, split }) {
  return (
    <>
      <table className="rows stack agency-table sortable-table">
        <caption>{caption}</caption>
        <thead>
          <SortHeads cols={cols} sort={sort} />
        </thead>
        <tbody>
          {sort.sorted.map((r) => (
            <tr key={cols[0].number(r)}>
              <th scope="row">{renderName(r)}</th>
              <td className="num" data-label={cols[1].label}>
                <Fig v={r.adopted} kind="adopted" year={fy} newest={newest} />
              </td>
              <td className="num" data-label={cols[2].label}>
                <VsLastYear prevRow={r.prev} row={r} year={fy} first={first} noun={noun} seenBefore={r.seenBefore} />
                {split?.(r)}
              </td>
              <td className="num" data-label={cols[3].label}>
                <Fig v={r.modified} kind="modified" year={fy} newest={newest} />
              </td>
              <td className="num" data-label={cols[4].label}>
                <VsAdopted row={r} year={fy} newest={newest} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <SortStatus text={sort.msg} />
    </>
  );
}

/** Whether a row had an adopted figure in any year before `fy`. */
const hadAdoptedBefore = (years, fy) => years.some((y) => y.fiscal_year < fy && y.adopted != null);

function ListScreen({ state, set, go, fy, years, newest, manifest }) {
  const q = useAgencyJson([agenciesPath()]);
  const heading = useFocusOnChange("list");
  const ready = !q.loading && !q.error && Boolean(q.data);
  const first = years.at(-1)?.fiscal_year;
  const rows = useMemo(() => {
    if (!q.data) return [];
    const all = q.data[agenciesPath()];
    const prev = new Map(agencyList(all, fy - 1).map((r) => [r.agency_number, r]));
    const earlier = new Set(years.filter((y) => y.fiscal_year < fy).flatMap((y) => agencyList(all, y.fiscal_year).filter((r) => r.adopted != null).map((r) => r.agency_number)));
    return agencyList(all, fy).map((r) => ({ ...r, prev: prev.get(r.agency_number) ?? null, seenBefore: earlier.has(r.agency_number) }));
  }, [q.data, fy, years]);
  const cols = useMemo(() => oneYearCols({ fy, first, newest, noun: "agency", number: (r) => r.agency_number, name: (r) => r.agency_name }), [fy, first, newest]);
  const sort = useSort(rows, cols, "agency");
  const cityRows = cityByYear(q.data?.[citywidePath()]);
  return (
    <Root ready={ready}>
      <h2 ref={heading} tabIndex={-1}>
        All City agencies
      </h2>
      <p className="lede">What New York City budgets for each agency, every year since FY{first}. Start with the whole city, then pick an agency.</p>
      <Explainer />
      {q.error ? <LoadError q={q} /> : null}
      {ready ? (
        <section className="trend" aria-labelledby="trend-h">
          <StepHeading n={1} id="trend-h">
            The whole city, over time
          </StepHeading>
          <TrendSummary rows={cityRows} newest={newest} />
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
        <StepHeading n={2} id="one-year-h">
          Agencies in FY{fy}
        </StepHeading>
        <p className="hint">Pick a year. Click a column title to sort; click again to flip it.</p>
        <YearPicker fy={fy} years={years} set={set} />
        <Live text={ready ? `Showing FY${fy}, all agencies, ${plural(rows.length, "agency", "agencies")}.` : ""} />
        {ready ? (
          <>
            <OneYearTable
              caption={`Adopted and modified budgets by agency, FY${fy} (${plural(rows.length, "agency", "agencies")})`}
              rows={rows}
              cols={cols}
              sort={sort}
              noun="agency"
              fy={fy}
              first={first}
              newest={newest}
              renderName={(r) => (
                <>
                  <HashLink href={writeHash({ ...state, abfy: fy, abag: r.agency_number, abunit: "" })} onGo={() => go({ abfy: fy, abag: r.agency_number, abunit: "" })}>
                    {r.agency_name}
                  </HashLink>{" "}
                  <span className="muted small">{r.agency_number}</span>
                </>
              )}
            />
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

/** The chart's two lines, as small keys for the explainer (decorative: the words say it). */
function Swatch({ kind }) {
  return <span className={`swatch swatch-${kind}`} aria-hidden="true" />;
}

/** What adopted and modified mean (#306): the full box on the list page. */
export const EXPLAINER_ID = "adopted-modified";
function Explainer() {
  return (
    <section className="explainer" id={EXPLAINER_ID} aria-labelledby={`${EXPLAINER_ID}-h`}>
      <h3 id={`${EXPLAINER_ID}-h`}>What adopted and modified mean</h3>
      <dl>
        <dt>
          <Swatch kind="adopted" />
          Adopted
        </dt>
        <dd>
          The budget the Mayor and City Council agree on in June, before the fiscal year starts. <strong>The plan.</strong>
        </dd>
        <dt>
          <Swatch kind="modified" />
          Modified
        </dt>
        <dd>
          The same budget as it stood the next June, near the end of the year, after the City moved money around. <strong>Closer to what happened.</strong>
        </dd>
      </dl>
      <p>
        The gap between the two lines shows where plans changed during the year. NYC's fiscal year runs July 1 to June 30, so FY2026 is July 2025 to June
        2026.
      </p>
    </section>
  );
}

/** The one-line version on an agency page (#307 wording), linking the full box on the list page. */
function ExplainerNote({ state, go }) {
  return (
    <p className="explainer-note">
      <strong>Adopted</strong> = the plan agreed on in June. <strong>Modified</strong> = where it stood a year later.{" "}
      <HashLink href={writeHash({ ...state, abag: "", abunit: "" })} onGo={() => go({ abag: "", abunit: "" })}>
        More about these
      </HashLink>
      .
    </p>
  );
}

/**
 * The trend in two sentences (#307, brand.html): the newest year with both figures, its adopted
 * against the year before and its modified against the plan; then the newest adopted, whose
 * modified is not published yet. Not tied to the year picker, which only changes Section 2.
 */
function TrendSummary({ rows, newest, who = null }) {
  const full = rows.filter((r) => r.adopted != null && r.modified != null).at(-1);
  if (!full) return null;
  const y = full.fiscal_year;
  const prev = rows.find((r) => r.fiscal_year === y - 1);
  const latest = rows.find((r) => r.fiscal_year === newest);
  const latestPrev = rows.find((r) => r.fiscal_year === newest - 1);
  const plan = change(full.adopted, full.modified);
  const vsPlan = plan && plan.dollars < 0 ? "below the plan" : plan && plan.dollars > 0 ? "above the plan" : "the same as the plan";
  return (
    <p className="big citywide-summary">
      In FY{y} the City adopted <strong><Money v={full.adopted} /></strong>
      {who ? ` for ${who}` : ""}
      {change(prev?.adopted, full.adopted)?.pct != null ? (
        <>
          {" "}
          (<Pct from={prev.adopted} to={full.adopted} /> from FY{y - 1})
        </>
      ) : null}
      . By year's end it stood at <strong><Money v={full.modified} /></strong>
      {plan?.pct != null ? (
        <>
          {" "}
          (<Pct from={full.adopted} to={full.modified} /> {vsPlan})
        </>
      ) : null}
      .
      {latest && latest.fiscal_year !== y && latest.adopted != null ? (
        <>
          {" "}
          FY{newest} adopted: <strong><Money v={latest.adopted} /></strong>
          {change(latestPrev?.adopted, latest.adopted)?.pct != null ? (
            <>
              {" "}
              (<Pct from={latestPrev.adopted} to={latest.adopted} /> from FY{newest - 1})
            </>
          ) : null}
          ; its modified figure is {NOT_PUBLISHED.toLowerCase()}.
        </>
      ) : null}
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
                  <VsLastYear prevRow={series[i - 1]?.row ?? null} row={s.row} year={s.year} first={first} noun={noun} seenBefore={series.slice(0, i).some((p) => p.adopted != null)} />
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
 * bare dash. `noun` names what is new ("agency", "unit"); `seenBefore` is false when no earlier
 * year had an adopted figure for it (a row missing for a year, then back, is not new).
 */
export function vsLastYearWords({ prevRow, row, year, first, noun, seenBefore = prevRow?.adopted != null }) {
  if (!row || row.adopted == null) return `No FY${year} adopted figure`;
  if (year === first) return `No FY${year - 1} figure`;
  if (noun && noun !== "figure" && !seenBefore) return `New ${noun} in FY${year}`;
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

/** A drop this large, in a year the agency added units, gets a note in words (#307). */
export const SPLIT_DROP_PCT = -25;
export const SPLIT_NOTE = "Units can be split or renumbered between years; a large change may be a move, not a cut.";

/**
 * Units new in `fy` (no adopted figure in any earlier year), and the units whose adopted fell by
 * SPLIT_DROP_PCT or more from the year before while those new units appeared. Only facts the
 * data shows: it cannot say where money went, so the words name the new units, not a move.
 */
export function splitHints(units, fy, first) {
  const added = fy > first ? units.filter((u) => !u.seenBefore && u.adopted != null).map((u) => u.unit_number) : [];
  const dropped = new Set(
    added.length ? units.filter((u) => u.prev?.adopted != null && u.adopted != null && (change(u.prev.adopted, u.adopted)?.pct ?? 0) <= SPLIT_DROP_PCT).map((u) => u.unit_number) : []
  );
  return { added, dropped };
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
      return { ...u, prev: prev.get(u.unit_number) ?? null, seenBefore: hadAdoptedBefore(yrs, fy) };
    });
  }, [file, fy]);
  const cols = useMemo(() => oneYearCols({ fy, first, newest, noun: "unit", number: (r) => r.unit_number, name: (r) => r.unit_name }), [fy, first, newest]);
  const sort = useSort(units, cols, "unit");
  const hints = useMemo(() => splitHints(units, fy, first), [units, fy, first]);
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
  const others = (u) => hints.added.filter((n) => n !== u.unit_number);
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
          <StepHeading n={1} id="trend-h">
            {name}, over time
          </StepHeading>
          <TrendSummary rows={byYear} newest={newest} who={name} />
          <ByYear rows={byYear} years={years} newest={newest} title={name} noun="agency" caption={`${name}: adopted and modified by fiscal year, FY${first}–FY${newest}`} />
        </section>
      ) : null}
      <section className="one-year" aria-labelledby="one-year-h">
        <StepHeading n={2} id="one-year-h">
          Its units in FY{fy}
        </StepHeading>
        <p className="hint">A unit of appropriation is a line the Council votes on. Click a column title to sort; click again to flip it.</p>
        <YearPicker fy={fy} years={years} set={set} />
        <Live text={ready ? `Showing FY${fy}, ${name}, ${plural(units.length, "unit")}.` : ""} />
        {ready ? (
          <>
            {units.length === 0 ? (
              <Notice>{name} has no unit in the FY{fy} budget.</Notice>
            ) : (
              <>
                {hints.added.length ? <p className="split-note">{SPLIT_NOTE}</p> : null}
                <OneYearTable
                  caption={`${name}: adopted and modified budget by unit of appropriation, FY${fy} (${plural(units.length, "unit")})`}
                  rows={units}
                  cols={cols}
                  sort={sort}
                  noun="unit"
                  fy={fy}
                  first={first}
                  newest={newest}
                  split={(u) =>
                    hints.dropped.has(u.unit_number) && others(u).length ? (
                      <span className="split">
                        {name} added unit{others(u).length > 1 ? "s" : ""} {others(u).join(", ")} in FY{fy}
                      </span>
                    ) : null
                  }
                  renderName={(u) => (
                    <HashLink href={writeHash({ ...state, abfy: fy, abag, abunit: u.unit_number })} onGo={() => go({ abfy: fy, abag, abunit: u.unit_number })}>
                      <span className="unit-number">{u.unit_number}</span> {u.unit_name}
                    </HashLink>
                  )}
                />
              </>
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

