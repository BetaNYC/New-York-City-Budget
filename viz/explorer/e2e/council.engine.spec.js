/**
 * Council views that need no query engine do not download it (#301, steps 1 and 4).
 *
 *   #view=about   About the data: manifest.json only.
 *   #view=review  on the public site: "No review queue in this build", with no engine and no
 *                 table. Before #301 it downloaded all 29 tables (22 MB) to say so.
 *
 * And leaving About for a view that needs the engine still loads it, so nothing is lost.
 * Each test is a fresh browser context: nothing comes from the cache.
 */
import { expect, test } from "@playwright/test";

const ENGINE = /duckdb|\.wasm(\?|$)/i;
const PARQUET = /\.parquet(\?|$)/i;

function urls(page) {
  const log = [];
  page.on("request", (r) => log.push(r.url()));
  return log;
}

test("About the data opens with no engine and no data file", async ({ page }) => {
  // FAILS if #view=about downloads DuckDB or any Parquet file.
  const log = urls(page);
  await page.goto("explorer/#view=about");
  await expect(page.getByRole("heading", { name: "About the data" })).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(log.filter((u) => ENGINE.test(u))).toEqual([]);
  expect(log.filter((u) => PARQUET.test(u))).toEqual([]);
});

test("Review on the public site says there is no queue, with no engine and no data file", async ({ page }) => {
  // FAILS if #view=review on a public build downloads DuckDB or any table before saying so.
  const log = urls(page);
  await page.goto("explorer/#view=review");
  await expect(page.getByText("No review queue in this build.")).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(log.filter((u) => ENGINE.test(u))).toEqual([]);
  expect(log.filter((u) => PARQUET.test(u))).toEqual([]);
});

for (const [name, path, cell] of [
  ["Years", "explorer/#view=years", "FY2026"],
  ["Council capital vs OMB", "explorer/#view=omb&ofy=2026", "2026"],
]) {
  test(`${name} shows its figures from the JSON files, with no engine and no data file`, async ({ page }) => {
    // FAILS if the view downloads DuckDB or any Parquet file, or shows no figures (#301 step 4).
    const log = urls(page);
    await page.goto(path);
    await expect(page.locator("main table").first()).toBeVisible({ timeout: 60_000 });
    await expect(page.locator("main table").first()).toContainText(cell);
    await page.waitForLoadState("networkidle");
    expect(log.filter((u) => ENGINE.test(u))).toEqual([]);
    expect(log.filter((u) => PARQUET.test(u))).toEqual([]);
    expect(log.some((u) => /\/data\/council\//.test(u))).toBe(true);
  });
}

test("the landing page opens on the newest year, from its file, with no engine", async ({ page }) => {
  // FAILS if the first page starts DuckDB or fetches Parquet, or is not the newest year (#301 step 5).
  const log = urls(page);
  await page.goto("explorer/");
  await expect(page.locator("main table").first()).toBeVisible({ timeout: 60_000 });
  await expect(page.getByLabel("Fiscal year")).toHaveValue(/^20\d\d$/);
  await page.waitForLoadState("networkidle");
  expect(log.filter((u) => ENGINE.test(u))).toEqual([]);
  expect(log.filter((u) => PARQUET.test(u))).toEqual([]);
  expect(log.some((u) => /\/data\/council\/awards\/fy20\d\d\.json/.test(u))).toBe(true);
});

test("a search over all years loads the engine", async ({ page }) => {
  // FAILS if an all-years text search is answered without DuckDB (it needs every year).
  const log = urls(page);
  await page.goto("explorer/#view=awards&fy=0&legal_name=food");
  await expect(page.locator("main table").first()).toBeVisible({ timeout: 150_000 });
  expect(log.some((u) => ENGINE.test(u))).toBe(true);
});

test("one award opens from its year's file; its Open Data and Schedule C panels load on request", async ({ page }) => {
  // FAILS if a link to one award starts DuckDB on its own, or the panels never come.
  const log = urls(page);
  await page.goto("explorer/#view=award&ay=2026&row=2");
  await expect(page.getByRole("heading", { name: "Every column" })).toBeVisible({ timeout: 60_000 });
  await page.waitForLoadState("networkidle");
  expect(log.filter((u) => ENGINE.test(u))).toEqual([]);
  await page.getByRole("button", { name: "Show them" }).click();
  await expect(page.getByRole("heading", { name: "On NYC Open Data?" })).toBeVisible({ timeout: 150_000 });
});

test("leaving About for the expense awards shows the list", async ({ page }) => {
  // FAILS if the list does not come after About (from the JSON files since #301 step 5).
  await page.goto("explorer/#view=about");
  await expect(page.getByRole("heading", { name: "About the data" })).toBeVisible();
  await page.getByRole("link", { name: "Expense awards" }).click();
  await expect(page.locator("table").first()).toBeVisible({ timeout: 150_000 });
});
