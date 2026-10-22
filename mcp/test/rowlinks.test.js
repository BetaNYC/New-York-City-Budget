/**
 * The row-link builder (src/rowlinks.ts, #210), shared with the explorer, which imports
 * dist/rowlinks.js. The explorer's test (viz/explorer/test/unit/rowlinks.test.js) proves its
 * writeHash agrees on every row; this one covers the MCP side: the published FY2027 example, the
 * GitHub links, and the publisher's copy, looked up by sha256 and never guessed.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { rowLinks, publisherCopy, githubLinks, REPO_URL } from "../dist/rowlinks.js";
import { render, OUT } from "../scripts/build-publisher-copies.mjs";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const sha256 = (rel) => createHash("sha256").update(readFileSync(join(REPO, rel))).digest("hex");

const MEDICARE = {
  source_pdf: "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf",
  pdf_page: 279,
  bbox_pt: "18.42,402.92,958.68,460.06",
  pdf_sha256: "63c03739d3ac5e4f53f8e869dff829e7d832634419067bbdc5699bced6eed955",
};

test("the FY2027 Medicare Rights Center row: the epic's source-view link, exactly", () => {
  const l = rowLinks(MEDICARE, { label: "Medicare Rights Center, $135,000", commit: "3af3c7cf29e5" });
  assert.equal(
    l.source_view,
    "https://betanyc.github.io/New-York-City-Budget/explorer/#view=source&spdf=source%2FFY27%2FFiscal-2027-Schedule-C-Final-3.pdf&spage=279&sbox=18.42%2C402.92%2C958.68%2C460.06&slabel=Medicare+Rights+Center%2C+%24135%2C000"
  );
  assert.equal(l.github, "https://github.com/BetaNYC/New-York-City-Budget/blob/3af3c7cf29e5/source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf");
  assert.equal(l.raw, "https://raw.githubusercontent.com/BetaNYC/New-York-City-Budget/3af3c7cf29e5/source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf");
  assert.equal(l.publisher, null, "no manifest records the Council's copy of this file");
});

test("no commit: no GitHub link (the source view needs none)", () => {
  const l = rowLinks(MEDICARE, { label: "x" });
  assert.equal(l.github, null);
  assert.equal(l.raw, null);
  assert.ok(l.source_view);
  assert.equal(githubLinks("abc", ""), null);
});

test("a page as text (as CSV rows carry it) gives the same link as a number", () => {
  assert.equal(rowLinks({ ...MEDICARE, pdf_page: "279" }).source_view, rowLinks(MEDICARE).source_view);
});

test("the publisher's copy is found by sha256 only, from source/gpp/MANIFEST.csv", () => {
  // FY2010 Schedule C: the portal's file is byte for byte the one in source/FY10 (same_as_existing).
  const sha = sha256("source/FY10/fy_2010_sched_c_final.pdf");
  const p = publisherCopy(sha);
  assert.ok(p, "the FY2010 Schedule C is on the portal");
  assert.equal(p.url, "https://a860-gpp.nyc.gov/downloads/5x21tg38b");
  assert.equal(p.manifest, "source/gpp/MANIFEST.csv");
  assert.deepEqual(rowLinks({ source_pdf: "source/FY10/fy_2010_sched_c_final.pdf", pdf_page: 3, pdf_sha256: sha.toUpperCase() }).publisher, p);
  assert.equal(publisherCopy("0".repeat(64)), null);
  assert.equal(publisherCopy(""), null);
  assert.equal(publisherCopy("constructor"), null, "only the table's own keys");
});

test("every publisher entry is a file the manifest downloaded (HTTP 200), keyed by its sha256", () => {
  const rows = parse(readFileSync(join(REPO, "source/gpp/MANIFEST.csv"), "utf8"), { columns: true, bom: true });
  for (const r of rows) {
    const p = publisherCopy(r.sha256);
    assert.ok(p, `${r.file || r.same_as || r.label}`);
    assert.equal(p.url, r.url);
    assert.match(p.url, /^https:\/\/a860-gpp\.nyc\.gov\/downloads\//);
  }
});

test("src/publisher-copies.ts is what scripts/build-publisher-copies.mjs writes from the manifest", () => {
  assert.equal(readFileSync(OUT, "utf8"), render(), "run: node scripts/build-publisher-copies.mjs");
});

test("the server cites the same repository the links point at", () => {
  assert.equal(REPO_URL, "https://github.com/BetaNYC/New-York-City-Budget");
  assert.match(readFileSync(join(REPO, "mcp/src/server.ts"), "utf8"), /import \{ REPO_URL \} from "\.\/rowlinks\.js";/);
});
