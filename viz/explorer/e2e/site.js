/**
 * Shared by the whole-site specs (#304; a spec file must not import another spec file): every page
 * of the site and every Council explorer view, and how to tell that each has finished loading.
 */
import { expect } from "@playwright/test";

/** The site's own pages, outside the explorer. agencies/ (the forwarding page) is in agencies.retired.spec.js. */
export const STATIC_PAGES = {
  home: "",
  about: "about.html",
  mcp: "mcp.html",
  legacy: "legacy.html",
  "agencies FAQ": "agencies/faq.html",
  "community boards": "agencies/boards.html",
  "community boards, one year": "agencies/boards.html#year=2027",
};

/** The Council explorer's views, as a visitor opens them (City agency budgets: agencies.a11y.spec.js). */
export const COUNCIL_VIEWS = {
  awards: "explorer/#view=awards",
  years: "explorer/#view=years",
  capital: "explorer/#view=capital",
  omb: "explorer/#view=omb",
  orgs: "explorer/#view=orgs",
  terms: "explorer/#view=terms",
  schedc: "explorer/#view=schedc",
  transparency: "explorer/#view=transparency",
  book: "explorer/#view=book",
  compare: "explorer/#view=compare",
  "about (explorer)": "explorer/#view=about",
};

/**
 * A Council view is ready when the query engine, its tables and its first query are done: no
 * loading notice, nothing aria-busy, no "Loading…" or "Updating…", and still so a moment later.
 */
export async function councilReady(page) {
  await page.locator("main#main").waitFor();
  const settled = () =>
    page.waitForFunction(
      () => {
        const main = document.querySelector("main#main");
        if (!main || document.querySelector(".loading, [aria-busy='true']")) return false;
        const text = main.innerText;
        return text.trim().length > 0 && !/Loading|Updating…|Starting…/.test(text);
      },
      null,
      { timeout: 150_000, polling: 250 },
    );
  await settled();
  await page.waitForTimeout(500);
  await settled();
}

/** Open a static page and wait until what it fetches (the community boards CSV) is on screen. */
export async function staticReady(page, path) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  if (/boards\.html#/.test(path)) await expect(page.locator("table tbody tr").first()).toBeVisible();
}

export async function open(page, path) {
  if (path.startsWith("explorer/")) {
    await page.goto(path);
    await councilReady(page);
  } else {
    await staticReady(page, path);
  }
}
