/**
 * No Council explorer view scrolls sideways on a phone (#330). Testing on main (2026-11-14) found two
 * that did on a Pixel 7 (412 CSS px): one award (230 px too wide) and one capital project (107 px),
 * because a long source URL and a sha256 in <code> did not wrap. Wide tables are fine: they
 * scroll inside their own .table-wrap, not the page.
 *
 * Phone project only (playwright.config.js, Pixel 7), at its own width and at 320 CSS px, the
 * width WCAG 1.4.10 (Reflow) names. City agency budgets has its own check
 * (agencies.mobile.spec.js).
 *
 * Measured against document.documentElement.clientWidth, the screen's width. Not
 * window.innerWidth: on a phone (a meta viewport and touch) the browser widens the layout to fit
 * content that sticks out, so innerWidth grows with the page and the check could never fail.
 */
import { expect, test } from "@playwright/test";

import { SITE_BUILT } from "./pending.js";
import { COUNCIL_VIEWS, open } from "./site.js";

/** Every Council view, plus one row of each kind and the PDF source viewer. */
export const REFLOW_VIEWS = {
  ...COUNCIL_VIEWS,
  "one award": "explorer/#view=award&ay=2026&row=2",
  "one capital project": "explorer/#view=capital-row&seq=1",
  review: "explorer/#view=review",
  // At a commit not on GitHub (a local build) the PDF cannot load, and the error quotes its URL:
  // that must wrap too.
  "PDF source viewer":
    "explorer/#view=source&spdf=source%2FFY27%2FFiscal-2027-Schedule-C-Final-3.pdf&spage=279&sbox=18.42%2C402.92%2C958.68%2C460.06&slabel=Medicare+Rights+Center%2C+%24135%2C000",
};

const PENDING = SITE_BUILT ? false : "e2e site not built: run `npm run e2e:site` first";
const describe = PENDING ? test.describe.skip : test.describe;

/**
 * What sticks out past the right edge, outside any element that scrolls on its own: an element
 * whose box passes the edge, or whose text overflows its box (a long word in a <p>).
 */
function overflowing() {
  const vw = document.documentElement.clientWidth;
  const scrolls = (el) => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX;
      if (o === "auto" || o === "scroll" || o === "hidden") return true;
    }
    return false;
  };
  return [...document.querySelectorAll("body *")]
    .filter((el) => (el.getBoundingClientRect().right > vw + 0.5 || el.scrollWidth > el.clientWidth + 1) && !scrolls(el))
    .slice(0, 5)
    .map((el) => `${el.tagName} ${el.outerHTML.slice(0, 100)}`);
}

describe(`Council explorer on a phone: no sideways scrolling${PENDING ? ` (${PENDING})` : ""}`, () => {
  for (const [name, path] of Object.entries(REFLOW_VIEWS)) {
    for (const width of [null, 320]) {
      test(`${name}, ${width ? `${width}px` : "phone viewport"}`, async ({ page }, info) => {
        test.skip(info.project.name !== "phone", "phone project only");
        if (width) await page.setViewportSize({ width, height: 740 });
        await open(page, path);
        // FAILS if the page is wider than the screen, naming what sticks out.
        const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        expect(over, `page wider than the viewport by ${over} CSS px: ${(await page.evaluate(overflowing)).join(" | ")}`).toBeLessThanOrEqual(0);
      });
    }
  }
});
