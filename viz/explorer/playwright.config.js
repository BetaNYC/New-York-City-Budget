/**
 * Accessibility and phone checks for the Agency budgets view (#270; specs in e2e/, built in #287).
 *
 *   npm run e2e:site     build the data and app, and assemble the site into e2e/.site/
 *   npm run test:e2e     run the specs (Playwright starts a static server on the assembled site)
 *
 * Browsers: `npx playwright install chromium` once. Until #286 lands, every spec is skipped with
 * the issue that builds it (e2e/pending.js), and no server is started.
 *
 * API from the official docs (checked 2026-11-12): https://playwright.dev/docs/test-configuration,
 * https://playwright.dev/docs/test-webserver, https://playwright.dev/docs/emulation.
 */
import { defineConfig, devices } from "@playwright/test";

import { BASE_URL, PORT, SITE_BUILT, SITE_ROOT } from "./e2e/pending.js";

export default defineConfig({
  testDir: "e2e",
  // The first visit downloads the query engine (about 33 MB) and the data.
  timeout: 180_000,
  expect: { timeout: 30_000 },
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never", outputFolder: "e2e/.report" }]] : "list",
  outputDir: "e2e/.results",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    // A phone: Chromium with a phone's viewport, touch and meta-viewport handling (Pixel 7 is a
    // Chromium device descriptor, so CI needs only one browser).
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
  // python3 is already a dependency of this repo's checks; http.server serves files as they are.
  webServer: SITE_BUILT
    ? {
        command: `python3 -m http.server ${PORT} --bind 127.0.0.1 --directory "${SITE_ROOT}"`,
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        stdout: "ignore",
        stderr: "pipe",
      }
    : undefined,
});
