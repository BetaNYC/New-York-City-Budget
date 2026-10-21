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

const RANK = ["same", "differs", "ambiguous", "context", "possible", "absent"];

function Badge({ status, children, title }) {
  const s = OD.OD_STATUS[status] ?? OD.OD_STATUS.not_covered;
  return (
    <span className={`od-badge od-${s.tone}`} title={title}>
      {children ?? s.label}
    </span>
  );
}

function label(x) {
  if (x.match_status === "ambiguous") {
    const b = OD.bucketCounts(x);
    if (OD.equalBucket(x)) return `On NYC Open Data (one of ${count(x.candidates)} identical rows)`;
    return b ? `Possibly on NYC Open Data: ${count(b[0])} of ours, ${count(b[1])} on the portal` : "Possibly on NYC Open Data";
  }
  if (x.match_status === "absent") return `Not on NYC Open Data as of ${x.snapshot_date}`;
  return OD.OD_STATUS[x.match_status]?.label;
}

function PortalLink({ x, children }) {
  const one = x.portal_row_id && !x.portal_row_id.includes(";");
  return <a href={one ? OD.rowUrl(x.dataset_id, x.portal_row_id) : OD.datasetUrl(x.dataset_id)}>{children ?? (one ? "portal row" : x.dataset_id)}</a>;
}

/** The table cell: the best status across datasets, linked to the portal. */
export function OdCell({ xs, coverage, fy }) {
  if (!xs || !xs.length) {
    const covering = OD.coveringDatasets(coverage, fy);
    if (coverage && !covering.length) return <td className="small"><Badge status="not_covered">No Open Data dataset</Badge></td>;
    return <td className="muted small">…</td>;
  }
  const best = [...xs].sort((a, b) => RANK.indexOf(OD.shownStatus(a)) - RANK.indexOf(OD.shownStatus(b)))[0];
  const all = xs.map((x) => `${x.dataset_id}: ${label(x)}`).join("\n");
  return (
    <td className="small">
      <Badge status={OD.shownStatus(best)} title={all}>
        {OD.shownStatus(best) === "ambiguous"
          ? "On Open Data (row not identifiable)"
          : OD.shownStatus(best) === "possible"
            ? label(best).replace("NYC ", "")
            : best.match_status === "absent"
              ? `Not on Open Data as of ${best.snapshot_date}`
              : OD.OD_STATUS[best.match_status].label.replace("NYC ", "")}
      </Badge>{" "}
      <PortalLink x={best}>{best.dataset_id}</PortalLink>
      {xs.length > 1 ? <div className="muted">+{xs.length - 1} more dataset{xs.length > 2 ? "s" : ""}</div> : null}
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
          <Badge status="not_covered" /> No NYC Open Data dataset the repo tracks covers FY{fy} for this kind of {what}.
        </p>
      ) : (
        <ul className="od-list">
          {covering.map((c) => {
            const x = (xs ?? []).find((r) => r.dataset_id === c.dataset_id);
            return (
              <li key={c.dataset_id}>
                <a href={OD.datasetUrl(c.dataset_id)}>{c.dataset_name ?? c.dataset_id}</a> <code className="small">{c.dataset_id}</code>, snapshot of{" "}
                {c.snapshot_date}:{" "}
                {!x ? (
                  <span className="muted">…</span>
                ) : (
                  <>
                    <Badge status={OD.shownStatus(x)}>{label(x)}</Badge>{" "}
                    {x.portal_row_id && !x.portal_row_id.includes(";") ? (
                      <>
                        · <PortalLink x={x}>row {x.portal_row_id}</PortalLink>
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
    </>
  );
}

/**
 * The per-year coverage strip: for each dataset, each year, the share of our records found on the
 * portal for certain (same, differs, context, and ambiguous rows whose presence is certain: no more of
 * ours than portal rows in the bucket), the ones not found, and the portal's
 * own count of rows with no record of ours (PLAN Q5: counted, not listed).
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
            <span className="muted small">snapshot {cs[0].snapshot_date}</span>
          </div>
          <ol className="od-years" aria-label={`${ds} by fiscal year`}>
            {cs.map((c) => {
              const covered = Number(c.covered) === 1;
              const found = Number(c.same) + Number(c.differs) + Number(c.context) + Number(c.ambiguous_present);
              const rec = Number(c.records);
              const pct = rec ? Math.round((100 * found) / rec) : 0;
              const tip = covered
                ? `FY${c.fiscal_year}: ${count(rec)} records; same ${count(c.same)}, differs ${count(c.differs)}, ambiguous ${count(c.ambiguous)} (certain ${count(c.ambiguous_present)}, possible ${count(Number(c.ambiguous) - Number(c.ambiguous_present))}), context ${count(c.context)}, not on the portal ${count(c.absent)}${Number(c.not_covered) ? `, not covered ${count(c.not_covered)}` : ""}; portal rows ${count(c.portal_rows ?? 0)}, portal-only ${count(c.portal_only ?? 0)}`
                : `FY${c.fiscal_year}: no dataset covers this year`;
              return (
                <li key={c.fiscal_year} className={covered ? (found < rec ? "od-y od-y-part" : "od-y od-y-all") : "od-y od-y-none"} title={tip}>
                  <span className="od-y-fy">FY{String(c.fiscal_year).slice(2)}</span>
                  <span className="od-y-pct">{covered ? `${pct}%` : "—"}</span>
                  {covered && Number(c.portal_only) ? <span className="od-y-only">+{count(c.portal_only)} portal-only</span> : null}
                </li>
              );
            })}
          </ol>
        </div>
      ))}
      <p className="muted small">
        Share of our {family === "capital_line" ? "budget lines" : family === "terms_unit" ? "units" : "records"} found on the portal for certain in each year (hover a year
        for the counts). "—": no tracked dataset covers that year. Portal-only rows are counted, not listed.
      </p>
    </details>
  );
}
