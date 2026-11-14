/**
 * Council members in the checked PDF tables (GitHub #51): search_schedule_c_awards and
 * search_transparency_changes resolve each row's printed member to a Legistar person per fiscal
 * year (data/pdf_council_member_crosswalk.csv, built with #72's rules), filter on that exactly
 * with council_member_id, and make the substring member filter list every printed name and
 * person it blended.
 *
 * #51's two acceptance tests are here, adapted to the 2.x tools: a name filter never answers
 * 'Williams' as one person, and one person's rows are complete across a change of label
 * ('Sanchez' to FY2026, 'P. Sanchez' in FY2027).
 *
 * The tables come from pretest (.pdf-test/release/pdf-tables.db); the crosswalk from the npm
 * index (data/budget.db). Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, rmSync, symlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { closePdfTables } from "../dist/pdfdata.js";
import { memberCrosswalk } from "../dist/db.js";
import { searchScheduleC, searchTransparency } from "../dist/pdfquery.js";
import { registerTextFunctions } from "../dist/textmatch.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const TABLES_DB = join(MCP, ".pdf-test", "release", "pdf-tables.db");
const TMP = join(MCP, ".pdf-test", "members");

// Legistar person IDs (data/reference/council_members_legistar.csv).
const JUMAANE = "7571";
const NANTASHA = "7817";
const PIERINA = "7808";
const JUSTIN = "7897";
const LEVIN = "7567";
const LEVINE = "7634";
const WON = "7816";
const WONG = "7900";

let client;
let db;
let members;
before(async () => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "pdf-tables"), { recursive: true });
  symlinkSync(TABLES_DB, join(TMP, "pdf-tables", "pdf-tables.db"));
  closePdfTables();
  process.env.NYC_BUDGET_DATA_DIR = TMP;
  delete process.env.NYC_BUDGET_PDF_DATA;
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "pdf-members-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
  db = new Database(TABLES_DB, { readonly: true });
  registerTextFunctions(db);
  members = memberCrosswalk();
});
after(async () => {
  await client.close();
  db.close();
  closePdfTables();
  rmSync(TMP, { recursive: true, force: true });
});

async function call(name, args = {}) {
  const res = await client.callTool({ name, arguments: args });
  return { text: res.content.map((c) => c.text).join("\n"), isError: !!res.isError };
}

const sc = (f) => searchScheduleC(db, "", f, members);
const tr = (f) => searchTransparency(db, "", f, members);

// ---------------------------------------------------------------- #51's acceptance tests

test("#51 acceptance: an ambiguous member label cannot silently resolve to one person", async () => {
  // Adapted: the 2.x tools do not throw on a surname (#72 chose to answer and disclose); they
  // must name every person it blended. FAILS if 'Williams' is answered without both Jumaane D.
  // Williams and Nantasha M. Williams, or without pointing to council_member_id.
  for (const tool of ["search_schedule_c_awards", "search_transparency_changes"]) {
    const { text, isError } = await call(tool, { member: "Williams" });
    assert.equal(isError, false, text);
    const note = text.split("\n").find((l) => l.startsWith("Note: the member filter is a substring match"));
    assert.ok(note, `${tool}: no member note\n${text.slice(0, 2000)}`);
    assert.match(note, new RegExp(`Jumaane D\\. Williams \\(Legistar person ${JUMAANE}\\)`), tool);
    assert.match(note, new RegExp(`Nantasha M\\. Williams \\(Legistar person ${NANTASHA}\\)`), tool);
    assert.match(note, /use council_member_id/, tool);
  }
});

test("#51 acceptance: a member's awards are complete across a naming-convention change", () => {
  // FAILS if council_member_id misses Pierina Ana Sanchez's rows printed 'Sanchez' (FY2023-FY2025)
  // or 'P. Sanchez' (FY2027), or counts a row printed 'J. Sanchez'.
  const res = sc({ council_member_id: PIERINA, limit: 500 });
  const years = new Set(res.by_year.map((y) => y.fiscal_year));
  assert.ok(years.size > 1, "must span more than one fiscal year");
  assert.ok(years.has(2027) && [2023, 2024, 2025].every((y) => years.has(y)), [...years].join(","));
  const labels = new Set(res.rows.map((s) => `${s.row.fiscal_year === 2027 ? "2027" : "earlier"}|${s.row.member}`));
  assert.ok(labels.has("2027|P. Sanchez") && labels.has("earlier|Sanchez"), [...labels].join(", "));
  assert.ok(![...labels].some((l) => l.endsWith("J. Sanchez")));
  const printed = Object.fromEntries(res.member_id.printed.map((p) => [p.council_member, p.years]));
  assert.deepEqual(Object.keys(printed).sort(), ["P. Sanchez", "Sanchez"]);
  assert.deepEqual(printed["P. Sanchez"], [2027]);
});

// ---------------------------------------------------------------- the exact filter

test("council_member_id counts exactly the crosswalk's rows for every person, in both tables", () => {
  // FAILS if the filter matches by substring or LIKE (Levin would count Levine), on a column
  // other than the printed member, or on the wrong year; or if the crosswalk's counts drift.
  for (const [family, search] of [["schedule_c", sc], ["transparency", tr]]) {
    const ids = [...new Set(members.entries.filter((e) => e.family === family && e.id).map((e) => e.id))];
    assert.ok(ids.length > 50, `${family}: ${ids.length} people`);
    for (const id of ids) {
      const want = members.pairs(family, id).reduce((t, p) => t + p.rows, 0);
      assert.equal(search({ council_member_id: id, limit: 1 }).matched, want, `${family} ${id}`);
    }
  }
});

test("Levin is not Levine and Won is not Wong, in both tables", () => {
  // FAILS if one person's exact search returns a row printed with the other's name.
  for (const search of [sc, tr]) {
    for (const [id, not] of [[LEVIN, "Levine"], [LEVINE, "Levin"], [WON, "Wong"], [WONG, "Won"]]) {
      const res = search({ council_member_id: id, limit: 500 });
      assert.ok(!res.rows.some((s) => s.row.member === not), `${id} returned a '${not}' row`);
    }
    assert.ok(search({ council_member_id: LEVIN, limit: 1 }).matched > 0);
    assert.ok(search({ council_member_id: LEVINE, limit: 1 }).matched > 0);
  }
});

test("an ambiguous year is never counted for either person, and the answer says so", async () => {
  // FY2026 Schedule C prints bare 'Sanchez' (138 rows) while both Sanchezes served: FAILS if
  // either ID counts them, or the answer does not say they could be the person.
  for (const id of [PIERINA, JUSTIN]) {
    const res = sc({ council_member_id: id, fiscal_year: 2026, limit: 500 });
    assert.ok(!res.rows.some((s) => s.row.member === "Sanchez"), id);
    assert.deepEqual(res.member_id.not_counted.map((m) => [m.fiscal_year, m.council_member, m.rows]), [[2026, "Sanchez", 138]]);
  }
  const { text } = await call("search_schedule_c_awards", { council_member_id: PIERINA, fiscal_year: 2026 });
  assert.match(text, /Not counted: 138 row\(s\) printed 'Sanchez' in FY2026/);
  assert.match(text, /Pierina Ana Sanchez \(Legistar person 7808\) or Justin E\. Sanchez \(Legistar person 7897\)/);
});

test("each row says who its printed member is, or why it is no one", async () => {
  // FAILS if a resolved row lacks its person, or FY2022 'Barron' (Charles and Inez Barron both
  // served) is given one.
  const { text } = await call("search_schedule_c_awards", { member: "Barron", fiscal_year: 2022, limit: 3 });
  assert.match(text, /member Barron \[not resolved: Charles Barron \(Legistar person 5288\) or Inez D\. Barron \(Legistar person 7623\); more than one member of that name served in FY2022\]/);
  const lv = await call("search_transparency_changes", { council_member_id: LEVINE, limit: 2 });
  assert.match(lv.text, /member Levine \[Mark Levine \(Legistar person 7634\)/);
  assert.match(lv.text, /^council_member_id 7634 is Mark Levine \(Legistar person 7634\)\. Counted:/m);
});

test("borough delegation labels still match the member filter and are never a person", async () => {
  // #51 "Do NOT break these". FAILS if 'Queens Delegation' stops matching, or a delegation row
  // carries a person tag.
  for (const tool of ["search_schedule_c_awards", "search_transparency_changes"]) {
    const { text } = await call(tool, { member: "Queens Delegation", limit: 5 });
    assert.match(text, /^\d[\d,]* matching/m, tool);
    assert.doesNotMatch(text, /Queens Delegation \[/, tool);
  }
});

test("council_member_id must be digits; the name goes in member", async () => {
  // FAILS if a name passed as an ID is searched (it would match nothing and look like an answer).
  const { text, isError } = await call("search_transparency_changes", { council_member_id: "Levin" });
  assert.equal(isError, true);
  assert.match(text, /council_member_id must be a Legistar person ID \(digits only\).*use member/);
  const ok = await call("search_schedule_c_awards", { council_member_id: Number(LEVIN), limit: 1 });
  assert.equal(ok.isError, false, ok.text);
});

test("a single-person name with a sponsor-only match says those rows are not resolved", async () => {
  // Schedule C's member filter also searches sponsor and delegation (co-sponsor lists, as
  // printed). FAILS if rows matched only there are silently folded into a person's count.
  const res = sc({ member: "Brannan", limit: 1 });
  const inMember = res.matched_members.reduce((t, m) => t + m.rows, 0);
  assert.equal(inMember + res.member_other_columns.rows, res.matched);
  assert.ok(res.member_other_columns.rows > 0);
  const { text } = await call("search_schedule_c_awards", { member: "Brannan", limit: 1 });
  assert.match(text, /match the member filter only in the sponsor or delegation column/);
});
