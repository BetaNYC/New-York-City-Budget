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

test("leaving About for the expense awards still loads the engine and the data", async ({ page }) => {
  // FAILS if the gate leaves a view that needs DuckDB without it.
  await page.goto("explorer/#view=about");
  await expect(page.getByRole("heading", { name: "About the data" })).toBeVisible();
  await page.getByRole("link", { name: "Expense awards" }).click();
  await expect(page.locator("table").first()).toBeVisible({ timeout: 150_000 });
});
