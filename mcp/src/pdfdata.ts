/**
 * The optional PDF-tables download (GitHub #215): where it lives, whether it is installed, and how
 * to fetch it. The npm package ships the spreadsheet index only (data/budget.db); the checked
 * tables read from the Council's PDFs (about 115 MB) and, if asked for, the PDFs themselves come
 * from this repo's GitHub Releases, checked against the sha256 values in the release's manifest
 * (scripts/build-pdf-release.mjs writes one; mcp/README.md documents the format).
 *
 * Two ways to get it, both landing in the same per-user folder (never node_modules):
 *   npx @betanyc/nyc-budget-mcp download --pdf-tables [--pdfs]
 *   NYC_BUDGET_PDF_DATA=on (or =pdfs, tables and PDFs) in the MCP's env: downloaded in the
 *   background on the next start, while the other tools answer as usual.
 *
 * Folder: NYC_BUDGET_DATA_DIR, else the platform's per-user data folder + "nyc-budget-mcp":
 *   <dir>/pdf-tables/pdf-tables.db         the tables (SQLite, read-only once installed)
 *   <dir>/pdf-tables/manifest.json         the manifest it came from, plus where and when
 *   <dir>/pdfs/<repo path>                 the PDFs, at their repo paths (with --pdfs)
 * Every file is downloaded to a temporary name, checked, then renamed into place, so a failed or
 * interrupted download never leaves a half file where the server would read it.
 */
import Database from "better-sqlite3";
import type { Database as DB } from "better-sqlite3";
import { createHash } from "crypto";
import { closeSync, createReadStream, createWriteStream, existsSync, mkdirSync, openSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync, writeSync } from "fs";
import { homedir } from "os";
import { dirname, isAbsolute, join, resolve, sep } from "path";
import { Readable, Transform } from "stream";
import { pipeline } from "stream/promises";
import { fileURLToPath, pathToFileURL } from "url";
import { createGunzip } from "zlib";
import { registerTextFunctions } from "./textmatch.js";
import { REPO } from "./rowlinks.js";

/** The download's format; any other is refused (scripts/build-pdf-release.mjs FORMAT). */
export const PDF_TABLES_FORMAT = "nyc-budget-pdf-tables/1";
export const MANIFEST_NAME = "pdf-tables.manifest.json";
/** Releases whose tag starts with this carry the PDF tables (W7, #216, publishes them). */
export const RELEASE_TAG_PREFIX = "pdf-tables-";
const RELEASES_API = `https://api.github.com/repos/${REPO}/releases?per_page=100`;

/** The tables and columns the four PDF tools read; a download without them is refused. */
export const REQUIRED_COLUMNS: Record<string, string[]> = {
  pdf_years: ["fiscal_year", "family", "status", "rows"],
  pdf_schedule_c: ["fiscal_year", "status", "award_id", "org", "ein", "amount", "amount_printed", "member", "sponsor", "category",
    "initiative", "agency", "purpose", "disclosure_status", "program_or_subheading", "review_not_completed", "fiscal_conduit",
    "fiscal_conduit_ein", "read_from_page_image", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"],
  pdf_schedule_c_subawards: ["fiscal_year", "parent_award_id", "org", "ein", "amount", "service_type"],
  pdf_transparency: ["fiscal_year", "status", "row_id", "resolution_number", "resolution_date", "budget_fiscal_year", "action",
    "chart_title", "member", "org", "ein", "agency", "amount", "amount_printed", "amount_kind", "purpose", "hidden_text",
    "fiscal_conduit", "read_from_page_image", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"],
  pdf_capital_sd: ["fiscal_year", "status", "part", "agency", "sub_id", "budget_line", "boro", "title", "sponsor",
    "amount_y1", "amount_y2", "amount_y3", "amount_y4", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"],
  pdf_terms: ["fiscal_year", "status", "item_number", "agency_name", "agency_code", "units_of_appropriation", "condition_text",
    "heading_raw", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"],
  pdf_terms_units: ["fiscal_year", "item_number", "unit_of_appropriation", "budget_line"],
  pdf_review: ["fiscal_year", "family", "review_id", "check_id", "severity", "note", "detail", "decision", "decision_note"],
  meta: ["key", "value"],
};

/** The per-user folder the download lives in. */
export function dataDir(): string {
  const env = process.env.NYC_BUDGET_DATA_DIR;
  if (env && env.trim() !== "") return resolve(env.trim());
  const home = homedir();
  if (process.platform === "darwin") return join(home, "Library", "Application Support", "nyc-budget-mcp");
  if (process.platform === "win32") return join(process.env.LOCALAPPDATA || join(home, "AppData", "Local"), "nyc-budget-mcp");
  return join(process.env.XDG_DATA_HOME || join(home, ".local", "share"), "nyc-budget-mcp");
}

export const tablesPath = () => join(dataDir(), "pdf-tables", "pdf-tables.db");
export const installedManifestPath = () => join(dataDir(), "pdf-tables", "manifest.json");
/** Where a downloaded PDF sits, by its repo path ("source/FY27/…pdf"); null for any other path. */
export function localPdfPath(repoPath: string): string | null {
  if (!/^source\/.+\.pdf$/i.test(repoPath) || repoPath.split("/").includes("..")) return null;
  return join(dataDir(), "pdfs", ...repoPath.split("/"));
}

// ---------------------------------------------------------------- the installed tables

export interface PdfTables {
  db: DB;
  path: string;
  meta: Record<string, string>;
}

let opened: (PdfTables & { stamp: string }) | null = null;
let openedFailure: { path: string; error: string; stamp: string } | null = null;

/** Which file is at `path` now: a download renames a new file into place, so this changes. */
function fileStamp(path: string): string {
  try {
    const st = statSync(path);
    return `${st.ino}:${st.size}:${st.mtimeMs}`;
  } catch {
    return "";
  }
}

/** Why an installed file cannot be used, or null. */
function checkTables(db: DB): string | null {
  for (const [t, cols] of Object.entries(REQUIRED_COLUMNS)) {
    const have = new Set((db.prepare(`PRAGMA table_info(${t})`).all() as { name: string }[]).map((c) => c.name));
    if (!have.size) return `it has no table ${t}`;
    const missing = cols.filter((c) => !have.has(c));
    if (missing.length) return `table ${t} lacks ${missing.join(", ")}`;
  }
  const format = (db.prepare("SELECT value FROM meta WHERE key = 'pdf_tables_format'").get() as { value: string } | undefined)?.value;
  if (format !== PDF_TABLES_FORMAT) return `its format is ${JSON.stringify(format ?? "")}, and this version of the server reads ${PDF_TABLES_FORMAT}`;
  return null;
}

/**
 * The installed PDF tables, opened read-only, or null with the reason (absent, or unusable). The
 * connection carries fold() and word_match() as SQL functions (src/textmatch.ts), so text filters
 * fold both sides with the same rule as every other tool (src/fold.ts), and whole-word matching
 * (#259) stays in SQL.
 */
export function openPdfTables(): { tables: PdfTables | null; problem: string | null } {
  const path = tablesPath();
  // Re-checked on every call, so an install by `download` in another process is picked up
  // without a restart, and a failure is not remembered after the file is replaced.
  const stamp = fileStamp(path);
  if (opened && (opened.path !== path || opened.stamp !== stamp)) closePdfTables();
  if (openedFailure && (openedFailure.path !== path || openedFailure.stamp !== stamp)) openedFailure = null;
  if (opened) return { tables: opened, problem: null };
  if (openedFailure) return { tables: null, problem: openedFailure.error };
  if (!stamp) return { tables: null, problem: null };
  try {
    const db = new Database(path, { readonly: true, fileMustExist: true });
    const bad = checkTables(db);
    if (bad) {
      db.close();
      openedFailure = { path, stamp, error: `The PDF tables at ${path} cannot be used: ${bad}. Download them again (see below).` };
      return { tables: null, problem: openedFailure.error };
    }
    registerTextFunctions(db);
    const meta = Object.fromEntries((db.prepare("SELECT key, value FROM meta").all() as { key: string; value: string }[]).map((r) => [r.key, r.value]));
    opened = { db, path, meta, stamp };
    return { tables: opened, problem: null };
  } catch (err) {
    openedFailure = { path, stamp, error: `The PDF tables at ${path} cannot be opened: ${err instanceof Error ? err.message : String(err)}.` };
    return { tables: null, problem: openedFailure.error };
  }
}

/** Forget the open file (after a download replaces it). */
export function closePdfTables(): void {
  opened?.db.close();
  opened = null;
  openedFailure = null;
}

// ---------------------------------------------------------------- the manifest

export interface ManifestFile {
  name: string;
  kind: "pdf_tables" | "pdf";
  bytes: number;
  sha256: string;
  /** pdf_tables: the gunzipped file's own size and sha256. */
  unpacked?: { name: string; bytes: number; sha256: string };
  /** pdf: its repo path. */
  path?: string;
}

export interface Manifest {
  format: string;
  built_at: string;
  source_commit: string;
  source_commit_check?: string;
  families: { fiscal_year: number; family: string; status: string; rows: number }[];
  pdfs_included: boolean;
  files: ManifestFile[];
}

const SHA = /^[0-9a-f]{64}$/;

/** The manifest, checked for shape, or an Error that says what is wrong. */
export function parseManifest(text: string): Manifest {
  let m: Manifest;
  try {
    m = JSON.parse(text) as Manifest;
  } catch {
    throw new Error("the manifest is not JSON");
  }
  if (m?.format !== PDF_TABLES_FORMAT) throw new Error(`the manifest's format is ${JSON.stringify(m?.format)}; this version reads ${PDF_TABLES_FORMAT}`);
  if (!Array.isArray(m.files)) throw new Error("the manifest lists no files");
  for (const f of m.files) {
    if (typeof f.name !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(f.name)) throw new Error(`the manifest names a file ${JSON.stringify(f.name)}, which is not a plain file name`);
    if (!SHA.test(f.sha256 ?? "") || !Number.isSafeInteger(f.bytes) || f.bytes < 0) throw new Error(`${f.name}: no valid sha256 and size in the manifest`);
    if (f.kind === "pdf_tables" && (!f.unpacked || !SHA.test(f.unpacked.sha256 ?? "") || !Number.isSafeInteger(f.unpacked.bytes))) throw new Error(`${f.name}: no unpacked sha256 and size`);
    if (f.kind === "pdf" && (typeof f.path !== "string" || localPdfPath(f.path) === null)) throw new Error(`${f.name}: its path ${JSON.stringify(f.path)} is not a source PDF path`);
    if (f.kind !== "pdf_tables" && f.kind !== "pdf") throw new Error(`${f.name}: unknown kind ${JSON.stringify(f.kind)}`);
  }
  if (m.files.filter((f) => f.kind === "pdf_tables").length !== 1) throw new Error("the manifest must list exactly one pdf_tables file");
  return m;
}

/**
 * The newest published release whose tag starts with RELEASE_TAG_PREFIX and that carries a
 * manifest: its manifest's download URL, or null. `releases` is GitHub's list-releases JSON.
 */
export function pickRelease(releases: unknown): string | null {
  if (!Array.isArray(releases)) return null;
  const ok = releases
    .filter((r) => r && !r.draft && !r.prerelease && typeof r.tag_name === "string" && r.tag_name.startsWith(RELEASE_TAG_PREFIX))
    .map((r) => ({ at: String(r.published_at ?? ""), asset: (r.assets ?? []).find((a: { name?: string }) => a?.name === MANIFEST_NAME) }))
    .filter((r) => r.asset?.browser_download_url)
    .sort((a, b) => (a.at < b.at ? 1 : a.at > b.at ? -1 : 0));
  return ok.length ? String(ok[0].asset.browser_download_url) : null;
}

// ---------------------------------------------------------------- fetching

/** A manifest location as a URL: http(s), file:, or a local path. */
function asUrl(loc: string): URL {
  const u = /^(https?|file):/i.test(loc) ? new URL(loc) : pathToFileURL(isAbsolute(loc) ? loc : resolve(loc));
  // Plain http only on this machine (a local test server); anything else must be https or a file.
  if (u.protocol === "http:" && !LOCAL_HOSTS.has(u.hostname)) throw new Error(`${u.href}: plain http is refused except on this machine; use https`);
  return u;
}

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]", "::1"]);

async function fetchStream(url: URL): Promise<Readable> {
  if (url.protocol === "file:") {
    const p = fileURLToPath(url);
    if (!existsSync(p)) throw new Error(`${p} does not exist`);
    return createReadStream(p);
  }
  const res = await fetch(url, { headers: { "user-agent": "nyc-budget-mcp", accept: "application/octet-stream, application/json" }, redirect: "follow" });
  if (!res.ok || !res.body) throw new Error(`${url.href}: HTTP ${res.status}`);
  return Readable.fromWeb(res.body as import("stream/web").ReadableStream);
}

/** A manifest, or GitHub's release list: small JSON. Anything past `max` bytes is refused. */
const MAX_TEXT_BYTES = 8 << 20;
async function fetchText(url: URL, max = MAX_TEXT_BYTES): Promise<string> {
  const chunks: Buffer[] = [];
  let n = 0;
  for await (const c of await fetchStream(url)) {
    n += c.length;
    if (n > max) throw new Error(`${url.href}: more than ${max} bytes; not a manifest`);
    chunks.push(Buffer.from(c));
  }
  return Buffer.concat(chunks).toString("utf8");
}

/** Counts bytes and hashes them as they pass; stops the download once more than `max` bytes come. */
function meter(onBytes: (n: number) => void, max: number, what: string): Transform & { digest: () => string; bytes: () => number } {
  const h = createHash("sha256");
  let n = 0;
  const t = new Transform({
    transform(chunk, _enc, cb) {
      n += chunk.length;
      if (n > max) return cb(new Error(`${what}: more than the manifest's ${max} bytes; stopped`));
      h.update(chunk);
      onBytes(chunk.length);
      cb(null, chunk);
    },
  }) as Transform & { digest: () => string; bytes: () => number };
  t.digest = () => h.digest("hex");
  t.bytes = () => n;
  return t;
}

export interface DownloadOptions {
  /** Manifest URL or path; default NYC_BUDGET_PDF_DATA_URL, else the newest pdf-tables-* release. */
  from?: string;
  pdfs?: boolean;
  /** Progress lines (to stderr; stdout is the MCP's channel). */
  log?: (line: string) => void;
}

export interface DownloadProgress {
  state: "idle" | "downloading" | "done" | "failed";
  started?: string;
  bytes: number;
  total: number;
  error?: string;
}

export const progress: DownloadProgress = { state: "idle", bytes: 0, total: 0 };

/** Where the manifest is: the option, the env, or the newest release (GitHub's API). */
async function manifestLocation(from?: string): Promise<string> {
  const loc = from ?? process.env.NYC_BUDGET_PDF_DATA_URL;
  if (loc && loc.trim() !== "") return loc.trim();
  const text = await fetchText(new URL(RELEASES_API));
  const url = pickRelease(JSON.parse(text));
  if (!url) throw new Error(`no release of ${REPO} carries the PDF tables yet (a release tagged ${RELEASE_TAG_PREFIX}… with ${MANIFEST_NAME}). Try again later, or set NYC_BUDGET_PDF_DATA_URL to a manifest.`);
  return url;
}

/** Download one manifest file next to `dest`, check size and sha256 (and the unpacked ones), rename. */
async function fetchVerified(base: URL, f: ManifestFile, dest: string): Promise<void> {
  mkdirSync(dirname(dest), { recursive: true });
  const tmp = `${dest}.download-${process.pid}`;
  rmSync(tmp, { force: true });
  try {
    const packed = meter((n) => (progress.bytes += n), f.bytes, f.name);
    const stages: NodeJS.ReadWriteStream[] = [packed];
    const unpacked = f.unpacked ? meter(() => {}, f.unpacked.bytes, `${f.name} unpacked`) : null;
    if (unpacked) stages.push(createGunzip(), unpacked);
    await pipeline(await fetchStream(new URL(f.name, base)), ...(stages as [Transform]), createWriteStream(tmp));
    if (packed.bytes() !== f.bytes || packed.digest() !== f.sha256) throw new Error(`${f.name}: the download does not match the manifest's size and sha256`);
    if (unpacked && (unpacked.bytes() !== f.unpacked!.bytes || unpacked.digest() !== f.unpacked!.sha256)) throw new Error(`${f.name}: the unpacked file does not match the manifest's size and sha256`);
    renameSync(tmp, dest);
  } catch (err) {
    rmSync(tmp, { force: true });
    throw err;
  }
}

/**
 * Download the PDF tables (and with `pdfs`, the PDFs), verify every file against the manifest's
 * sha256, and install them. Returns the installed manifest. A failure leaves what was installed
 * before in place.
 */
export async function downloadPdfData(opts: DownloadOptions = {}): Promise<Manifest> {
  const log = opts.log ?? ((l: string) => process.stderr.write(l + "\n"));
  Object.assign(progress, { state: "downloading", started: new Date().toISOString(), bytes: 0, total: 0, error: undefined });
  let unlock: (() => void) | null = null;
  const stage = `${tablesPath()}.verified-${process.pid}`;
  try {
    mkdirSync(dirname(tablesPath()), { recursive: true });
    unlock = takeLock();
    sweepStale();
    const loc = await manifestLocation(opts.from);
    const url = asUrl(loc);
    log(`Manifest: ${url.href}`);
    const m = parseManifest(await fetchText(url));
    const want = m.files.filter((f) => f.kind === "pdf_tables" || (opts.pdfs && f.kind === "pdf"));
    if (opts.pdfs && !m.pdfs_included) log("This release does not include the PDF files; downloading the tables only.");
    progress.total = want.reduce((t, f) => t + f.bytes, 0);
    log(`Downloading ${want.length} file(s), ${(progress.total / 1e6).toFixed(1)} MB, built ${m.built_at} from commit ${m.source_commit || "(none recorded)"}.`);
    const tables = want.find((f) => f.kind === "pdf_tables")!;
    await fetchVerified(url, tables, stage);
    // The file must also open and carry what the tools read before it replaces anything.
    const check = new Database(stage, { readonly: true });
    const bad = checkTables(check);
    const commit = (check.prepare("SELECT value FROM meta WHERE key = 'source_commit'").get() as { value: string } | undefined)?.value ?? "";
    check.close();
    if (bad) throw new Error(`the downloaded tables cannot be used: ${bad}`);
    if (commit !== (m.source_commit ?? "")) throw new Error(`the downloaded tables were built from commit ${JSON.stringify(commit)}, the manifest says ${JSON.stringify(m.source_commit)}`);
    for (const f of want.filter((f) => f.kind === "pdf")) {
      const dest = localPdfPath(f.path!)!;
      if (!dest.startsWith(join(dataDir(), "pdfs") + sep)) throw new Error(`${f.path}: outside the data folder`);
      await fetchVerified(url, f, dest);
    }
    closePdfTables();
    try {
      renameSync(stage, tablesPath());
    } catch (err) {
      // Windows refuses to replace a file another server has open (EPERM). If what is installed
      // is already this release, the job is done; otherwise say what to do.
      if (!installedIs(m)) throw new Error(`the new tables could not replace ${tablesPath()} (${err instanceof Error ? err.message : String(err)}); another nyc-budget-mcp may have it open. Stop it and run the download again.`);
      log("The tables installed are already this release.");
    }
    writeFileSync(installedManifestPath(), JSON.stringify({ ...m, pdfs_requested: !!opts.pdfs, installed_from: url.href, installed_at: new Date().toISOString() }, null, 2) + "\n");
    progress.state = "done";
    log(`Installed: ${tablesPath()}`);
    return m;
  } catch (err) {
    progress.state = "failed";
    progress.error = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    // A staged file is never left behind, whatever failed (it is 116 MB).
    rmSync(stage, { force: true });
    unlock?.();
  }
}

/** Whether the installed tables were built from the same commit as this manifest's. */
function installedIs(m: Manifest): boolean {
  try {
    const db = new Database(tablesPath(), { readonly: true, fileMustExist: true });
    try {
      const commit = (db.prepare("SELECT value FROM meta WHERE key = 'source_commit'").get() as { value: string } | undefined)?.value;
      const built = (db.prepare("SELECT value FROM meta WHERE key = 'built_at'").get() as { value: string } | undefined)?.value;
      return checkTables(db) === null && commit === m.source_commit && built === m.built_at;
    } finally {
      db.close();
    }
  } catch {
    return false;
  }
}

/** Whether a process with this id is running (signal 0 only checks). */
function alive(pid: number): boolean {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  if (pid === process.pid) return true;
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return (err as NodeJS.ErrnoException).code === "EPERM";
  }
}

export const lockPath = () => join(dataDir(), "pdf-tables", "download.lock");

/**
 * One download at a time per data folder: a lock file holding the downloader's pid, taken with
 * O_EXCL. A lock whose process is gone (killed mid-download) is taken over.
 */
function takeLock(): () => void {
  const path = lockPath();
  const takeover = `${path}.takeover`;
  const tryCreate = (p: string) => {
    try {
      const fd = openSync(p, "wx");
      writeSync(fd, String(process.pid));
      closeSync(fd);
      return true;
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code === "EEXIST") return false;
      throw err;
    }
  };
  const owner = (p: string) => {
    try {
      return Number(readFileSync(p, "utf8").trim());
    } catch {
      return NaN;
    }
  };
  const busy = (pid: number) => new Error(`another download into ${dataDir()} is running (process ${pid}); wait for it to finish`);
  if (tryCreate(path)) return () => rmSync(path, { force: true });
  const pid = owner(path);
  if (alive(pid)) throw busy(pid);
  // The lock's process is gone. Only one process may take it over: whoever creates the takeover
  // file (O_EXCL) replaces the lock; any other sees a download in progress. A takeover file left by
  // a killed process is itself cleared by pid.
  if (!tryCreate(takeover)) {
    const t = owner(takeover);
    if (alive(t)) throw busy(t);
    rmSync(takeover, { force: true });
    if (!tryCreate(takeover)) throw busy(owner(takeover));
  }
  try {
    // Re-read under the takeover: the lock may have been replaced by a live process meanwhile.
    const now = owner(path);
    if (alive(now)) throw busy(now);
    rmSync(path, { force: true });
    if (!tryCreate(path)) throw busy(owner(path));
    return () => rmSync(path, { force: true });
  } finally {
    rmSync(takeover, { force: true });
  }
}

const STALE = /\.(download|verified)-(\d+)$/;

/** Remove temporary files a killed download left (`*.download-<pid>`, `*.verified-<pid>`), when that process is gone. */
export function sweepStale(): string[] {
  const removed: string[] = [];
  const walk = (dir: string) => {
    let entries: import("fs").Dirent[];
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const p = join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else {
        const m = STALE.exec(e.name);
        if (m && !alive(Number(m[2]))) {
          rmSync(p, { force: true });
          removed.push(p);
        }
      }
    }
  };
  walk(join(dataDir(), "pdf-tables"));
  walk(join(dataDir(), "pdfs"));
  return removed;
}

/** The installed manifest, if any. */
export function installedManifest(): (Manifest & { pdfs_requested?: boolean; installed_from?: string; installed_at?: string }) | null {
  try {
    return JSON.parse(readFileSync(installedManifestPath(), "utf8"));
  } catch {
    return null;
  }
}

/**
 * NYC_BUDGET_PDF_DATA: "on" or "tables" downloads the tables on start when they are absent;
 * "pdfs" also the PDFs. Anything else (unset, "off") does nothing.
 */
export function autoDownloadSetting(): { tables: boolean; pdfs: boolean } {
  const v = (process.env.NYC_BUDGET_PDF_DATA ?? "").trim().toLowerCase();
  if (v === "pdfs") return { tables: true, pdfs: true };
  return { tables: v === "on" || v === "tables" || v === "yes" || v === "1" || v === "true", pdfs: false };
}

/**
 * Whether NYC_BUDGET_PDF_DATA=pdfs still has PDFs to fetch. Satisfied when the installed release
 * carries no PDFs and was installed asking for them (nothing more to get; a restart must not
 * download again), or when every PDF its manifest lists is on disk.
 */
export function pdfsMissing(): boolean {
  const m = installedManifest();
  if (!m) return true;
  if (!m.pdfs_included) return !m.pdfs_requested;
  return m.files.filter((f) => f.kind === "pdf").some((f) => !existsSync(localPdfPath(f.path!) ?? ""));
}

/** Start the background download the setting asks for, once per process, if it is needed. */
export function maybeAutoDownload(): void {
  try {
    sweepStale();
  } catch {
    // A folder this process cannot read is reported by the download itself, if one runs.
  }
  const s = autoDownloadSetting();
  if (!s.tables || progress.state !== "idle") return;
  if (existsSync(tablesPath()) && !(s.pdfs && pdfsMissing())) return;
  downloadPdfData({ pdfs: s.pdfs }).catch((err) => process.stderr.write(`nyc-budget-mcp: the PDF tables download failed: ${err instanceof Error ? err.message : String(err)}\n`));
}

/** How to add the PDF tables, for an answer that needs them. */
export function howToAdd(): string {
  return [
    "To add them (about 17 MB to download, 115 MB on disk; checked against the sha256 values this repo publishes), either:",
    "  • run once in a terminal: npx @betanyc/nyc-budget-mcp download --pdf-tables   (add --pdfs for the PDF files too)",
    '  • or set NYC_BUDGET_PDF_DATA=on in this MCP server\'s "env" settings and restart it: it downloads them in the background on the next start.',
    `They are saved in ${dataDir()} (set NYC_BUDGET_DATA_DIR to choose another folder), not in the npm package.`,
  ].join("\n");
}
