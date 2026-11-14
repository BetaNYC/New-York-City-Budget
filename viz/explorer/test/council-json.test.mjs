/**
 * The Council explorer's JSON files (#301, third PR; scripts/council-json.mjs): written from the
 * index by `npm run data`, checked against it on every build. Needs the data build
 * (public/data/manifest.json and .cache/ or mcp/data/ budget.db).
 *
 * Each test says what result would make it FAIL.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { cpSync, existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import Database from "better-sqlite3";

import { verifyCouncilJson } from "../scripts/council-json.mjs";
import { COUNCIL_JSON_DIR, awardsYearPath, capitalYearPath, councilYearsPath } from "../src/council/paths.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const DATA = join(ROOT, "public", "data");
const MANIFEST = JSON.parse(readFileSync(join(DATA, "manifest.json"), "utf8"));
const DB = join(ROOT, "..", "..", MANIFEST.index);

let sqlite;
before(() => {
  sqlite = new Database(DB, { readonly: true, fileMustExist: true });
});
after(() => sqlite?.close());

test("every file agrees with the index, cell for cell and total for total", () => {
  // FAILS if any JSON value differs from budget.db (the build would have stopped too).
  const { diffs, cells } = verifyCouncilJson(sqlite, DATA);
  assert.deepEqual(diffs.slice(0, 10), []);
  assert.ok(cells > 1_000_000, `${cells} cells compared`);
});

test("one changed cell is caught", () => {
  // FAILS if the check would let a wrong amount, or a dropped row, onto the site.
  const copy = mkdtempSync(join(tmpdir(), "council-json-"));
  cpSync(join(DATA, COUNCIL_JSON_DIR), join(copy, COUNCIL_JSON_DIR), { recursive: true });
  const years = JSON.parse(readFileSync(join(DATA, councilYearsPath()), "utf8")).disclosure_years;
  const newest = Math.max(...years.filter((y) => y.loaded).map((y) => y.fiscal_year));
  const p = join(copy, awardsYearPath(newest));
  const f = JSON.parse(readFileSync(p, "utf8"));
  const amt = f.columns.indexOf("amount");
  // A dictionary-encoded amount points at another of its values; a plain one gains a dollar.
  if (f.dicts.amount) f.rows[0][amt] = (f.rows[0][amt] + 1) % f.dicts.amount.length;
  else f.rows[0][amt] += 1;
  writeFileSync(p, JSON.stringify(f));
  const { diffs } = verifyCouncilJson(sqlite, copy);
  assert.equal(diffs.length, 1, diffs.join("\n"));
  assert.match(diffs[0], new RegExp(`fy${newest}.json row 1 amount`));
  f.rows.pop();
  writeFileSync(p, JSON.stringify(f));
  assert.match(verifyCouncilJson(sqlite, copy).diffs.join("\n"), /rows, table/);
});

test("the manifest lists each file with its size and sha256", () => {
  // FAILS if the app could fetch a file the manifest does not name, or a stale one.
  const list = MANIFEST.council_json?.files ?? {};
  assert.ok(list[councilYearsPath()]);
  for (const [path, { bytes, sha256 }] of Object.entries(list)) {
    const text = readFileSync(join(DATA, path));
    assert.equal(text.length, bytes, path);
    assert.equal(createHash("sha256").update(text).digest("hex"), sha256, path);
  }
});

test("a fast view's files stay small: each year file under 0.4 MB over the wire and 3 MB decoded", () => {
  // FAILS if a year file grows past what plan step 3 sized (the largest, FY2026, about 0.35 MB
  // gzipped). The budget for a whole first visit is checked in the browser (e2e/council.weight.spec.js).
  const list = MANIFEST.council_json.files;
  for (const [path] of Object.entries(list)) {
    const text = readFileSync(join(DATA, path));
    const wire = gzipSync(text, { level: 6 }).length;
    assert.ok(wire < 400_000, `${path}: ${wire} bytes gzipped`);
    assert.ok(text.length < 3_000_000, `${path}: ${text.length} bytes`);
  }
  assert.ok(existsSync(join(DATA, capitalYearPath(2018))), "FY2018 capital (PDF-derived, #202) has its file");
});
