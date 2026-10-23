/**
 * source-commit.mjs — the commit an index is built from, for build-index.mjs (meta.source_commit),
 * checked so a row's GitHub link never points at a commit GitHub may not have, or at a file that
 * differs from the one the row was read from. Its own module so test/source-commit.test.js can
 * run it on a small throwaway repository.
 */
import { execFileSync } from "node:child_process";
import { join } from "node:path";

/**
 * The git commit this index is built from, for the links to a row's PDF on GitHub (#212): never a
 * branch name, which moves. NYC_BUDGET_SOURCE_COMMIT overrides `git rev-parse HEAD` (a build from
 * an exported tree). The commit is recorded with a check of the PDFs the loaded rows cite:
 *   pdfs_match      every cited PDF is in that commit with exactly these bytes (git blob ids), the
 *                   commit is on origin/main, and data/ and source/ have no uncommitted change
 *   no_pdfs_cited   no PDF rows loaded (the npm package's index)
 *   mismatch: <p>   a cited PDF differs from (or is missing in) the commit
 *   not_on_main     the commit is not on origin/main: a local or squash-merged commit can be
 *                   missing on GitHub, so its links would 404
 *   dirty: <paths>  data/ or source/ has uncommitted changes: the tables are not "built from" it
 *   no_git          no commit could be found
 * Every check but pdfs_match blanks the commit, so no GitHub link is built rather than a wrong one.
 *
 * --allow-local-commit (tests and local trial releases only) skips the origin/main and clean-tree
 * conditions and records source_commit_scope = "local", which the manifest carries; a release for
 * GitHub (W7, #216) must be built without it.
 */
export function sourceCommit(repo, pdfs, { allowLocal = false, env = "" } = {}) {
  const git = (...a) => execFileSync("git", ["-C", repo, ...a], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  let commit = env ?? "";
  if (commit !== "" && !/^[0-9a-f]{40}$/i.test(commit)) throw new Error(`NYC_BUDGET_SOURCE_COMMIT must be a full 40-digit commit id; got ${JSON.stringify(commit)}`);
  try {
    if (commit === "") commit = git("rev-parse", "HEAD");
    else commit = git("rev-parse", "--verify", `${commit}^{commit}`);
  } catch {
    return { commit: "", check: "no_git" };
  }
  if (!pdfs.length) return { commit, check: "no_pdfs_cited" };
  if (!allowLocal) {
    let onMain = false;
    try {
      git("merge-base", "--is-ancestor", commit, "origin/main");
      onMain = true;
    } catch {
      onMain = false;
    }
    if (!onMain) return { commit: "", check: "not_on_main" };
    const dirty = git("status", "--porcelain", "--", "data", "source").split("\n").filter(Boolean);
    if (dirty.length) return { commit: "", check: `dirty: ${dirty.slice(0, 3).map((l) => l.trim().replace(/^\S+\s+/, "")).join(", ")}${dirty.length > 3 ? ", …" : ""}` };
  }
  const want = new Map();
  for (let i = 0; i < pdfs.length; i += 200) {
    const chunk = pdfs.slice(i, i + 200);
    const have = git("hash-object", "--", ...chunk.map((p) => join(repo, p))).split("\n");
    chunk.forEach((p, k) => want.set(p, have[k]));
  }
  const inCommit = new Map(git("ls-tree", "-r", commit, "--", ...pdfs).split("\n").filter(Boolean).map((l) => {
    const [meta, path] = l.split("\t");
    return [path, meta.split(" ")[2]];
  }));
  const bad = pdfs.find((p) => inCommit.get(p) !== want.get(p));
  return bad ? { commit: "", check: `mismatch: ${bad}` } : { commit, check: "pdfs_match" };
}

