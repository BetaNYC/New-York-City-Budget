/**
 * The citywide chart and summary on the agency list (#300): the old /agencies/ app opened with
 * them; the new view must too, accessibly, with the newest year's modified "Not yet published".
 * Axe and reflow run on the same page in agencies.a11y / agencies.mobile; this checks the content.
 */
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const describe = VIEW_PENDING ? test.describe.skip : test.describe;

describe(`City agency budgets: citywide chart and summary${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  test("FY2026: the old app's figures and changes, a chart with a text alternative, and a table", async ({ page }) => {
    await openView(page, "explorer/#view=agencies&abfy=2026");
    const city = page.locator("section.citywide");
    await expect(city.getByRole("heading", { level: 3 })).toHaveText(/^New York City budget, FY2017–FY\d{4}$/);
    const summary = city.locator(".citywide-summary");
    await expect(summary).toContainText("adopted $117,791,473,676 (+3.0% from FY2025)");
    await expect(summary).toContainText("modified $129,228,819,136 (+4.3% from FY2025)");
    await expect(city.getByRole("img", { name: /^New York City budget: adopted and modified budget, FY2017–FY/ })).toBeVisible();
    // The table is in a closed "Show the citywide numbers as a table": open it from the keyboard.
    const opener = city.getByText("Show the citywide numbers as a table");
    await opener.focus();
    await page.keyboard.press("Enter");
    const table = city.getByRole("table");
    await expect(table.locator("caption")).toContainText("New York City budget, all agencies");
    await expect(table.getByRole("row")).toHaveCount(1 + 11);
  });

  test("the newest year: modified is not yet published, never $0", async ({ page }) => {
    await openView(page, PAGES.list.replace("abfy=2025", "abfy=2027"));
    const summary = page.locator(".citywide-summary");
    await expect(summary).toContainText("modified Not yet published");
    await expect(summary).not.toContainText("$0");
    await page.locator("section.citywide summary").click();
    const last = page.locator("section.citywide table tbody tr").last();
    await expect(last.locator("th")).toHaveText("FY2027");
    await expect(last.locator('td[data-label="Modified"]')).toHaveText("Not yet published");
  });

  test("the chart comes before the agency table, and the table is reachable by keyboard scrolling", async ({ page }) => {
    await openView(page, PAGES.list);
    const order = await page.evaluate(() => {
      const a = document.querySelector("section.citywide");
      const b = document.querySelector("table.agency-table");
      return Boolean(a && b && a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    });
    expect(order).toBe(true);
    // Nothing in the citywide section scrolls on its own (a scroll area a keyboard can't reach).
    const scrollers = await page.evaluate(() =>
      [...document.querySelectorAll("section.citywide *")].filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== "visible").length
    );
    expect(scrollers).toBe(0);
  });
});
