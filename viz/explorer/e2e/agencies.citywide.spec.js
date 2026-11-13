/**
 * Trend first, then one year (#306; the citywide chart came back in #300). Every level answers
 * "how did this change over time" before "what did it look like in one year":
 *   list:   h2 (no year) · "What adopted and modified mean" · "The whole city, over time"
 *           (summary, chart, open table) · "Agencies in FY…" (year picker, then the agency table)
 *   agency: h2 · one-line note linking the explainer · "[Agency], over time" · "Its units in FY…"
 * Axe and reflow run on the same pages in agencies.a11y / agencies.mobile; this checks the content
 * and the order.
 */
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const describe = VIEW_PENDING ? test.describe.skip : test.describe;
const view = (page) => page.locator('[data-view="agencies"]');

/** Where in the document an element is, for order checks: -1 before, 1 after. */
async function before(page, a, b) {
  return page.evaluate(
    ([sa, sb]) => {
      const x = document.querySelector(sa);
      const y = document.querySelector(sb);
      return Boolean(x && y && x.compareDocumentPosition(y) & Node.DOCUMENT_POSITION_FOLLOWING);
    },
    [a, b]
  );
}

const PICKER = '[data-view="agencies"] select';
const CHART = '[data-view="agencies"] svg[role="img"]';

describe(`City agency budgets: trend first, then one year${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  for (const name of ["list", "agency"]) {
    test(`the year picker comes after the over-time chart, inside the one-year section: ${name}`, async ({ page }) => {
      // FAILS if the year picker is put back above the chart it does not change (Noel, #306).
      await openView(page, PAGES[name]);
      expect(await before(page, CHART, PICKER), "chart before picker in DOM order").toBe(true);
      expect(await before(page, '[data-view="agencies"] section.trend', '[data-view="agencies"] section.one-year')).toBe(true);
      await expect(page.locator("section.one-year select")).toHaveCount(1);
      await expect(page.locator("section.trend select")).toHaveCount(0);
      // The picker is labeled by the section it changes, and changing it leaves the trend alone.
      const chartName = () => page.locator(CHART).evaluate((el) => document.getElementById(el.getAttribute("aria-labelledby") ?? "")?.textContent ?? el.getAttribute("aria-label"));
      const label = await chartName();
      expect(label).toMatch(/FY2017–FY2027/);
      await page.getByLabel("Fiscal year").selectOption("2024");
      await expect(page.locator("section.one-year h3")).toHaveText(/FY2024$/);
      expect(await chartName()).toBe(label);
    });

    test(`only the one-year section's heading names a year: ${name}`, async ({ page }) => {
      // FAILS if the page heading or the over-time heading says "FY2025" again.
      await openView(page, PAGES[name]);
      const headings = await view(page).locator("h2, h3").allTextContents();
      const withYear = headings.filter((h) => /FY\s?\d{4}(?!–)/.test(h) && !/FY\d{4}–FY\d{4}/.test(h));
      expect(withYear).toEqual([await page.locator("section.one-year h3").textContent()]);
      expect(withYear[0]).toMatch(/^2\s/);
    });

    test(`change columns say which change, never a bare "Change": ${name}`, async ({ page }) => {
      await openView(page, PAGES[name]);
      for (const th of await view(page).locator("thead th").allTextContents()) expect(th.trim()).not.toMatch(/^(change|—)$/i);
      await expect(view(page).locator("thead th", { hasText: /^Modified vs\. adopted\s*$/ })).toHaveCount(2);
      // No change cell is a bare dash: a missing figure says why.
      const cells = await view(page).locator("tbody td").allTextContents();
      expect(cells.filter((c) => c.trim() === "—")).toEqual([]);
    });
  }

  test("list: the explainer, then the whole city over time with its table open", async ({ page }) => {
    await openView(page, "explorer/#view=agencies&abfy=2026");
    await expect(view(page).locator("h2")).toHaveText("All City agencies");
    const box = page.locator("section.explainer");
    await expect(box.getByRole("heading", { level: 3 })).toHaveText("What adopted and modified mean");
    await expect(box).toContainText("The budget the Mayor and City Council agree on in June, before the fiscal year starts. The plan.");
    await expect(box).toContainText("after the City moved money around. Closer to what happened.");
    await expect(box).toContainText("so FY2026 is July 2025 to June 2026");
    expect(await before(page, "section.explainer", "section.trend")).toBe(true);

    const trend = page.locator("section.trend");
    await expect(trend.getByRole("heading", { level: 3, name: "The whole city, over time" })).toBeVisible();
    await expect(trend.locator(".step")).toHaveText("1");
    // Short money on screen; the exact figure for screen readers and on hover (#307).
    const summary = trend.locator(".citywide-summary");
    await expect(summary).toContainText("In FY2026 the City adopted $117.8B");
    await expect(summary).toContainText("By year's end it stood at $129.2B");
    await expect(summary.locator('[title="$117,791,473,676"] .visually-hidden')).toHaveText("$117,791,473,676");
    await expect(trend.getByRole("img", { name: /^New York City budget: adopted and modified budget, FY2017–FY/ })).toBeVisible();
    const table = trend.getByRole("table");
    await expect(table).toBeVisible(); // open, not in a closed box
    await expect(table.locator("thead th")).toHaveText(["Fiscal year", "Adopted", "Adopted vs. year before", "Modified", "Modified vs. adopted"]);
    const shown = (cell) => cell.locator('[aria-hidden="true"]').first();
    await expect(table.locator("tbody tr")).toHaveCount(11);
    // The old /agencies/ app's FY2026 figures (Noel's QA), and the change from FY2025.
    const fy26 = table.locator("tbody tr", { has: page.locator("th", { hasText: /^FY2026$/ }) });
    await expect(shown(fy26.locator("td").nth(0))).toHaveText("$117.8B");
    await expect(fy26.locator("td").nth(0).locator(".visually-hidden")).toHaveText("$117,791,473,676");
    await expect(shown(fy26.locator("td").nth(1))).toHaveText("+3.0%");
    await expect(fy26.locator("td").nth(1).locator(".visually-hidden")).toHaveText("+$3,406,481,844 (+3.0%)");
    await expect(fy26.locator("td").nth(1).locator(".up")).toHaveCount(1);
    await expect(fy26.locator("td").nth(2).locator(".visually-hidden")).toHaveText("$129,228,819,136");
    await expect(table.locator("tbody tr").first().locator("td").nth(1)).toHaveText("No FY2016 figure");
    const fy27 = table.locator("tbody tr").last();
    await expect(fy27.locator("td").nth(2)).toHaveText("Not yet published");
    await expect(fy27.locator("td").nth(3)).toHaveText("Not yet published");

    const year = page.locator("section.one-year");
    await expect(year.getByRole("heading", { level: 3, name: "Agencies in FY2026" })).toBeVisible();
    await expect(year.locator(".step")).toHaveText("2");
    await expect(year.getByLabel("Fiscal year")).toHaveValue("2026");
    await expect(year.locator("table.agency-table")).toBeVisible();
    // A visible boundary between the two sections.
    const rule = await year.evaluate((el) => getComputedStyle(el).borderTopStyle !== "none" && parseFloat(getComputedStyle(el).borderTopWidth) > 0);
    expect(rule).toBe(true);
  });

  test("agency: a one-line note that links to the explainer, the trend, then its units in one year", async ({ page }) => {
    await openView(page, PAGES.agency);
    const note = view(page).locator(".explainer-note");
    await expect(note).toContainText(/adopted/i);
    await expect(note).toHaveText("Adopted = the plan agreed on in June. Modified = where it stood a year later. More about these.");
    await expect(view(page).getByRole("heading", { level: 3, name: "POLICE DEPARTMENT, over time" })).toBeVisible();
    await expect(view(page).locator("section.trend .citywide-summary")).toContainText(/In FY2026 the City adopted \$[\d.]+B\$[\d,]+ for POLICE DEPARTMENT/);
    await expect(view(page).locator("section.trend table")).toBeVisible();
    await expect(view(page).getByRole("heading", { level: 3, name: "Its units in FY2025" })).toBeVisible();
    await note.getByRole("link", { name: "More about these" }).click();
    await expect(page.locator("section.explainer h3")).toHaveText("What adopted and modified mean");
    await expect(page).not.toHaveURL(/abag=/);
  });

  test("the newest year: modified is not yet published, never $0", async ({ page }) => {
    await openView(page, PAGES.list.replace("abfy=2025", "abfy=2027"));
    const table = page.locator("section.one-year table");
    await expect(table.locator('td[data-label="Modified FY2027"]').first()).toHaveText("Not yet published");
    await expect(table.locator('td[data-label="Modified vs. adopted"]').first()).toHaveText("Not yet published");
    await expect(page.locator("section.trend .citywide-summary")).toContainText("its modified figure is not yet published");
    await expect(page.locator("section.trend .citywide-summary")).not.toContainText("$0");
  });

  test("nothing in the trend section scrolls on its own (a scroll area a keyboard can't reach)", async ({ page }) => {
    await openView(page, PAGES.list);
    const scrollers = await page.evaluate(() =>
      [...document.querySelectorAll("section.trend *")].filter((el) => !el.closest(".visually-hidden") && el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible").length
    );
    expect(scrollers).toBe(0);
  });
});
