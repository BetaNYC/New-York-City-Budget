/**
 * Sortable one-year tables, colored changes and split units (#307, from Noel's demos
 * /tmp/mock-gen/sort-colors.html and brand.html). Axe (with color-contrast) and Pixel 7 target
 * size run on the same pages in agencies.a11y / agencies.mobile; this checks the behavior.
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const describe = VIEW_PENDING ? test.describe.skip : test.describe;
const NYPD_26 = "explorer/#view=agencies&abfy=2026&abag=056";

/** The exact figures in one column, top to bottom (null for words). */
async function column(page, label) {
  return page.locator(`section.one-year tbody td[data-label="${label}"]`).evaluateAll((tds) =>
    tds.map((td) => {
      const t = td.querySelector(".visually-hidden")?.textContent;
      return t ? Number(t.replace(/[^0-9.-]/g, "")) : null;
    })
  );
}
const isSorted = (xs, dir) => {
  const nums = xs.filter((x) => x !== null);
  const tail = xs.slice(nums.length);
  return tail.every((x) => x === null) && nums.every((x, i) => i === 0 || (dir === "asc" ? nums[i - 1] <= x : nums[i - 1] >= x));
};

describe(`City agency budgets: sorting, colors, split units${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  for (const [name, path, noun] of [
    ["list", PAGES.list, "agency"],
    ["agency", NYPD_26, "unit"],
  ]) {
    test(`default is adopted high to low; headers are buttons with aria-sort: ${name}`, async ({ page }) => {
      await openView(page, path);
      const heads = page.locator("section.one-year thead th");
      await expect(heads).toHaveCount(5);
      for (const th of await heads.all()) await expect(th.locator("button")).toHaveCount(1);
      await expect(page.locator('section.one-year thead th[aria-sort]')).toHaveCount(1);
      await expect(heads.nth(1)).toHaveAttribute("aria-sort", "descending");
      await expect(heads.nth(1).locator(".arrow")).toHaveText("▼");
      const fy = path.includes("2026") ? 2026 : 2025;
      expect(isSorted(await column(page, `Adopted FY${fy}`), "desc")).toBe(true);
    });

    test(`sort by keyboard: aria-sort, arrow, order and the live message all follow: ${name}`, async ({ page }) => {
      // FAILS if a keyboard user cannot sort, or the change is not announced.
      await openView(page, path);
      const fy = path.includes("2026") ? 2026 : 2025;
      const heads = page.locator("section.one-year thead th");
      const status = page.locator("section.one-year .sort-status");
      await expect(status).toHaveAttribute("aria-live", "polite");

      const modified = heads.nth(3).locator("button");
      await modified.focus();
      await page.keyboard.press("Enter");
      await expect(heads.nth(3)).toHaveAttribute("aria-sort", "ascending");
      await expect(heads.nth(3).locator(".arrow")).toHaveText("▲");
      await expect(heads.nth(1)).not.toHaveAttribute("aria-sort", /.+/);
      await expect(status).toHaveText(`Sorted by Modified FY${fy}, low to high. Rows with no figure are last.`);
      expect(isSorted(await column(page, `Modified FY${fy}`), "asc")).toBe(true);
      await page.keyboard.press("Space");
      await expect(heads.nth(3)).toHaveAttribute("aria-sort", "descending");
      await expect(status).toContainText("high to low");
      expect(isSorted(await column(page, `Modified FY${fy}`), "desc")).toBe(true);

      const nameBtn = heads.nth(0).locator("button");
      await nameBtn.focus();
      await page.keyboard.press("Enter");
      await expect(status).toHaveText(`Sorted by ${noun} number.`);
      await expect(heads.nth(0)).toHaveAttribute("aria-sort", "ascending");
      await page.keyboard.press("Enter");
      await expect(status).toHaveText(`Sorted by ${noun} name, A to Z.`);
      await expect(heads.nth(0).locator(".arrow")).toHaveText("A–Z");
    });

    test(`changes are green up and red down, bold, with their sign; contrast passes: ${name}`, async ({ page }) => {
      // FAILS if color is the only signal, or the green/red fail 4.5:1 (axe color-contrast).
      await openView(page, path);
      const up = page.locator("section.one-year tbody .up").first();
      const down = page.locator("section.one-year tbody .down").first();
      await expect(up).toBeVisible();
      await expect(down).toBeVisible();
      expect(await up.evaluate((el) => [getComputedStyle(el).color, getComputedStyle(el).fontWeight])).toEqual(["rgb(10, 122, 61)", "600"]);
      expect(await down.evaluate((el) => [getComputedStyle(el).color, getComputedStyle(el).fontWeight])).toEqual(["rgb(179, 38, 30)", "600"]);
      await expect(up.locator('[aria-hidden="true"]')).toHaveText(/^\+/);
      await expect(down.locator('[aria-hidden="true"]')).toHaveText(/^−/);
      // Both change columns carry the color.
      for (const label of [/^vs\. FY\d{4} adopted$/, /^Modified vs\. adopted$/]) {
        const n = await page.locator("section.one-year tbody td").evaluateAll((tds, src) => tds.filter((td) => new RegExp(src).test(td.dataset.label) && td.querySelector(".up, .down")).length, label.source);
        expect(n, String(label)).toBeGreaterThan(0);
      }
      const results = await new AxeBuilder({ page }).withRules(["color-contrast"]).analyze();
      expect(results.violations.flatMap((v) => v.nodes.map((n) => n.target.join(" ")))).toEqual([]);
    });
  }

  test("NYPD FY2026: the note above the units, and 001's drop names the units new that year", async ({ page }) => {
    await openView(page, NYPD_26);
    await expect(page.locator("section.one-year .split-note")).toHaveText("Units can be split or renumbered between years; a large change may be a move, not a cut.");
    const row = page.locator("section.one-year tbody tr", { has: page.locator("th", { hasText: /^001\s/ }) });
    await expect(row.locator(".split")).toHaveText("POLICE DEPARTMENT added units 011, 012, 110, 120 in FY2026");
    const unit11 = page.locator("section.one-year tbody tr", { has: page.locator("th", { hasText: /^011\s/ }) });
    await expect(unit11.locator('td[data-label="vs. FY2025 adopted"]')).toHaveText("New unit in FY2026");
  });

  test("short money in the one-year table, the exact figure on hover and for screen readers", async ({ page }) => {
    await openView(page, NYPD_26);
    const cell = page.locator("section.one-year tbody tr", { has: page.locator("th", { hasText: /^011\s/ }) }).locator('td[data-label="Adopted FY2026"]');
    await expect(cell.locator('[aria-hidden="true"]')).toHaveText("$766.6M");
    await expect(cell.locator("[title]")).toHaveAttribute("title", "$766,619,276");
    await expect(cell.locator(".visually-hidden")).toHaveText("$766,619,276");
  });
});
