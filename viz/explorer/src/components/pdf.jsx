import { useState } from "react";

import { useQueries } from "../duckdb/useDuckDB.js";
import { REVIEWED_LABEL, reviewNotesQuery } from "../query/pdf.js";
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
  return block ? <p className="reviewed-block">{text} This comes from a PDF re-read for GitHub issue #102; every printed total was checked, and the doubts are listed, but a person has not signed it off yet.</p> : text;
}

/**
 * A row's review flags as a badge. Opening it loads the notes from pdf_review (the family's
 * review CSV), so a reader sees why the row was flagged in the reviewer's words.
 */
export function FlagBadge({ flags, reviewId }) {
  const [open, setOpen] = useState(false);
  const list = String(flags ?? "").split(";").filter(Boolean);
  if (!list.length) return null;
  return (
    <details className="flagbadge" onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary title={list.join(", ")}>
        {list.length === 1 ? "1 review flag" : `${list.length} review flags`}
      </summary>
      {open ? <ReviewNotes reviewId={reviewId} /> : null}
    </details>
  );
}

function ReviewNotes({ reviewId }) {
  const q = useQueries(true, String(reviewId), () => {
    const rq = reviewNotesQuery(reviewId);
    return rq ? { notes: rq } : null;
  });
  if (q.loading) return <p className="muted small">Loading the notes…</p>;
  if (q.error) return <p className="muted small">The notes could not be loaded.</p>;
  const notes = q.data?.notes ?? [];
  if (!notes.length) return <p className="muted small">No note recorded.</p>;
  return (
    <ul className="flagnotes">
      {notes.map((n) => (
        <li key={n.review_id}>
          <code>{n.check_id}</code> <span className={`sev sev-${n.severity}`}>{n.severity}</span>
          {n.pdf_page ? <span className="muted"> p.{n.pdf_page}</span> : null}: {n.note}
        </li>
      ))}
    </ul>
  );
}

/** A link that opens the PDF page in the source viewer, with the row's box highlighted. */
export function SourcePageLink({ state, go, pdf, page, bbox, label, children }) {
  if (!pdf || !page) return null;
  const target = { view: "source", spdf: pdf, spage: Number(page), sbox: bbox || "", slabel: label || "" };
  return (
    <HashLink href={writeHash({ ...state, ...target })} onGo={() => go(target)} className="pagelink">
      {children ?? `p.${page}`}
    </HashLink>
  );
}
