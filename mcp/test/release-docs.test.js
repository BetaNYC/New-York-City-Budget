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

// This stack's entry (epic #334). Its title may not change while it is Unreleased (whats_changed.py).
const STACK_TITLE = "Server tools say they only read, and more answers link to the City's data";
// The 2.1.0 entry already on main, dated 2026-11-14 before the tag and so treated as published
// by the append-only check: it keeps its date until tag day, when #312 sets the real one.
const MAIN_TITLE = "Server adds City agency budgets, FY2027 changes and Council Members by person";

/** WHATS-CHANGED.md's entry headings, in order: { date (null if Unreleased), title }. */
function entries() {
  return [...read("WHATS-CHANGED.md").matchAll(/^## (?:(\d{4}-\d{2}-\d{2})|Unreleased): (.+)$/gm)].map((m) => ({ date: m[1] ?? null, title: m[2] }));
}

test("at most one Unreleased entry, and only as the first entry", () => {
  // FAILS if a second Unreleased entry is added, or one sits below a dated entry. Publishing with
  // one left is blocked by release.yml's `whats_changed.py check --release`, not here (#312's tag
  // day dates it as the last step before the tag).
  const all = entries();
  const unreleased = all.flatMap((e, i) => (e.date === null ? [i] : []));
  assert.ok(unreleased.length <= 1, `${unreleased.length} Unreleased entries`);
  if (unreleased.length) assert.equal(unreleased[0], 0, "the Unreleased entry is not the first entry");
});

test("the release date is the same in every place that states it", () => {
  // FAILS if the CHANGELOG's date for this version is changed and one of the others is not; or,
  // before the tag (CHANGELOG "— Unreleased"), if this stack's entry is not the Unreleased first
  // entry linking the CHANGELOG with no anchor, or the other places disagree on their placeholder date.
  const v = PKG.version;
  const heading = new RegExp(`^## ${v.replaceAll(".", "\\.")} — (\\d{4}-\\d{2}-\\d{2}|Unreleased)$`, "m").exec(read("mcp/CHANGELOG.md"))?.[1];
  assert.ok(heading, `CHANGELOG.md has a ${v} heading, dated or "— Unreleased"`);
  const all = entries();
  if (heading === "Unreleased") {
    // Before the tag: this stack's entry is the one Unreleased entry, first, and its MCP version
    // link names the CHANGELOG with no anchor (a "— Unreleased" heading's anchor changes on tag day).
    assert.deepEqual(all[0], { date: null, title: STACK_TITLE });
    const body = read("WHATS-CHANGED.md").split(/^## /m)[1];
    assert.ok(body.includes(`- **MCP version:** [nyc-budget-mcp ${v}](mcp/CHANGELOG.md)\n`), "the MCP version link is not mcp/CHANGELOG.md with no anchor");
  }
  // The date every other place states: the CHANGELOG's once dated, else the placeholder they share.
  const date = heading === "Unreleased" ? /\*\*Version [\d.]+\*\* \((\d{4}-\d{2}-\d{2})\)/.exec(read("mcp/README.md"))?.[1] : heading;
  assert.ok(date, "mcp/README.md states no date for this version");
  const places = [
    ["mcp/README.md", `**Version ${v}** (${date})`],
    ["README.md", `**${v} (${date}, tagged by a maintainer):**`],
    ["DATA-ANOMALIES.md", `**Since ${v} (#270, ${date}): one year rule.**`],
    ["WHATS-CHANGED.md", `## ${date}: ${MAIN_TITLE}`],
  ];
  if (heading !== "Unreleased") places.push(["WHATS-CHANGED.md", `## ${date}: ${STACK_TITLE}`]);
  for (const [file, text] of places) assert.ok(read(file).includes(text), `${file} lacks: ${text}`);
  if (heading !== "Unreleased") assert.ok(!all.some((e) => e.date === null && e.title === STACK_TITLE), `${v} is dated but its entry is still Unreleased`);
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
