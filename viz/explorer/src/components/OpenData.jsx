import { useQueries } from "../duckdb/useDuckDB.js";
import { count } from "../format.js";
import * as OD from "../query/opendata.js";

/**
 * "Is this record on NYC Open Data?" (PLAN 2026-10-21 §1, §5): a per-row badge with a link to the
 * portal row, a detail panel, and a per-year coverage strip. Structured data, so the public build
 * shows it too; crosswalk rows about PDF-derived records exist only in a reviewed build.
 */

/** The family's coverage rows (one query per family, cached by key). */
export function useOdCoverage(family) {
  const q = useQueries(true, `odcov|${family}`, () => ({ c: OD.coverageQuery(family) }));
  return q.data?.c ?? null;
}

/**
 * Crosswalk rows for the records on screen: Map recordKey -> [rows]. `keyOf(row)` returns
 * [fiscal_year, record_row, amount_fy?].
 */
export function useOdForRows(family, rows, keyOf, opts = {}) {
  const keys = (rows ?? []).map(keyOf);
  const withFy = family === "capital_award";
  const key = keys.map((k) => OD.recordKey(k[0], k[1], withFy ? k[2] ?? null : undefined)).join(",");
  const q = useQueries(true, `od|${family}|${opts.pdf ?? 0}|${key}`, () => {
    const oq = OD.odForRecordsQuery(family, keys, opts);
    return oq ? { x: oq } : null;
  });
  return q.data?.x ? OD.indexByRecord(q.data.x, withFy) : null;
}

const RANK = ["found", "maybe", "notfound", "nocheck"];

/** A state badge: the words say it; the tone only repeats it. */
export function StateBadge({ state, title, children }) {
  const s = OD.STATES[state] ?? OD.STATES.nocheck;
  return (
    <span className={`od-badge od-${s.tone}`} title={title}>
      {children ?? s.label}
    </span>
  );
}

/** "How we check": shown beside every coverage strip and on About the data. */
export function HowWeCheck() {
  const [lead, ...rest] = OD.HOW_WE_CHECK.split(". ");
  return (
    <p className="small od-how">
      <strong>{lead}.</strong> {rest.join(". ").replace("tell us.", "")}
      <a href="https://github.com/BetaNYC/New-York-City-Budget/issues">tell us</a>.
    </p>
  );
}

function PortalLink({ x, children }) {
  const one = x.portal_row_id && !x.portal_row_id.includes(";");
  return <a href={one ? OD.rowUrl(x.dataset_id, x.portal_row_id) : OD.datasetUrl(x.dataset_id)}>{children ?? (one ? "portal row" : x.dataset_id)}</a>;
}

/** The table cell: the best state across the datasets that cover the year, with its date and link. */
export function OdCell({ xs, coverage, fy }) {
  if (!xs || !xs.length) {
    const covering = OD.coveringDatasets(coverage, fy);
    if (coverage && !covering.length) {
      return (
        <td className="small">
          <StateBadge state="nocheck" title={OD.tooltipOf(null)} />
        </td>
      );
    }
    return <td className="muted small">…</td>;
  }
  const best = [...xs].sort((a, b) => RANK.indexOf(OD.stateOf(a)) - RANK.indexOf(OD.stateOf(b)))[0];
  const st = OD.stateOf(best);
  const all = xs.map((x) => OD.tooltipOf(x, OD.coveredRange(coverage, x.dataset_id))).join("\n");
  return (
    <td className="small">
      <StateBadge state={st} title={all} />
      <div className="muted">
        as of {best.snapshot_date} · <PortalLink x={best}>{st === "found" && best.portal_row_id && !best.portal_row_id.includes(";") ? "see row" : best.dataset_id}</PortalLink>
        {xs.length > 1 ? ` · +${xs.length - 1} more dataset${xs.length > 2 ? "s" : ""}` : ""}
      </div>
    </td>
  );
}

/** The detail page's section: every dataset that covers the record's year, and what it says. */
export function OdPanel({ xs, coverage, fy, what = "record" }) {
  const covering = OD.coveringDatasets(coverage, fy);
  return (
    <>
      <h3>On NYC Open Data?</h3>
      {!covering.length ? (
        <p>
          <StateBadge state="nocheck" title={OD.tooltipOf(null)} /> No NYC Open Data dataset covers FY{fy} for this kind of {what}, so we couldn't check.
        </p>
      ) : (
        <ul className="od-list">
          {covering.map((c) => {
            const x = (xs ?? []).find((r) => r.dataset_id === c.dataset_id);
            return (
              <li key={c.dataset_id}>
                <a href={OD.datasetUrl(c.dataset_id)}>{c.dataset_name ?? c.dataset_id}</a> <code className="small">{c.dataset_id}</code>:{" "}
                {!x ? (
                  <span className="muted">…</span>
                ) : (
                  <>
                    <StateBadge state={OD.stateOf(x)} /> <span className="small">{OD.tooltipOf(x, OD.coveredRange(coverage, c.dataset_id))}</span>
                    {x.portal_row_id && !x.portal_row_id.includes(";") ? (
                      <>
                        {" "}
                        <PortalLink x={x}>See the row</PortalLink>
                      </>
                    ) : null}
                    {x.differing_fields ? <div className="small">Differs: {x.differing_fields}</div> : null}
                    {x.portal_status ? (
                      <div className="small">
                        Portal says: <strong>{x.portal_status}</strong>
                        {x.portal_as_of ? `, as of ${x.portal_as_of}` : ""}
                      </div>
                    ) : null}
                    {x.portal_value ? <div className="small muted">Portal value: {x.portal_value}</div> : null}
                    <div className="small muted">Rule: {x.match_rule}</div>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <HowWeCheck />
    </>
  );
}

/**
 * The per-year coverage strip. Each year: the share found (state 1 only: same, differs, context)
 * and, separately, the share maybe found (state 2, ambiguous), e.g. "82% found · 6% maybe"; and the
 * portal's own count of rows with no record of ours (PLAN Q5: counted, not listed).
 */
export function CoverageStrip({ family, coverage, title = "On NYC Open Data, by year" }) {
  if (!coverage?.length) return null;
  const byDs = new Map();
  for (const c of coverage) {
    if (!byDs.has(c.dataset_id)) byDs.set(c.dataset_id, []);
    byDs.get(c.dataset_id).push(c);
  }
  return (
    <details className="od-strip" open>
      <summary>{title}</summary>
      {[...byDs.entries()].map(([ds, cs]) => (
        <div key={ds} className="od-strip-row">
          <div className="od-strip-name">
            <a href={OD.datasetUrl(ds)}>{cs[0].dataset_name ?? ds}</a> <code className="small">{ds}</code>{" "}
            <span className="muted small">as of {cs[0].snapshot_date}</span>
          </div>
          <ol className="od-years" aria-label={`${ds} by fiscal year`}>
            {cs.map((c) => {
              const covered = Number(c.covered) === 1;
              const rec = Number(c.records);
              const sh = OD.stripShares(c);
              const tip = covered
                ? `FY${c.fiscal_year}, as of ${c.snapshot_date}: ${count(rec)} of our records; found ${count(sh.found)}, maybe ${count(sh.maybe)}, not found ${count(c.absent)}${Number(c.not_covered) ? `, no Open Data to check ${count(c.not_covered)}` : ""}; portal rows ${count(c.portal_rows ?? 0)}, portal-only ${count(c.portal_only ?? 0)}`
                : `FY${c.fiscal_year}: no NYC Open Data dataset covers this year, so we couldn't check.`;
              return (
                <li key={c.fiscal_year} className={covered ? (sh.found < rec ? "od-y od-y-part" : "od-y od-y-all") : "od-y od-y-none"} title={tip}>
                  <span className="od-y-fy">FY{String(c.fiscal_year).slice(2)}</span>
                  {covered ? (
                    <>
                      <span className="od-y-pct">{sh.foundPct}% found</span>
                      {sh.maybe ? <span className="od-y-maybe">{sh.maybePct}% maybe</span> : null}
                    </>
                  ) : (
                    <span className="od-y-pct">no data</span>
                  )}
                  {covered && Number(c.portal_only) ? <span className="od-y-only">+{count(c.portal_only)} portal-only</span> : null}
                </li>
              );
            })}
          </ol>
        </div>
      ))}
      <p className="muted small">
        Share of our {family === "capital_line" ? "budget lines" : family === "terms_unit" ? "units" : "records"} found on the portal each year, and the share that only
        maybe is (hover a year for the counts). "No data": no NYC Open Data dataset covers that year. Portal-only rows are counted, not listed.
      </p>
      <HowWeCheck />
    </details>
  );
}
