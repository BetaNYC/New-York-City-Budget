/**
 * Retiring the old Backbone app at /agencies/ (#270, done in #288): every old link still works.
 *
 * PENDING #288: skipped while viz/agencies/index.html is still the Backbone app (e2e/pending.js).
 *
 * The old app's links: #(?year=Y), #fund-detail/<agency>(/<unit>)?year=Y, and
 * #control-officer-detail/... (which #266 already forwarded to fund-detail). GitHub Pages can't
 * redirect on a #fragment (browsers don't send it), so /agencies/ becomes a small page whose script
 * forwards to ../explorer/#view=agencies&legacy=<path>&abfy=Y, with a plain link for no script.
 */
import { expect, test } from "@playwright/test";

import { RETIRED_PENDING } from "./pending.js";

const describe = RETIRED_PENDING ? test.describe.skip : test.describe;

const ready = (page) => page.locator('[data-view="agencies"][data-ready="true"]').waitFor({ timeout: 150_000 });

describe(`/agencies/ forwards to the explorer${RETIRED_PENDING ? ` (${RETIRED_PENDING})` : ""}`, () => {
  const CASES = [
    ["agencies/", { view: "agencies" }],
    ["agencies/#?year=2019", { abfy: "2019" }],
    ["agencies/#fund-detail/police-department?year=2025", { abag: "056", abfy: "2025" }],
    ["agencies/#fund-detail/police-department/operations?year=2024", { abag: "056", abunit: "001", abfy: "2024" }],
    ["agencies/#control-officer-detail/manhattan-community-board-1?year=2025", { abag: "341", abfy: "2025" }],
    ["agencies/#fund-detail/department-of-consumer-affairs", { abag: "866" }],
  ];
  for (const [from, want] of CASES) {
    test(`${from} lands on the same agency and year in the explorer`, async ({ page }) => {
      // FAILS if an old link people saved or shared now lands on the wrong place, or nowhere.
      await page.goto(from);
      await page.waitForURL(/\/explorer\//);
      await ready(page);
      const params = new URLSearchParams(new URL(page.url()).hash.slice(1));
      expect(params.get("view")).toBe("agencies");
      for (const [k, v] of Object.entries(want)) if (k !== "view") expect(params.get(k), k).toBe(v);
    });
  }

  test("a unit link whose name two units share asks which one, instead of guessing", async ({ page }) => {
    // FAILS if the page silently picks one of City Council's two "Committee on the Aging" units.
    await page.goto("agencies/#fund-detail/city-council/committee-on-the-aging");
    await page.waitForURL(/\/explorer\//);
    await ready(page);
    const view = page.locator('[data-view="agencies"]');
    await expect(view.getByRole("link", { name: /600/ })).toBeVisible();
    await expect(view.getByRole("link", { name: /800/ })).toBeVisible();
  });

  test("without JavaScript, /agencies/ still offers a link to the new view", async ({ browser }) => {
    // FAILS if a visitor with scripts off is stuck on a blank page.
    const ctx = await browser.newContext({ javaScriptEnabled: false });
    const page = await ctx.newPage();
    await page.goto("agencies/");
    await expect(page.locator('a[href^="../explorer/#view=agencies"]').first()).toBeVisible();
    await ctx.close();
  });

  test("the CSV download keeps its address", async ({ request }) => {
    // FAILS if a script or spreadsheet that fetches agencies/data/nyc_budget.csv breaks.
    const res = await request.get("agencies/data/nyc_budget.csv");
    expect(res.status()).toBe(200);
    expect((await res.text()).split("\n")[0]).toMatch(/^Fund,Department,Department ID,Adopted 2017,Modified 2017/);
  });
});
