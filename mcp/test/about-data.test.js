/**
 * about_data answers from DATA-SOURCES.json (#329; BetaNYC's about-data standard, through the
 * shared module copied in unchanged). Each test says what result would make it FAIL.
 *
 * The PDF tables download is pointed at an empty folder, so its source must say "not fetched".
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { assertEveryToolExplained } from "../dist/betanyc-tools.js";
import { newYorkDay } from "../dist/freshness.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const ROOT_FILE = join(MCP, "..", "DATA-SOURCES.json");
const DOC = JSON.parse(readFileSync(ROOT_FILE, "utf8"));
/** A committed CSV, by repo path: the expected dates come from these, never from the index. */
const csv = (rel) => parse(readFileSync(join(MCP, "..", rel), "utf8"), { columns: true, bom: true, skip_empty_lines: true });
const manifestDate = (dir, file) => csv(`source/${dir}/MANIFEST.csv`).find((r) => r.file === file).retrieved_at.slice(0, 10);
/** The day a date-time falls on in New York, the way about_data shows it. */
const nyDay = (v) => (/T/.test(v) ? new Date(v).toLocaleDateString("en-CA", { timeZone: "America/New_York" }) : v);

let client;
let TOOLS;
before(async () => {
  process.env.NYC_BUDGET_DATA_DIR = mkdtempSync(join(tmpdir(), "nyc-budget-about-data-"));
  const budgetServer = await import("../dist/server.js");
  TOOLS = budgetServer.TOOLS;
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "about-data-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

const call = (args = {}) => client.callTool({ name: "about_data", arguments: args });
const text = (r) => r.content.map((c) => c.text).join("\n");

test("every tool says where its data comes from, and no source names a tool the server lacks", () => {
  // FAILS if a tool is added without a source in DATA-SOURCES.json, or the file has an error.
  assertEveryToolExplained(readFileSync(ROOT_FILE, "utf8"), TOOLS.map((t) => t.name));
});

test("the copy the package ships is the repo's file", () => {
  // FAILS if mcp/DATA-SOURCES.json (the prebuild copy) differs from the root file.
  assert.equal(readFileSync(join(MCP, "DATA-SOURCES.json"), "utf8"), readFileSync(ROOT_FILE, "utf8"));
});

test("with no topic, about_data lists every source from the file, with BetaNYC's contact", async () => {
  // FAILS if the server is not wired to the file, a source is left out, or the contact is lost.
  const r = await call();
  assert.equal(r.isError, undefined, text(r));
  const sc = r.structuredContent;
  assert.deepEqual(sc.sources.map((s) => s.topic), DOC.sources.map((s) => s.id));
  assert.deepEqual(sc.left_out, []);
  assert.equal(sc.contact_email, "lab@beta.nyc");
  assert.match(sc.source_file, /^https:\/\/github\.com\/BetaNYC\/New-York-City-Budget\/blob\/HEAD\/DATA-SOURCES\.json$/);
});

test("the figures are official only where BetaNYC passed the values on unchanged", async () => {
  // FAILS if a source BetaNYC read from a PDF, matched, filtered or summed is called official,
  // or the member crosswalk (BetaNYC's own matching) is called an official record.
  const sc = (await call()).structuredContent;
  const official = Object.fromEntries(sc.sources.map((s) => [s.topic, s.figures_official]));
  assert.deepEqual(Object.keys(official).filter((k) => official[k]), ["cpdb-commitments", "cpdb-projects"]);
  for (const id of ["fy2018-capital-book", "pdf-tables", "expense-disclosure", "agency-budgets", "member-crosswalk"]) assert.equal(official[id], false, id);
  assert.equal(sc.sources.find((s) => s.topic === "member-crosswalk").official, false);
});

test("each source's date is the day its committed copy was downloaded, never typed in the file", async () => {
  // FAILS if a hook is unwired (reported "not reported by this server"), reads another source's
  // date, or shows a time or a UTC day. The expected dates come from the committed manifests.
  const sc = (await call()).structuredContent;
  const asOf = Object.fromEntries(sc.sources.map((s) => [s.topic, [s.as_of_status, s.as_of]]));
  const years = csv("data/disclosure_years.csv").filter((r) => r.loaded === "yes");
  const max = (xs) => xs.sort().at(-1);
  assert.deepEqual(asOf["expense-disclosure"], ["read", max(years.filter((r) => r.source_kind === "council_rnd").map((r) => r.retrieved))]);
  assert.deepEqual(asOf["council-capital-workbook"], ["read", csv("source/expense-funding-disclosure/MANIFEST.csv").find((r) => r.file === "Capital-Database.xlsx").retrieved]);
  assert.deepEqual(asOf["council-capital-open-data"], ["read", manifestDate("open-data-t474-a92g", "t474-a92g.csv.gz")]);
  assert.deepEqual(asOf["agency-budgets"], ["read", nyDay(max(csv("source/agency-budget-qa/MANIFEST.csv").map((r) => r.retrieved_at)))]);
  assert.deepEqual(asOf["capital-plan"], ["read", manifestDate("open-data-2cmn-uidm", "2cmn-uidm.csv.gz")]);
  assert.deepEqual(asOf["cpdb-commitments"], ["read", manifestDate("open-data-djxg-kcfi", "djxg-kcfi.csv.gz")]);
  assert.deepEqual(asOf["cpdb-projects"], ["read", manifestDate("open-data-fi59-268w", "fi59-268w.csv.gz")]);
  const roster = Object.fromEntries(csv("data/reference/council_members_legistar_meta.csv").map((r) => [r.key, r.value]));
  assert.deepEqual(asOf["member-crosswalk"], ["read", nyDay(roster.db_last_indexed_at)]);
  for (const id of ["wayback-copies", "omb-capital-budget"]) assert.match(asOf[id][1], /^\d{4}-\d{2}-\d{2}$/, id);
  for (const [id, [status, v]] of Object.entries(asOf)) if (status === "read") assert.match(v, /^\d{4}-\d{2}-\d{2}$/, `${id}: a day, no time`);
  // No download date is recorded for the FY2018 book; it says so instead of inventing one.
  assert.equal(asOf["fy2018-capital-book"][0], "unavailable");
  // The PDF tables are not installed in this test's data folder.
  assert.equal(asOf["pdf-tables"][0], "not-fetched");
  assert.ok(DOC.sources.every((s) => s.freshness.kind === "hook"), "no date typed into the file");
});

test("a topic answers with that source only: capital-plan, in thousands, with where to check it", async () => {
  // FAILS if the topic picks another source, or the plan's unit or route for errors is lost.
  const r = await call({ topic: "capital-plan" });
  assert.equal(r.isError, undefined, text(r));
  const [s] = r.structuredContent.sources;
  assert.equal(r.structuredContent.sources.length, 1);
  assert.equal(s.source_url, "https://data.cityofnewyork.us/d/2cmn-uidm");
  assert.match(s.publisher, /Office of Management and Budget/);
  assert.equal(s.figures_official, false);
  assert.ok(s.caveats.some((c) => /thousands of dollars/.test(c)));
  assert.match(text(r), /2cmn-uidm/);
});

test("a tool name as the topic gives every source behind that tool", async () => {
  // FAILS if search_capital_plan's answer leaves out a source its rows come from.
  const r = await call({ topic: "search_capital_plan" });
  assert.deepEqual(r.structuredContent.sources.map((s) => s.topic).sort(),
    ["capital-plan", "council-capital-open-data", "council-capital-workbook", "cpdb-commitments", "cpdb-projects", "fy2018-capital-book", "wayback-copies"]);
});

test("a topic in other words is refused with the list of topics, not guessed", async () => {
  // FAILS if "capital plan" (with a space) silently matches something, or the topics are not listed.
  const r = await call({ topic: "capital plan" });
  assert.equal(r.isError, true);
  assert.match(text(r), /Topics: .*capital-plan/);
});

test("a date-time is shown as its day in New York, so a late-evening download is not a day late", () => {
  // FAILS if a UTC time is cut to its UTC day: 03:37 UTC on November 10 is still November 9 in New York.
  assert.equal(newYorkDay("2026-11-10T03:37:52Z"), "2026-11-09");
  assert.equal(newYorkDay("2026-11-14T22:07:26.232Z"), "2026-11-14");
  assert.equal(newYorkDay("2026-10-14T06:58:58-04:00"), "2026-10-14");
  assert.equal(newYorkDay("2026-10-12"), "2026-10-12");
  assert.equal(newYorkDay(null), null);
});

test("a source's update code never contradicts its caveats, and no license is claimed for the publisher", () => {
  // FAILS if a source says "irregular" while a caveat gives its schedule, or a license line asserts
  // a copyright holder the publisher never stated.
  for (const s of DOC.sources) {
    if (s.caveats.some((c) => /times a year|every four months/.test(c))) assert.equal(s.update_frequency, undefined, s.id);
    assert.doesNotMatch(s.terms.license_name ?? "", /©|reproduced as/, s.id);
  }
});
