import { describe, expect, test } from "vitest";

import { docUrl, sourceLinks } from "../../src/paths.js";

describe("source links", () => {
  const sha = "c389f5744a2ef6e8daa6c567edd17ed8b8d610f0";

  test("pin the file to the build's commit, raw and GitHub page", () => {
    const l = sourceLinks(sha, "source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx");
    expect(l.raw).toBe(`https://raw.githubusercontent.com/BetaNYC/New-York-City-Budget/${sha}/source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx`);
    expect(l.page).toBe(`https://github.com/BetaNYC/New-York-City-Budget/blob/${sha}/source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx`);
  });

  test("encode each path segment but keep the slashes", () => {
    expect(sourceLinks(sha, "source/a b/c#d.xlsx").raw).toMatch(/\/source\/a%20b\/c%23d\.xlsx$/);
  });

  test("no commit or no path: no link, never a guess", () => {
    expect(sourceLinks("", "source/x.xlsx")).toBeNull();
    expect(sourceLinks(sha, "")).toBeNull();
  });

  test("docUrl falls back to main only when no commit is known", () => {
    expect(docUrl(null, "DATA-DICTIONARY.md")).toBe("https://github.com/BetaNYC/New-York-City-Budget/blob/main/DATA-DICTIONARY.md");
  });
});
