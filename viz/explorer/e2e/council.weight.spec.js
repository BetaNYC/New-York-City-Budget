/**
 * What a first visit to each Council explorer view downloads (#301, second PR). REPORT ONLY: it
 * records, it does not fail on size yet. A later #301 PR turns the budget on: the fast views under
 * 1 MB over the wire and 3 MB decoded, with no query engine.
 *
 * Two numbers per view, as the #301 triage counted them
 * (https://github.com/BetaNYC/New-York-City-Budget/issues/301#issuecomment-6872266067):
 *
 *   wire     what GitHub Pages sends: each compressible response gzipped (zlib level 6; Pages
 *            sends .html, .css, .js, .json, .wasm and .parquet gzipped), others as they are.
 *   decoded  the bytes on disk, after decompression.
 *
 * The test server (python3 http.server) sends files uncompressed, so `wire` is computed here from
 * each body, not read from the network. Requests to other hosts (DuckDB's extension server) count
 * at their body size in both columns. Each view is a fresh browser context: nothing is cached.
 * The engine's .wasm streams into WebAssembly as it downloads, so its body is fetched again to
 * be measured.
 * Desktop and the Pixel 7 project both run; the triage found they fetch the same files.
 *
 * The figures go to the test's annotations and to e2e/.results/council-weight-<project>.json.
 *
 * API from the official docs (checked 2026-11-14): https://playwright.dev/docs/api/class-response#response-body,
 * https://playwright.dev/docs/api/class-testinfo#test-info-annotations.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { test } from "@playwright/test";

import { councilReady } from "./site.js";

/** The Council views, as #301's triage measured them, plus a straight link to one award and one capital project. */
export const WEIGHT_VIEWS = {
  "expense awards (landing)": "explorer/",
  "expense awards": "explorer/#view=awards",
  "one award": "explorer/#view=award&ay=2026&row=2",
  years: "explorer/#view=years",
  omb: "explorer/#view=omb",
  capital: "explorer/#view=capital",
  "one capital project": "explorer/#view=capital-row&seq=1",
  about: "explorer/#view=about",
  compare: "explorer/#view=compare",
  orgs: "explorer/#view=orgs",
  terms: "explorer/#view=terms",
  schedc: "explorer/#view=schedc",
  transparency: "explorer/#view=transparency",
  book: "explorer/#view=book",
  review: "explorer/#view=review",
};

const COMPRESSIBLE = /\.(html?|css|m?js|json|wasm|parquet|svg|txt|csv)(\?|$)|\/(\?|$)/i;
const ENGINE = /duckdb|\.wasm(\?|$)/i;

/** Every finished response's decoded and wire size, and whether it was the engine. */
function record(page) {
  const log = { files: [], pending: [] };
  page.on("response", (res) => {
    log.pending.push(
      res
        .body()
        // A streamed body (the engine's .wasm, compiled while it downloads) cannot be read back:
        // fetch the same URL again, outside the page, to measure it.
        .catch(() => page.request.get(res.url()).then((again) => again.body()))
        .then(async (body) => {
          const url = res.url();
          const local = new URL(url).hostname === "127.0.0.1";
          // Another host sends its own encoding: count what it sent.
          const sent = local ? null : (await res.request().sizes()).responseBodySize;
          const wire = local ? (COMPRESSIBLE.test(url) ? gzipSync(body, { level: 6 }).length : body.length) : sent;
          log.files.push({ url, decoded: body.length, wire, engine: ENGINE.test(url) });
        })
        .catch(() => {})
    );
  });
  return log;
}

const results = {};

test.describe("Council views: first-visit download (report only)", () => {
  test.describe.configure({ mode: "serial" });

  for (const [name, path] of Object.entries(WEIGHT_VIEWS)) {
    test(`first visit: ${name}`, async ({ page }, info) => {
      const log = record(page);
      await page.goto(path);
      await councilReady(page);
      await page.waitForLoadState("networkidle");
      await Promise.all(log.pending);
      const sum = (k, f = () => true) => log.files.filter(f).reduce((t, x) => t + x[k], 0);
      const r = {
        path,
        requests: log.files.length,
        wire: sum("wire"),
        decoded: sum("decoded"),
        engine_wire: sum("wire", (x) => x.engine),
        parquet_wire: sum("wire", (x) => /\.parquet(\?|$)/.test(x.url)),
        engine: log.files.some((x) => x.engine),
      };
      results[name] = r;
      info.annotations.push({ type: "first visit", description: JSON.stringify(r) });
      console.log(`${info.project.name} · ${name}: ${(r.wire / 1e6).toFixed(2)} MB wire, ${(r.decoded / 1e6).toFixed(2)} MB decoded, ${r.requests} requests${r.engine ? ", engine" : ""}`);
    });
  }

  test.afterAll(async ({}, info) => {
    mkdirSync("e2e/.results", { recursive: true });
    writeFileSync(`e2e/.results/council-weight-${info.project.name}.json`, JSON.stringify(results, null, 2));
  });
});
