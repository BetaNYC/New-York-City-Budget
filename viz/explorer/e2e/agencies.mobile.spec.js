/**
 * The Agency budgets view on a phone (#270; view in #286, checks in #287).
 *
 * PENDING #286 / #284: skipped until the view and its data exist (e2e/pending.js).
 *
 * Runs in both projects (desktop and phone, playwright.config.js) and also at 320 CSS px, the
 * width WCAG 1.4.10 (Reflow) names: content must fit with no sideways scrolling. Tables reflow
 * (stacked rows or fewer columns), they do not scroll sideways.
 * Touch targets: at least 24x24 CSS px for every control (WCAG 2.2, 2.5.8, AA), and 44x44 for
 * the view's own buttons, selects and inputs (the site shell's rule, viz/site_shell.py).
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const describe = VIEW_PENDING ? test.describe.skip : test.describe;

/** Widths to check: the project's own, and 320 (WCAG reflow) and 375 (a small phone). */
const WIDTHS = [null, 320, 375];

describe(`Agency budgets on a phone${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  for (const [name, path] of Object.entries(PAGES)) {
    for (const width of WIDTHS) {
      const label = width ? `${width}px` : "project viewport";
      test(`no sideways scrolling: ${name}, ${label}`, async ({ page }) => {
        // FAILS if the page, or any table in the view, is wider than the screen.
        if (width) await page.setViewportSize({ width, height: 740 });
        await openView(page, path);
        const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        expect(over, "page wider than the viewport, in CSS px").toBeLessThanOrEqual(0);
        for (const t of await page.locator('[data-view="agencies"] table').all()) {
          const box = await t.boundingBox();
          if (!box) continue;
          expect(box.x, "table starts on screen").toBeGreaterThanOrEqual(0);
          expect(box.x + box.width, "table ends on screen").toBeLessThanOrEqual(await page.evaluate(() => window.innerWidth) + 0.5);
        }
      });
    }

    test(`touch targets: ${name}`, async ({ page }) => {
      // FAILS if a control is smaller than 24x24 (2.5.8), or the view's own buttons, selects and
      // inputs are smaller than 44x44.
      await page.setViewportSize({ width: 375, height: 740 });
      await openView(page, path);
      const results = await new AxeBuilder({ page }).withRules(["target-size"]).analyze();
      expect(results.violations.map((v) => v.nodes.map((n) => n.target.join(" "))).flat()).toEqual([]);
      const small = await page.locator('[data-view="agencies"] :is(button, select, input, summary)').evaluateAll((els) =>
        els
          .filter((el) => el.offsetParent !== null)
          .map((el) => ({ el: el.outerHTML.slice(0, 80), w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height }))
          .filter((b) => b.w < 44 || b.h < 44)
      );
      expect(small).toEqual([]);
    });
  }

  for (const name of ["list", "agency"]) {
    test(`the open over-time table stacks at 320px, every cell labeled, picker below it: ${name}`, async ({ page }) => {
      // FAILS if the five-column trend table (#306) scrolls sideways or loses its labels when
      // stacked, or the year picker moves above the chart on a phone.
      await page.setViewportSize({ width: 320, height: 740 });
      await openView(page, PAGES[name]);
      const table = page.locator("section.trend table");
      await expect(table).toBeVisible();
      const unlabeled = await table.locator("tbody td").evaluateAll((tds) => tds.filter((td) => !td.getAttribute("data-label")).length);
      expect(unlabeled).toBe(0);
      const chart = await page.locator('section.trend svg[role="img"]').boundingBox();
      const picker = await page.locator("section.one-year select").boundingBox();
      expect(picker.y, "picker is below the chart").toBeGreaterThan(chart.y + chart.height);
      expect(picker.height).toBeGreaterThanOrEqual(44);
    });
  }

  test("text at 200% still fits: list at 375px", async ({ page }) => {
    // FAILS if enlarged text (WCAG 1.4.4) pushes the list off the side of a phone.
    await page.setViewportSize({ width: 375, height: 740 });
    await openView(page, PAGES.list);
    await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(over).toBeLessThanOrEqual(0);
  });
});
