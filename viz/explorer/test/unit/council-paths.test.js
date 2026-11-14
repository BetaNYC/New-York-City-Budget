import { describe, expect, test } from "vitest";

import { decodeRows } from "../../src/council/paths.js";

/** The Council JSON row format (#301; scripts/council-json.mjs writes it). */
describe("decodeRows", () => {
  test("plain and dictionary columns come back as the stored values, null kept", () => {
    // FAILS if a dictionary cell is not looked up, or a null is lost or turned into a value.
    const f = { columns: ["n", "status", "amount"], dicts: { status: ["Cleared", null] }, rows: [[1, 0, 5.5], [2, 1, null]] };
    expect(decodeRows(f)).toEqual([
      { n: 1, status: "Cleared", amount: 5.5 },
      { n: 2, status: null, amount: null },
    ]);
  });
  test("a file with no dictionaries is read as it is", () => {
    expect(decodeRows({ columns: ["a"], rows: [["x"]] })).toEqual([{ a: "x" }]);
  });
});
