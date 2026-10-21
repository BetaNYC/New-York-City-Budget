import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";

import { crc32, makeZip } from "../../src/review/zip.js";
import * as R from "../../src/review/queue.js";

describe("zip", () => {
  test("crc32 matches the standard check value", () => {
    expect(crc32(new TextEncoder().encode("123456789"))).toBe(0xcbf43926);
  });
  test("a zip that unzip reads back byte for byte", () => {
    const files = [
      { name: "fy27_capital_sd_review_decisions.csv", text: "review_id,decision,note,decided_by,decided_at\na,accepted_as_printed,\"x, y\",Noel,2026-10-21\n" },
      { name: "fy26_sc_review_decisions.csv", text: "review_id,decision,note,decided_by,decided_at\nb,source_error,Avilés,Noel,2026-10-21\n" },
    ];
    const dir = mkdtempSync(join(tmpdir(), "zip-"));
    const zip = join(dir, "t.zip");
    writeFileSync(zip, makeZip(files));
    const t = spawnSync("unzip", ["-t", zip], { encoding: "utf8" });
    expect(t.status, t.stdout + t.stderr).toBe(0);
    spawnSync("unzip", ["-q", zip, "-d", join(dir, "out")]);
    for (const f of files) expect(readFileSync(join(dir, "out", f.name), "utf8")).toBe(f.text);
  });
});

describe("Export all my decisions", () => {
  const items = [
    { family: "capital_sd", fiscal_year: 2027, review_id: "a", severity: "warn", dollars: 1 },
    { family: "capital_sd", fiscal_year: 2027, review_id: "b", severity: "warn", dollars: 2 },
    { family: "schedule_c", fiscal_year: 2026, review_id: "c", severity: "warn", dollars: 3 },
    { family: "schedule_c", fiscal_year: 2027, review_id: "d", severity: "warn", dollars: 4, decision: "source_error" },
    { family: "terms", fiscal_year: 2027, review_id: "e", severity: "warn", dollars: 5 },
  ];
  const now = new Date("2026-10-21T08:00:00Z");
  const dec = Object.fromEntries(["a", "c", "d"].map((id) => {
    const it = items.find((x) => x.review_id === id);
    return [R.itemKey(it), R.decide("keep", it, { by: "Noel", now })];
  }));
  test("one file per family/year with a new decision; committed and undecided items are left out", () => {
    const g = R.exportGroups(items, dec, { capital_sd: { 2027: "research/x/fy27_capital_sd_review_decisions.csv" } });
    expect(g.map((x) => [x.family, x.fiscal_year, x.count, x.name])).toEqual([
      ["capital_sd", 2027, 1, "fy27_capital_sd_review_decisions.csv"],
      ["schedule_c", 2026, 1, "fy26_schedule_c_review_decisions.csv"],
    ]);
    expect(g[0].text).toBe("review_id,decision,note,decided_by,decided_at\na,accepted_as_printed,,Noel,2026-10-21T08:00:00.000Z\n");
    expect(R.exportGroups(items, {})).toEqual([]);
  });
});
