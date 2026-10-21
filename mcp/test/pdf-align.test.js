/**
 * scripts/pdf-families.mjs alignScheduleC on small cases: the rule of code/schedc/disclosure.py.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { alignScheduleC, streamOf } from "../scripts/pdf-families.mjs";

const d = (row, ein, amount, status, name, source) => ({ row, ein, amount, status, name, source });
const a = (award_id, section, ein, amount, org) => ({ award_id, section, ein, amount, org });

test("streams", () => {
  assert.deepEqual(["Local", " aging", "Youth", "Speaker's Initiative", "Speaker’s Initiative", "Anti-Poverty"].map(streamOf),
    ["local", "aging", "youth", "speaker", "speaker", "initiative"]);
});

test("a key pairs once per row; a body row prefers a non-appendix stream, then Cleared, then sheet order", () => {
  const disc = [d(1, "111", 500, "pending", "X", "Local"), d(2, "111", 500, "pending", "X", "Anti-Poverty"), d(3, "111", 500, "cleared", "X", "Anti-Poverty")];
  const r = alignScheduleC([a("b1", "body", "111", 500, "X"), a("c1", "appendix_b", "111", 500, "X")], disc);
  assert.equal(r.pairs.get("b1"), 2); // row 3: initiative stream, cleared
  assert.equal(r.pairs.get("c1"), 0); // row 1: its own stream (local)
  assert.deepEqual(r.discOnly.map((x) => [x.i, x.reason]), [[1, "amount_or_count_differs"]]);
});

test("the City's EIN pairs only when the disclosure name prefixes the PDF organization", () => {
  const disc = [d(1, "136400434", 1000, "cleared", "Dept. of Youth", "Anti-Poverty")];
  const no = alignScheduleC([a("p1", "body", "136400434", 1000, "Department for the Aging - meals")], disc);
  assert.equal(no.pairs.size, 0);
  assert.equal(no.pdfOnly[0].reason, "city_ein_name_mismatch");
  const yes = alignScheduleC([a("p1", "body", "136400434", 1000, "DEPT OF YOUTH - camps")], disc);
  assert.equal(yes.pairs.get("p1"), 0);
});

test("waterfall reasons", () => {
  const disc = [d(1, "222", 700, "cleared", "Y", "Local")];
  const r = alignScheduleC([a("p1", "body", "222", 500, "Y"), a("p2", "body", "333", 500, "Z")], disc);
  assert.deepEqual(r.pdfOnly.map((u) => [u.award.award_id, u.reason, u.near]), [["p1", "amount_differs", 700], ["p2", "ein_not_in_disclosure", null]]);
});
