/**
 * The row-link builder the explorer shares with the MCP (mcp/src/rowlinks.ts, imported from
 * mcp/dist/rowlinks.js; #210). For every row of every PDF family-year in data/fy* /pdf/, the
 * MCP's source-view link and the explorer's own writeHash give the same hash, and readHash reads
 * the row back exactly.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";

import { EXPLORER_URL, rowLinks, sourceViewHash, sourceViewState } from "../../../../mcp/dist/rowlinks.js";
import { SourcePageLink } from "../../src/components/pdf.jsx";
import { DEFAULT_STATE, readHash, writeHash } from "../../src/state/hash.js";

const REPO = join(import.meta.dirname, "..", "..", "..", "..");

/** RFC 4180 CSV (quoted fields may hold commas, quotes and newlines) -> objects. */
function readCsv(path) {
  const text = readFileSync(path, "utf8").replace(/^﻿/, "");
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') (field += '"'), i++;
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") row.push(field), (field = "");
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field), rows.push(row), (row = []), (field = "");
    } else field += c;
  }
  if (field || row.length) row.push(field), rows.push(row);
  const [head, ...body] = rows;
  return body.filter((r) => r.length > 1).map((r) => Object.fromEntries(head.map((h, j) => [h, r[j] ?? ""])));
}

const walk = (dir) => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? walk(join(dir, f)) : [join(dir, f)]));

/** Every data row file: data/fy*\/pdf/<family>/*.csv, not the review queues (page 0 = whole file). */
const ROW_FILES = readdirSync(join(REPO, "data"))
  .filter((d) => /^fy\d\d$/.test(d))
  .flatMap((d) => {
    const p = join(REPO, "data", d, "pdf");
    try {
      return walk(p).filter((f) => f.endsWith(".csv") && !f.endsWith("_review.csv"));
    } catch {
      return [];
    }
  });

/** A short label like the explorer's own, with the characters that need encoding. */
const labelOf = (r) => [r.org || r.organization || r.title || r.agency_name || r.chart_title || r.name || r.category || "", r.amount ? `$${Number(r.amount).toLocaleString("en-US")}` : ""].filter(Boolean).join(", ");

const MEDICARE = {
  source_pdf: "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf",
  pdf_page: 279,
  bbox_pt: "18.42,402.92,958.68,460.06",
  pdf_sha256: "63c03739d3ac5e4f53f8e869dff829e7d832634419067bbdc5699bced6eed955",
};
const MEDICARE_URL =
  "https://betanyc.github.io/New-York-City-Budget/explorer/#view=source&spdf=source%2FFY27%2FFiscal-2027-Schedule-C-Final-3.pdf&spage=279&sbox=18.42%2C402.92%2C958.68%2C460.06&slabel=Medicare+Rights+Center%2C+%24135%2C000";

describe("the FY2027 example (Medicare Rights Center, Schedule C p.279)", () => {
  test("the shared builder writes the epic's link exactly", () => {
    expect(rowLinks(MEDICARE, { label: "Medicare Rights Center, $135,000", commit: "3af3c7c" }).source_view).toBe(MEDICARE_URL);
  });
  test("the explorer's writeHash writes the same hash, and readHash reads the row back", () => {
    const hash = new URL(MEDICARE_URL).hash;
    expect(writeHash({ ...DEFAULT_STATE, ...sourceViewState(MEDICARE, "Medicare Rights Center, $135,000") })).toBe(hash);
    const s = readHash(hash);
    expect([s.view, s.spdf, s.spage, s.sbox, s.slabel]).toEqual(["source", MEDICARE.source_pdf, 279, MEDICARE.bbox_pt, "Medicare Rights Center, $135,000"]);
    expect(writeHash(s)).toBe(hash);
  });
  test("the row is in the committed data at that page and box", () => {
    const rows = readCsv(join(REPO, "data/fy27/pdf/schedule_c/fy27_sc_awards.csv"));
    const r = rows.find((x) => x.pdf_page === "279" && x.bbox_pt === MEDICARE.bbox_pt);
    expect(r?.org).toMatch(/^Medicare Rights Center/);
    expect(Number(r?.amount)).toBe(135000);
    expect(r.pdf_sha256).toBe(MEDICARE.pdf_sha256);
  });
});

describe("every row of every family-year: one link, both ways", () => {
  test("the files cover all four families", () => {
    const fams = new Set(ROW_FILES.map((f) => f.split("/pdf/")[1].split("/")[0]));
    expect([...fams].sort()).toEqual(["capital_sd", "schedule_c", "terms", "transparency"]);
  });

  test("sourceViewHash equals writeHash and round-trips through readHash", () => {
    let checked = 0;
    const seen = new Set();
    for (const f of ROW_FILES) {
      for (const r of readCsv(f)) {
        if (!r.source_pdf || !r.pdf_page) continue;
        const label = labelOf(r);
        const state = sourceViewState(r, label);
        expect(state, `${f}: ${r.source_pdf} p.${r.pdf_page}`).not.toBeNull();
        const hash = sourceViewHash(r, label);
        expect(writeHash({ ...DEFAULT_STATE, ...state })).toBe(hash);
        const back = readHash(hash);
        expect(back.spdf).toBe(r.source_pdf);
        expect(back.spage).toBe(Number(r.pdf_page));
        expect(back.sbox).toBe(r.bbox_pt ?? "");
        expect(back.slabel).toBe(label);
        seen.add(f.split("/pdf/")[1].split("/")[0] + "|" + r.fiscal_year);
        checked++;
      }
    }
    // Every family-year in data/pdf_years.csv.
    const years = readCsv(join(REPO, "data/pdf_years.csv")).map((y) => `${y.family}|${y.fiscal_year}`);
    expect([...seen].sort()).toEqual([...new Set(years)].sort());
    expect(checked).toBeGreaterThan(100_000);
  }, 120_000);

  test("SourcePageLink (the explorer's in-app link) uses the same target state", () => {
    const html = renderToStaticMarkup(
      createElement(SourcePageLink, { state: DEFAULT_STATE, go: () => {}, pdf: MEDICARE.source_pdf, page: "279", bbox: MEDICARE.bbox_pt, label: "Medicare Rights Center, $135,000" })
    );
    const href = /href="([^"]+)"/.exec(html)[1].replaceAll("&amp;", "&");
    expect(href).toBe(new URL(MEDICARE_URL).hash);
  });
});

describe("edge cases", () => {
  test("labels with &, #, +, = and non-ASCII survive the trip", () => {
    const label = "Ali Forney Center & Co. #2 + 1 = Fornay–Avilés ‘café’";
    const hash = sourceViewHash({ source_pdf: "source/FY27/a b.pdf", pdf_page: "3", bbox_pt: "1,2,3,4" }, label);
    expect(writeHash({ ...DEFAULT_STATE, ...readHash(hash) })).toBe(hash);
    expect(readHash(hash).slabel).toBe(label);
    expect(readHash(hash).spdf).toBe("source/FY27/a b.pdf");
  });
  test("no box or no label: the keys are left out, as writeHash leaves them out", () => {
    const r = { source_pdf: "source/FY27/x.pdf", pdf_page: 61 };
    expect(sourceViewHash(r)).toBe("#view=source&spdf=source%2FFY27%2Fx.pdf&spage=61");
    expect(writeHash({ ...DEFAULT_STATE, ...sourceViewState(r) })).toBe(sourceViewHash(r));
  });
  test("no page, a page that is not a whole number, or a path outside source/: no link", () => {
    expect(sourceViewState({ source_pdf: "source/FY27/x.pdf", pdf_page: "" })).toBeNull();
    expect(sourceViewState({ source_pdf: "source/FY27/x.pdf", pdf_page: "0" })).toBeNull(); // a review item about the whole file
    expect(sourceViewState({ source_pdf: "source/FY27/x.pdf", pdf_page: "2.5" })).toBeNull();
    expect(sourceViewState({ source_pdf: "data/x.pdf", pdf_page: 2 })).toBeNull();
    expect(sourceViewState({ source_pdf: "source/FY26/transparency-resolutions/", pdf_page: 2 })).toBeNull();
    expect(rowLinks({ source_pdf: "data/x.pdf", pdf_page: 2 }, { commit: "abc" })).toEqual({ source_view: null, github: null, raw: null, publisher: null });
  });
  test("a malformed box is dropped, never passed on", () => {
    expect(sourceViewState({ source_pdf: "source/FY27/x.pdf", pdf_page: 1, bbox_pt: "1,2,3" }).sbox).toBe("");
    expect(sourceViewState({ source_pdf: "source/FY27/x.pdf", pdf_page: 1, bbox_pt: " 1, 2,3,4 " }).sbox).toBe("1,2,3,4");
  });
  test("the explorer link is the deployed explorer", () => {
    expect(EXPLORER_URL).toBe("https://betanyc.github.io/New-York-City-Budget/explorer/");
  });
});
