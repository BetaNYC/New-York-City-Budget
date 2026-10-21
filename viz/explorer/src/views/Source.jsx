import { lazy, Suspense } from "react";

import { Notice } from "../components/ui.jsx";
import { sourceLinks } from "../paths.js";

// pdf.js is about 1 MB; load it only when a page is opened.
const PdfViewer = lazy(() => import("../components/PdfViewer.jsx"));

/**
 * One page of a source PDF, with the row's box highlighted. The PDF is read from GitHub at the
 * commit the data was built from (manifest.json source_commit), like the spreadsheets, so the page
 * shown is the exact file the row was read from. Never copied into the site.
 */
export default function Source({ state, back, manifest }) {
  const links = sourceLinks(manifest.source_commit, state.spdf);
  if (!state.spdf || !links || !/^source\/.+\.pdf$/i.test(state.spdf)) {
    return <Notice tone="warn">No source PDF named in this link.</Notice>;
  }
  return (
    <section>
      <p>
        <button type="button" className="linkish" onClick={back}>
          ← Back
        </button>
      </p>
      <h2>
        Source page {state.spage ?? 1} <span className="muted">of {state.spdf.split("/").at(-1)}</span>
      </h2>
      {state.slabel ? <p className="lede">{state.slabel}</p> : null}
      <p className="muted small">
        The highlighted box is the row as read from the PDF. File as committed at <code>{manifest.source_commit.slice(0, 7)}</code>:{" "}
        <a href={links.raw}>download</a> · <a href={links.page}>its page on GitHub</a>.
      </p>
      <Suspense fallback={<p className="muted">Loading the PDF viewer…</p>}>
        <PdfViewer src={links.raw} initialPage={state.spage ?? 1} bbox={state.sbox} label={state.spdf.split("/").at(-1)} fallbackUrl={links.page} />
      </Suspense>
    </section>
  );
}
