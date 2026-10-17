/**
 * search_disclosure_awards (v1.5.0) — the Council's expense funding disclosure, served as its
 * own tool next to (never merged into) the adopted-Schedule-C award tools.
 *
 * Every expected figure is computed here from the committed source files — the per-year
 * data/fyNN/expense_disclosure/fyNN_expense_awards.csv and
 * source/expense-funding-disclosure/MANIFEST.csv — read with csv-parse, independently of the
 * SQLite index the server queries. A test that compared the tool with its own index would pass
 * on a loading bug; these do not.
 *
 * Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import * as budgetServer from "../dist/server.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const DB_PATH = join(HERE, "..", "data", "budget.db");
const TOOL = "search_disclosure_awards";
const YEARS = Array.from({ length: 15 }, (_, i) => 2013 + i);

const readCsv = (p) => parse(readFileSync(p, "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const yy = (fy) => String(fy % 100).padStart(2, "0");
const disclosureCsv = (fy) =>
  readCsv(join(REPO, "data", `fy${yy(fy)}`, "expense_disclosure", `fy${yy(fy)}_expense_awards.csv`));
const MANIFEST = readCsv(join(REPO, "source", "expense-funding-disclosure", "MANIFEST.csv"));

/** "$1,234" / "$1,234.5" — the tool's own display rule (rounded to cents). */
const usd = (n) => {
  const c = Math.round(n * 100) / 100;
  const s = Math.abs(c).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return c < 0 ? `-$${s}` : `$${s}`;
};
const sum = (rows) => rows.reduce((s, r) => s + Number(r.amount), 0);
const byStatus = (rows, s) => rows.filter((r) => r.status_norm === s);

let client;

before(async () => {
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await budgetServer.server.connect(serverTransport);
  client = new Client({ name: "disclosure-test", version: "0" }, { capabilities: {} });
  await client.connect(clientTransport);
});

after(async () => {
  await client.close();
});

async function call(args) {
  const res = await client.callTool({ name: TOOL, arguments: args });
  return { isError: res.isError === true, text: res.content.map((c) => c.text).join("\n") };
}

/** Amounts of the rows the tool printed, in printed order. */
const shownAmounts = (text) =>
  [...text.matchAll(/^FY\d{4}(?: · [^·\n]+)? · \$([\d,.]+) · /gm)].map((m) => Number(m[1].replace(/,/g, "")));

// ---------------------------------------------------------------- the index

test("the index holds every committed disclosure row, per year, with the manifest's provenance", () => {
  // FAILS if a year is skipped, a row is dropped or duplicated, an amount is mis-parsed, or a
  // year's snapshot row does not name the file and retrieval date MANIFEST.csv records.
  const db = new Database(DB_PATH, { readonly: true });
  try {
    for (const fy of YEARS) {
      const rows = disclosureCsv(fy);
      const got = db
        .prepare("SELECT COUNT(*) AS n, SUM(amount) AS amt FROM disclosure WHERE fiscal_year = ?")
        .get(fy);
      assert.equal(got.n, rows.length, `FY${fy} row count`);
      assert.equal(usd(got.amt), usd(sum(rows)), `FY${fy} total`);
      const m = MANIFEST.find((r) => new RegExp(`^funded_disclosure_FY${fy}\\.xlsx?$`).test(r.file));
      const snap = db.prepare("SELECT * FROM disclosure_snapshots WHERE fiscal_year = ?").get(fy);
      assert.deepEqual(
        [snap.file, snap.sheet, snap.retrieved, snap.sha256, snap.award_rows],
        [m.file, m.sheet, m.retrieved, m.sha256, Number(m.award_rows)],
        `FY${fy} snapshot`
      );
      assert.equal(usd(Number(m.total_amount)), usd(sum(rows)), `FY${fy} manifest total`);
    }
  } finally {
    db.close();
  }
});

test("the disclosure is a separate table: the adopted-Schedule-C awards table is untouched", () => {
  // FAILS if disclosure rows leak into `awards` (whose counts the existing tools publish).
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const n = db.prepare("SELECT COUNT(*) AS n FROM awards").get().n;
    assert.equal(n, 33638 + 28575); // main body + appendix, exactly as in v1.4.0
  } finally {
    db.close();
  }
});

// ---------------------------------------------------------------- the canonical query

test("EIN 133179546 FY2026: true match count, status totals over ALL matches, snapshot date", async () => {
  // FAILS if the count or a total is computed from the shown page instead of every match, if
  // Cleared and Pending are not reported separately, if the hyphenated EIN does not match, or if
  // the year's retrieval date / sheet is missing.
  const rows = disclosureCsv(2026).filter((r) => r.ein === "133179546");
  assert.ok(rows.length > 50, "fixture premise: more matches than the default limit");
  const { isError, text } = await call({ ein: "13-3179546", fiscal_year: 2026 });
  assert.ok(!isError, text);
  assert.match(text, new RegExp(`^${rows.length} matching designation\\(s\\)`, "m"));
  assert.match(text, new RegExp(`Showing 50 of ${rows.length}, highest amount first`));
  const cleared = byStatus(rows, "cleared");
  const pending = byStatus(rows, "pending");
  assert.ok(
    text.includes(`Cleared (headline): ${cleared.length} row(s), ${usd(sum(cleared))}`),
    "cleared total over every match"
  );
  assert.ok(text.includes(`Pending:            ${pending.length} row(s), ${usd(sum(pending))}`));
  const m = MANIFEST.find((r) => r.file === "funded_disclosure_FY2026.xlsx");
  assert.ok(text.includes(`sheet "${m.sheet}", retrieved ${m.retrieved}`), "snapshot provenance");
  assert.equal(shownAmounts(text).length, 50);
});

test("truncation discloses the real count, and the totals do not shrink with the page", async () => {
  // FAILS if limiting the rows changes any total, or if a short page is presented without the
  // number of rows it leaves out (issue #49).
  const full = await call({ ein: "133179546", fiscal_year: 2026, limit: 500 });
  const page = await call({ ein: "133179546", fiscal_year: 2026, limit: 3 });
  const totalsBlock = (t) => t.slice(t.indexOf("Totals over all"), t.indexOf("Snapshot ("));
  assert.equal(totalsBlock(page.text), totalsBlock(full.text));
  const n = disclosureCsv(2026).filter((r) => r.ein === "133179546").length;
  assert.match(page.text, new RegExp(`Showing 3 of ${n}`));
  assert.match(full.text, new RegExp(`Showing all ${n}`));
});

test("rows are the highest amounts, ordered before the limit", async () => {
  // FAILS if the limit is applied before ordering by amount (the #41 bug shape), or if the page
  // is not in descending amount order.
  const top = disclosureCsv(2026)
    .filter((r) => r.ein === "133179546")
    .map((r) => Number(r.amount))
    .sort((a, b) => b - a)
    .slice(0, 5);
  const { text } = await call({ ein: "133179546", fiscal_year: 2026, limit: 5 });
  assert.deepEqual(shownAmounts(text), top);
});

test("a query wider than the 500-row cap still reports every match", async () => {
  // FAILS if the 500-row page silently stands in for the whole result (issue #42).
  const rows = disclosureCsv(2027);
  const { text } = await call({ fiscal_year: 2027, limit: 10000 });
  assert.match(text, new RegExp(`Showing 500 of ${rows.length.toLocaleString("en-US")}`));
  assert.ok(text.includes(`All statuses (not a headline figure): ${rows.length.toLocaleString("en-US")} row(s), ${usd(sum(rows))}`));
  assert.equal(shownAmounts(text).length, 500);
});

// ---------------------------------------------------------------- status

test("status: default returns both, totals stay separate; a status filter returns only that status", async () => {
  // FAILS if the default drops Pending rows, if Pending dollars are folded into the Cleared
  // headline, or if status:"pending" returns a Cleared row.
  const fy27 = disclosureCsv(2027);
  const pending = byStatus(fy27, "pending");
  const cleared = byStatus(fy27, "cleared");
  assert.ok(pending.length && cleared.length, "fixture premise: FY2027 has both statuses");
  const all = await call({ fiscal_year: 2027, limit: 1 });
  assert.ok(all.text.includes(`Cleared (headline): ${cleared.length.toLocaleString("en-US")} row(s), ${usd(sum(cleared))}`));
  assert.ok(all.text.includes(`Pending:            ${pending.length.toLocaleString("en-US")} row(s), ${usd(sum(pending))}`));
  const only = await call({ fiscal_year: 2027, status: "pending", limit: 500 });
  assert.match(only.text, new RegExp(`^${pending.length.toLocaleString("en-US")} matching`, "m"));
  assert.ok(only.text.includes("Cleared (headline): 0 row(s), $0"));
  assert.doesNotMatch(only.text, / · Cleared · /);
});

test("min/max amount bound the match inclusively, and an empty range is an error", async () => {
  // FAILS if a bound is exclusive or ignored, or if min > max quietly returns "no matches".
  const rows = disclosureCsv(2026).filter((r) => r.ein === "133179546");
  const want = rows.filter((r) => Number(r.amount) >= 30000 && Number(r.amount) <= 1000000);
  const { text } = await call({ ein: "133179546", fiscal_year: 2026, min_amount: 30000, max_amount: 1000000 });
  assert.match(text, new RegExp(`^${want.length} matching`, "m"));
  const bad = await call({ min_amount: 10, max_amount: 5 });
  assert.equal(bad.isError, true);
  assert.match(bad.text, /min_amount .* greater than max_amount/);
});

test("multi-year results carry a per-year split and every year's snapshot", async () => {
  // FAILS if a multi-year answer gives one blended total with no per-year breakdown, or names
  // the snapshot of only one of the years it draws on.
  const { text } = await call({ ein: "133179546", limit: 1 });
  const years = YEARS.filter((fy) => disclosureCsv(fy).some((r) => r.ein === "133179546"));
  assert.ok(years.length > 1, "fixture premise");
  assert.match(text, /By fiscal year \(cleared \/ pending\):/);
  for (const fy of years) {
    const m = MANIFEST.find((r) => new RegExp(`^funded_disclosure_FY${fy}\\.xlsx?$`).test(r.file));
    assert.ok(text.includes(`FY${fy}: ${m.file}, sheet "${m.sheet}", retrieved ${m.retrieved}`), `FY${fy}`);
  }
});

// ---------------------------------------------------------------- honesty

test("every answer carries the caveat and its own source footer, not the adopted-budget one", async () => {
  // FAILS if the caveat (roster at export time; post-adoption designations; not Schedule C) is
  // dropped, or if the disclosure is presented under the Schedule C footer.
  for (const args of [{ ein: "133179546", fiscal_year: 2026, limit: 1 }, { fiscal_year: 2031 }]) {
    const { text } = await call(args);
    assert.match(text, /roster when the workbook was exported/);
    assert.match(text, /designations made after adoption, so it is not the adopted Schedule C/);
    assert.match(text, /expense funding disclosure workbooks/);
    assert.doesNotMatch(text, /from the NYC Council's adopted-budget documents/);
  }
});

test("no match names the covered years", async () => {
  // FAILS if an out-of-range year reads as a confident empty answer with no coverage statement.
  const { isError, text } = await call({ fiscal_year: 2031 });
  assert.ok(!isError);
  assert.match(text, /^No matching designations .*\(covers FY2013–FY2027\)/);
});

// ---------------------------------------------------------------- strict schema

test("unknown parameters are rejected, with the disclosure's own parameter named", async () => {
  // FAILS if an unknown filter is silently dropped (returning unfiltered rows — issue #37 / PR
  // #40), or if the hint names a parameter this tool does not have.
  const res = await call({ organization: "Food Bank", fiscal_year: 2026 });
  assert.equal(res.isError, true);
  assert.match(res.text, /does not accept `organization`/);
  assert.match(res.text, /Use `legal_name` instead of `organization`/);
  const d = await call({ council_district: 3 });
  assert.equal(d.isError, true);
  assert.match(d.text, /Use `council_member` instead of `council_district`/);
  assert.match(d.text, /disclosure names a council member/);
  assert.doesNotMatch(d.text, /sponsor/);
  const s = await call({ status: "Cleared" });
  assert.equal(s.isError, true, "status is the normalized lower-case value");
});

test("the existing tools' alias hints are unchanged by the new entries", async () => {
  // FAILS if the disclosure-specific hints leak into a tool that lacks legal_name/program_name.
  const res = await client.callTool({ name: "search_capital_projects", arguments: { organization: "x" } });
  const text = res.content.map((c) => c.text).join("\n");
  assert.equal(res.isError, true);
  assert.doesNotMatch(text, /legal_name/);
  const q = await client.callTool({ name: "search_awards", arguments: { query: "x" } });
  const qt = q.content.map((c) => c.text).join("\n");
  assert.match(qt, /Use `organization` or `program` instead of `query`/);
});

test("rows carrying an Excel '#N/A' cell are indexed and served like any other row (#71)", async () => {
  // FAILS if a row whose ZIP, address or city is the Excel error '#N/A' (published as text,
  // 25 rows: FY2014 19, FY2017 6) is dropped from the index, has its amount or name altered,
  // or cannot be found by its grantee name.
  const hits = [];
  for (const fy of YEARS) {
    for (const r of disclosureCsv(fy)) {
      if (Object.values(r).some((v) => v === "#N/A")) hits.push(r);
    }
  }
  assert.equal(hits.length, 25);
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const get = db.prepare("SELECT legal_name, amount, ein FROM disclosure WHERE fiscal_year = ? AND source_row = ?");
    for (const r of hits) {
      const got = get.get(Number(r.fiscal_year), Number(r.source_row));
      assert.ok(got, `FY${r.fiscal_year} row ${r.source_row} missing from the index`);
      assert.equal(got.legal_name, r.legal_name);
      assert.equal(got.amount, Number(r.amount));
      assert.equal(got.ein, r.ein);
    }
  } finally {
    db.close();
  }
  const r = hits[0];
  const res = await call({ fiscal_year: Number(r.fiscal_year), legal_name: r.legal_name, limit: 500 });
  assert.equal(res.isError, false);
  assert.match(res.text, new RegExp(`workbook row ${r.source_row}\\b`));
});

test("exact-copy rows are flagged and counted inside the totals (#69)", async () => {
  // FAILS if the index loses duplicate_group, if the answer's exact-copy count or the dollars
  // beyond the first copy differ from the committed CSVs, if a copy row is not marked, or if the
  // note appears on an answer with no flagged rows.
  const fy = 2016;
  const rows = disclosureCsv(fy);
  const flagged = rows.filter((r) => r.duplicate_group !== "");
  const extra = flagged.filter((r) => r.duplicate_group !== r.source_row);
  const groups = new Set(flagged.map((r) => r.duplicate_group)).size;
  assert.ok(flagged.length > 0, "FY2016 has exact copies in the committed CSV");
  const res = await call({ fiscal_year: fy, limit: 1 });
  assert.ok(
    res.text.includes(`Note: ${flagged.length.toLocaleString("en-US")} of the matched rows are exact copies (${groups} group(s)`),
    res.text
  );
  assert.ok(res.text.includes(`${extra.length.toLocaleString("en-US")} row(s), ${usd(sum(extra))}, are copies beyond the first`), res.text);

  // One group, shown in full: every copy is marked, the first as the group's first.
  const g = extra[0];
  const members = rows.filter((r) => r.duplicate_group === g.duplicate_group);
  const one = await call({ fiscal_year: fy, legal_name: g.legal_name, min_amount: Number(g.amount), max_amount: Number(g.amount), limit: 500 });
  assert.match(one.text, new RegExp(`workbook row ${g.duplicate_group} · exact-copy group: first`));
  for (const m of members.filter((r) => r.source_row !== g.duplicate_group))
    assert.match(one.text, new RegExp(`workbook row ${m.source_row} · exact copy of workbook row ${g.duplicate_group}`));

  // FY2024+ carries none (distinct MOCS IDs): no note.
  const none = await call({ fiscal_year: 2025, limit: 1 });
  assert.equal(disclosureCsv(2025).filter((r) => r.duplicate_group !== "").length, 0);
  assert.doesNotMatch(none.text, /exact copies/);
});

// ---------------------------------------------------------------- #72 member IDs, exact filters

const allRows = () => YEARS.flatMap((fy) => disclosureCsv(fy));

test("every row's council_member_id and type are indexed as the CSV has them (#72)", () => {
  // FAILS if the index drops or alters a person ID or a type for any row.
  const want = new Map();
  for (const r of allRows()) {
    const k = `${r.council_member_type}|${r.council_member_id}`;
    want.set(k, (want.get(k) ?? 0) + 1);
  }
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const got = db
      .prepare("SELECT council_member_type AS t, council_member_id AS id, COUNT(*) AS n FROM disclosure GROUP BY 1, 2")
      .all();
    assert.deepEqual(new Map(got.map((g) => [`${g.t}|${g.id}`, g.n])), want);
  } finally {
    db.close();
  }
});

test("council_member_id is exact: Levin (7567) and Levine (7634) never blend (#72)", async () => {
  // FAILS if the ID filter matches by substring or by name, if its count or Cleared total
  // differs from the CSV rows carrying that ID, or if a Levine row is counted under Levin.
  const rows = allRows();
  for (const [id, name] of [["7567", "Levin"], ["7634", "Levine"]]) {
    const mine = rows.filter((r) => r.council_member_id === id);
    assert.ok(mine.length > 0 && mine.every((r) => r.council_member === name), id);
    const res = await call({ council_member_id: id, limit: 1 });
    assert.equal(res.isError, false);
    assert.ok(res.text.startsWith(`${mine.length.toLocaleString("en-US")} matching designation(s)`), res.text.slice(0, 80));
    assert.ok(res.text.includes(`Cleared (headline): ${byStatus(mine, "cleared").length.toLocaleString("en-US")} row(s), ${usd(sum(byStatus(mine, "cleared")))}`));
    assert.match(res.text, new RegExp(`${name} \\[Legistar person ${id}\\]`));
  }
  // A number is accepted as well as a string.
  const asNumber = await call({ council_member_id: 7567, limit: 1 });
  assert.equal(asNumber.text.split("\n")[0], (await call({ council_member_id: "7567", limit: 1 })).text.split("\n")[0]);
  // The substring filter still blends them, and now says which person each value is.
  const sub = await call({ council_member: "Levin", limit: 1 });
  assert.match(sub.text, /Levin \[Legistar person 7567\]/);
  assert.match(sub.text, /Levine \[Legistar person 7634\]/);
  assert.match(sub.text, /use council_member_id/);
});

test("council_member_id refuses a non-ID and finds nothing for an unknown one (#72)", async () => {
  // FAILS if 'Levin' or '75 67' is accepted as an ID (it would match nothing, silently), or if
  // an unknown numeric ID is an error rather than an empty answer.
  for (const bad of ["Levin", "75 67", "-1"]) {
    const res = await call({ council_member_id: bad });
    assert.equal(res.isError, true, bad);
    assert.match(res.text, /digits only/);
  }
  const none = await call({ council_member_id: "1" });
  assert.equal(none.isError, false);
  assert.match(none.text, /No matching designations/);
});

test("a name from the export-time roster says its person had no vote that year (#72)", async () => {
  // FAILS if FY2025 'Wong' rows (re-attributed from Holden by the 2026 roster; Phil Wong first
  // voted in FY2026) are shown as an ordinary member, or lose the ID.
  const res = await call({ fiscal_year: 2025, council_member_id: "7900", limit: 1 });
  const want = disclosureCsv(2025).filter((r) => r.council_member_id === "7900");
  assert.ok(want.length > 0 && want.every((r) => r.council_member_type === "member_outside_fy"));
  assert.match(res.text, /Wong \[Legistar person 7900; no recorded vote in FY2025: the export-time roster\]/);
});

test("source_exact matches one stream; source still matches by substring (#72)", async () => {
  // FAILS if source_exact 'youth' also matches 'Summer Youth Employment Program', is case-
  // sensitive, or its count differs from the CSV rows whose source is exactly Youth.
  const rows = allRows();
  const exact = rows.filter((r) => r.source.trim().toLowerCase() === "youth");
  const loose = rows.filter((r) => r.source.toLowerCase().includes("youth"));
  assert.ok(loose.length > exact.length && exact.length > 0);
  const res = await call({ source_exact: "  youth ", limit: 1 });
  assert.ok(res.text.startsWith(`${exact.length.toLocaleString("en-US")} matching designation(s)`), res.text.slice(0, 80));
  assert.doesNotMatch(res.text, /substring match/);
  const sub = await call({ source: "Youth", limit: 1 });
  assert.ok(sub.text.startsWith(`${loose.length.toLocaleString("en-US")} matching designation(s)`));
  assert.match(sub.text, /use source_exact/);
  const empty = await call({ source_exact: " " });
  assert.equal(empty.isError, true);
});

// ---------------------------------------------------------------- grantee addresses, zip (1.5.0)

test("every row's address, postal_code, zip, zip_status and zip_candidates are indexed exactly as the CSV has them", () => {
  // FAILS if the index drops, trims or alters any address field, the published postal_code, the
  // derived zip, its status or its candidates, for any of the 139,556 rows.
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const got = new Map(
      db
        .prepare(
          `SELECT fiscal_year, source_row, address1, address2, city, state, postal_code, zip, zip_status, zip_candidates FROM disclosure`
        )
        .all()
        .map((g) => [`${g.fiscal_year}:${g.source_row}`, g])
    );
    const rows = allRows();
    assert.equal(got.size, rows.length);
    for (const r of rows) {
      const g = got.get(`${r.fiscal_year}:${r.source_row}`);
      assert.ok(g, `FY${r.fiscal_year} row ${r.source_row} missing`);
      for (const k of ["address1", "address2", "city", "state", "postal_code", "zip", "zip_status", "zip_candidates"])
        assert.equal(g[k], r[k], `FY${r.fiscal_year} row ${r.source_row} ${k}`);
    }
  } finally {
    db.close();
  }
});

test("zip is an exact 5-digit filter on the derived zip, trimmed rows included", async () => {
  // FAILS if zip matches by substring or on postal_code instead of the derived zip (the 24
  // '11203-' rows have postal_code '11203-' and zip 11203), if its count or Cleared total differs
  // from the CSV rows carrying that zip, or if a ZIP+4 / 4-digit / text value is accepted.
  const rows = allRows();
  const mine = rows.filter((r) => r.zip === "11203");
  assert.ok(mine.some((r) => r.zip_status === "trimmed" && r.postal_code === "11203-"));
  const res = await call({ zip: " 11203 ", limit: 1 });
  assert.equal(res.isError, false);
  assert.ok(res.text.startsWith(`${mine.length.toLocaleString("en-US")} matching designation(s)`), res.text.slice(0, 80));
  assert.ok(res.text.includes(`Cleared (headline): ${byStatus(mine, "cleared").length.toLocaleString("en-US")} row(s), ${usd(sum(byStatus(mine, "cleared")))}`));
  const plus4 = await call({ zip: "11203-1234" });
  assert.equal(plus4.isError, true);
  assert.match(plus4.text, /exactly 5 digits.*give its first five digits \("11203"\)/s);
  for (const bad of ["1120", "112030", "Brooklyn", ""]) {
    const r = await call({ zip: bad });
    assert.equal(r.isError, true, bad);
  }
  const alias = await call({ postal_code: "11203" });
  assert.equal(alias.isError, true);
  assert.match(alias.text, /Use `zip` instead of `postal_code`/);
});

test("zip_status filters one status; 35 trimmed, 35 repaired, 30 ambiguous six-digit rows", async () => {
  // FAILS if zip_status is not an exact filter, if the trimmed / extra-digit counts are not the
  // CSV's, or if a status outside the documented nine is accepted.
  const rows = allRows();
  for (const st of ["trimmed", "repaired_extra_digit", "ambiguous_extra_digit", "invalid", "blank"]) {
    const mine = rows.filter((r) => r.zip_status === st);
    const res = await call({ zip_status: st, limit: 1 });
    assert.ok(res.text.startsWith(`${mine.length.toLocaleString("en-US")} matching designation(s)`), `${st}: ${res.text.slice(0, 80)}`);
  }
  assert.equal(rows.filter((r) => r.zip_status === "trimmed").length, 35);
  assert.equal(rows.filter((r) => r.zip_status === "repaired_extra_digit").length, 35);
  assert.equal(rows.filter((r) => r.zip_status === "ambiguous_extra_digit").length, 30);
  const bad = await call({ zip_status: "ok" });
  assert.equal(bad.isError, true);
});

test("city is exact and case-insensitive, never a substring", async () => {
  // FAILS if city matches by substring ('Brooklyn' would then include 'Brooklyn,' and 'Brooklyn
  // NY'), is case-sensitive, or its count differs from the CSV; or if an empty city is accepted.
  const rows = allRows();
  const exact = rows.filter((r) => r.city.trim().toLowerCase() === "brooklyn");
  const loose = rows.filter((r) => r.city.toLowerCase().includes("brooklyn"));
  assert.ok(loose.length > exact.length && exact.some((r) => r.city === "BROOKLYN"));
  const res = await call({ city: " brooklyn ", limit: 1 });
  assert.ok(res.text.startsWith(`${exact.length.toLocaleString("en-US")} matching designation(s)`), res.text.slice(0, 80));
  const empty = await call({ city: "  " });
  assert.equal(empty.isError, true);
});

test("each row shows the grantee mailing address as printed, its zip and zip_status", async () => {
  // FAILS if a row's address line is missing, if the published postal_code is replaced by the
  // derived zip, if the zip_status is not named, or if the caveat stops saying the address is a
  // mailing address, not where services were delivered.
  const r = allRows().find((x) => x.zip_status === "trimmed" && x.address1 && x.city);
  const res = await call({ fiscal_year: Number(r.fiscal_year), legal_name: r.legal_name, limit: 500 });
  const want =
    `grantee mailing address: ${[r.address1, r.address2, r.city].filter(Boolean).join(", ")}, ${r.state} ${r.postal_code}` +
    ` · zip ${r.zip} (trimmed: first five digits of a ragged ZIP+4`;
  assert.ok(res.text.includes(want), `${want}\n---\n${res.text}`);
  assert.match(res.text, /mailing address as printed, not where services were delivered/);
  const blank = allRows().find((x) => x.zip_status === "blank" && !x.address1 && !x.address2 && !x.city && !x.state);
  assert.ok(blank, "the CSVs hold rows with no address at all");
  const b = await call({ fiscal_year: Number(blank.fiscal_year), legal_name: blank.legal_name, zip_status: "blank", limit: 500 });
  assert.match(b.text, /grantee mailing address: \(none printed\) · zip — \(blank: no ZIP printed\)/);
});

test("a six-digit ZIP: repaired rows file under their zip; ambiguous rows show every candidate, no zip", async () => {
  // FAILS if a repaired_extra_digit row ('111691', Far Rockaway) is not found under its
  // repaired zip 11691, if an ambiguous_extra_digit row ('114345') is found under either
  // candidate, if its row does not list both candidates, or if a candidate is shown on a row of
  // any other status.
  const rows = allRows();
  const rep = rows.filter((r) => r.zip_status === "repaired_extra_digit" && r.postal_code === "111691");
  assert.ok(rep.length > 0 && rep.every((r) => r.zip === "11691"));
  const under = await call({ zip: "11691", zip_status: "repaired_extra_digit", limit: 1 });
  assert.ok(under.text.startsWith(`${rows.filter((r) => r.zip === "11691" && r.zip_status === "repaired_extra_digit").length.toLocaleString("en-US")} matching designation(s)`), under.text.slice(0, 80));
  const amb = rows.find((r) => r.zip_status === "ambiguous_extra_digit" && r.postal_code === "114345");
  assert.equal(amb.zip, "");
  assert.equal(amb.zip_candidates, "11434;11435");
  for (const z of ["11434", "11435"]) {
    const res = await call({ zip: z, zip_status: "ambiguous_extra_digit" });
    assert.match(res.text, /^No matching designations/, z);
  }
  const res = await call({ fiscal_year: Number(amb.fiscal_year), legal_name: amb.legal_name, zip_status: "ambiguous_extra_digit", limit: 500 });
  assert.ok(res.text.includes(" · zip — (ambiguous_extra_digit: six digits printed; more than one one-digit deletion is an in-state 2020 ZCTA, none picked) · candidates 11434, 11435"), res.text);
  const other = await call({ zip: "11691", zip_status: "repaired_extra_digit", limit: 500 });
  assert.doesNotMatch(other.text, /candidates/);
});
