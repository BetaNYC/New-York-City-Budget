/**
 * A printed value pasted back exactly must find its own rows (review S2, 2026-10-17). The fold
 * twin is skipped where folding changes only ASCII case; this proves that skip never hides a row,
 * for every distinct non-ASCII value in every substring-searched column, including the t474
 * mojibake ("OssΘ", "AvilΘs", "Avil├⌐s", "Cabßn", "FAΤADE") the source carries as published.
 * Expected counts come from the committed CSVs, never from the index.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { searchDisclosure, searchCapital } from "../dist/db.js";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const readCsv = (rel) => parse(readFileSync(join(REPO, rel), "utf8"), { columns: true, skip_empty_lines: true, bom: true });
const nonAscii = (s) => /[^\x00-\x7f]/.test(s);

function distinct(rows, cols) {
  const m = new Map();
  for (const r of rows)
    for (const c of cols)
      if (nonAscii(r[c] ?? "")) m.set(`${c}\t${r[c]}`, (m.get(`${c}\t${r[c]}`) ?? 0) + 1);
  return [...m.entries()].map(([k, n]) => [...k.split("\t"), n]);
}

test("every non-ASCII capital sponsor, title and description finds its own rows", () => {
  const cap = readCsv("data/capital/council_capital_awards.csv");
  const vals = distinct(cap, ["sponsor", "title", "description"]);
  assert.ok(vals.some(([c, v]) => c === "sponsor" && v === "OssΘ"), "premise: the t474 mojibake is present");
  assert.ok(vals.some(([c, v]) => c === "description" && v.includes("FAΤADE")));
  for (const [col, v, n] of vals) {
    const res = searchCapital({ [col]: v, limit: 1 });
    assert.ok(res.matched >= n, `${col} ${JSON.stringify(v)}: ${res.matched} < ${n}`);
  }
  assert.equal(searchCapital({ sponsor: "OssΘ", limit: 1 }).matched >= 16, true);
  assert.equal(searchCapital({ sponsor: "AvilΘs", limit: 1 }).matched >= 20, true);
});

test("every non-ASCII disclosure legal_name, member, source, agency and program finds its own rows", () => {
  const dirs = readdirSync(join(REPO, "data")).filter((d) => /^fy\d\d$/.test(d));
  const rows = dirs.flatMap((d) => {
    try {
      return readCsv(`data/${d}/expense_disclosure/${d}_expense_awards.csv`);
    } catch {
      return [];
    }
  });
  const vals = distinct(rows, ["legal_name", "council_member", "source", "agency", "program_name"]);
  assert.ok(vals.length > 100, "premise");
  for (const [col, v, n] of vals) {
    const res = searchDisclosure({ [col]: v, limit: 1 });
    assert.ok(res.matched >= n, `${col} ${JSON.stringify(v)}: ${res.matched} < ${n}`);
  }
});

test("fold edge cases: capital sharp s, dotless i, zero-width characters, okina, guillemets", async () => {
  // Review nit 1 (2026-10-17). FAILS if any pair below folds differently.
  const { fold } = await import("../dist/fold.js");
  for (const [a, b] of [
    ["STRAẞE", "strasse"], ["Straße", "strasse"], ["Kadıköy", "kadikoy"], ["İstanbul", "istanbul"],
    ["Fifth​Avenue", "fifthavenue"], ["Hawaiʻi", "hawai'i"], ["«Casa»", '"casa"'],
    ["Łódź", "lodz"], ["Ærø", "aero"], ["Women’s", "women's"], ["Jewish Émigré", "jewish emigre"],
    ["  A  B  ", "a b"], ["ＡＢＣ１２３", "abc123"],
  ])
    assert.equal(fold(a), b, a);
});
