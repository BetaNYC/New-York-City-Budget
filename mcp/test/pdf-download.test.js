/**
 * The optional PDF-tables download (#215), tested against a local HTTP server and a local folder
 * serving the release that pretest built (scripts/build-pdf-release.mjs). Never against GitHub:
 * no release exists yet, and a test must not depend on the network.
 *
 *   - `download --pdf-tables` (the CLI) installs the tables into NYC_BUDGET_DATA_DIR, checked
 *     against the manifest's sha256; the tools then answer from them.
 *   - `--pdfs` also installs the PDFs, at their repo paths, and rows name the local copy.
 *   - a wrong sha256, a wrong size, a bad name or a missing file installs nothing and leaves a
 *     working install in place.
 *   - NYC_BUDGET_PDF_DATA=on downloads on start, in the background.
 *   - the newest pdf-tables-* release is picked from GitHub's release list (pickRelease).
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";
import { parseManifest, pickRelease } from "../dist/pdfdata.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");
const RELEASE = join(MCP, ".pdf-test", "release");
const TMP = join(MCP, ".pdf-test", "download");
const SERVE = join(TMP, "serve");
const sha256 = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");

let server;
let base;
const requests = [];

/** The release folder: pretest's tables, plus two PDFs so --pdfs has something to fetch. */
function makeRelease(dir, edit = (m) => m) {
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const m = JSON.parse(readFileSync(join(RELEASE, "pdf-tables.manifest.json"), "utf8"));
  copyFileSync(join(RELEASE, "pdf-tables.db.gz"), join(dir, "pdf-tables.db.gz"));
  m.files = m.files.filter((f) => f.kind === "pdf_tables");
  for (const path of ["source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf", "source/FY27/FY27-FINAL-Terms-and-Conditions-6.30.26.pdf"]) {
    const sha = sha256(join(REPO, path));
    copyFileSync(join(REPO, path), join(dir, `${sha}.pdf`));
    m.files.push({ name: `${sha}.pdf`, kind: "pdf", path, bytes: statSync(join(REPO, path)).size, sha256: sha });
  }
  m.pdfs_included = true;
  writeFileSync(join(dir, "pdf-tables.manifest.json"), JSON.stringify(edit(m), null, 2));
}

before(async () => {
  rmSync(TMP, { recursive: true, force: true });
  makeRelease(SERVE);
  server = createServer((req, res) => {
    requests.push(req.url);
    const p = join(SERVE, decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, ""));
    if (!p.startsWith(SERVE) || !existsSync(p)) {
      res.writeHead(404).end();
      return;
    }
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

/** Run the CLI (dist/index.js) and collect its exit code and output. */
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

/** Ask a tool through a fresh server process with this data folder. */
function ask(dir, name, args) {
  const script = `
    import { Client } from "@modelcontextprotocol/sdk/client/index.js";
    import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
    const { server } = await import(${JSON.stringify(join(MCP, "dist", "server.js"))});
    const [ct, st] = InMemoryTransport.createLinkedPair();
    await server.connect(st);
    const client = new Client({ name: "dl", version: "0" }, { capabilities: {} });
    await client.connect(ct);
    const r = await client.callTool({ name: ${JSON.stringify(name)}, arguments: ${JSON.stringify(args)} });
    process.stdout.write(r.content.map((c) => c.text).join("\\n"));
    await client.close();
  `;
  return new Promise((resolve) => {
    const p = spawn(process.execPath, ["--input-type=module", "-e", script], { cwd: MCP, env: { ...process.env, NYC_BUDGET_DATA_DIR: dir, NYC_BUDGET_PDF_DATA: "" } });
    let out = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (out += d));
    p.on("exit", () => resolve(out));
  });
}

test("download --pdf-tables installs the checked tables from a release over HTTP", async () => {
  // FAILS if the CLI does not install, installs a file whose sha256 differs from the manifest's,
  // or the tools still say the tables are missing.
  const dir = join(TMP, "user1");
  const before = await ask(dir, "search_schedule_c_awards", { fiscal_year: 2027, organization: "medicare rights" });
  assert.match(before, /They are not installed on this machine/);
  const r = await cli(["download", "--pdf-tables", "--from", `${base}/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
  assert.equal(r.code, 0, r.out);
  const m = JSON.parse(readFileSync(join(SERVE, "pdf-tables.manifest.json"), "utf8"));
  const db = join(dir, "pdf-tables", "pdf-tables.db");
  assert.equal(sha256(db), m.files[0].unpacked.sha256);
  assert.equal(JSON.parse(readFileSync(join(dir, "pdf-tables", "manifest.json"), "utf8")).installed_from, `${base}/pdf-tables.manifest.json`);
  assert.ok(!existsSync(join(dir, "pdfs")), "no PDFs without --pdfs");
  assert.deepEqual(readdirSync(join(dir, "pdf-tables")).sort(), ["manifest.json", "pdf-tables.db"], "no temp file left");
  const after = await ask(dir, "search_schedule_c_awards", { fiscal_year: 2027, organization: "medicare rights" });
  assert.match(after, /11 matching award row\(s\)/);
  assert.match(after, /status: checked, review in progress/);
  assert.doesNotMatch(after, /on this machine:/);
});

test("--pdfs also installs the PDFs, and rows name the local copy", async () => {
  const dir = join(TMP, "user2");
  const r = await cli(["download", "--pdfs", "--from", `${base}/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
  assert.equal(r.code, 0, r.out);
  const local = join(dir, "pdfs", "source", "FY27", "Fiscal-2027-Schedule-C-Final-3.pdf");
  assert.equal(sha256(local), sha256(join(REPO, "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf")));
  const out = await ask(dir, "search_schedule_c_awards", { fiscal_year: 2027, organization: "medicare rights", limit: 1 });
  assert.ok(out.includes(`on this machine: ${local}`), out.slice(0, 2000));
});

test("a local manifest path works too (no HTTP)", async () => {
  const dir = join(TMP, "user3");
  const r = await cli(["download", "--pdf-tables", "--from", join(SERVE, "pdf-tables.manifest.json")], { NYC_BUDGET_DATA_DIR: dir });
  assert.equal(r.code, 0, r.out);
  assert.ok(existsSync(join(dir, "pdf-tables", "pdf-tables.db")));
  const r2 = await cli(["download", "--pdf-tables"], { NYC_BUDGET_DATA_DIR: join(TMP, "user3b"), NYC_BUDGET_PDF_DATA_URL: pathToFileURL(join(SERVE, "pdf-tables.manifest.json")).href });
  assert.equal(r2.code, 0, r2.out);
});

test("a file that does not match the manifest installs nothing and keeps the working install", async () => {
  // FAILS if a corrupt or tampered download replaces anything.
  const dir = join(TMP, "user1"); // installed by the first test
  const good = sha256(join(dir, "pdf-tables", "pdf-tables.db"));
  const cases = [
    ["sha", (m) => ((m.files[0].sha256 = "0".repeat(64)), m), /does not match the manifest's size and sha256/],
    ["unpacked", (m) => ((m.files[0].unpacked.sha256 = "1".repeat(64)), m), /the unpacked file does not match/],
    ["size", (m) => ((m.files[0].bytes += 1), m), /does not match the manifest's size and sha256/],
    // More bytes than the manifest says: stopped as they arrive, packed or unpacked (a gzip bomb).
    ["too-big", (m) => ((m.files[0].bytes -= 1), m), /more than the manifest's \d+ bytes; stopped/],
    ["too-big-unpacked", (m) => ((m.files[0].unpacked.bytes = 1000), m), /unpacked: more than the manifest's 1000 bytes; stopped/],
    // A PDF that fails after the tables were staged: the 116 MB staged file must go too.
    ["pdf-sha", (m) => ((m.files[1].sha256 = "2".repeat(64)), m), /does not match the manifest's size and sha256/],
    ["name", (m) => ((m.files[0].name = "../pdf-tables.db.gz"), m), /not a plain file name/],
    ["path", (m) => ((m.files[1].path = "source/../../etc/x.pdf"), m), /is not a source PDF path/],
    ["format", (m) => ((m.format = "nyc-budget-pdf-tables/9"), m), /this version reads nyc-budget-pdf-tables\/1/],
    ["missing", (m) => ((m.files[0].name = "nope.db.gz"), m), /HTTP 404/],
  ];
  for (const [label, edit, re] of cases) {
    const dirServe = join(TMP, `bad-${label}`);
    makeRelease(dirServe, edit);
    let r;
    if (label === "missing") {
      // Over HTTP, so the server's 404 is what fails.
      mkdirSync(join(SERVE, "bad-missing"), { recursive: true });
      for (const f of readdirSync(dirServe)) copyFileSync(join(dirServe, f), join(SERVE, "bad-missing", f));
      r = await cli(["download", "--pdf-tables", "--from", `${base}/bad-missing/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
    } else {
      r = await cli(["download", "--pdfs", "--from", join(dirServe, "pdf-tables.manifest.json")], { NYC_BUDGET_DATA_DIR: dir });
    }
    assert.notEqual(r.code, 0, label);
    assert.match(r.out, re, label);
    assert.equal(sha256(join(dir, "pdf-tables", "pdf-tables.db")), good, `${label}: the working install is untouched`);
    assert.deepEqual(readdirSync(join(dir, "pdf-tables")).sort(), ["manifest.json", "pdf-tables.db"], `${label}: no temp or lock file left`);
    assert.deepEqual(tempFiles(dir), [], `${label}: no temp file anywhere`);
  }
});

/** Every *.download-<pid> or *.verified-<pid> file under a data folder. */
function tempFiles(dir) {
  const out = [];
  const walk = (d) => {
    if (!existsSync(d)) return;
    for (const e of readdirSync(d, { withFileTypes: true })) {
      if (e.isDirectory()) walk(join(d, e.name));
      else if (/\.(download|verified)-\d+$/.test(e.name)) out.push(join(d, e.name));
    }
  };
  walk(dir);
  return out;
}

/** A process id that is not running: a child that has exited. */
async function deadPid() {
  const p = spawn(process.execPath, ["-e", ""]);
  await new Promise((r) => p.on("exit", r));
  return p.pid;
}

test("a download removes temp files a killed download left, but not a running one's", async () => {
  // FAILS if a *.verified-<pid> (116 MB) or *.download-<pid> file of a dead process survives the
  // next download, or a live process's file is removed under it.
  const dir = join(TMP, "user6");
  const dead = await deadPid();
  mkdirSync(join(dir, "pdf-tables"), { recursive: true });
  mkdirSync(join(dir, "pdfs", "source", "FY27"), { recursive: true });
  const leftovers = [
    join(dir, "pdf-tables", `pdf-tables.db.verified-${dead}`),
    join(dir, "pdf-tables", `pdf-tables.db.verified-${dead}.download-${dead}`),
    join(dir, "pdfs", "source", "FY27", `x.pdf.download-${dead}`),
  ];
  const live = join(dir, "pdf-tables", `pdf-tables.db.verified-${process.pid}`);
  for (const f of [...leftovers, live]) writeFileSync(f, "x");
  const r = await cli(["download", "--pdf-tables", "--from", `${base}/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
  assert.equal(r.code, 0, r.out);
  for (const f of leftovers) assert.ok(!existsSync(f), f);
  assert.ok(existsSync(live), "a running process's file is kept");
});

test("one download at a time per folder; a dead downloader's lock is taken over", async () => {
  const dir = join(TMP, "user7");
  mkdirSync(join(dir, "pdf-tables"), { recursive: true });
  writeFileSync(join(dir, "pdf-tables", "download.lock"), String(process.pid));
  const busy = await cli(["download", "--pdf-tables", "--from", `${base}/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
  assert.notEqual(busy.code, 0);
  assert.match(busy.out, new RegExp(`another download into .* is running \\(process ${process.pid}\\)`));
  assert.ok(existsSync(join(dir, "pdf-tables", "download.lock")), "the other process's lock is left alone");
  writeFileSync(join(dir, "pdf-tables", "download.lock"), String(await deadPid()));
  const ok = await cli(["download", "--pdf-tables", "--from", `${base}/pdf-tables.manifest.json`], { NYC_BUDGET_DATA_DIR: dir });
  assert.equal(ok.code, 0, ok.out);
  assert.ok(!existsSync(join(dir, "pdf-tables", "download.lock")), "the lock is released");
});

test("plain http is refused except on this machine", async () => {
  const r = await cli(["download", "--pdf-tables", "--from", "http://example.org/pdf-tables.manifest.json"], { NYC_BUDGET_DATA_DIR: join(TMP, "user8") });
  assert.notEqual(r.code, 0);
  assert.match(r.out, /plain http is refused except on this machine; use https/);
});

test("the CLI refuses a download with no --pdf-tables or --pdfs", async () => {
  const r = await cli(["download"], { NYC_BUDGET_DATA_DIR: join(TMP, "user4") });
  assert.equal(r.code, 2);
  assert.match(r.out, /download --pdf-tables \[--pdfs\]/);
});

test("NYC_BUDGET_PDF_DATA=on downloads on start, in the background", async () => {
  // FAILS if the setting does nothing, or the server waits for the download before answering.
  const dir = join(TMP, "user5");
  const script = `
    import { Client } from "@modelcontextprotocol/sdk/client/index.js";
    import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
    const { server } = await import(${JSON.stringify(join(MCP, "dist", "server.js"))});
    const { maybeAutoDownload, progress } = await import(${JSON.stringify(join(MCP, "dist", "pdfdata.js"))});
    maybeAutoDownload();
    const [ct, st] = InMemoryTransport.createLinkedPair();
    await server.connect(st);
    const client = new Client({ name: "auto", version: "0" }, { capabilities: {} });
    await client.connect(ct);
    const first = await client.callTool({ name: "search_terms_conditions", arguments: { fiscal_year: 2027, limit: 1 } });
    while (progress.state === "downloading") await new Promise((r) => setTimeout(r, 50));
    const second = await client.callTool({ name: "search_terms_conditions", arguments: { fiscal_year: 2027, limit: 1 } });
    process.stdout.write(JSON.stringify([progress.state, first.content[0].text, second.content[0].text]));
    await client.close();
  `;
  const out = await new Promise((resolve) => {
    const p = spawn(process.execPath, ["--input-type=module", "-e", script], {
      cwd: MCP, env: { ...process.env, NYC_BUDGET_DATA_DIR: dir, NYC_BUDGET_PDF_DATA: "on", NYC_BUDGET_PDF_DATA_URL: `${base}/pdf-tables.manifest.json` },
    });
    let s = "";
    p.stdout.on("data", (d) => (s += d));
    p.stderr.on("data", () => {});
    p.on("exit", () => resolve(s));
  });
  const [state, first, second] = JSON.parse(out);
  assert.equal(state, "done");
  assert.match(first, /They are downloading now/);
  assert.match(second, /item 1 \(pages/);
  assert.ok(existsSync(join(dir, "pdf-tables", "pdf-tables.db")));
});

/** Start the server's auto-download once with this env; resolve with the final progress state. */
function autoStart(dir, env) {
  const script = `
    const { maybeAutoDownload, progress } = await import(${JSON.stringify(join(MCP, "dist", "pdfdata.js"))});
    maybeAutoDownload();
    while (progress.state === "downloading") await new Promise((r) => setTimeout(r, 50));
    process.stdout.write(progress.state + (progress.error ? ": " + progress.error : ""));
  `;
  return new Promise((resolve) => {
    const p = spawn(process.execPath, ["--input-type=module", "-e", script], { cwd: MCP, env: { ...process.env, NYC_BUDGET_DATA_DIR: dir, ...env } });
    let s = "";
    p.stdout.on("data", (d) => (s += d));
    p.stderr.on("data", () => {});
    p.on("exit", () => resolve(s));
  });
}

test("NYC_BUDGET_PDF_DATA=pdfs with a release that has no PDFs downloads once, not on every start", async () => {
  // FAILS if each start downloads the tables again because the release carries no PDFs.
  const noPdfs = join(SERVE, "no-pdfs");
  makeRelease(noPdfs, (m) => ({ ...m, pdfs_included: false, files: m.files.filter((f) => f.kind === "pdf_tables") }));
  const url = `${base}/no-pdfs/pdf-tables.manifest.json`;
  const dir = join(TMP, "user9");
  const env = { NYC_BUDGET_PDF_DATA: "pdfs", NYC_BUDGET_PDF_DATA_URL: url };
  const before = requests.length;
  assert.equal(await autoStart(dir, env), "done");
  const first = requests.length - before;
  assert.ok(first >= 2, "premise: the first start downloaded (manifest and tables)");
  assert.equal(await autoStart(dir, env), "idle", "the second start has nothing to do");
  assert.equal(requests.length - before, first, "no request on the second start");
  // A release WITH PDFs whose files are not all on disk still downloads them.
  const dir2 = join(TMP, "user10");
  assert.equal(await autoStart(dir2, { NYC_BUDGET_PDF_DATA: "on", NYC_BUDGET_PDF_DATA_URL: `${base}/pdf-tables.manifest.json` }), "done");
  assert.equal(await autoStart(dir2, { NYC_BUDGET_PDF_DATA: "pdfs", NYC_BUDGET_PDF_DATA_URL: `${base}/pdf-tables.manifest.json` }), "done", "tables-only install, then pdfs asked: downloads");
  assert.ok(existsSync(join(dir2, "pdfs", "source", "FY27", "Fiscal-2027-Schedule-C-Final-3.pdf")));
  assert.equal(await autoStart(dir2, { NYC_BUDGET_PDF_DATA: "pdfs", NYC_BUDGET_PDF_DATA_URL: `${base}/pdf-tables.manifest.json` }), "idle");
});

test("the newest pdf-tables-* release with a manifest is picked; others are ignored", () => {
  const asset = (tag) => ({ name: "pdf-tables.manifest.json", browser_download_url: `https://github.com/BetaNYC/New-York-City-Budget/releases/download/${tag}/pdf-tables.manifest.json` });
  const releases = [
    { tag_name: "mcp-v2.0.1", published_at: "2026-10-30T00:00:00Z", assets: [] },
    { tag_name: "pdf-tables-2026-10-25", published_at: "2026-10-25T00:00:00Z", draft: true, assets: [asset("pdf-tables-2026-10-25")] },
    { tag_name: "pdf-tables-2026-10-24", published_at: "2026-10-24T00:00:00Z", prerelease: true, assets: [asset("pdf-tables-2026-10-24")] },
    { tag_name: "pdf-tables-2026-10-23", published_at: "2026-10-23T00:00:00Z", assets: [asset("pdf-tables-2026-10-23")] },
    { tag_name: "pdf-tables-2026-10-22", published_at: "2026-10-22T00:00:00Z", assets: [asset("pdf-tables-2026-10-22")] },
    { tag_name: "pdf-tables-2026-10-26", published_at: "2026-10-26T00:00:00Z", assets: [] },
  ];
  assert.equal(pickRelease(releases), asset("pdf-tables-2026-10-23").browser_download_url);
  assert.equal(pickRelease([]), null);
  assert.equal(pickRelease({ message: "rate limited" }), null);
});

test("the release manifest pretest built is well formed", () => {
  const m = parseManifest(readFileSync(join(RELEASE, "pdf-tables.manifest.json"), "utf8"));
  assert.equal(m.format, "nyc-budget-pdf-tables/1");
  assert.match(m.source_commit, /^[0-9a-f]{40}$/);
  assert.equal(m.files[0].sha256, sha256(join(RELEASE, "pdf-tables.db.gz")));
  assert.equal(m.files[0].unpacked.sha256, sha256(join(RELEASE, "pdf-tables.db")));
  assert.equal(m.families.length, 36);
  assert.equal(m.source_commit_scope, "local", "pretest builds with --allow-local-commit");
  assert.ok(requests.every((u) => !/github/.test(u)));
});
