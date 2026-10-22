import { useState } from "react";

import { sourceViewState } from "../../../../mcp/dist/rowlinks.js";

import { useQueries } from "../duckdb/useDuckDB.js";
import { DECISION_WORDS, REVIEWED_LABEL, flagState, reviewNotesQuery } from "../query/pdf.js";
import { writeHash } from "../state/hash.js";
import { HashLink } from "./ui.jsx";

/**
 * Shown on every row, page and chart built from a reviewed PDF family (status = reviewed): the
 * checks ran and their flags are listed, but a person has not signed off (INTEGRATION.md §3).
 * A closed family shows nothing.
 */
export function ReviewedLabel({ status, block = false }) {
  if (status !== "reviewed") return null;
  const text = <span className="reviewed">{REVIEWED_LABEL}</span>;
  return block ? <p className="reviewed-block">{text} This comes from a PDF re-read in the PDF review (GitHub epic #101, one issue per fiscal year); every printed total was checked, and the doubts are listed, but a person has not signed it off yet.</p> : text;
}

/**
 * A row's review flags as a badge, with the recorded decision when there is one (a person's
 * decision, committed in the family's decisions file and carried into its review CSV). Opening it
 * shows each flag's note from pdf_review in the reviewer's words.
 */
export function FlagBadge({ flags, reviewId }) {
  const [open, setOpen] = useState(false);
  const list = String(flags ?? "").split(";").filter(Boolean);
  const q = useQueries(true, `flag|${reviewId}`, () => {
    const rq = reviewNotesQuery(reviewId);
    return rq ? { notes: rq } : null;
  });
  if (!list.length) return null;
  const notes = q.data?.notes ?? [];
  const st = flagState(notes);
  const count = list.length === 1 ? "1 review flag" : `${list.length} review flags`;
  const tail = st.state === "decided" ? ` · decided: ${st.decisions.map((d) => DECISION_WORDS[d] ?? d).join(", ")}` : st.state === "open" ? " · open" : "";
  return (
    <details className={`flagbadge flag-${st.state}`} onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary title={list.join(", ")}>
        {count}
        {tail}
      </summary>
      {open ? <ReviewNotes notes={notes} loading={q.loading} error={q.error} /> : null}
    </details>
  );
}

function ReviewNotes({ notes, loading, error }) {
  if (loading) return <p className="muted small">Loading the notes…</p>;
  if (error) return <p className="muted small">The notes could not be loaded.</p>;
  if (!notes.length) return <p className="muted small">No note recorded.</p>;
  return (
    <ul className="flagnotes">
      {notes.map((n) => (
        <li key={n.review_id}>
          <code>{n.check_id}</code> <span className={`sev sev-${n.severity}`}>{n.severity}</span>
          {n.pdf_page ? <span className="muted"> p.{n.pdf_page}</span> : null}: {n.note}
          {n.decision ? (
            <div className="decision-line">
              Decision: <code>{n.decision}</code> ({DECISION_WORDS[n.decision] ?? n.decision}){n.decision_note ? ` — ${n.decision_note}` : ""}
            </div>
          ) : (
            <div className="muted small">No decision recorded yet.</div>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * A link that opens the PDF page in the source viewer, with the row's box highlighted. The target
 * state comes from the MCP's row-link builder (mcp/src/rowlinks.ts), the same one that writes the
 * MCP's source-view links (#210); the href keeps the visitor's other state, as every in-app link does.
 */
export function SourcePageLink({ state, go, pdf, page, bbox, label, children }) {
  const target = sourceViewState({ source_pdf: pdf, pdf_page: page, bbox_pt: bbox }, label);
  if (!target) return null;
  return (
    <HashLink href={writeHash({ ...state, ...target })} onGo={() => go(target)} className="pagelink">
      {children ?? `p.${page}`}
    </HashLink>
  );
}
