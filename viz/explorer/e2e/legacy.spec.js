/**
 * legacy.html, the retired first Council explorer (#304): a "this moved" page, and every old link
 * still lands somewhere useful.
 *
 * The old look-at-cook app's links: #?year=Y, #fund-detail/<category>(/<initiative>)?year=Y and
 * #control-officer-detail/<agency>(/<initiative>)?year=Y, with slugs for names. GitHub Pages can't
 * redirect on a #fragment, so the page's script forwards them into the explorer's Schedule C
 * search, and anything it can't map to the explorer's home.
 */
import { expect, test } from "@playwright/test";

import { SITE_BUILT } from "./pending.js";
import { councilReady } from "./site.js";

const PENDING = SITE_BUILT ? false : "e2e site not built: run `npm run e2e:site` first";
const describe = PENDING ? test.describe.skip : test.describe;

const hashOf = (page) => new URLSearchParams(new URL(page.url()).hash.slice(1));

describe(`legacy.html: this moved, and old links forward${PENDING ? ` (${PENDING})` : ""}`, () => {
  test("with no old link, the page stays and says where the explorer went", async ({ page }) => {
    // FAILS if a plain visit is bounced away, or the page doesn't point at the explorer.
    await page.goto("legacy.html");
    await expect(page.locator("h1")).toContainText(/moved/i);
    await expect(page.locator('main a[href="explorer/"]')).toBeVisible();
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/legacy\.html$/);
  });

  const SCHEDC = [
    ["legacy.html#?year=2025", { scfy: "2025" }],
    ["legacy.html#fund-detail/housing/community-land-trust?year=2026", { scfy: "2026", sccat: null, scinit: "Community Land Trust" }],
    ["legacy.html#control-officer-detail/dsny/community-composting?year=2026", { scfy: "2026", scagency: null, scinit: "Community Composting" }],
    ["legacy.html#fund-detail/housing?year=2026", { scfy: "2026", sccat: "Housing" }],
    ["legacy.html#control-officer-detail/dsny?year=2026", { scfy: "2026", scagency: "DSNY" }],
  ];
  for (const [from, want] of SCHEDC) {
    test(`${from} opens the same year and names in Schedule C`, async ({ page }) => {
      // FAILS if an old link people saved or shared lands on the wrong place, or on no rows.
      await page.goto(from);
      await page.waitForURL(/\/explorer\/#/);
      await councilReady(page);
      const params = hashOf(page);
      expect(params.get("view")).toBe("schedc");
      for (const [k, v] of Object.entries(want)) expect(params.get(k), k).toBe(v);
      await expect(page.locator("main .matched").first()).toHaveText(/^\d[\d,]* .* match\.$/);
    });
  }

  for (const from of ["legacy.html#?year=2016", "legacy.html#Fund/Something", "legacy.html#fund-detail/housing?year=2031"]) {
    test(`${from} goes to the explorer's home`, async ({ page }) => {
      // FAILS if a link the explorer can't show strands the visitor on the old page.
      await page.goto(from);
      await page.waitForURL(/\/explorer\/$/);
      await councilReady(page);
    });
  }

  test("the page's own skip link does not forward it", async ({ page }) => {
    // FAILS if a keyboard user who skips to the content and reloads is sent away.
    await page.goto("legacy.html#content");
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/legacy\.html#content$/);
  });
});
