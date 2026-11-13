/**
 * The Agency budgets view meets WCAG 2.2 AA (#270; view in #286, checks in #287).
 *
 * PENDING #286 / #284: skipped until the view and its data exist (e2e/pending.js).
 *
 * The view's contract with these specs (docs/plans/2026-11-12-270-agency-budgets.md):
 *   - Its root is `[data-view="agencies"]`, with data-ready="true" once its numbers are on screen.
 *   - The page's h1 names the half: "City agency budgets".
 *   - Every table has a caption and th scope; the year chart is an svg with role="img" and a name,
 *     next to a table with the same numbers.
 *   - The year picker is a <select> labeled "Fiscal year", inside the one-year section, after
 *     the over-time chart (#306; the order is checked in agencies.citywide.spec.js).
 *   - A polite live region says what is shown after a change ("Showing FY2024 ...").
 *   - Moving to an agency or unit puts focus on its heading.
 *
 * axe-core via @axe-core/playwright, as in https://playwright.dev/docs/accessibility-testing.
 * The tag list adds "wcag22aa" (axe-core 4.14: the target-size rule, WCAG 2.5.8).
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const WCAG_22_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
/** Readable axe failures: rule, help, and the first few elements. */
const report = (violations) => violations.map((v) => `${v.id}: ${v.help} (${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join("; ")})`);

const describe = VIEW_PENDING ? test.describe.skip : test.describe;

describe(`Agency budgets: WCAG 2.2 AA${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  for (const [name, path] of Object.entries(PAGES)) {
    test(`axe finds no WCAG 2.2 A or AA violation: ${name}`, async ({ page }) => {
      // FAILS on any axe violation for these tags, on the whole page (shell, header and view).
      await openView(page, path);
      const results = await new AxeBuilder({ page }).withTags(WCAG_22_AA).analyze();
      expect(report(results.violations)).toEqual([]);
    });

    test(`landmarks and headings: ${name}`, async ({ page }) => {
      // FAILS if there is not exactly one main and one h1, a nav has no name, or a heading level
      // is skipped (h2 straight to h4).
      await openView(page, path);
      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);
      await expect(page.locator("h1")).toContainText(/city agency budgets/i);
      for (const nav of await page.locator("nav").all()) {
        const named = await nav.evaluate((el) => Boolean(el.getAttribute("aria-label") || el.getAttribute("aria-labelledby")));
        expect(named, await nav.evaluate((el) => el.outerHTML.slice(0, 120))).toBe(true);
      }
      const levels = await page.locator("h1, h2, h3, h4, h5, h6").evaluateAll((hs) => hs.map((h) => Number(h.tagName[1])));
      for (let i = 1; i < levels.length; i++) expect(levels[i] - levels[i - 1], `heading levels ${levels.join(",")}`).toBeLessThanOrEqual(1);
    });

    test(`tables have captions and header scopes: ${name}`, async ({ page }) => {
      // FAILS if a screen reader can't tell what a table is, or which header a cell belongs to.
      await openView(page, path);
      const tables = page.locator('[data-view="agencies"] table');
      expect(await tables.count()).toBeGreaterThan(0);
      for (const t of await tables.all()) {
        await expect(t.locator("caption")).toHaveCount(1);
        // textContent, not innerText, so a table inside a closed <details> would still count.
        expect(((await t.locator("caption").textContent()) ?? "").trim().length).toBeGreaterThan(0);
        for (const th of await t.locator("th").all()) expect(["col", "row", "colgroup", "rowgroup"]).toContain(await th.getAttribute("scope"));
      }
      await expect(page.locator('[data-view="agencies"] th:visible', { hasText: /adopted/i }).first()).toBeVisible();
      await expect(page.locator('[data-view="agencies"] th:visible', { hasText: /modified/i }).first()).toBeVisible();
    });
  }

  test("the year chart has a text alternative and a table with the same numbers", async ({ page }) => {
    // FAILS if the chart is an unlabeled picture, or its numbers exist only as shapes.
    await openView(page, PAGES.agency);
    const chart = page.locator('[data-view="agencies"] svg[role="img"]');
    await expect(chart).toHaveCount(1);
    const name = await chart.evaluate((el) => el.getAttribute("aria-label") || document.getElementById(el.getAttribute("aria-labelledby") ?? "")?.textContent || "");
    expect(name).toMatch(/adopted/i);
    expect(name).toMatch(/modified/i);
    expect(name).toMatch(/2017/);
    const yearTable = page.locator('[data-view="agencies"] table', { has: page.locator("caption", { hasText: /by (fiscal )?year/i }) });
    await expect(yearTable).toHaveCount(1);
    await expect(yearTable.locator("tbody tr")).toHaveCount(11); // FY2017-FY2027
  });

  test("keyboard only: skip link, year picker, open an agency, focus lands on its heading", async ({ page }) => {
    // FAILS if a keyboard user can't skip the menus, reach the year picker, open an agency, or is
    // left with focus at the top of the page after the view changes.
    await openView(page, PAGES.list);
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toHaveText(/skip to/i);
    await page.keyboard.press("Enter");
    const year = page.getByLabel(/fiscal year/i);
    for (let i = 0; i < 40 && !(await year.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
    await expect(year).toBeFocused();
    const outline = await year.evaluate((el) => getComputedStyle(el).outlineStyle);
    expect(outline, "focus is visible on the year picker").not.toBe("none");
    const nypd = page.locator('[data-view="agencies"] a', { hasText: "POLICE DEPARTMENT" }).first();
    await nypd.focus();
    await page.keyboard.press("Enter");
    await page.locator('[data-view="agencies"][data-ready="true"]').waitFor();
    await expect(page).toHaveURL(/abag=056/);
    const focused = page.locator(":focus");
    await expect(focused).toHaveText(/POLICE DEPARTMENT/);
    expect(await focused.evaluate((el) => /^H[1-6]$/.test(el.tagName))).toBe(true);
  });

  test("the explainer and the trend are in the page's outline, before the one-year section", async ({ page }) => {
    // FAILS if a screen reader user browsing by heading meets the year picker's section before
    // the explanation and the trend (#306), or the explainer's terms are not a list.
    await openView(page, PAGES.list);
    const h3 = await page.locator('[data-view="agencies"] h3').allTextContents();
    expect(h3.slice(0, 3)).toEqual(["What adopted and modified mean", "The whole city, over time", "Agencies in FY2025"]);
    await expect(page.locator("section.explainer dt")).toHaveText(["Adopted", "Modified"]);
    for (const id of ["section.explainer", "section.trend", "section.one-year"]) {
      const named = await page.locator(id).evaluate((el) => document.getElementById(el.getAttribute("aria-labelledby") ?? "")?.textContent ?? "");
      expect(named.length, `${id} is named by its heading`).toBeGreaterThan(0);
    }
  });

  test("a change of year is announced in a polite live region", async ({ page }) => {
    // FAILS if a screen reader user changes the year and hears nothing.
    await openView(page, PAGES.list);
    await page.getByLabel(/fiscal year/i).selectOption("2024");
    const live = page.locator('[data-view="agencies"] [aria-live="polite"], [data-view="agencies"] [role="status"]');
    await expect(live.first()).toContainText(/FY ?2024/);
  });

  test("unpublished and absent figures are words, never $0", async ({ page }) => {
    // FAILS if the newest year's modified, or a unit not in a year's budget, shows as $0.
    await openView(page, "explorer/#view=agencies&abag=056&abunit=011");
    const view = page.locator('[data-view="agencies"]');
    await expect(view).toContainText(/not yet published/i); // FY2027 modified
    await expect(view).toContainText(/not in this year's budget/i); // NYPD 011, FY2025 adopted
  });

  test("an old /agencies/ link resolved in the explorer lands on the agency", async ({ page }) => {
    // FAILS if the legacy key isn't resolved and replaced (#288's forwarding page relies on it).
    await openView(page, "explorer/#view=agencies&legacy=police-department&abfy=2025");
    await expect(page).toHaveURL(/abag=056/);
    await expect(page).not.toHaveURL(/legacy=/);
  });
});
