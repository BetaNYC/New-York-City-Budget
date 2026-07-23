import { test } from "node:test";
import assert from "node:assert/strict";
import { searchAwards } from "../dist/db.js";

test("organization-filtered limits keep the highest-value awards", () => {
  const filters = {
    organization: "Association of Community Employment",
    fiscal_year: 2026,
  };
  const all = searchAwards({ ...filters, limit: 500 });
  const expected = [...all]
    .sort((a, b) => (b.amount ?? 0) - (a.amount ?? 0))
    .slice(0, 4);

  assert.deepEqual(
    searchAwards({ ...filters, limit: 4 }).map((row) => row.amount),
    expected.map((row) => row.amount)
  );
});
