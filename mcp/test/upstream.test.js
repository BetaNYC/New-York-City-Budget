/**
 * The PDF tables download's requests (#337; BetaNYC MCP practice 18): a User-Agent naming the
 * package, its version and repo; a timeout for the response and for a stalled body; up to three
 * tries on 429 and 5xx that honor Retry-After. Against a local server only, never GitHub. Each
 * test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { HTTP, USER_AGENT, fetchText, retryAfterMs } from "../dist/pdfdata.js";

const VERSION = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")).version;
const hits = new Map();
const agents = [];
let server;
let base;

before(async () => {
  Object.assign(HTTP, { headersMs: 300, stallMs: 300, tries: 3, maxWaitMs: 2000 });
  server = createServer((req, res) => {
    const n = (hits.get(req.url) ?? 0) + 1;
    hits.set(req.url, n);
    agents.push(req.headers["user-agent"]);
    if (req.url === "/ok") return res.end("fine");
    if (req.url === "/429-once") return n === 1 ? res.writeHead(429, { "retry-after": "0" }).end() : res.end("second try");
    if (req.url === "/503-always") return res.writeHead(503).end("down");
    if (req.url === "/429-long") return res.writeHead(429, { "retry-after": "120" }).end();
    if (req.url === "/404") return res.writeHead(404).end();
    if (req.url === "/no-answer") return; // never answers
    if (req.url === "/stall") {
      res.writeHead(200);
      res.write("part");
      return; // never finishes
    }
    res.writeHead(500).end();
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  base = `http://127.0.0.1:${server.address().port}`;
});
after(() => {
  server.closeAllConnections();
  server.close();
});

const get = (path) => fetchText(new URL(path, base));

test("every request names the package, its version and the repo", async () => {
  // FAILS if the User-Agent loses the version or the repo, or is not sent.
  assert.equal(await get("/ok"), "fine");
  assert.equal(USER_AGENT, `nyc-budget-mcp/${VERSION} (+https://github.com/BetaNYC/New-York-City-Budget)`);
  assert.ok(agents.length > 0 && agents.every((a) => a === USER_AGENT), agents.join(" | "));
});

test("a 429 is tried again after Retry-After, and the second answer is used", async () => {
  // FAILS if a 429 is not retried, or retried more than needed.
  assert.equal(await get("/429-once"), "second try");
  assert.equal(hits.get("/429-once"), 2);
});

test("a 5xx is tried three times, then fails with the status", async () => {
  // FAILS if the retries are unbounded, missing, or the error hides the status.
  await assert.rejects(get("/503-always"), /HTTP 503 after 3 tries/);
  assert.equal(hits.get("/503-always"), 3);
});

test("a Retry-After longer than the cap is not waited out", async () => {
  // FAILS if the download sleeps for minutes, or retries anyway.
  await assert.rejects(get("/429-long"), /asks to wait 120 s/);
  assert.equal(hits.get("/429-long"), 1);
});

test("a 404 is not retried", async () => {
  // FAILS if a client error is tried again.
  await assert.rejects(get("/404"), /HTTP 404$/);
  assert.equal(hits.get("/404"), 1);
});

test("a server that never answers times out with a plain reason", async () => {
  // FAILS if the request hangs, or the error does not say it timed out.
  await assert.rejects(get("/no-answer"), /no answer within 0.3 s/);
});

test("a body that stops coming times out with a plain reason", async () => {
  // FAILS if a stalled download hangs for good.
  await assert.rejects(get("/stall"), /no data for 0.3 s; stopped/);
});

test("Retry-After is read as seconds or as an HTTP date", () => {
  // FAILS if either form of the header (RFC 9110 § 10.2.3) is misread.
  assert.equal(retryAfterMs("5"), 5000);
  assert.equal(retryAfterMs("Wed, 18 Nov 2026 12:00:10 GMT", Date.parse("Wed, 18 Nov 2026 12:00:00 GMT")), 10_000);
  assert.equal(retryAfterMs(null), null);
  assert.equal(retryAfterMs("soon"), null);
});
