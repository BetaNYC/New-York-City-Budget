/**
 * search_disclosure_awards, audited with the questions the Schedule C audits asked
 * (data/DISCLOSURE-AUDIT.md, "The MCP tool" section; ids M1–M12 there).
 *
 * Every expected value is computed here from the committed CSVs
 * (data/fyNN/expense_disclosure/fyNN_expense_awards.csv) with csv-parse, never from the SQLite
 * index the tool reads, so a loading or query bug cannot agree with itself. Money is summed
 * EXACTLY (BigInt at 1e-12 dollars) and rounded to cents once, so float residue in the tool's
 * SQL sums would show up as a one-cent disagreement.
 *
 * Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const TOOL = "search_disclosure_awards";
const YEARS = Array.from({ length: 15 }, (_, i) => 2013 + i);
const STATUSES = ["cleared", "pending", "other"];
const yy = (fy) => String(fy % 100).padStart(2, "0");
const CSV = Object.fromEntries(
  YEARS.map((fy) => [
    fy,
    parse(readFileSync(join(REPO, "data", `fy${yy(fy)}`, "expense_disclosure", `fy${yy(fy)}_expense_awards.csv`), "utf8"), {
      columns: true,
      skip_empty_lines: true,
      bom: true,
    }),
  ])
);
const ALL = YEARS.flatMap((fy) => CSV[fy]);
const fmt = (n) => n.toLocaleString("en-US");

// ---- exact money: amounts as BigInt in units of 1e-12 dollars
const SCALE = 12;
function toUnits(s) {
  const [i, f = ""] = s.split(".");
  return BigInt(i) * 10n ** BigInt(SCALE) + BigInt((f + "0".repeat(SCALE)).slice(0, SCALE) || "0");
}
function exactUsd(rows) {
  let t = 0n;
  for (const r of rows) t += toUnits(r.amount);
  const unit = 10n ** BigInt(SCALE - 2); // one cent
  const cents = (t + unit / 2n) / unit; // half-up; every amount here is positive
  const dollars = cents / 100n;
  const c = Number(cents % 100n);
  const d = Number(dollars).toLocaleString("en-US");
  return c ? `$${d}.${String(c).padStart(2, "0").replace(/0$/, "")}` : `$${d}`;
}

let client;
before(async () => {
  const [ct, st] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(st);
  client = new Client({ name: "disclosure-audit", version: "0" }, { capabilities: {} });
  await client.connect(ct);
});
after(async () => {
  await client.close();
});

async function call(args) {
  const res = await client.callTool({ name: TOOL, arguments: args });
  return { isError: res.isError === true, text: res.content.map((c) => c.text).join("\n") };
}
const matchedOf = (text) => {
  const m = /^([\d,]+) matching designation/m.exec(text);
  return m ? Number(m[1].replace(/,/g, "")) : 0;
};
const shownAmounts = (text) =>
  [...text.matchAll(/^FY\d{4}(?: · [^·\n]+)? · \$([\d,.]+) · /gm)].map((m) => Number(m[1].replace(/,/g, "")));
const LABEL = { cleared: "Cleared (headline):", pending: "Pending:           ", other: "Other status:      " };

// ---------------------------------------------------------------- M1, M11 totals

test("M1/M11: totals equal the exact CSV sum, to the cent, for every fiscal_year x status", async () => {
  // FAILS if any year x status total differs from the committed CSV by a row or a cent --
  // a dropped or doubled row, a mis-normalized status, or float residue in the SQL sum.
  let checked = 0;
  for (const fy of YEARS) {
    const { text } = await call({ fiscal_year: fy, limit: 1 });
    for (const s of STATUSES) {
      const rows = CSV[fy].filter((r) => r.status_norm === s);
      if (s === "other" && rows.length === 0) {
        assert.doesNotMatch(text, /Other status:/, `FY${fy}`);
        continue;
      }
      const line = `${LABEL[s]} ${fmt(rows.length)} row(s), ${exactUsd(rows)}`;
      assert.ok(text.includes(line), `FY${fy} ${s}: expected "${line}"`);
      checked++;
    }
  }
  assert.ok(checked >= 30, "fixture premise: cleared and pending exist in most years");
});

// ---------------------------------------------------------------- M2 truncation

test("M2: matched is the true count however small the page (limit 1, 50, 500)", async () => {
  // FAILS if a truncated page reports its own length as the match count (#49), or if the
  // totals shrink with the page.
  const want = CSV[2026].length;
  const blocks = [];
  for (const limit of [1, 50, 500]) {
    const { text } = await call({ fiscal_year: 2026, limit });
    assert.equal(matchedOf(text), want, `limit ${limit}`);
    assert.equal(shownAmounts(text).length, limit);
    assert.match(text, new RegExp(`Showing ${limit} of ${fmt(want)}`));
    blocks.push(text.slice(text.indexOf("Totals over all"), text.indexOf("Snapshot (")));
  }
  assert.equal(new Set(blocks).size, 1);
});

// ---------------------------------------------------------------- M3 sort before limit

test("M3: an unfiltered page is the top amounts of ALL years, sorted before the limit", async () => {
  // FAILS if the limit is applied before ordering (#41/#48: a fiscal_year-first sort shows only
  // the earliest year), or if the page is not in descending order.
  const top = ALL.map((r) => Number(r.amount)).sort((a, b) => b - a).slice(0, 500);
  const { text } = await call({ limit: 500 });
  assert.deepEqual(shownAmounts(text), top);
  const years = new Set([...text.matchAll(/^FY(\d{4}) · /gm)].map((m) => m[1]));
  assert.ok(years.size > 1, "the top 500 span more than one year");
});

// ---------------------------------------------------------------- M4 limit edges

test("M4: limit below 1 is an error; 1 and 500 are honored; above 500 is capped with totals intact", async () => {
  // FAILS if limit 0 or -5 silently returns a row (it used to return 1), or if 501 shows more
  // than 500 rows or changes a total.
  for (const limit of [0, -5]) {
    const r = await call({ fiscal_year: 2027, limit });
    assert.equal(r.isError, true, `limit ${limit}`);
    assert.match(r.text, /limit must be at least 1/);
  }
  const one = await call({ fiscal_year: 2027, limit: 1 });
  assert.equal(shownAmounts(one.text).length, 1);
  const a = await call({ fiscal_year: 2027, limit: 500 });
  const b = await call({ fiscal_year: 2027, limit: 501 });
  assert.equal(shownAmounts(a.text).length, 500);
  assert.equal(shownAmounts(b.text).length, 500);
  const totals = (t) => t.slice(t.indexOf("Totals over all"), t.indexOf("Snapshot ("));
  assert.equal(totals(a.text), totals(b.text));
  const fractional = await call({ fiscal_year: 2027, limit: 2.5 });
  assert.equal(fractional.isError, true, "limit must be an integer");
});

// ---------------------------------------------------------------- M5 unknown parameters

test("M5: an unknown parameter is rejected, not ignored", async () => {
  // FAILS if a misspelled filter is dropped and the unfiltered answer returned (#37/#40).
  const r = await call({ fiscal_year: 2027, legal_nme: "Food Bank" });
  assert.equal(r.isError, true);
  assert.match(r.text, /does not accept `legal_nme`/);
});

// ---------------------------------------------------------------- M6 EIN

test("M6: EIN with or without a hyphen is the same query; a leading zero is significant", async () => {
  // FAILS if the hyphenated form matches differently, or if a 9-digit EIN with a leading zero
  // does not find its rows.
  const a = await call({ ein: "13-2612524", limit: 1 });
  const b = await call({ ein: "132612524", limit: 1 });
  assert.equal(matchedOf(a.text), ALL.filter((r) => r.ein === "132612524").length);
  assert.equal(a.text, b.text);
  const lead = ALL.find((r) => r.ein.startsWith("0"));
  const n = ALL.filter((r) => r.ein === lead.ein).length;
  const c = await call({ ein: lead.ein, limit: 1 });
  assert.equal(matchedOf(c.text), n);
});

test("M6: an EIN that is not 9 digits is an error, never a match on blank-EIN rows or a guess", async () => {
  // FAILS if 'N/A' (no digits) matches the blank-EIN rows (it matched 6), if an 8-digit EIN
  // quietly returns nothing instead of saying why, or if it is silently padded.
  const blanks = ALL.filter((r) => r.ein === "").length;
  assert.ok(blanks > 0, "fixture premise: blank-EIN rows exist");
  for (const ein of ["N/A", "", "--", "1234567890"]) {
    const r = await call({ ein });
    assert.equal(r.isError, true, JSON.stringify(ein));
    assert.match(r.text, /ein must be 9 digits/);
  }
  const lead = ALL.find((r) => r.ein.startsWith("0")).ein;
  const r8 = await call({ ein: lead.slice(1) });
  assert.equal(r8.isError, true);
  assert.ok(r8.text.includes(`try "${lead}"`), r8.text);
});

test("M6: the ein filter matches the grantee EIN only, never the fiscal conduit's", async () => {
  // FAILS if the filter also matches fiscal_conduit_ein (mutating the WHERE to OR the conduit
  // column changes 320 rows' worth of answers and passed every earlier test).
  const conduits = [...new Set(ALL.map((r) => r.fiscal_conduit_ein).filter((e) => /^\d{9}$/.test(e)))];
  let differs = 0;
  for (const e of conduits) {
    const want = ALL.filter((r) => r.ein === e).length;
    if (want !== ALL.filter((r) => r.ein === e || r.fiscal_conduit_ein === e).length) differs++;
    const { text } = await call({ ein: e, limit: 1 });
    assert.equal(matchedOf(text), want, `conduit EIN ${e}`);
  }
  assert.ok(differs > 0, "fixture premise: some conduit EIN would change the answer if matched");
});

test("M6: an EIN that pools many names says so (the City's own EIN)", async () => {
  // FAILS if a lookup on 136400434 reads as one grantee: the answer must count the distinct
  // legal names it covers. And a single-name EIN must not carry the note.
  const want = new Set(CSV[2027].filter((r) => r.ein === "136400434").map((r) => r.legal_name)).size;
  assert.ok(want > 1);
  const { text } = await call({ ein: "136400434", fiscal_year: 2027, limit: 1 });
  assert.ok(text.includes(`Note: ${fmt(want)} different legal names carry this EIN`), text.slice(0, 400));
  const single = Object.entries(
    CSV[2027].reduce((m, r) => ((m[r.ein] ??= new Set()).add(r.legal_name), m), {})
  ).find(([e, s]) => e && s.size === 1)[0];
  const one = await call({ ein: single, fiscal_year: 2027 });
  assert.doesNotMatch(one.text, /different legal names carry this EIN/);
});

// ---------------------------------------------------------------- M7 case and whitespace

test("M7: text filters ignore case and surrounding whitespace", async () => {
  // FAILS if 'FOOD BANK', '  food bank  ' and 'Food Bank' disagree, or disagree with a
  // case-insensitive substring count over the CSV.
  const want = ALL.filter((r) => r.legal_name.toLowerCase().includes("food bank")).length;
  assert.ok(want > 0);
  for (const v of ["FOOD BANK", "  food bank  ", "Food Bank"]) {
    const { text } = await call({ legal_name: v, limit: 1 });
    assert.equal(matchedOf(text), want, JSON.stringify(v));
  }
});

// ---------------------------------------------------------------- M8 LIKE wildcards

test("M8: '%' and '_' in a filter are literal characters, not wildcards", async () => {
  // FAILS if legal_name '_' matches every row (it matched all 139,556) or '%' does, i.e. if
  // LIKE metacharacters reach SQLite unescaped.
  for (const ch of ["_", "%", "\\"]) {
    const want = ALL.filter((r) => r.legal_name.includes(ch)).length;
    const r = await call({ legal_name: ch, limit: 1 });
    assert.ok(!r.isError);
    assert.equal(matchedOf(r.text), want, JSON.stringify(ch));
    assert.ok(want < ALL.length);
  }
  const pct = ALL.find((r) => /\d%/.test(r.program_name));
  if (pct) {
    const v = /\d+%/.exec(pct.program_name)[0];
    const want = ALL.filter((r) => r.program_name.toLowerCase().includes(v)).length;
    const { text } = await call({ program_name: v, limit: 1 });
    assert.equal(matchedOf(text), want);
  }
});

// ---------------------------------------------------------------- M9 substring ambiguity

test("M9: a member filter that matches several members lists each, with its rows and dollars", async () => {
  // FAILS if 'Levin' (FY2016) silently sums Levin and Levine (#51), or if the listed split
  // does not equal the CSV's.
  const rows = CSV[2016].filter((r) => r.council_member.toLowerCase().includes("levin"));
  const vals = [...new Set(rows.map((r) => r.council_member))].sort();
  assert.deepEqual(vals, ["Levin", "Levine"], "fixture premise");
  const { text } = await call({ council_member: "Levin", fiscal_year: 2016, limit: 1 });
  assert.match(text, /Note: the council_member filter is a substring match and matched 2 different values/);
  for (const v of vals) {
    const g = rows.filter((r) => r.council_member === v);
    assert.ok(text.includes(`${v} (${fmt(g.length)} row(s), ${exactUsd(g)})`), v);
  }
});

test("M9: a source filter that catches named initiatives says so; an exact single value does not", async () => {
  // FAILS if 'Youth' is presented as the Youth stream while also counting 'Summer Youth
  // Employment Program' etc., or if a filter that matches one value carries a spurious note.
  const vals = new Set(CSV[2027].filter((r) => r.source.toLowerCase().includes("youth")).map((r) => r.source));
  assert.ok(vals.size > 1, "fixture premise");
  const { text } = await call({ source: "Youth", fiscal_year: 2027, limit: 1 });
  assert.match(text, new RegExp(`the source filter is a substring match and matched ${vals.size} different values`));
  const aging = new Set(CSV[2016].filter((r) => r.source.toLowerCase().includes("speaker's initiative")).map((r) => r.source));
  assert.equal(aging.size, 1, "fixture premise");
  const one = await call({ source: "Speaker's Initiative", fiscal_year: 2016, limit: 1 });
  assert.doesNotMatch(one.text, /filter is a substring match/);
});

// ---------------------------------------------------------------- M10 empty result

test("M10: an empty result is not an error and names the coverage and snapshot", async () => {
  // FAILS if a filter that matches nothing is reported as an error, or as a bare 'no results'
  // with no statement of what was searched.
  const r = await call({ legal_name: "zz-no-such-grantee-zz", fiscal_year: 2025 });
  assert.equal(r.isError, false);
  assert.match(r.text, /^No matching designations .*\(covers FY2013–FY2027\)/);
  assert.match(r.text, /FY2025 is from funded_disclosure_FY2025\.xlsx/);
});

// ---------------------------------------------------------------- M12 top rows are not defects

test("M12: the rows at the top of an unfiltered answer are clean designations", async () => {
  // FAILS if a mangled row (merged name, blank EIN, a name that is prose or an amount) reaches
  // the first page, the #48 CSSA shape.
  const { text } = await call({ limit: 20 });
  const names = [...text.matchAll(/→ (.+) \(EIN ([^)]*)\)/g)];
  assert.equal(names.length, 20);
  for (const [, name, ein] of names) {
    assert.match(ein, /^\d{9}$/, name);
    assert.doesNotMatch(name, /\b(to provide|will be used|funds will)\b|^\$?[\d,.]+$/i, name);
  }
});
