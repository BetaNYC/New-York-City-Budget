import { useQueries } from "../duckdb/useDuckDB.js";
import { count, money, plural } from "../format.js";
import * as D from "../compare/diff.js";
import * as Q from "../compare/queries.js";
import { writeHash } from "../state/hash.js";
import { FlagBadge, ReviewedLabel, SourcePageLink } from "../components/pdf.jsx";
import { HashLink, Notice, SelectFilter, Status } from "../components/ui.jsx";

const SECTIONS = [
  ["totals", "Totals by source"],
  ["agency", Q.DIM_LABEL.agency],
  ["member", Q.DIM_LABEL.member],
  ["org", Q.DIM_LABEL.org],
  ["line", Q.DIM_LABEL.line],
  ["terms", "Terms & Conditions"],
];
const TOP = 100;
const CITY_EIN = "136400434";
const keyLabel = (k, label, dim) =>
  k === Q.BLANK ? "(blank as printed)" : dim === "org" && k === CITY_EIN ? "The City of New York's own EIN (many City agencies pool on it)" : label || k;

/**
 * Two fiscal years side by side: totals by source, then by agency, Council member or sponsor,
 * organization (EIN) and capital budget line, and the Terms and Conditions. Every number links to
 * the rows behind it. A source with no data for a year shows the gap and its reason, never $0,
 * and is never compared as if everything were "new" or "dropped".
 */
export default function Compare({ state, set, go, manifest, years, capitalYears, pdfYears }) {
  const fyA = state.cmpa ?? 2026;
  const fyB = state.cmpb ?? 2027;
  const sec = state.csec || "totals";
  const ctx = { years, capitalYears, capitalGaps: manifest.capital?.gaps ?? [], pdfYears };
  const allYears = [...new Set([...years.map((y) => y.fiscal_year), ...capitalYears, ...pdfYears.map((p) => p.fiscal_year)])].sort((a, b) => b - a);
  const yearOpts = allYears.map((y) => [String(y), `FY${y}`]);
  return (
    <section>
      <h2>Compare two fiscal years</h2>
      <p className="lede">
        A prototype. Pick two years; every figure is this repository's sum of the rows it links to. Amounts are compared to the cent. A source that has no data
        for a year says so; nothing is shown as $0 or as "dropped" because a year is missing.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Year A" value={String(fyA)} options={yearOpts} onApply={(v) => set({ cmpa: Number(v), ckey: "" })} />
        <SelectFilter label="Year B" value={String(fyB)} options={yearOpts} onApply={(v) => set({ cmpb: Number(v), ckey: "" })} />
        <div className="field">
          <span>&nbsp;</span>
          <button type="button" onClick={() => set({ cmpa: fyB, cmpb: fyA, ckey: "" })}>
            Swap
          </button>
        </div>
      </form>
      <nav className="subtabs" aria-label="Compare by">
        {SECTIONS.map(([k, label]) => (
          <HashLink key={k} href={writeHash({ ...state, view: "compare", csec: k, ckey: "", cstat: "" })} onGo={() => go({ csec: k, ckey: "", cstat: "" })} current={sec === k} className={sec === k ? "active" : undefined}>
            {label}
          </HashLink>
        ))}
      </nav>
      {sec === "totals" ? (
        <Totals fyA={fyA} fyB={fyB} ctx={ctx} state={state} go={go} />
      ) : sec === "terms" ? (
        <Terms fyA={fyA} fyB={fyB} ctx={ctx} state={state} go={go} />
      ) : (
        <Dimension dim={sec} fyA={fyA} fyB={fyB} ctx={ctx} state={state} set={set} go={go} />
      )}
      {state.ckey ? <Drill state={state} set={set} go={go} /> : null}
    </section>
  );
}

/** A link to the rows behind one figure (the drill-down below). */
function CellLink({ state, go, src, dim, fy, k, children }) {
  const target = { csrc: src, cdim: dim, cfyd: fy, ckey: k };
  return (
    <HashLink href={writeHash({ ...state, view: "compare", ...target })} onGo={() => go(target)}>
      {children}
    </HashLink>
  );
}

function Gap({ fy, reason }) {
  return (
    <span className="gap" title={reason}>
      no data for FY{fy}: <span className="small">{reason}</span>
    </span>
  );
}

// ---------------------------------------------------------------- totals

function Totals({ fyA, fyB, ctx, state, go }) {
  const q = useQueries(true, `cmptot|${fyA}|${fyB}`, () => Q.totalsQueries(fyA, fyB));
  const rows = [
    ["disclosure", "Expense disclosure (Council spreadsheet)"],
    ["schedule_c", "Schedule C (adopted budget PDF)"],
    ["capital", "Council capital, the list's own year"],
    ["capital_sd", "Capital §254 book, Part I (PDF)"],
    ["terms", "Terms and Conditions (conditions)"],
  ];
  return (
    <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
      {q.data && (
        <div className="table-wrap">
          <table className="rows compare">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col" className="num">
                  FY{fyA}
                </th>
                <th scope="col" className="num">
                  FY{fyB}
                </th>
                <th scope="col" className="num">
                  Change
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([src, label]) => {
                const cell = (fy) => {
                  const av = Q.availability(src, fy, ctx);
                  if (!av.ok) return { gap: av.reason };
                  const r = (q.data[src] ?? []).find((x) => Number(x.fy) === fy);
                  if (!r || Number(r.n) === 0) return { gap: `No ${label.toLowerCase()} rows for FY${fy} in this build.` };
                  return { r, status: av.status, note: av.note };
                };
                const a = cell(fyA);
                const b = cell(fyB);
                const show = (c, fy) =>
                  c.gap ? (
                    <Gap fy={fy} reason={c.gap} />
                  ) : (
                    <>
                      {src === "terms" ? (
                        plural(c.r.n, "condition")
                      ) : (
                        <CellLink state={state} go={go} src={src} dim={Object.keys(Q.SOURCES[src].dims)[0]} fy={fy} k="*">
                          {money(c.r.amount)}
                        </CellLink>
                      )}
                      {src !== "terms" ? <div className="muted small">{plural(c.r.n, "row")}</div> : null}
                      {src === "disclosure" ? <div className="muted small">cleared {money(c.r.cleared)} · pending {money(c.r.pending)}</div> : null}
                      {c.note ? <div className="muted small">early snapshot</div> : null} <ReviewedLabel status={c.status} />
                    </>
                  );
                const both = !a.gap && !b.gap;
                return (
                  <tr key={src}>
                    <th scope="row">{label}</th>
                    <td className="num">{show(a, fyA)}</td>
                    <td className="num">{show(b, fyB)}</td>
                    <td className="num">{both ? (src === "terms" ? `${Number(b.r.n) - Number(a.r.n) >= 0 ? "+" : ""}${Number(b.r.n) - Number(a.r.n)}` : signed(Number(b.r.amount) - Number(a.r.amount))) : <span className="muted">—</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="muted small">
        The disclosure and Schedule C are two records of the same kind of award: Schedule C is printed at adoption, the disclosure is the Council's later
        spreadsheet. Their totals are not meant to agree. Capital compares the amounts each year's list gives for its own year.
      </p>
    </Status>
  );
}

const signed = (v) => (v > 0 ? `+${money(v)}` : v < 0 ? `−${money(-v)}` : money(0));

// ---------------------------------------------------------------- one dimension

function Dimension({ dim, fyA, fyB, ctx, state, set, go }) {
  const sources = Q.DIM_SOURCES[dim];
  const src = sources.includes(state.csrc) ? state.csrc : sources[0];
  const avA = Q.availability(src, fyA, ctx);
  const avB = Q.availability(src, fyB, ctx);
  const ok = avA.ok && avB.ok;
  const q = useQueries(true, `cmp|${dim}|${src}|${fyA}|${fyB}|${ok}`, () => (ok ? { a: Q.groupQuery(src, dim, fyA), b: Q.groupQuery(src, dim, fyB) } : null));
  const diff = q.data ? D.diffKeyed(q.data.a, q.data.b) : null;
  const shown = diff ? D.sortDiff(diff.rows, state.cstat) : [];
  return (
    <>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter
          label="Source"
          value={src}
          options={sources.map((s) => {
            const both = Q.availability(s, fyA, ctx).ok && Q.availability(s, fyB, ctx).ok;
            return [s, `${Q.SOURCES[s].label}${both ? "" : " (a year missing)"}`];
          })}
          onApply={(v) => set({ csrc: v, cstat: "", ckey: "" })}
        />
      </form>
      {dim === "member" && (
        <Notice>
          Names as printed. <strong>"Speaker" is the role</strong> and is shown as printed; who held it is not resolved here (the Speaker can change in the
          middle of a fiscal year). A sponsor list such as "Speaker, Marte" is one sponsor string, not split between people. In the disclosure,{" "}
          <code>council_member</code> is the roster when the workbook was exported.
        </Notice>
      )}
      {dim === "org" && (
        <Notice>
          Grouped by EIN. One EIN can pool many bodies: a fiscal sponsor, or the City itself (13-6400434, every City agency). Rows with no EIN printed are one
          group, "(blank as printed)".
        </Notice>
      )}
      {!ok ? (
        <Notice tone="warn">
          {Q.SOURCES[src].label}: {!avA.ok && <Gap fy={fyA} reason={avA.reason} />} {!avB.ok && <Gap fy={fyB} reason={avB.reason} />} Nothing is compared, so
          nothing is called new or dropped because a year is missing.
        </Notice>
      ) : (
        <Status loading={q.loading && !q.data} updating={q.loading && Boolean(q.data)} error={q.error}>
          {diff && (
            <>
              <p>
                <ReviewedLabel status={avA.status ?? avB.status} />
              </p>
              <table className="totals">
                <caption>
                  {Q.SOURCES[src].label}, {count(diff.rows.length)} {dim === "org" ? "EINs" : "keys"}. Click a status to list only those.
                </caption>
                <tbody>
                  {D.STATUSES.map((s) => (
                    <tr key={s}>
                      <th scope="row">
                        <button type="button" className="linkish" aria-pressed={state.cstat === s} onClick={() => set({ cstat: state.cstat === s ? "" : s })}>
                          {D.STATUS_LABEL[s]}
                        </button>
                      </th>
                      <td>{count(diff.summary[s].count)}</td>
                      <td className="num">FY{fyA} {s === "new" ? "—" : money(diff.summary[s].a)}</td>
                      <td className="num">FY{fyB} {s === "dropped" ? "—" : money(diff.summary[s].b)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="table-wrap">
                <table className="rows compare">
                  <thead>
                    <tr>
                      <th scope="col">{dim === "org" ? "Organization (EIN)" : dim === "line" ? "Budget line" : dim === "agency" ? "Agency" : "Member / sponsor (as printed)"}</th>
                      <th scope="col" className="num">
                        FY{fyA}
                      </th>
                      <th scope="col" className="num">
                        FY{fyB}
                      </th>
                      <th scope="col" className="num">
                        Change
                      </th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.slice(0, TOP).map((r) => (
                      <tr key={r.key}>
                        <td>
                          {keyLabel(r.key, r.label, dim)}
                          {dim === "org" && r.key !== Q.BLANK ? <div className="muted small">EIN {r.key}</div> : null}
                        </td>
                        <td className="num">
                          {r.a === null ? (
                            <span className="muted">not listed</span>
                          ) : (
                            <CellLink state={state} go={go} src={src} dim={dim} fy={fyA} k={r.key}>
                              {money(r.a)}
                            </CellLink>
                          )}
                          {r.a_n ? <div className="muted small">{plural(r.a_n, "row")}</div> : null}
                        </td>
                        <td className="num">
                          {r.b === null ? (
                            <span className="muted">not listed</span>
                          ) : (
                            <CellLink state={state} go={go} src={src} dim={dim} fy={fyB} k={r.key}>
                              {money(r.b)}
                            </CellLink>
                          )}
                          {r.b_n ? <div className="muted small">{plural(r.b_n, "row")}</div> : null}
                        </td>
                        <td className="num">{signed(r.delta)}</td>
                        <td>
                          <span className={`cmp cmp-${r.status}`}>{D.STATUS_LABEL[r.status]}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {shown.length > TOP ? <p className="muted small">The {TOP} largest changes of {count(shown.length)}.</p> : null}
            </>
          )}
        </Status>
      )}
    </>
  );
}

// ---------------------------------------------------------------- Terms and Conditions

function Terms({ fyA, fyB, ctx, state, go }) {
  const avA = Q.availability("terms", fyA, ctx);
  const avB = Q.availability("terms", fyB, ctx);
  const ok = avA.ok && avB.ok;
  const q = useQueries(true, `cmpterms|${fyA}|${fyB}|${ok}`, () => (ok ? { a: Q.termsQuery(fyA), b: Q.termsQuery(fyB) } : null));
  if (!ok) {
    return (
      <Notice tone="warn">
        Terms and Conditions: {!avA.ok && <Gap fy={fyA} reason={avA.reason} />} {!avB.ok && <Gap fy={fyB} reason={avB.reason} />}
      </Notice>
    );
  }
  const out = q.data ? D.diffTerms(q.data.a, q.data.b) : [];
  const n = (s) => out.filter((o) => o.status === s).length;
  const link = (c) => <SourcePageLink state={state} go={go} pdf={c.source_pdf} page={c.pdf_page} bbox={c.bbox_pt} label={`FY${c.fiscal_year} condition ${c.item_number}: ${c.agency_name}`}>#{c.item_number}</SourcePageLink>;
  return (
    <Status loading={q.loading && !q.data} error={q.error}>
      <p>
        <ReviewedLabel status={avA.status ?? avB.status} /> {D.TERMS_STATUSES.map((s) => `${n(s)} ${s}`).join(" · ")}. "Same" ignores year numbers in the
        text; "changed" pairs conditions that name the same agencies and units.
      </p>
      <div className="table-wrap">
        <table className="rows compare">
          <thead>
            <tr>
              <th scope="col">Status</th>
              <th scope="col">FY{fyA}</th>
              <th scope="col">FY{fyB}</th>
            </tr>
          </thead>
          <tbody>
            {out
              .filter((o) => o.status !== "same")
              .concat(out.filter((o) => o.status === "same"))
              .map((o, i) => (
                <tr key={i}>
                  <td>
                    <span className={`cmp cmp-${o.status}`}>{o.status}</span>
                  </td>
                  <td className="small">{o.a ? <>{link(o.a)} {o.a.agency_name}: {o.a.condition_text.slice(0, 220)}{o.a.condition_text.length > 220 ? "…" : ""}</> : <span className="muted">—</span>}</td>
                  <td className="small">{o.b ? <>{link(o.b)} {o.b.agency_name}: {o.b.condition_text.slice(0, 220)}{o.b.condition_text.length > 220 ? "…" : ""}</> : <span className="muted">—</span>}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </Status>
  );
}

// ---------------------------------------------------------------- the rows behind a figure

function Drill({ state, set, go }) {
  const src = state.csrc;
  const s = Q.SOURCES[src];
  const dim = state.cdim;
  const q = useQueries(true, `drill|${src}|${dim}|${state.cfyd}|${state.ckey}`, () => {
    if (!s || !dim || state.cfyd == null) return null;
    const d = Q.drillQuery(src, dim, state.cfyd, state.ckey);
    return { rows: d, total: { sql: d.countSql, params: d.params } };
  });
  if (!s) return null;
  const t = q.data?.total?.[0];
  return (
    <div className="drill" id="drill">
      <h3>
        The rows behind it: {s.label}, FY{state.cfyd}
        {state.ckey !== "*" ? <>, {Q.DIM_LABEL[dim]?.replace(/^By /, "").replace(/^Capital by /, "")} = "{keyLabel(state.ckey, state.ckey, dim)}"</> : null}{" "}
        <button type="button" className="linkish" onClick={() => set({ ckey: "" })}>
          close
        </button>
      </h3>
      <Status loading={q.loading} error={q.error}>
        {t && (
          <p className="muted">
            {plural(t.n, "row")}, {money(t.amount)}
            {Number(t.n) > 200 ? " (the 200 largest shown)" : ""}.
          </p>
        )}
        <div className="table-wrap">
          <table className="rows">
            <thead>
              <tr>
                <th>Name / title</th>
                <th>EIN or line</th>
                <th>Member / sponsor</th>
                <th>Agency or stream</th>
                <th className="num">Amount</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {(q.data?.rows ?? []).map((r, i) => (
                <tr key={i}>
                  <td>
                    {r.name} <ReviewedLabel status={r.status} /> {r.flags ? <FlagBadge flags={r.flags} reviewId={r.review_id} /> : null}
                  </td>
                  <td>{r.ein ?? r.line}</td>
                  <td>{r.member}</td>
                  <td>{[r.agency, r.stream].filter(Boolean).join(" · ")}</td>
                  <td className="num">{money(r.amount)}</td>
                  <td>
                    {src === "disclosure" ? (
                      <HashLink href={writeHash({ ...state, view: "award", ay: r.fiscal_year, row: r.source_row })} onGo={() => go({ view: "award", ay: r.fiscal_year, row: r.source_row })}>
                        row {r.source_row}
                      </HashLink>
                    ) : src === "capital" ? (
                      <HashLink href={writeHash({ ...state, view: "capital-row", seq: r.seq })} onGo={() => go({ view: "capital-row", seq: r.seq })}>
                        record
                      </HashLink>
                    ) : (
                      <SourcePageLink state={state} go={go} pdf={r.source_pdf} page={r.pdf_page} bbox={r.bbox_pt} label={r.name} />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Status>
    </div>
  );
}
