/**
 * Whole-word matching for short text-filter terms (GitHub #259).
 *
 * Found in a fresh 2.0.3 install: search_schedule_c_awards with ein 132612524 and organization
 * "AI " returned 34 rows; one was the "AI Training Program" wanted, the rest matched "Jamaica" and
 * "AIDS". A term of 3 or fewer letters and digits now matches whole words by default, any tool's
 * whole_word argument overrides that either way, and the answer says when it applied.
 *
 * The matching rule is tested on its own (src/textmatch.ts), then in SQL on both databases: the
 * spreadsheet index (expected counts from the committed CSVs, never from the index) and the PDF
 * tables pretest builds (.pdf-test/release/pdf-tables.db). Each test says what result would make
 * it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import Database from "better-sqlite3";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";
import { fold } from "../dist/fold.js";
import { containsWord, useWholeWord, alnumCount, registerTextFunctions, wholeWordNote, SHORT_TERM } from "../dist/textmatch.js";
import { searchDisclosure, searchCapital } from "../dist/db.js";
import { searchScheduleC, searchTransparency, searchCapitalBook, searchTerms } from "../dist/pdfquery.js";
import { closePdfTables } from "../dist/pdfdata.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const TABLES_DB = join(MCP, ".pdf-test", "release", "pdf-tables.db");
const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });
/** The rule, applied to a raw cell and a raw term exactly as the server folds them. */
const word = (cell, term) => containsWord(fold(cell), fold(term));

// ---------------------------------------------------------------- the rule

test("'AI' as a whole word, inside a word, and at the start and end of the text", () => {
  // FAILS if "AI" matches inside "Jamaica" or "AIDS", or misses it at either end of the text.
  assert.equal(word("AI Training Program", "AI"), true, "start of the text");
  assert.equal(word("Training in AI", "AI"), true, "end of the text");
  assert.equal(word("AI", "AI"), true, "the whole text");
  assert.equal(word("Civic AI Lab", "AI"), true, "middle");
  assert.equal(word("Jamaica Bay-Rockaway Parks Conservancy", "AI"), false, "inside 'Jamaica'");
  assert.equal(word("Legal Hand Jamaica", "AI"), false, "inside a word at the end");
  assert.equal(word("Sisterhood Mobilized for AIDS/HIV Research", "AI"), false, "start of 'AIDS'");
  assert.equal(word("Said", "AI"), false, "inside a one-word text");
  // A miss inside a word does not stop the search: the later whole word is found.
  assert.equal(word("Jamaica AI Program", "AI"), true, "after an earlier miss");
});

test("punctuation is a word edge: BetaNYC's, AI-powered, (AI), AI/ML, curly apostrophes", () => {
  // FAILS if punctuation next to a term stops it matching, or a letter or digit next to it does not.
  assert.equal(word("AI-powered tools", "AI"), true);
  assert.equal(word("Tools (AI) for all", "AI"), true);
  assert.equal(word("AI/ML", "AI"), true);
  assert.equal(word("Fund for the City of New York, Inc. – AI Training Program", "AI"), true, "after an en dash");
  assert.equal(word("BetaNYC's Civic RADARs", "BetaNYC"), true);
  assert.equal(word("BetaNYC’s Civic RADARs", "BetaNYC"), true, "curly apostrophe folds to straight");
  assert.equal(word("BetaNYC's Civic RADARs", "BetaNYC's"), true, "a term with an apostrophe");
  assert.equal(word("AI2 Labs", "AI"), false, "a digit is part of the word");
  assert.equal(word("CD22", "CD"), false);
  assert.equal(word("CD 22", "CD"), true);
});

test("an accented term matches its unaccented spelling as a whole word, and not inside a longer word", () => {
  // FAILS if folding is lost in whole-word mode: "Émigré" must find "Emigre" and "émigré".
  assert.equal(word("Jewish Emigre Services", "Émigré"), true);
  assert.equal(word("JEWISH ÉMIGRÉ SERVICES", "emigre"), true);
  assert.equal(word("Jewish Émigrés", "Émigré"), false, "plural is a longer word");
  assert.equal(word("Avilés", "AVILES"), true);
  assert.equal(useWholeWord("Ñ"), true, "one accented letter counts as one letter");
  assert.equal(word("Año Nuevo", "Ñ"), false);
});

test("the default: 1 to 3 letters and digits match whole words, longer terms are substrings, override either way", () => {
  // FAILS if the 3-character boundary is off by one, trailing spaces count, punctuation counts, or
  // an explicit whole_word does not override the default in both directions.
  assert.equal(SHORT_TERM, 3);
  for (const t of ["AI", "AI ", " ai ", "ESL", "DOE", "072", "P.S.", "C++"]) assert.equal(useWholeWord(t), true, JSON.stringify(t));
  for (const t of ["CUNY", "Fellow", "BetaNYC", "DYCD", "1013-2025"]) assert.equal(useWholeWord(t), false, JSON.stringify(t));
  assert.equal(alnumCount("P.S."), 2);
  // No letter or digit: word edges mean nothing, so a substring, as before (% and _ stay literal).
  for (const t of ["%", "_", "\\", "&"]) assert.equal(useWholeWord(t), false, JSON.stringify(t));
  assert.equal(useWholeWord("AI", false), false, "override: a short term as a substring");
  assert.equal(useWholeWord("Fellow", true), true, "override: a long term as a whole word");
  assert.equal(useWholeWord("%", true), true);
});

test("word_match() in SQL: % and _ are literal, NULL never matches", () => {
  // FAILS if the SQL function treats LIKE wildcards as wildcards or matches a NULL cell.
  const d = new Database(":memory:");
  try {
    registerTextFunctions(d);
    const m = (v, q) => d.prepare("SELECT word_match(?, ?) AS m").get(v, fold(q)).m;
    assert.equal(m("AI Training", "AI"), 1);
    assert.equal(m("Jamaica", "AI"), 0);
    assert.equal(m("abc", "_"), 0);
    assert.equal(m("100 % done", "%"), 1);
    assert.equal(m(null, "AI"), 0);
    assert.equal(d.prepare("SELECT fold(?) AS f").get("Émigré").f, "emigre");
  } finally {
    d.close();
  }
});

test("the answer's note names the filters and how to ask for a substring", () => {
  // FAILS if the note is printed with no whole-word filter, or omits the filter, value or way out.
  assert.equal(wholeWordNote([]), "");
  const d = wholeWordNote([{ filter: "organization", value: "AI " }]);
  assert.match(d, /organization "AI"/);
  assert.match(d, /whole_word: false/);
  assert.match(d, /3 or fewer letters and digits/);
  assert.match(wholeWordNote([{ filter: "title", value: "Fellow" }], true), /whole_word is true/);
});

// ---------------------------------------------------------------- the spreadsheet index

const disclosureRows = (() => {
  const dirs = readdirSync(join(REPO, "data")).filter((d) => /^fy\d\d$/.test(d));
  return dirs.flatMap((d) => {
    try {
      return readCsv(`data/${d}/expense_disclosure/${d}_expense_awards.csv`);
    } catch {
      return [];
    }
  });
})();

test("disclosure: a short term matches the CSV's whole-word rows, and the totals are those rows' sum", () => {
  // FAILS if the index's whole-word count differs from the rule applied to the committed CSVs, if
  // a row shown fails the rule, or if the totals cover any row the filter does not select.
  const want = disclosureRows.filter((r) => word(r.program_name, "AI"));
  assert.ok(want.length > 0 && want.length <= 500, `premise: ${want.length} rows`);
  const res = searchDisclosure({ program_name: "AI", limit: 500 });
  assert.equal(res.matched, want.length);
  assert.equal(res.rows.length, want.length);
  for (const r of res.rows) assert.ok(word(r.program_name, "AI"), r.program_name);
  const t = res.totals;
  const total = t.cleared.amount + t.pending.amount + t.other.amount;
  const rowSum = res.rows.reduce((s, r) => s + r.amount, 0);
  assert.ok(Math.abs(total - rowSum) < 0.005, `${total} vs ${rowSum}`);
  assert.deepEqual(res.word_filters, [{ filter: "program_name", value: "AI" }]);
  // whole_word: false is the old substring, far more rows.
  const sub = searchDisclosure({ program_name: "AI", whole_word: false, limit: 1 });
  assert.equal(sub.matched, disclosureRows.filter((r) => fold(r.program_name).includes("ai")).length);
  assert.ok(sub.matched > res.matched * 10);
  assert.deepEqual(sub.word_filters, []);
});

test("disclosure: a long term stays a substring unless whole_word is true", () => {
  // FAILS if "Fellow" stops finding "Fellowship" by default, or whole_word: true does not stop it.
  const sub = disclosureRows.filter((r) => fold(r.program_name).includes("fellow"));
  const whole = disclosureRows.filter((r) => word(r.program_name, "Fellow"));
  assert.ok(sub.length > whole.length, "premise: some program names say Fellowship");
  assert.equal(searchDisclosure({ program_name: "Fellow", limit: 1 }).matched, sub.length);
  assert.equal(searchDisclosure({ program_name: "Fellow", whole_word: true, limit: 1 }).matched, whole.length);
});

test("council capital: title and sponsor follow the same rule", () => {
  // FAILS if search_council_capital's text filters ignore the default or the override.
  const cap = readCsv("data/capital/council_capital_awards.csv");
  const whole = cap.filter((r) => word(r.title, "PS"));
  const sub = cap.filter((r) => fold(r.title).includes("ps"));
  assert.ok(whole.length > 0 && sub.length > whole.length, "premise");
  assert.equal(searchCapital({ title: "PS", limit: 1 }).matched, whole.length);
  assert.equal(searchCapital({ title: "PS", whole_word: false, limit: 1 }).matched, sub.length);
});

// ---------------------------------------------------------------- the PDF tables

let db;
before(() => {
  db = new Database(TABLES_DB, { readonly: true });
  registerTextFunctions(db);
});
after(() => db.close());

test("Schedule C: 'AI' matches whole words only, and the totals equal the rows' sum", () => {
  // FAILS if any row matched only inside a longer word, if a whole-word row is missed (checked
  // against the substring result filtered by the rule in JS), or if a total covers other rows.
  // The issue's search: the Fund for the City of New York's EIN, organization "AI".
  const sub = searchScheduleC(db, "", { ein: "132612524", organization: "AI", whole_word: false, limit: 500 });
  const res = searchScheduleC(db, "", { ein: "132612524", organization: "AI", limit: 500 });
  assert.ok(sub.matched <= 500, "premise: the substring result fits on one page");
  const want = sub.rows.filter((s) => word(s.row.org, "AI")).map((s) => `${s.row.fiscal_year}|${s.row.award_id}`);
  assert.ok(want.length > 0 && want.length < sub.matched, "premise: some rows say AI, more only contain it");
  assert.deepEqual(res.rows.map((s) => `${s.row.fiscal_year}|${s.row.award_id}`).sort(), want.sort());
  assert.equal(res.matched, want.length);
  assert.equal(res.amount, res.rows.reduce((t, s) => t + (s.row.amount ?? 0), 0));
  assert.equal(res.with_amount, res.rows.filter((s) => s.row.amount != null).length);
  assert.equal(res.by_year.reduce((t, y) => t + y.rows, 0), res.matched);
  assert.equal(res.by_disclosure.reduce((t, y) => t + y.amount, 0), res.amount);
  for (const s of res.rows) assert.doesNotMatch(s.row.org, /jamaica|aids/i);
});

test("transparency, capital book and Terms: the default and the override reach every text filter", () => {
  // FAILS if a PDF tool's text filter keeps substring matching for a short term, or ignores
  // whole_word: false.
  const tr = (f) => searchTransparency(db, "", { ...f, limit: 1 });
  assert.ok(tr({ organization: "Inc" }).matched < tr({ organization: "Inc", whole_word: false }).matched);
  assert.deepEqual(tr({ organization: "Inc" }).word_filters.map((w) => w.filter), ["organization"]);
  const cb = (f) => searchCapitalBook(db, "", { ...f, limit: 1 });
  assert.ok(cb({ title: "PS" }).matched < cb({ title: "PS", whole_word: false }).matched);
  const te = (f) => searchTerms(db, "", { ...f, limit: 1 });
  assert.ok(te({ text: "DOE" }).matched <= te({ text: "DOE", whole_word: false }).matched);
  assert.deepEqual(te({ text: "DOE", agency: "education" }).word_filters.map((w) => w.filter), ["text"]);
});

// ---------------------------------------------------------------- the tools

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "whole-word-test", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
  closePdfTables();
});
const call = async (name, args) => (await client.callTool({ name, arguments: args })).content.map((c) => c.text).join("\n");

test("every tool with a free-text filter takes whole_word and says what it does", async () => {
  // FAILS if a text-filter tool lacks whole_word, a tool without text filters gains it, or a
  // description does not state the rule.
  const { tools } = await client.listTools();
  const withText = ["search_disclosure_awards", "search_council_capital", "search_schedule_c_awards", "search_transparency_changes", "search_capital_book", "search_terms_conditions"];
  for (const t of tools) {
    const has = Object.hasOwn(t.inputSchema.properties ?? {}, "whole_word");
    assert.equal(has, withText.includes(t.name), t.name);
    if (has) {
      assert.equal(t.inputSchema.properties.whole_word.type, "boolean");
      assert.match(t.description, /3 or fewer letters and digits matches whole words/, t.name);
      assert.match(t.inputSchema.properties.whole_word.description, /Jamaica/);
    }
  }
});

test("the answer prints one line when a filter matched as whole words, and none otherwise", async () => {
  // FAILS if the note is missing for a short term or for whole_word: true, or printed for a
  // substring match.
  const short = await call("search_disclosure_awards", { program_name: "AI", limit: 1 });
  assert.match(short.split("\n")[1], /^Matched as whole words, because a term of 3 or fewer letters and digits does by default: program_name "AI"\. Pass whole_word: false/);
  assert.equal(short.match(/Matched as whole words/g).length, 1);
  const forced = await call("search_council_capital", { title: "Library", whole_word: true, limit: 1 });
  assert.match(forced, /Matched as whole words \(whole_word is true\): title "Library"/);
  const off = await call("search_disclosure_awards", { program_name: "AI", whole_word: false, limit: 1 });
  assert.doesNotMatch(off, /Matched as whole words/);
  const long = await call("search_disclosure_awards", { program_name: "Fellow", limit: 1 });
  assert.doesNotMatch(long, /Matched as whole words/);
  // A search that finds nothing still says so: the rule may be why.
  const none = await call("search_disclosure_awards", { legal_name: "Ai", fiscal_year: 2027 });
  assert.match(none, /^No matching designations/);
  assert.match(none, /Matched as whole words.*legal_name "Ai"/);
  const bad = await client.callTool({ name: "search_disclosure_awards", arguments: { legal_name: "AI", whole_word: "yes" } });
  assert.equal(bad.isError, true, "whole_word must be a boolean");
});
