/**
 * The automatic PDF-tables release (W7, #216): scripts/verify-pdf-release.mjs, which the workflow
 * (.github/workflows/pdf-tables-release.yml) runs before publishing, and the release it hands
 * over, served from a local HTTP server as GitHub would serve it. Never against GitHub.
 *
 *   - the release pretest built verifies, and lists exactly the manifest's files, manifest last;
 *   - a local build (source_commit_scope "local"), a tampered, missing or extra-byte file, or
 *     another commit is refused, with the reason;
 *   - the tag the workflow makes is one the downloader picks (pickRelease), and the downloader
 *     (the CLI) installs the tables from exactly the files the workflow would upload;
 *   - the workflow itself: no pull_request trigger, contents: write only on the publish job,
 *     never --allow-local-commit, dry_run defaulting to true.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { pickRelease, RELEASE_TAG_PREFIX } from "../dist/pdfdata.js";
import { ASSET_LIST, releaseNotes, releaseTag, verifyRelease } from "../scripts/verify-pdf-release.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const RELEASE = join(MCP, ".pdf-test", "release");
const TMP = join(MCP, ".pdf-test", "release-check");
const WORKFLOW = join(REPO, ".github", "workflows", "pdf-tables-release.yml");
const sha256 = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");
const MANIFEST = JSON.parse(readFileSync(join(RELEASE, "pdf-tables.manifest.json"), "utf8"));

/** A copy of pretest's release (links to its big files, so the shared folder is never written). */
function release(name, edit = () => {}) {
  const dir = join(TMP, name);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  for (const f of ["pdf-tables.manifest.json", "pdf-tables.db.gz", "pdf-tables.db"]) symlinkSync(join(RELEASE, f), join(dir, f));
  edit(dir);
  return dir;
}

let server;
let base;
let serveDir;
before(async () => {
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(TMP, { recursive: true });
  server = createServer((req, res) => {
    const p = join(serveDir, decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, ""));
    if (!p.startsWith(serveDir) || !existsSync(p)) return res.writeHead(404).end();
    res.writeHead(200, { "content-length": statSync(p).size });
    res.end(readFileSync(p));
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  base = `http://127.0.0.1:${server.address().port}`;
});
after(() => {
  server.close();
  rmSync(TMP, { recursive: true, force: true });
});

function cli(args, env = {}) {
  return new Promise((resolve) => {
    const p = spawn(process.execPath, [join(MCP, "dist", "index.js"), ...args], {
      cwd: MCP, env: { ...process.env, NYC_BUDGET_PDF_DATA: "", NYC_BUDGET_PDF_DATA_URL: "", ...env },
    });
    let out = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (out += d));
    p.on("exit", (code) => resolve({ code, out }));
  });
}

test("pretest's release verifies, and the upload list is the manifest's files with the manifest last", async () => {
  // FAILS if a correct release is refused, or the upload list leaves out or adds a file.
  assert.equal(MANIFEST.source_commit_scope, "local", "pretest builds with --allow-local-commit");
  const dir = release("ok");
  assert.deepEqual(await verifyRelease(dir, { allowLocal: true }), []);
  const assets = readFileSync(join(dir, ASSET_LIST), "utf8").trim().split("\n");
  assert.deepEqual(assets, [...MANIFEST.files.map((f) => f.name), "pdf-tables.manifest.json"]);
  assert.ok(!assets.includes("pdf-tables.db"), "the unpacked tables are never uploaded");
});

test("a local build is never publishable: scope local, a commit not on origin/main", async () => {
  // FAILS if verify (without --allow-local-commit, as the workflow runs it) accepts scope "local".
  const dir = release("local");
  const problems = await verifyRelease(dir, { commit: MANIFEST.source_commit });
  assert.ok(problems.some((p) => /source_commit_scope is "local"/.test(p)), problems.join("\n"));
  assert.ok(!existsSync(join(dir, ASSET_LIST)), "no upload list for a refused release");
});

test("the pushed commit must be the one the tables were built from", async () => {
  const dir = release("other-commit", (d) => {
    rmSync(join(d, "pdf-tables.manifest.json"));
    writeFileSync(join(d, "pdf-tables.manifest.json"), JSON.stringify({ ...MANIFEST, source_commit_scope: "origin/main" }));
  });
  const problems = await verifyRelease(dir, { commit: "f".repeat(40) });
  assert.ok(problems.some((p) => p.includes(`not the pushed commit ${"f".repeat(40)}`)), problems.join("\n"));
  assert.ok(problems.some((p) => /not on origin\/main|checkout is at/.test(p)), problems.join("\n"));
  assert.ok((await verifyRelease(dir, { commit: "main" })).some((p) => /full 40-digit/.test(p)));
});

test("a tampered, missing or unlisted-format file is refused, with the file named", async () => {
  // FAILS if a byte changed in the tables, a missing PDF or a bad manifest passes the check.
  const tampered = release("tampered", (d) => {
    rmSync(join(d, "pdf-tables.db.gz"));
    copyFileSync(join(RELEASE, "pdf-tables.db.gz"), join(d, "pdf-tables.db.gz"));
    writeFileSync(join(d, "pdf-tables.db.gz"), Buffer.from([0]), { flag: "a" });
  });
  assert.ok((await verifyRelease(tampered, { allowLocal: true })).some((p) => p.startsWith("pdf-tables.db.gz:")));

  const missing = release("missing", (d) => {
    rmSync(join(d, "pdf-tables.manifest.json"));
    const m = { ...MANIFEST, files: [...MANIFEST.files, { name: `${"a".repeat(64)}.pdf`, kind: "pdf", path: "source/FY27/x.pdf", bytes: 1, sha256: "a".repeat(64) }] };
    writeFileSync(join(d, "pdf-tables.manifest.json"), JSON.stringify(m));
  });
  assert.ok((await verifyRelease(missing, { allowLocal: true })).some((p) => /missing from the folder/.test(p)));

  const badFormat = release("format", (d) => {
    rmSync(join(d, "pdf-tables.manifest.json"));
    writeFileSync(join(d, "pdf-tables.manifest.json"), JSON.stringify({ ...MANIFEST, format: "nyc-budget-pdf-tables/2" }));
  });
  assert.ok((await verifyRelease(badFormat, { allowLocal: true }))[0].startsWith("the downloader would refuse the manifest"));
});

test("the workflow's tag is one the downloader picks, and it installs exactly the uploaded files", async () => {
  // FAILS if the tag format or the asset names drift from what src/pdfdata.ts looks for, or the
  // files the workflow uploads (release-assets.txt) are not enough to install the tables.
  const commit = "0123456789abcdef0123456789abcdef01234567";
  const tag = releaseTag(new Date("2026-10-23T05:00:00Z"), commit);
  assert.equal(tag, "pdf-tables-2026-10-23-0123456");
  assert.ok(tag.startsWith(RELEASE_TAG_PREFIX));
  assert.throws(() => releaseTag(new Date(), "0123456"), /full commit id/);

  // What the publish job uploads: only the listed files, flat, as GitHub serves release assets.
  const dir = release("upload");
  assert.deepEqual(await verifyRelease(dir, { allowLocal: true }), []);
  serveDir = join(TMP, "served");
  mkdirSync(serveDir, { recursive: true });
  for (const f of readFileSync(join(dir, ASSET_LIST), "utf8").trim().split("\n")) copyFileSync(join(dir, f), join(serveDir, f));
  const releases = [
    { tag_name: "mcp-v2.0.1", draft: false, prerelease: false, published_at: "2026-10-24T00:00:00Z", assets: [] },
    { tag_name: tag, draft: false, prerelease: false, published_at: "2026-10-23T05:00:00Z",
      assets: readFileSync(join(dir, ASSET_LIST), "utf8").trim().split("\n").map((name) => ({ name, browser_download_url: `${base}/${name}` })) },
    // A draft (the workflow's state mid-upload) is never picked.
    { tag_name: releaseTag(new Date("2026-10-25T00:00:00Z"), commit), draft: true, prerelease: false, published_at: null,
      assets: [{ name: "pdf-tables.manifest.json", browser_download_url: `${base}/draft.json` }] },
  ];
  const url = pickRelease(releases);
  assert.equal(url, `${base}/pdf-tables.manifest.json`);

  const home = join(TMP, "user");
  const r = await cli(["download", "--pdf-tables", "--from", url], { NYC_BUDGET_DATA_DIR: home });
  assert.equal(r.code, 0, r.out);
  assert.equal(sha256(join(home, "pdf-tables", "pdf-tables.db")), MANIFEST.files.find((f) => f.kind === "pdf_tables").unpacked.sha256);
});

test("the release notes name the commit, how to install, and every family-year", () => {
  const out = join(TMP, "notes.md");
  const text = releaseNotes(RELEASE, out);
  assert.ok(text.includes(MANIFEST.source_commit));
  assert.match(text, /npx @betanyc\/nyc-budget-mcp download --pdf-tables/);
  assert.equal((text.match(/^- FY\d{4} /gm) ?? []).length, MANIFEST.families.length);
});

test("the workflow: main only, never a PR, write access on the publish job only, never a local build", () => {
  // FAILS if someone adds a pull_request trigger, widens the permissions, or lets a local build through.
  const y = readFileSync(WORKFLOW, "utf8");
  const code = y.split("\n").filter((l) => !l.trim().startsWith("#")).join("\n");
  assert.doesNotMatch(code, /pull_request/);
  assert.match(code, /^permissions: \{\}$/m);
  assert.equal((code.match(/contents: write/g) ?? []).length, 1);
  const publish = code.slice(code.indexOf("\n  publish:"));
  assert.match(publish, /contents: write/);
  assert.doesNotMatch(code.slice(0, code.indexOf("\n  publish:")), /contents: write/);
  assert.doesNotMatch(code, /--allow-local-commit/);
  assert.match(code, /verify-pdf-release\.mjs --dir "\$RUNNER_TEMP\/pdf-release" --commit "\$GITHUB_SHA"/);
  assert.match(code, /dry_run:[\s\S]*?default: true/);
  assert.match(code, /inputs\.dry_run == false/);
  // A push publishes only once a maintainer sets the repository variable (the first run is theirs).
  assert.match(publish, /github\.event_name == 'push' && vars\.PDF_TABLES_AUTO_PUBLISH == 'true'/);
  assert.equal((code.match(/github\.repository == 'BetaNYC\/New-York-City-Budget' && github\.ref == 'refs\/heads\/main'/g) ?? []).length, 2);
  assert.match(code, /--draft/);
  assert.match(code, /--latest=false/);
});
