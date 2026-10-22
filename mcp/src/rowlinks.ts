/**
 * The links for a row read from a source PDF, built ONE way for both front ends: the MCP imports
 * this module, and the explorer imports the compiled mcp/dist/rowlinks.js (as it does fold.js), so
 * an answer and the explorer can never point the same row at different places (GitHub #210).
 *
 * A row (the row contract in viz/explorer/INTEGRATION.md: source_pdf, pdf_page, bbox_pt,
 * pdf_sha256) gets three links:
 *   1. source_view: the explorer's source view at the row, the page opened with the row's box
 *      highlighted. The hash is exactly what the explorer's writeHash (src/state/hash.js) writes
 *      for the same state: keys in its order (view, spdf, spage, sbox, slabel), URLSearchParams
 *      encoding, empty values left out.
 *   2. github: the PDF on GitHub at the build's commit, so the link never points at a changed
 *      file; raw is the same file as a download (raw.githubusercontent.com serves PDFs as
 *      application/octet-stream, so a #page=N there would do nothing and is not added).
 *   3. publisher: the publisher's own copy, only where a manifest records a file with the same
 *      sha256 (publisher-copies.ts, from source/gpp/MANIFEST.csv). Unknown is null, never a guess.
 */
import { PUBLISHER_COPIES, type PublisherCopy } from "./publisher-copies.js";

export type { PublisherCopy };

export const REPO = "BetaNYC/New-York-City-Budget";
export const REPO_URL = `https://github.com/${REPO}`;
export const EXPLORER_URL = "https://betanyc.github.io/New-York-City-Budget/explorer/";

/** The fields of a row these links read. bbox_pt: x0,top,x1,bottom in points, unrotated page. */
export interface RowRef {
  source_pdf?: string | null;
  pdf_page?: number | string | null;
  bbox_pt?: string | readonly number[] | null;
  pdf_sha256?: string | null;
}

/** The explorer's URL state for the source view (the spdf/spage/sbox/slabel keys of hash.js). */
export interface SourceViewState {
  view: "source";
  spdf: string;
  spage: number;
  sbox: string;
  slabel: string;
}

export interface RowLinks {
  source_view: string | null;
  github: string | null;
  raw: string | null;
  publisher: PublisherCopy | null;
}

const encodePath = (p: string) => String(p).split("/").map(encodeURIComponent).join("/");

/** A source PDF's repo path, as the source view accepts it (Source.jsx), or null. */
export function sourcePdfPath(p: unknown): string | null {
  const s = typeof p === "string" ? p.trim() : "";
  return /^source\/.+\.pdf$/i.test(s) ? s : null;
}

/** A 1-based page number, or null. */
export function pdfPage(p: unknown): number | null {
  const n = typeof p === "number" ? p : typeof p === "string" && /^\s*\d+\s*$/.test(p) ? Number(p) : NaN;
  return Number.isInteger(n) && n >= 1 ? n : null;
}

/**
 * The box as the row carries it ("x0,top,x1,bottom"), whitespace removed; "" when absent or not
 * four numbers. Numbers are never reformatted, so the link carries the row's own digits.
 */
export function bboxParam(b: RowRef["bbox_pt"]): string {
  const s = Array.isArray(b) ? b.join(",") : typeof b === "string" ? b.replace(/\s+/g, "") : "";
  const parts = s.split(",");
  return parts.length === 4 && parts.every((x) => x !== "" && Number.isFinite(Number(x))) ? s : "";
}

/** The source view's state for a row, or null when the row names no PDF page. */
export function sourceViewState(row: RowRef, label = ""): SourceViewState | null {
  const spdf = sourcePdfPath(row.source_pdf);
  const spage = pdfPage(row.pdf_page);
  if (!spdf || spage === null) return null;
  return { view: "source", spdf, spage, sbox: bboxParam(row.bbox_pt), slabel: String(label ?? "").trim() };
}

/** "#view=source&spdf=…&spage=…&sbox=…&slabel=…", byte for byte what writeHash writes; "" if none. */
export function sourceViewHash(row: RowRef, label = ""): string {
  const s = sourceViewState(row, label);
  if (!s) return "";
  const params = new URLSearchParams();
  for (const key of ["view", "spdf", "spage", "sbox", "slabel"] as const) {
    const v = s[key];
    if (v === "" || v === null || v === undefined) continue;
    params.set(key, String(v));
  }
  return `#${params.toString()}`;
}

/** A repo file at a commit: GitHub's page for it and the raw download. Null without a commit. */
export function githubLinks(commit: string | null | undefined, path: string | null | undefined): { page: string; raw: string } | null {
  if (!commit || !path) return null;
  return {
    raw: `https://raw.githubusercontent.com/${REPO}/${encodeURIComponent(commit)}/${encodePath(path)}`,
    page: `${REPO_URL}/blob/${encodeURIComponent(commit)}/${encodePath(path)}`,
  };
}

/** The publisher's copy of a file with this sha256, or null when no manifest records one. */
export function publisherCopy(sha256: string | null | undefined): PublisherCopy | null {
  const k = String(sha256 ?? "").trim().toLowerCase();
  return Object.hasOwn(PUBLISHER_COPIES, k) ? PUBLISHER_COPIES[k] : null;
}

/**
 * A row's three links. `label` is the short text the source view shows above the page (e.g.
 * "Medicare Rights Center, $135,000"); `commit` is the commit the data was built from.
 */
export function rowLinks(row: RowRef, opts: { label?: string; commit?: string | null; explorerUrl?: string } = {}): RowLinks {
  const hash = sourceViewHash(row, opts.label);
  const pdf = sourcePdfPath(row.source_pdf);
  const gh = pdf ? githubLinks(opts.commit, pdf) : null;
  return {
    source_view: hash ? `${opts.explorerUrl ?? EXPLORER_URL}${hash}` : null,
    github: gh?.page ?? null,
    raw: gh?.raw ?? null,
    publisher: publisherCopy(row.pdf_sha256),
  };
}
