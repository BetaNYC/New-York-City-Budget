/**
 * The commit a build records for the PDF links (scripts/source-commit.mjs, #212 review), on a
 * small throwaway repository: a link is built only from a commit on origin/main, with data/ and
 * source/ clean and every cited PDF the same file there. Anything else records no commit, so no
 * GitHub link can 404 or point at a different file. --allow-local-commit (tests, local trials)
 * skips only the origin/main and clean-tree conditions.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { sourceCommit } from "../scripts/source-commit.mjs";

const TMP = join(dirname(fileURLToPath(import.meta.url)), "..", ".pdf-test", "source-commit");
const PDF = "source/FY27/a.pdf";
const git = (...a) => execFileSync("git", ["-C", TMP, ...a], { encoding: "utf8" }).trim();

let main;
before(() => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(join(TMP, "source", "FY27"), { recursive: true });
  mkdirSync(join(TMP, "data"), { recursive: true });
  git("init", "-q");
  git("config", "user.email", "test@example.org");
  git("config", "user.name", "test");
  git("config", "commit.gpgsign", "false");
  writeFileSync(join(TMP, PDF), "%PDF-1.4 one");
  writeFileSync(join(TMP, "data", "x.csv"), "a\n1\n");
  git("add", "-A");
  git("commit", "-q", "-m", "one");
  main = git("rev-parse", "HEAD");
  git("update-ref", "refs/remotes/origin/main", main);
});
after(() => rmSync(TMP, { recursive: true, force: true }));

test("a clean commit on origin/main whose PDFs match: recorded", () => {
  assert.deepEqual(sourceCommit(TMP, [PDF]), { commit: main, check: "pdfs_match" });
  assert.deepEqual(sourceCommit(TMP, []), { commit: main, check: "no_pdfs_cited" });
});

test("data/ or source/ changed but not committed: no commit", () => {
  writeFileSync(join(TMP, "data", "x.csv"), "a\n2\n");
  try {
    const r = sourceCommit(TMP, [PDF]);
    assert.equal(r.commit, "");
    assert.match(r.check, /^dirty: data\/x\.csv/);
  } finally {
    git("checkout", "-q", "--", "data/x.csv");
  }
});

test("a commit not on origin/main (a branch, a squash merge): no commit, unless --allow-local-commit", () => {
  writeFileSync(join(TMP, "data", "y.csv"), "b\n");
  git("add", "-A");
  git("commit", "-q", "-m", "two");
  const local = git("rev-parse", "HEAD");
  try {
    assert.deepEqual(sourceCommit(TMP, [PDF]), { commit: "", check: "not_on_main" });
    assert.deepEqual(sourceCommit(TMP, [PDF], { allowLocal: true }), { commit: local, check: "pdfs_match" });
  } finally {
    git("reset", "-q", "--hard", main);
  }
});

test("a PDF that differs from the commit's: no commit, even with --allow-local-commit", () => {
  writeFileSync(join(TMP, PDF), "%PDF-1.4 changed");
  try {
    assert.equal(sourceCommit(TMP, [PDF]).commit, "", "dirty source/");
    assert.deepEqual(sourceCommit(TMP, [PDF], { allowLocal: true }), { commit: "", check: `mismatch: ${PDF}` });
  } finally {
    git("checkout", "-q", "--", PDF);
  }
});

test("NYC_BUDGET_SOURCE_COMMIT must be a full commit id", () => {
  assert.throws(() => sourceCommit(TMP, [PDF], { env: "main" }), /must be a full 40-digit commit id/);
  assert.deepEqual(sourceCommit(TMP, [PDF], { env: main }), { commit: main, check: "pdfs_match" });
});
