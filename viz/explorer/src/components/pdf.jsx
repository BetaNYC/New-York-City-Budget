import { createContext, useContext, useState } from "react";

import { rowLinks, sourceViewState } from "../../../../mcp/dist/rowlinks.js";

import { useQueries } from "../duckdb/useDuckDB.js";
import * as P from "../query/pdf.js";
import { DECISION_WORDS, flagState, reviewNotesQuery } from "../query/pdf.js";
import { writeHash } from "../state/hash.js";
import { HashLink } from "./ui.jsx";

/**
 * Shown on every row, page and chart built from a PDF family (#190): "checked, review in progress"
 * (status = reviewed: the checks ran and their flags are listed, but a person has not signed the
 * year off) or "checked and reviewed" (status = closed: signed off). Nothing for any other value.
 */
export function ReviewedLabel({ status, block = false }) {
  const words = P.statusLabel(status);
  if (!words) return null;
  const text = <span className={status === "closed" ? "closed-label" : "reviewed"}>{words}</span>;
  if (!block) return text;
  return status === "closed" ? (
    <p className="reviewed-block">
      {text} This comes from a PDF re-read in the PDF review (<a href="https://github.com/BetaNYC/New-York-City-Budget/issues/101">GitHub epic #101</a>, one issue per fiscal year): every printed total was checked, every doubt was
      decided, and a person signed the year off.
    </p>
  ) : (
    <p className="reviewed-block">
      {text} This comes from a PDF re-read in the PDF review (<a href="https://github.com/BetaNYC/New-York-City-Budget/issues/101">GitHub epic #101</a>, one issue per fiscal year); every printed total was checked, and the doubts are
      listed, but a person has not signed it off yet.
    </p>
  );
}

/** Text the PDF holds but a reader cannot see on the printed page (#209), always labeled as such. */
export function HiddenText({ text }) {
  if (!text) return null;
  return (
    <div className="hidden-text small">
      <span className="hidden-text-label">{P.HIDDEN_TEXT_LABEL}:</span> <q>{text}</q>
    </div>
  );
}

/** "read_from_page_image": fields a person confirmed from the page image, where the text layer disagreed (#209). */
export function PageImageNote({ fields }) {
  if (!fields) return null;
  return <div className="small muted">Read from the page image, checked by a person: {String(fields).replaceAll(";", ", ")}</div>;
}

/**
 * Whether this build has the review screen (manifest.review_screen; App.jsx provides it). The
 * public build shows a row's checks in plain words only; a review build shows the full detail.
 */
export const ReviewScreenContext = createContext(false);

/**
 * A row's review flags as a badge, with the recorded decision when there is one (a person's
 * decision, committed in the family's decisions file and carried into its review CSV). Opening it
 * shows each review entry's note from pdf_review. In a review build: the check ids, severity and
 * decision codes. In the public build: only "N things to check on this row", each entry's note
 * and its decision in plain words, never a check id or a severity (a "critical" next to an
 * organization's name reads as a charge against it; it is about our reading of the PDF).
 */
export function FlagBadge({ flags, reviewId }) {
  const full = useContext(ReviewScreenContext);
  const [open, setOpen] = useState(false);
  const list = String(flags ?? "").split(";").filter(Boolean);
  const q = useQueries(true, `flag|${full ? 1 : 0}|${reviewId}`, () => {
    const rq = reviewNotesQuery(reviewId, { full });
    return rq ? { notes: rq } : null;
  });
  if (!list.length) return null;
  const notes = q.data?.notes ?? [];
  const st = flagState(notes);
  if (!full) {
    // Counted by review entries, the notes opening the badge shows; nothing until they load, and
    // nothing for flags with no entry (there is no note to show).
    if (!notes.length) return null;
    const count = notes.length === 1 ? "1 thing to check on this row" : `${notes.length} things to check on this row`;
    const tail = st.state === "decided" ? ` · decided: ${st.decisions.map((d) => DECISION_WORDS[d] ?? d).join(", ")}` : " · not yet decided";
    return (
      <details className={`flagbadge flag-${st.state} flag-public`} onToggle={(e) => setOpen(e.currentTarget.open)}>
        <summary>
          {count}
          {tail}
        </summary>
        {open ? <PublicNotes notes={notes} /> : null}
      </details>
    );
  }
  const count = list.length === 1 ? "1 review flag" : `${list.length} review flags`;
  const entries = notes.length && notes.length !== list.length ? ` in ${notes.length === 1 ? "1 entry" : `${notes.length} entries`}` : "";
  const tail = st.state === "decided" ? ` · decided: ${st.decisions.map((d) => DECISION_WORDS[d] ?? d).join(", ")}` : st.state === "open" ? " · open" : "";
  return (
    <details className={`flagbadge flag-${st.state}`} onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary title={list.join(", ")}>
        {count}
        {entries}
        {tail}
      </summary>
      {open ? (
        <>
          <p className="muted small">Flags: {list.map((f) => <code key={f}>{f} </code>)}</p>
          <ReviewNotes notes={notes} loading={q.loading} error={q.error} />
        </>
      ) : null}
    </details>
  );
}

/** The public build's notes: what to check, in the reviewer's words, and the decision in plain words. */
export function PublicNotes({ notes }) {
  return (
    <div className="flagnotes small">
      <p className="muted">
        These are notes from our checks of how this row was read from the PDF. They are about the reading, not about the organization.
      </p>
      <ul>
        {notes.map((n) => (
          <li key={n.review_id}>
            {n.pdf_page ? <span className="muted">Page {n.pdf_page}: </span> : null}
            {n.note || "A value on this row differs between two readings of the page."}
            <div className={n.decision ? "decision-line" : "muted"}>
              {n.decision ? `Decided: ${DECISION_WORDS[n.decision] ?? n.decision}${n.decision_note ? `. ${n.decision_note}` : ""}` : "Not yet decided."}
            </div>
          </li>
        ))}
      </ul>
    </div>
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

/**
 * A row's three links (#190), all from the MCP's row-link builder (mcp/src/rowlinks.ts): its page
 * in the source view with the row highlighted, the PDF on GitHub at the commit this site was built
 * from, and the publisher's own copy where a manifest records one with the same sha256.
 */
export function RowLinks({ state, go, manifest, row, label }) {
  const l = rowLinks(row, { label, commit: manifest?.source_commit });
  const page = sourceViewState(row, label);
  if (!page) return null;
  return (
    <span className="rowlinks small">
      <SourcePageLink state={state} go={go} pdf={row.source_pdf} page={row.pdf_page} bbox={row.bbox_pt} label={label}>
        p.{page.spage}
      </SourcePageLink>
      {l.github ? (
        <>
          {" · "}
          <a href={l.github} aria-label="The PDF on GitHub">
            PDF
          </a>
        </>
      ) : null}
      {l.publisher ? (
        <>
          {" · "}
          <a href={l.publisher.url} aria-label={`The publisher's copy${l.publisher.publisher ? ` (${l.publisher.publisher})` : ""}`}>
            publisher's copy
          </a>
        </>
      ) : null}
    </span>
  );
}
