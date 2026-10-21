import { lazy, Suspense, useEffect, useMemo, useState } from "react";

import { useQueries } from "../duckdb/useDuckDB.js";
import { money } from "../format.js";
import { sourceLinks } from "../paths.js";
import * as P from "../query/pdf.js";
import * as R from "../review/queue.js";
import { ReviewedLabel } from "../components/pdf.jsx";
import { Notice, SelectFilter, Status } from "../components/ui.jsx";

const PdfViewer = lazy(() => import("../components/PdfViewer.jsx"));

/** Contract and bookkeeping columns, not shown among a row's parsed values. */
const HIDDEN = new Set(["fiscal_year", "source_pdf", "pdf_sha256", "bbox_pt", "review_id", "flags", "family", "status", "page_boxes", "org_bbox_pt"]);
const browserStorage = () => (typeof window !== "undefined" ? window.localStorage : null);

/**
 * The review queue: every flagged row of every reviewed PDF family, one at a time, with the PDF
 * page (the row's box highlighted), the parsed values, the reviewer's suggestion and the decision
 * buttons. Only in a --include-reviewed build. Decisions stay in this browser until exported.
 */
export default function Review({ state, set, manifest, pdfYears }) {
  const q = useQueries(true, "reviewqueue", () => ({ items: P.reviewQueueQuery() }));
  const [decisions, setDecisions] = useState(() => R.loadStore(browserStorage()));
  const [name, setName] = useState(() => browserStorage()?.getItem(R.NAME_KEY) ?? "");
  const [msg, setMsg] = useState(null);
  useEffect(() => R.saveStore(browserStorage(), decisions), [decisions]);
  useEffect(() => browserStorage()?.setItem(R.NAME_KEY, name), [name]);

  const all = useMemo(() => R.sortQueue((q.data?.items ?? []).map((it) => ({ ...it, fiscal_year: Number(it.fiscal_year), dollars: Number(it.dollars ?? 0) }))), [q.data]);
  const f = { family: state.rfam, fiscal_year: state.rfy, check_id: state.rcheck, severity: state.rsev, state: state.rstate };
  const shown = R.filterQueue(all, f, decisions);
  const current = shown.find((it) => it.review_id === state.rid) ?? shown[0];
  const prog = R.progress(all, decisions);
  const families = manifest.pdf_families ?? {};
  const pairs = [...new Map(all.map((it) => [`${it.family}|${it.fiscal_year}`, it])).values()];

  const record = (d) => setDecisions((cur) => ({ ...cur, [R.itemKey(d)]: d }));
  const clear = (it) =>
    setDecisions((cur) => {
      const next = { ...cur };
      delete next[R.itemKey(it)];
      return next;
    });

  const exportCsv = (family, fy) => {
    const csv = R.toDecisionsCsv(all, decisions, family, fy);
    const path = families[family]?.decisions?.[fy] ?? `fy${String(fy).slice(2)}_${family}_review_decisions.csv`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = path.split("/").at(-1);
    a.click();
    URL.revokeObjectURL(a.href);
  };
  const importCsv = async (file) => {
    const { decisions: got, errors } = R.importDecisions(await file.text(), all);
    setDecisions((cur) => ({ ...cur, ...got }));
    setMsg({ tone: errors.length ? "warn" : "info", text: `Imported ${Object.keys(got).length} decisions from ${file.name}.`, errors });
  };

  if (q.error) return <Notice tone="error">{String(q.error.message ?? q.error)}</Notice>;
  if (!q.data) return <p className="muted">Loading the review queue…</p>;
  if (!manifest.include_reviewed || !all.length) return <Notice>No review queue in this build. It appears in a local build made with <code>npm run data -- --include-reviewed</code>.</Notice>;

  return (
    <section>
      <h2>Review queue</h2>
      <ReviewedLabel status="reviewed" block />
      <p className="lede">
        Every row a check flagged, across the PDF families, most serious and largest dollar amount first. Look at the page, compare the parsed values, then
        record a decision. Nothing changes the data: decisions are saved in this browser until you export them and commit the file.
      </p>
      <div className="review-top">
        <label className={`field reviewer-name${name.trim() ? "" : " needs-name"}`}>
          <span>
            Your name (recorded as <code>decided_by</code>) <span className="required">required</span>
          </span>
          <input
            id="reviewer-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Noel Hidalgo"
            required
            aria-required="true"
            aria-describedby="reviewer-name-hint"
            autoComplete="name"
          />
          <span id="reviewer-name-hint" className="small">
            {name.trim() ? "Saved in this browser; every decision you record carries it." : "Enter your name before deciding: the decision buttons stay off until you do."}
          </span>
        </label>
        <p className="review-progress">
          <strong>{prog.decided}</strong> of {prog.total} decided ({prog.committed} already in the repository) · {prog.open} open · {prog.needs_info} need more information
        </p>
      </div>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <SelectFilter label="Family" value={state.rfam} options={[["", "All"], ...Object.entries(families).filter(([k]) => all.some((it) => it.family === k)).map(([k, v]) => [k, v.label])]} onApply={(v) => set({ rfam: v, rid: "" })} />
        <SelectFilter label="Year" value={state.rfy ?? ""} options={[["", "All"], ...[...new Set(all.map((it) => it.fiscal_year))].map((y) => [String(y), `FY${y}`])]} onApply={(v) => set({ rfy: v === "" ? null : Number(v), rid: "" })} />
        <SelectFilter label="Check" value={state.rcheck} options={[["", "All"], ...[...new Set(all.map((it) => it.check_id))].sort().map((c) => [c, c])]} onApply={(v) => set({ rcheck: v, rid: "" })} />
        <SelectFilter label="Severity" value={state.rsev} options={[["", "Any"], ["critical", "Critical"], ["warn", "Warn"]]} onApply={(v) => set({ rsev: v, rid: "" })} />
        <SelectFilter label="Show" value={state.rstate} options={[["", "All"], ["open", "Open"], ["decided", "Decided"]]} onApply={(v) => set({ rstate: v, rid: "" })} />
      </form>

      <div className="review-layout">
        <ol className="review-list" aria-label="Queue">
          {shown.map((it) => {
            const d = R.decisionOf(it, decisions);
            return (
              <li key={R.itemKey(it)} className={it === current ? "selected" : undefined}>
                <button type="button" className="review-item" onClick={() => set({ rid: it.review_id }, { keepPage: true })}>
                  <span className={`sev sev-${it.severity}`}>{it.severity}</span> <strong>{money(it.dollars)}</strong> <span className="muted small">{families[it.family]?.label ?? it.family}</span>
                  <br />
                  <code className="small">{it.check_id}</code> <span className="muted small">p.{it.pdf_page || "—"}</span>{" "}
                  {d ? <span className="decided">{d.committed ? "closed: " : ""}{R.DECISION_LABEL[d.decision]}</span> : <span className="muted small">open</span>}
                </button>
              </li>
            );
          })}
          {!shown.length && <li className="muted">Nothing matches these filters.</li>}
        </ol>
        <div className="review-panel">{current ? <Item key={R.itemKey(current)} it={current} manifest={manifest} families={families} decided={decisions[R.itemKey(current)]} name={name} onDecide={record} onClear={clear} /> : null}</div>
      </div>

      <h3>Save your decisions to the repository</h3>
      {msg && (
        <Notice tone={msg.tone}>
          {msg.text}
          {msg.errors?.length ? (
            <ul>
              {msg.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          ) : null}
        </Notice>
      )}
      <div className="howto">
        <p>
          This site cannot write to the repository. Your decisions are kept in this browser only (clearing site data loses them). Rows already decided in the
          repository are closed and are not exported again. Export your new decisions, merge each file into the committed file below (the merge refuses to
          change a decision already there), and commit:
        </p>
        <table className="rows small">
          <thead>
            <tr>
              <th>Family</th>
              <th>Decided</th>
              <th>File to commit</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {pairs.map((it) => {
              const path = families[it.family]?.decisions?.[it.fiscal_year] ?? "(no path configured)";
              const p = R.progress(all.filter((x) => x.family === it.family && x.fiscal_year === it.fiscal_year), decisions);
              return (
                <tr key={`${it.family}|${it.fiscal_year}`}>
                  <td>
                    FY{it.fiscal_year} {families[it.family]?.label ?? it.family}
                  </td>
                  <td>
                    {p.decided} of {p.total}
                  </td>
                  <td>
                    <code>{path}</code>
                  </td>
                  <td>
                    <button type="button" onClick={() => exportCsv(it.family, it.fiscal_year)}>
                      Export CSV
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <pre className="small">
          {`# from the repository root, for each exported file:
.venv/bin/python code/validate_review_decisions.py \\
    --review data/fyNN/pdf/<family>/<the family's>_review.csv \\
    --decisions <the path above> \\
    --add ~/Downloads/<the exported file> --write
git add <the path above> && git commit -m "Review decisions (#<the year's issue: #102 FY2027, #103 FY2026>)"`}
        </pre>
        <p>
          To pick up where you (or someone else) left off, import a decisions file: it replaces this browser's decision for each review_id it names.{" "}
          <label className="linkish">
            Import a decisions CSV…{" "}
            <input type="file" accept=".csv,text/csv" onChange={(e) => e.target.files?.[0] && importCsv(e.target.files[0])} />
          </label>
        </p>
      </div>
    </section>
  );
}

/** One queue item: the page, the parsed values, the suggestion, the decision. */
function Item({ it, manifest, families, decided, name, onDecide, onClear }) {
  const tables = families[it.family]?.tables ?? [];
  const q = useQueries(true, `rrow|${R.itemKey(it)}`, () => Object.fromEntries(tables.map((t) => [t, P.reviewRowQuery(t, it.fiscal_year, it.review_id)])));
  const found = q.data ? tables.map((t) => [t, q.data[t]?.[0]]).find(([, r]) => r) : null;
  const row = found?.[1];
  const page = Number(row?.pdf_page || it.pdf_page || 0);
  const bbox = row?.bbox_pt || "";
  const links = sourceLinks(manifest.source_commit, it.source_pdf);
  const detail = it.detail ? JSON.parse(it.detail) : {};
  const [note, setNote] = useState("");
  const [change, setChange] = useState("");
  const [err, setErr] = useState(null);
  const act = (kind) => {
    try {
      onDecide(R.decide(kind, it, { note, change, by: name }));
      setErr(null);
    } catch (e) {
      setErr(String(e.message ?? e));
    }
  };
  return (
    <article>
      <h3>
        {families[it.family]?.label ?? it.family} FY{it.fiscal_year}: <code>{it.check_id}</code> <span className={`sev sev-${it.severity}`}>{it.severity}</span>{" "}
        {money(it.dollars)}
      </h3>
      <p>{it.note}</p>
      <dl className="fields compact">
        {[["review_id", it.review_id], ["page", page || "none"], ["field", it.field], ["expected", it.expected], ["observed", it.observed], ...Object.entries(detail)]
          .filter(([, v]) => v !== "" && v != null)
          .map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
      </dl>
      <div className="review-decide">
        <p>
          <strong>Suggested:</strong> {it.suggested_decision ? <code>{it.suggested_decision}</code> : <span className="muted">no suggestion</span>}{" "}
          {it.suggested_note ? <span>{it.suggested_note}</span> : null} <span className="muted small">({it.suggestion_source})</span>
        </p>
        {R.isCommitted(it) ? (
          <Notice>
            <strong>Closed.</strong> Decided in the repository: <code>{it.decision}</code> ({R.DECISION_LABEL[it.decision]})
            {it.decision_note ? <> · {it.decision_note}</> : null}. To change it, edit the family's committed decisions file.
          </Notice>
        ) : decided ? (
          <Notice>
            Decided: <code>{decided.decision}</code> ({R.DECISION_LABEL[decided.decision]}) by {decided.decided_by}, {decided.decided_at.slice(0, 16).replace("T", " ")}
            {decided.note ? <> · {decided.note}</> : null}{" "}
            <button type="button" className="linkish" onClick={() => onClear(it)}>
              undo
            </button>
          </Notice>
        ) : null}
        {R.isCommitted(it) ? null : (
        <>
        <label className="field wide">
          <span>Note (optional)</span>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="why" />
        </label>
        <div className="buttons" aria-describedby="decide-hint">
          <button type="button" onClick={() => act("keep")} disabled={Boolean(R.blockedReason("keep", it, { by: name }))}>
            Keep as printed
          </button>
          <button type="button" onClick={() => act("suggestion")} disabled={Boolean(R.blockedReason("suggestion", it, { by: name }))}>
            {R.suggestionLabel(it)}
          </button>
          <button type="button" onClick={() => act("needs_info")} disabled={Boolean(R.blockedReason("needs_info", it, { by: name }))}>
            Needs more information
          </button>
          <span className="change">
            <input value={change} onChange={(e) => setChange(e.target.value)} placeholder="the right value" aria-label="Change to" />
            <button type="button" onClick={() => act("change")} disabled={Boolean(R.blockedReason("change", it, { by: name, change }))}>
              Change to…
            </button>
          </span>
        </div>
        <p id="decide-hint" className={`decide-hint${err || !name.trim() ? " warn" : ""}`} role="status" aria-live="polite">
          {err ?? R.blockedReason("keep", it, { by: name }) ?? (change.trim() ? null : "To record a different value, type it, then Change to…")}
        </p>
        </>
        )}
      </div>
      <div className="review-columns">
        <div>
          <h4>Parsed values</h4>
          <Status loading={q.loading} error={q.error}>
            {row ? (
              <dl className="fields compact">
                {Object.entries(row)
                  .filter(([k, v]) => !HIDDEN.has(k) && v !== "" && v != null)
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt>{k}</dt>
                      <dd>{typeof v === "number" && /amount|dollars|printed_y|org_printed/.test(k) ? money(v) : String(v)}</dd>
                    </div>
                  ))}
              </dl>
            ) : (
              <p className="muted">This flag is about a total or the page as a whole, not one row.</p>
            )}
          </Status>
        </div>
        <div>
          <h4>The page</h4>
          {page && links ? (
            <Suspense fallback={<p className="muted">Loading the PDF viewer…</p>}>
              <PdfViewer src={links.raw} initialPage={page} bbox={bbox} label={it.source_pdf.split("/").at(-1)} fallbackUrl={links.page} />
            </Suspense>
          ) : (
            <p className="muted">No page recorded for this flag.</p>
          )}
        </div>
      </div>
    </article>
  );
}
