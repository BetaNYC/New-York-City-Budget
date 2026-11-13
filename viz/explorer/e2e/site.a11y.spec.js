/**
 * Every page of the site and every Council explorer view meets WCAG 2.2 AA (#304), with the same
 * checks agencies.a11y.spec.js runs on City agency budgets: axe-core with the WCAG 2.2 A and AA
 * tags (wcag22aa adds target-size, WCAG 2.5.8, which matters most on the phone project), exactly
 * one main and one h1, every nav named, no skipped heading level, and a caption on every table.
 * Runs in both projects: desktop and Pixel 7 (playwright.config.js).
 *
 * axe-core via @axe-core/playwright, as in https://playwright.dev/docs/accessibility-testing.
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { SITE_BUILT } from "./pending.js";
import { COUNCIL_VIEWS, STATIC_PAGES, open } from "./site.js";

const WCAG_22_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const report = (violations) => violations.map((v) => `${v.id}: ${v.help} (${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join("; ")})`);

const PENDING = SITE_BUILT ? false : "e2e site not built: run `npm run e2e:site` first";
const describe = PENDING ? test.describe.skip : test.describe;

describe(`Every page and view: WCAG 2.2 AA${PENDING ? ` (${PENDING})` : ""}`, () => {
  for (const [name, path] of Object.entries({ ...STATIC_PAGES, ...COUNCIL_VIEWS })) {
    test(`axe, landmarks, headings and table captions: ${name}`, async ({ page }) => {
      await open(page, path);

      // FAILS on any axe violation for these tags, on the whole page (shell, header and content).
      const results = await new AxeBuilder({ page }).withTags(WCAG_22_AA).analyze();
      expect(report(results.violations)).toEqual([]);

      // FAILS if there is not exactly one main and one h1, or a nav has no name.
      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);
      for (const nav of await page.locator("nav").all()) {
        const named = await nav.evaluate((el) => Boolean(el.getAttribute("aria-label") || el.getAttribute("aria-labelledby")));
        expect(named, await nav.evaluate((el) => el.outerHTML.slice(0, 120))).toBe(true);
      }

      // FAILS if a heading level is skipped (h2 straight to h4).
      const levels = await page.locator("h1, h2, h3, h4, h5, h6").evaluateAll((hs) => hs.map((h) => Number(h.tagName[1])));
      for (let i = 1; i < levels.length; i++) expect(levels[i] - levels[i - 1], `heading levels ${levels.join(",")}`).toBeLessThanOrEqual(1);

      // FAILS if a screen reader can't tell what a table is. textContent, not innerText: a
      // visually hidden caption, or a table in a closed <details>, is still a caption.
      for (const t of await page.locator("table").all()) {
        await expect(t.locator(":scope > caption")).toHaveCount(1);
        expect(((await t.locator(":scope > caption").textContent()) ?? "").trim().length, await t.evaluate((el) => el.outerHTML.slice(0, 120))).toBeGreaterThan(0);
      }
    });
  }
});
