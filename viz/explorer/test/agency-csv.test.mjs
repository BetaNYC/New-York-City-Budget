/**
 * The City agency budgets download (viz/agencies/data/nyc_budget.csv) is written from the index
 * (scripts/agency-csv.mjs, #288), and the committed file equals what the index gives, byte for
 * byte. FAILS if the file is edited by hand, or the index and the file drift apart (rebuild the
 * file with `node scripts/agency-csv.mjs`, in a PR that says why).
 *
 *   node --test test/agency-csv.test.mjs   (needs mcp/data/budget.db: `npm ci` in mcp/)
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { CSV_PATH, agencyCsv, readRows } from "../scripts/agency-csv.mjs";

test("nyc_budget.csv equals the index, byte for byte", () => {
  const want = agencyCsv(readRows());
  const have = readFileSync(CSV_PATH, "utf8");
  assert.equal(have.split("\r\n")[0], want.split("\r\n")[0], "header");
  assert.equal(have.length, want.length, "length");
  assert.ok(have === want, "nyc_budget.csv differs from the index");
});

test("the file keeps its shape: header, 0 for absent, newest Modified empty", () => {
  const rows = agencyCsv([
    { fiscal_year: 2017, agency_number: "001", agency_name: "A, INC", unit_number: "001", unit_name: "U", adopted: 5, modified: null },
    { fiscal_year: 2018, agency_number: "001", agency_name: "A, INC", unit_number: "001", unit_name: "U", adopted: null, modified: null },
  ]);
  assert.equal(rows, 'Fund,Department,Department ID,Adopted 2017,Modified 2017,Adopted 2018,Modified 2018\r\n"A, INC",U,001,5,0,0,\r\n');
});
