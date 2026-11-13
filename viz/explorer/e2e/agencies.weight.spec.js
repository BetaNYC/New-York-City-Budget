/**
 * How much a first visit to City agency budgets downloads (#299): under 1 MB, and never the
 * DuckDB engine (its .wasm is about 33 MB; its JS is about 1 MB more).
 *
 * Every response is counted from the network log (request.sizes(): headers plus body as sent).
 * The test server (python3 http.server) sends files uncompressed, so this is the most a visit can
 * cost; GitHub Pages compresses text, so the real figure is smaller.
 * Runs at each project's own viewport (desktop and Pixel 7) and at 375 CSS px. Each test is a
 * fresh browser context: nothing comes from the cache.
 *
 * API from the official docs (checked 2026-11-12): https://playwright.dev/docs/api/class-request#request-sizes,
 * https://playwright.dev/docs/network.
 */
import { expect, test } from "@playwright/test";

import { PAGES, openView } from "./helpers.js";
import { VIEW_PENDING } from "./pending.js";

const describe = VIEW_PENDING ? test.describe.skip : test.describe;

export const FIRST_VISIT_LIMIT = 1_000_000;
const ENGINE = /duckdb|\.wasm(\?|$)/i;

/** Record every finished response's size, and every URL asked for. */
function networkLog(page) {
  const log = { urls: [], bytes: 0, done: [] };
  page.on("request", (r) => log.urls.push(r.url()));
  page.on("requestfinished", (r) => {
    log.done.push(
      r.sizes().then((s) => {
        log.bytes += s.responseHeadersSize + s.responseBodySize;
      })
    );
  });
  return log;
}

async function settle(page, log) {
  await page.waitForLoadState("networkidle");
  await Promise.all(log.done);
}

describe(`City agency budgets: first-visit download${VIEW_PENDING ? ` (${VIEW_PENDING})` : ""}`, () => {
  for (const width of [null, 375]) {
    const label = width ? `${width}px` : "project viewport";
    test(`first visit to all agencies is under 1 MB, with no DuckDB: ${label}`, async ({ page }, info) => {
      // FAILS if the agency view loads the query engine, or its first visit grows past 1 MB.
      if (width) await page.setViewportSize({ width, height: 740 });
      const log = networkLog(page);
      await openView(page, PAGES.list);
      await settle(page, log);
      const engine = log.urls.filter((u) => ENGINE.test(u));
      expect(engine, "DuckDB requested").toEqual([]);
      info.annotations.push({ type: "first-visit bytes", description: String(log.bytes) });
      console.log(`first visit (${info.project.name}, ${label}): ${log.bytes} bytes, ${log.urls.length} requests`);
      expect(log.bytes).toBeLessThan(FIRST_VISIT_LIMIT);
    });
  }

  test("opening an agency fetches only that agency's file, still no DuckDB", async ({ page }) => {
    const log = networkLog(page);
    await openView(page, PAGES.list);
    await settle(page, log);
    const before = log.urls.length;
    await page.getByRole("link", { name: /^Police Department$/ }).click();
    await page.locator('[data-view="agencies"][data-ready="true"] h2', { hasText: "Police Department" }).waitFor();
    await settle(page, log);
    const fetched = log.urls.slice(before).map((u) => new URL(u).pathname.split("/").slice(-2).join("/"));
    expect(fetched).toEqual(["agency/056.json"]);
    expect(log.urls.filter((u) => ENGINE.test(u))).toEqual([]);
  });

  test("a straight link to a unit is also under 1 MB, with no DuckDB", async ({ page }) => {
    const log = networkLog(page);
    await openView(page, PAGES.unit);
    await settle(page, log);
    expect(log.urls.filter((u) => ENGINE.test(u))).toEqual([]);
    expect(log.bytes).toBeLessThan(FIRST_VISIT_LIMIT);
  });
});
