import * as pdfjs from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { EventBus, PDFLinkService, PDFViewer } from "pdfjs-dist/web/pdf_viewer.mjs";
import { useEffect, useRef, useState } from "react";

import { bboxToPdfRect, viewportBox } from "../query/pdf.js";

import "pdfjs-dist/web/pdf_viewer.css";

/**
 * A source PDF in pdf.js's own viewer component, opened at a page with one row's box highlighted.
 *
 * Adapted from nyc-eo-explorer's src/components/PdfViewer.jsx (MIT, BetaNYC; commit 45e47a8):
 * the same PDFViewer + EventBus + PDFLinkService setup, the same "wait for pagesPromise, fit, then
 * land" opening jump, and the same refit on resize. Dropped: its range-request transport for
 * media.githubusercontent.com (these PDFs come from raw.githubusercontent.com and are under 1 MB
 * for capital and T&C; Schedule C is 8.5 MB and may want it back) and the JBIG2 wasm path (these
 * PDFs are born-digital). Added: the highlight, drawn on every render of the target page.
 *
 * `bbox` is the row contract's `bbox_pt`: x0,top,x1,bottom in points on the UNROTATED page. The
 * viewport pdf.js renders with already applies the page's /Rotate (the capital book's pages are
 * /Rotate 90), so the box goes through viewport.convertToViewportRectangle and lands where the
 * row is drawn.
 */
pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

const ZOOM_STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4];

export default function PdfViewer({ src, initialPage = 1, bbox = "", label, fallbackUrl = null }) {
  const [page, setPage] = useState(initialPage);
  const [numPages, setNumPages] = useState(0);
  const [scale, setScale] = useState(1);
  const [fitWidth, setFitWidth] = useState(true);
  const [error, setError] = useState(null);

  const containerRef = useRef(null);
  const viewerElRef = useRef(null);
  const viewerRef = useRef(null);
  const fitWidthRef = useRef(fitWidth);
  fitWidthRef.current = fitWidth;
  const landedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setNumPages(0);
    landedRef.current = false;

    const eventBus = new EventBus();
    const linkService = new PDFLinkService({ eventBus });
    const viewer = new PDFViewer({ container: containerRef.current, viewer: viewerElRef.current, eventBus, linkService });
    linkService.setViewer(viewer);
    viewerRef.current = viewer;
    const target = Math.trunc(Number(initialPage));

    eventBus.on("pagechanging", ({ pageNumber }) => setPage(pageNumber));
    eventBus.on("scalechanging", ({ scale: s }) => setScale(s));
    // The highlight: redrawn each time the target page renders (a zoom re-renders it).
    eventBus.on("pagerendered", ({ pageNumber, source }) => {
      if (pageNumber !== target || !bbox) return;
      const div = source.div;
      div.querySelector(".rowhighlight")?.remove();
      const rect = bboxToPdfRect(bbox, source.pdfPage.view);
      if (!rect) return;
      const box = viewportBox(source.viewport.convertToViewportRectangle(rect));
      const pad = 3;
      const el = document.createElement("div");
      el.className = "rowhighlight";
      el.setAttribute("aria-hidden", "true");
      Object.assign(el.style, {
        left: `${box.left - pad}px`,
        top: `${box.top - pad}px`,
        width: `${box.width + 2 * pad}px`,
        height: `${box.height + 2 * pad}px`,
      });
      div.appendChild(el);
    });
    eventBus.on("pagesinit", async () => {
      const live = () => !cancelled && viewer === viewerRef.current && viewer.pdfDocument;
      viewer.currentScaleValue = "page-width";
      if (!Number.isInteger(target) || target <= 1) {
        landedRef.current = true;
        return;
      }
      // Wait for every page's own viewport before jumping (see nyc-eo-explorer's notes).
      await viewer.pagesPromise;
      if (!live()) return;
      viewer.currentScaleValue = "page-width";
      if (target <= viewer.pagesCount) viewer.currentPageNumber = target;
      requestAnimationFrame(() => {
        if (live() && viewer.currentPageNumber !== target && target <= viewer.pagesCount) viewer.currentPageNumber = target;
        landedRef.current = true;
      });
    });

    const task = pdfjs.getDocument({ url: src });
    task.promise
      .then((doc) => {
        if (cancelled) return;
        viewer.setDocument(doc);
        linkService.setDocument(doc, null);
        setNumPages(doc.numPages);
      })
      .catch((e) => {
        if (!cancelled) setError(e);
      });

    const ro = new ResizeObserver(() => {
      if (landedRef.current && fitWidthRef.current && viewerRef.current?.pdfDocument) viewerRef.current.currentScaleValue = "page-width";
    });
    ro.observe(containerRef.current);

    return () => {
      cancelled = true;
      ro.disconnect();
      viewer.setDocument(null);
      linkService.setDocument(null);
      viewerRef.current = null;
      task.destroy();
    };
  }, [src, initialPage, bbox]);

  const goToPage = (n) => {
    const viewer = viewerRef.current;
    if (!viewer || !numPages || !Number.isFinite(n)) return;
    viewer.currentPageNumber = Math.min(Math.max(Math.trunc(n), 1), numPages);
  };
  const zoomBy = (dir) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const next = dir > 0 ? ZOOM_STEPS.find((z) => z > scale + 0.001) ?? ZOOM_STEPS.at(-1) : ZOOM_STEPS.filter((z) => z < scale - 0.001).at(-1) ?? ZOOM_STEPS[0];
    setFitWidth(false);
    viewer.currentScaleValue = String(next);
  };
  const refit = () => {
    setFitWidth(true);
    if (viewerRef.current?.pdfDocument) viewerRef.current.currentScaleValue = "page-width";
  };

  return (
    <div className="pdfviewer">
      <div className="pdfnav">
        <button type="button" onClick={() => goToPage(page - 1)} disabled={page <= 1} title="Previous page">
          ‹
        </button>
        <label>
          Page <input type="number" min="1" max={numPages || undefined} value={page} onChange={(e) => goToPage(Number(e.target.value))} />
        </label>
        <span className="muted">of {numPages || "…"}</span>
        <button type="button" onClick={() => goToPage(page + 1)} disabled={!numPages || page >= numPages} title="Next page">
          ›
        </button>
        <span className="pdfzoom">
          <button type="button" onClick={() => zoomBy(-1)} disabled={scale <= ZOOM_STEPS[0]} title="Zoom out">
            −
          </button>
          <button type="button" onClick={refit} aria-pressed={fitWidth} title="Fit the pane's width">
            {fitWidth ? "Fit" : `${Math.round(scale * 100)}%`}
          </button>
          <button type="button" onClick={() => zoomBy(1)} disabled={scale >= ZOOM_STEPS.at(-1)} title="Zoom in">
            +
          </button>
        </span>
        {page !== initialPage && numPages ? (
          <button type="button" className="linkish" onClick={() => goToPage(initialPage)}>
            back to p.{initialPage}
          </button>
        ) : null}
      </div>
      {error ? (
        <div className="pdfmissing">
          <p>Could not load the PDF ({String(error.message ?? error)}).</p>
          <p>
            <a href={src}>Download it directly</a>
            {fallbackUrl ? (
              <>
                {" · "}
                <a href={fallbackUrl}>its page on GitHub</a>
              </>
            ) : null}
          </p>
        </div>
      ) : null}
      <div className="pdfstage" hidden={!!error}>
        <div className="pdfscroll" ref={containerRef}>
          <div className="pdfViewer" ref={viewerElRef} />
        </div>
        {!numPages ? <p className="pdfloading">Loading {label ?? "PDF"}…</p> : null}
      </div>
    </div>
  );
}
