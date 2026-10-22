/**
 * The source view opens with the row's box in view (#211), on rotated pages too. The pages are
 * real: pdf.js (its Node build) opens the committed PDFs, and the text pdf.js finds inside the
 * box must be the row's own text, so the box is where the row is drawn after /Rotate.
 */
import { join } from "node:path";
import { describe, expect, test } from "vitest";

import * as pdfjs from "pdfjs-dist/legacy/build/pdf.mjs";

import { landingSpot, rowBoxOnViewport } from "../../src/query/pdf.js";

const REPO = join(import.meta.dirname, "..", "..", "..", "..");

async function openPage(rel, n) {
  const doc = await pdfjs.getDocument({ url: join(REPO, rel), verbosity: 0 }).promise;
  return doc.getPage(n);
}

/** The text pdf.js draws with its origin inside the box (viewport pixels, padded). */
async function textInBox(page, viewport, box, pad = 2) {
  const { items } = await page.getTextContent();
  return items
    .filter((it) => {
      const [x, y] = viewport.convertToViewportPoint(it.transform[4], it.transform[5]);
      return x >= box.left - pad && x <= box.left + box.width + pad && y >= box.top - pad && y <= box.top + box.height + pad;
    })
    .map((it) => it.str)
    .join(" ");
}

/** After scrolling to the spot, is the whole box inside a pane of this size? */
const inPane = (box, spot, w, h) => box.top - spot.top >= 0 && box.top + box.height - spot.top <= h && box.left - spot.left >= 0 && box.left + box.width - spot.left <= w;

const CAPITAL = "source/FY27/Supporting-Detail-for-FY2027-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254.V4.pdf";

describe("a rotated page (FY2027 capital book p.47, /Rotate 90): HR CC0168", () => {
  const bbox = "489.30,176.03,506.46,769.62"; // data/fy27/pdf/capital_sd/fy27_capital_sd_projects.csv

  test("the box lands on the row as drawn, a wide strip across the turned page", async () => {
    const page = await openPage(CAPITAL, 47);
    expect(page.rotate).toBe(90);
    const vp = page.getViewport({ scale: 1.5 });
    const box = rowBoxOnViewport(bbox, page.view, vp);
    expect(box.width).toBeGreaterThan(box.height * 10); // a row across the landscape page
    expect(box.left).toBeGreaterThanOrEqual(0);
    expect(box.top).toBeGreaterThanOrEqual(0);
    expect(box.left + box.width).toBeLessThanOrEqual(vp.width);
    expect(box.top + box.height).toBeLessThanOrEqual(vp.height);
    const text = await textInBox(page, vp, box);
    expect(text).toContain("CC0168");
    expect(text).toContain("ALI FORNEY");
    expect(text).not.toContain("CC0167");
  });

  test("the landing spot puts the whole box in the pane, and survives pdf.js's XYZ jump", async () => {
    const page = await openPage(CAPITAL, 47);
    for (const scale of [0.8, 1.5, 3]) {
      const vp = page.getViewport({ scale });
      const box = rowBoxOnViewport(bbox, page.view, vp);
      const spot = landingSpot(box, 500);
      expect(inPane(box, spot, Math.max(box.width + 48, 400), 500)).toBe(true);
      // PdfViewer hands pdf.js the spot in PDF space; pdf.js maps it back with the same viewport.
      const [x, y] = vp.convertToPdfPoint(spot.left, spot.top);
      const [l, t] = vp.convertToViewportPoint(x, y);
      expect(l).toBeCloseTo(spot.left, 6);
      expect(t).toBeCloseTo(spot.top, 6);
    }
  });
});

describe("an upright page (FY2027 Schedule C p.279): the Medicare Rights Center row", () => {
  test("the box holds the row, and the landing spot shows it in a short pane", async () => {
    const page = await openPage("source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf", 279);
    expect(page.rotate).toBe(0);
    const vp = page.getViewport({ scale: 1.25 });
    const box = rowBoxOnViewport("18.42,402.92,958.68,460.06", page.view, vp);
    expect(await textInBox(page, vp, box)).toContain("Medicare Rights Center");
    // A pane shorter than the box's distance from the page top: at the page top the row is out of view.
    const pane = 400;
    expect(box.top + box.height).toBeGreaterThan(pane);
    expect(inPane(box, landingSpot(box, pane), vp.width, pane)).toBe(true);
  });
});

describe("landingSpot", () => {
  test("a quarter of the pane above the box, a margin to its left", () => {
    expect(landingSpot({ left: 100, top: 900, width: 500, height: 40 }, 600)).toEqual({ left: 76, top: 750 });
  });
  test("near the page top: never above the page", () => {
    expect(landingSpot({ left: 10, top: 50, width: 500, height: 40 }, 600)).toEqual({ left: 0, top: 0 });
  });
  test("a box too tall for a quarter-pane gap starts one margin down", () => {
    expect(landingSpot({ left: 100, top: 900, width: 500, height: 500 }, 600)).toEqual({ left: 76, top: 876 });
  });
});
