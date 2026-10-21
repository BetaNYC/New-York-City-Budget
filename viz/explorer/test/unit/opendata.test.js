import { describe, expect, test } from "vitest";

import { bucketCounts, equalBucket, shownStatus } from "../../src/query/opendata.js";

// QA 2026-10-21: an ambiguous bucket with more of ours than portal rows must not claim presence.
describe("Open Data badge status", () => {
  const rule = (n, m, certain) =>
    `fy_ein_amount: bucket holds ${n} of ours and ${m} on the portal; ${certain ? "presence certain: every one of ours has a portal row" : "presence uncertain: more of ours than on the portal"}`;
  test("claims presence only when ours fit", () => {
    expect(shownStatus({ match_status: "ambiguous", match_rule: rule(2, 3, true) })).toBe("ambiguous");
    expect(shownStatus({ match_status: "ambiguous", match_rule: rule(2, 1, false) })).toBe("possible");
    expect(equalBucket({ match_rule: rule(2, 1, false) })).toBe(false);
    expect(bucketCounts({ match_rule: rule(2, 1, false) })).toEqual([2, 1]);
  });
  test("other statuses pass through", () => {
    for (const s of ["same", "differs", "absent", "context"]) expect(shownStatus({ match_status: s })).toBe(s);
  });
});
