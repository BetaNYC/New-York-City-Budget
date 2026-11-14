/**
 * What the release says about itself (the 2.1.0 docs sweep, epic #312): one release date
 * everywhere, and listings that fit their registries. Each test says what result would make it FAIL.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const MCP = join(dirname(fileURLToPath(import.meta.url)), "..");
const REPO = join(MCP, "..");
const read = (rel) => readFileSync(join(REPO, rel), "utf8");
const PKG = JSON.parse(read("mcp/package.json"));
const SERVER = JSON.parse(read("mcp/server.json"));

test("the release date is the same in every place that states it", () => {
  // FAILS if the CHANGELOG's date for this version is changed and one of the others is not.
  const v = PKG.version;
  const date = new RegExp(`^## ${v.replaceAll(".", "\\.")} — (\\d{4}-\\d{2}-\\d{2})$`, "m").exec(read("mcp/CHANGELOG.md"))?.[1];
  assert.ok(date, `CHANGELOG.md has a dated ${v} heading`);
  const places = [
    ["mcp/README.md", `**Version ${v}** (${date})`],
    ["README.md", `**${v} (${date}, tagged by a maintainer):**`],
    ["DATA-ANOMALIES.md", `**Since ${v} (#270, ${date}): one year rule.**`],
    ["WHATS-CHANGED.md", `## ${date}: Server adds City agency budgets, FY2027 changes and Council Members by person`],
  ];
  for (const [file, text] of places) assert.ok(read(file).includes(text), `${file} lacks: ${text}`);
  assert.ok(!/^## Unreleased:/m.test(read("WHATS-CHANGED.md")), "WHATS-CHANGED.md still has an Unreleased entry");
});

test("the MCP Registry description fits the Registry's limit and says what ships", () => {
  // FAILS if the description passes the 100 characters the Registry's server.schema.json allows
  // (ServerDetail.description maxLength), or leaves out what this release adds.
  assert.ok(SERVER.description.length <= 100, `${SERVER.description.length} characters`);
  assert.match(SERVER.description, /agency budgets/);
  assert.match(SERVER.description, /capital plan/);
  assert.equal(SERVER.version, PKG.version);
});

test("the npm description is current", () => {
  // FAILS if it still calls FY2018 capital missing, or leaves out agency budgets or the capital plan.
  assert.doesNotMatch(PKG.description, /missing/i);
  assert.match(PKG.description, /City agency budgets/);
  assert.match(PKG.description, /capital commitment plan/);
  assert.match(PKG.description, /FY2018/);
});
