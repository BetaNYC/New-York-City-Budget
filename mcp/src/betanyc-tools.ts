// betanyc-shared: betanyc-tools.ts v1.5.0
// betanyc-shared-sha256: 7c16016c691086bd4b8d43cc1b9d7b04ee49161d79a31215d6dd984cb23084f4
// Canonical copy: betanyc-ai-workspace scripts/mcp_shared/betanyc-tools.ts. Do not edit a copy
// in a server repo; change the canonical file, re-stamp it, and copy it again.
// Drift check: scripts/whats_changed_drift.py. Standard: platform/system/whats-changed-standard.md.
//
// The three tools BetaNYC is adding to each of its MCP servers (the standards require all three),
// with identical names, inputs and output:
//   whats_changed   query this server's WHATS-CHANGED.md
//   about_betanyc   who built this server and how to reach BetaNYC
//   about_data      where this server's data comes from, from its DATA-SOURCES.json
//                   (standard: platform/system/about-data-standard.md)
// From 1.5.0, helpers for a server's OWN tools, so all servers do these the same way:
//   readOnlyAnnotations, annotateTools, assertEveryToolAnnotated   tool annotations
//   provenance        the source, publisher, link and as-of line for one answer
//   toolError         an isError result: plain sentence, cut upstream body, secrets redacted
//   toolListSize      characters in tools/list plus instructions, for a size-budget test
//
// Dependency-free: only node:fs and node:url. Uses no TypeScript syntax that needs transforming (no enums,
// namespaces or parameter properties), so Node 22.18+ runs it directly by type stripping and
// tsc compiles it in a server repo unchanged.
//
// MCP contract followed (spec 2025-11-25, as shipped in @modelcontextprotocol/sdk 1.32.2
// types.js): a tool may declare `outputSchema` (root `type: "object"`); when it does, a
// successful result MUST carry `structuredContent` matching it. Clients skip that check when
// `isError` is true. `annotations` uses ToolAnnotations (title, readOnlyHint, openWorldHint;
// checked 2026-11-18 against the spec's schema/2025-11-25/schema.ts and SDK 1.32.2 types.js).

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

export const SHARED_MODULE_VERSION = "1.5.0";

// --------------------------------------------------------------------------- types

export type Tag = "Site" | "Data" | "MCP" | "Correction";
export const TAGS: readonly Tag[] = ["Site", "Data", "MCP", "Correction"];
const SUBJECT_TAGS: readonly Tag[] = ["Site", "Data", "MCP"];

export interface EntryLink {
  text: string;
  url: string;
}

export interface EntryUpdate {
  date: string;
  text: string;
}

/** One entry, as parsed. Same keys and values as `whats_changed.py json`. */
export interface Entry {
  /** YYYY-MM-DD, or null for the one "## Unreleased: Title" entry waiting for its release date. */
  date: string | null;
  /** True for the "## Unreleased:" entry. The whats_changed tool never returns it. */
  unreleased: boolean;
  title: string;
  anchor: string;
  tags: Tag[];
  summary: string | null;
  if_you_used_the_old_numbers: string | null;
  who_it_affects: string | null;
  mcp_version: string | null;
  notice_on: string[];
  more_detail: string | null;
  updates: EntryUpdate[];
  links: EntryLink[];
  line: number;
  /** False when any error falls inside this entry. Invalid entries are never shown. */
  valid: boolean;
}

export interface ParseError {
  code: string;
  line: number;
}

export interface ParsedFile {
  title: string;
  history_begins: string | null;
  data_refresh: string | null;
  intro: string;
  entries: Entry[];
  errors: ParseError[];
}

export type TextContent = {
  type: "text";
  text: string;
};

/** A CallToolResult. A type alias with an index signature, not an interface, so it is
 * assignable to the SDK's own result type (which is a loose object) in a server's handler. */
export type ToolResult = {
  [key: string]: unknown;
  content: TextContent[];
  structuredContent?: Record<string, unknown>;
  isError?: boolean;
};

/** A tool's input or output JSON Schema, typed to match the MCP SDK's `Tool` type
 * (`@modelcontextprotocol/sdk` 1.29 to 1.32, `types.d.ts` ToolSchema): a literal `type: "object"`,
 * optional `properties` and `required`, and any other keys. So these definitions can go into a
 * server's `Tool[]` with no cast and without this file importing the SDK. */
export type ObjectJsonSchema = {
  type: "object";
  properties?: Record<string, object>;
  required?: string[];
  [key: string]: unknown;
};

/** ToolAnnotations as the SDK declares them (all optional). */
export type ToolAnnotations = {
  title?: string;
  readOnlyHint?: boolean;
  destructiveHint?: boolean;
  idempotentHint?: boolean;
  openWorldHint?: boolean;
};

export interface ToolDefinition {
  name: string;
  title: string;
  description: string;
  inputSchema: ObjectJsonSchema;
  outputSchema: ObjectJsonSchema;
  annotations: ToolAnnotations;
}

/** Return this from a freshness hook when the server downloads its data on demand and has not
 * fetched it yet on this machine. */
export const FRESHNESS_NOT_FETCHED: { readonly notFetched: true } = Object.freeze({ notFetched: true as const });
export type FreshnessValue = string | null | undefined | { readonly notFetched: true };
export type FreshnessHook = () => FreshnessValue | Promise<FreshnessValue>;

export interface BetanycServerConfig {
  /** The server's name, as in `new Server({ name })`, e.g. "nyc-charter-laws-rules". */
  serverName: string;
  /** The package version the server reports. */
  version: string;
  /** https://github.com/BetaNYC/<repo>, no trailing slash needed. */
  repoUrl: string;
  /** Where WHATS-CHANGED.md is at run time, e.g. new URL("../WHATS-CHANGED.md", import.meta.url). */
  whatsChangedPath?: string | URL;
  /** The file's text, when the build embeds it instead of shipping the file. Wins over the path. */
  whatsChangedText?: string;
  /** The site's "What's changed" page, when there is one. Entry links point there. */
  pageUrl?: string;
  /** Map repo-relative links under `prefix` (e.g. "viz/") to `url` (the published site). */
  siteBase?: { prefix: string; url: string };
  /** Where DATA-SOURCES.json is at run time, e.g. new URL("../DATA-SOURCES.json", import.meta.url). */
  dataSourcesPath?: string | URL;
  /** The file's text, when the build embeds it instead of shipping the file. Wins over the path. */
  dataSourcesText?: string;
  /** Folder that freshness `file` paths are relative to (default: the folder holding DATA-SOURCES.json). */
  dataRoot?: string | URL;
  /** Freshness hooks, by the `key` a source's `freshness` (kind "hook" or "copied") names. Each
   * returns, or resolves to, a date or date-time read from something real (an index, a saved
   * download, a constant written beside copied text); FRESHNESS_NOT_FETCHED when nothing has
   * been downloaded on this machine yet; or null when the data is there but has no readable date.
   * An async hook needs `callAsync` (or handleAboutDataAsync); the sync `call` reports it as
   * unavailable. */
  freshness?: Record<string, FreshnessHook>;
  /** Where the generated catalogs are published, when they are. about_data links to them. */
  catalogUrls?: { dataJson?: string; croissantJson?: string };
  /** callAsync's wait per freshness hook, in milliseconds (default ABOUT_DATA_HOOK_TIMEOUT_MS, 3000). */
  hookTimeoutMs?: number;
  /** Sources this running server cannot reach, by source id, each with a plain reason, for
   * example { live: "the live Legistar API is not set up (no LEGISTAR_TOKEN)" }. about_data then
   * reports that source's as_of as "not available on this server: <reason>" (as_of_status
   * "unavailable") instead of its freshness. Optional; set it at startup. An unknown id or an
   * empty reason throws in createBetanycTools. Added in 1.3.6. */
  unavailableSources?: Record<string, string>;
}

// --------------------------------------------------------------------------- parsing

const FIELDS: Record<string, keyof Entry> = {
  "Tags": "tags",
  "What changed": "summary",
  "If you used the old numbers": "if_you_used_the_old_numbers",
  "Who it affects": "who_it_affects",
  "MCP version": "mcp_version",
  "Notice on": "notice_on",
  "More detail": "more_detail",
};
const PREAMBLE_FIELDS: Record<string, "history_begins" | "data_refresh"> = {
  "History begins": "history_begins",
  "Data refresh": "data_refresh",
};

const DATE_RE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
const MIN_YEAR = 1990;
const H1_RE = /^# (.+?)[ \t]*$/s; // s: "." matches U+2028/2029, as Python's "." does
const H2_RE = /^## (.*?)[ \t]*$/s;
const DEEPER_RE = /^#{3,} /;
const ENTRY_HEADING_RE = /^([0-9]{4}-[0-9]{2}-[0-9]{2}): ([^ \t].*)$/s;
// A version bump merges before its tag, so the newest entry may wait for its release date.
const UNRELEASED_HEADING_RE = /^Unreleased: ([^ \t].*)$/s;
const FIELD_RE = /^- \*\*(.+?):\*\*(?: (.*))?$/s;
const UPDATE_LABEL_RE = /^Update ([^ \t]+)$/;
const CONT_RE = /^ {2,}[^ \t]/;
// Link text may not contain brackets: that keeps matching linear on lines full of "[".
const LINK_RE = /\[([^\[\]]+)\]\(([^() \t]+)\)/g;
// An optional "v" before the version ("v0.4.5") is allowed; it is not part of the version.
const SEMVER_RE = /(?<![0-9A-Za-z.])v?([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]*[0-9A-Za-z])?)(?![0-9A-Za-z])/;
// Characters GitHub treats as markup or entities in a heading, so its anchor would not match ours.
const TITLE_MARKUP_RE = /[*`\[\]<>&_~#\\]/;
const FENCE_RE = /^(```|~~~)/;
const HISTORY_RE = /^([0-9]{4}-[0-9]{2}-[0-9]{2})(?![0-9-])/;
const SCHEME_RE = /^([A-Za-z][A-Za-z0-9+.-]*):/;
const SAFE_SCHEMES = ["http", "https", "mailto"];
const CONTROL_RE = /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]/; // C0, DEL, C1, line/para separators
const PLACEHOLDER_RE = /SITE OR SERVER NAME|HOW OFTEN THE DATA UPDATES|BetaNYC\/REPO(?![A-Za-z0-9_-])/;
const EXAMPLE_TITLE_RE = /^example:/i;
/** The one whitespace set both parsers trim (space, tab, no-break space, BOM). */
const TRIM_CHARS = " \t\u00a0\ufeff";
export const MAX_CHARS = 1_000_000;
export const MAX_LINE = 5_000;
/** File-level problems: they do not make the entry they sit beside invalid. */
const FILE_LEVEL_CODES = [
  "unterminated-comment", "unterminated-fence", "no-h1", "missing-history-begins", "bad-history-begins",
  "history-after-entry", "file-too-large",
];

function trim(s: string): string {
  let a = 0;
  let b = s.length;
  while (a < b && TRIM_CHARS.includes(s[a])) a++;
  while (b > a && TRIM_CHARS.includes(s[b - 1])) b--;
  return s.slice(a, b);
}

function rtrim(s: string): string {
  let b = s.length;
  while (b > 0 && TRIM_CHARS.includes(s[b - 1])) b--;
  return s.slice(0, b);
}

function ltrim(s: string): string {
  let a = 0;
  while (a < s.length && TRIM_CHARS.includes(s[a])) a++;
  return s.slice(a);
}

/** The anchor GitHub gives a heading (docs.github.com, "Section links"): lowercase, spaces
 * become hyphens, other punctuation and whitespace removed. Letters, marks, numbers,
 * underscores (connector punctuation) and hyphens are kept. */
export function githubSlug(text: string): string {
  return trim(text).toLowerCase().replace(/[^\p{L}\p{M}\p{N}\p{Pc} -]/gu, "").replace(/ /g, "-");
}

/** YYYY-MM-DD in ASCII digits, a real calendar day, year 1990 or later. */
export function isRealDate(s: string): boolean {
  if (!DATE_RE.test(s)) return false;
  const [y, m, d] = s.split("-").map(Number);
  if (y < MIN_YEAR) return false;
  const t = new Date(0);
  t.setUTCFullYear(y, m - 1, d); // setUTCFullYear, unlike Date.UTC, never maps years 0-99 to 1900s
  return t.getUTCFullYear() === y && t.getUTCMonth() === m - 1 && t.getUTCDate() === d;
}

/** Only http, https, mailto, relative paths and #fragments. Never javascript:, data:, or //host. */
export function isSafeUrl(url: string): boolean {
  if (url.startsWith("#")) return true;
  if (url.startsWith("//")) return false;
  const m = SCHEME_RE.exec(url);
  return m === null || SAFE_SCHEMES.includes(m[1].toLowerCase());
}

function localToday(): string {
  const now = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`;
}

function extractLinks(values: string[]): EntryLink[] {
  const links: EntryLink[] = [];
  const seen = new Set<string>();
  for (const value of values) {
    for (const m of value.matchAll(LINK_RE)) {
      const url = m[2];
      if (seen.has(url) || !isSafeUrl(url)) continue;
      seen.add(url);
      links.push({ text: m[1], url });
    }
  }
  return links;
}

function hasUnsafeLink(value: string): boolean {
  for (const m of value.matchAll(LINK_RE)) if (!isSafeUrl(m[2])) return true;
  return false;
}

function splitList(value: string): string[] {
  return value.split(",").map(trim).filter((t) => t.length > 0);
}

interface Working extends Entry {
  _seen: Set<string>;
  _rawTags: [string, number] | null;
  _fieldLines: Record<string, number>;
  _updateLines: number[];
}

/** Parse WHATS-CHANGED.md. Never throws on bad input: problems come back in `errors`, and each
 * entry says whether it is `valid` (no error inside it). `today` (YYYY-MM-DD) is used for the
 * future-date checks; default is the local date. */
export function parseWhatsChanged(input: string, today?: string): ParsedFile {
  const day = today ?? localToday();
  if (input.length > MAX_CHARS) {
    return { title: "", history_begins: null, data_refresh: null, intro: "", entries: [], errors: [{ code: "file-too-large", line: 1 }] };
  }
  const text = input.startsWith("\ufeff") ? input.slice(1) : input;
  const lines = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
  const errors: ParseError[] = [];
  const err = (code: string, line: number) => errors.push({ code, line });
  const checkPlaceholders = (value: string, lineno: number) => {
    if (PLACEHOLDER_RE.test(value)) err("template-placeholder", lineno);
  };

  let i = 0;
  if (lines.length && trim(lines[0]) === "---") {
    for (let j = 1; j < lines.length; j++) {
      if (trim(lines[j]) === "---") {
        i = j + 1;
        break;
      }
    }
  }

  let title: string | null = null;
  const intro: string[] = [];
  const preamble: { history_begins: string | null; data_refresh: string | null } = {
    history_begins: null,
    data_refresh: null,
  };
  const preambleLines: Record<string, number> = {};
  const entries: Working[] = [];
  const h2Lines: number[] = [];
  let current: Working | null = null;
  let skipping = false;
  let lastField: string | null = null;
  let inComment = false;
  let commentStart = 0;
  let inFence = false;
  let fenceStart = 0;

  for (let idx = i; idx < lines.length; idx++) {
    const lineno = idx + 1;
    const raw = lines[idx];
    if (raw.length > MAX_LINE) {
      err("line-too-long", lineno);
      continue;
    }
    if (CONTROL_RE.test(raw)) err("control-character", lineno);
    const line = rtrim(raw);

    if (inComment) {
      if (line.includes("-->")) {
        inComment = false;
        if (trim(line.slice(line.indexOf("-->") + 3))) err("text-after-comment", lineno); // GitHub shows it; we would drop it
      }
      continue;
    }
    if (!inFence && ltrim(line).startsWith("<!--")) {
      if (!line.includes("-->")) {
        inComment = true;
        commentStart = lineno;
      } else if (trim(line.slice(line.indexOf("-->") + 3))) {
        err("text-after-comment", lineno);
      }
      continue;
    }
    if (!inFence && line.includes("<!--")) err("inline-comment", lineno);

    if (title === null) {
      if (!trim(line)) continue;
      const m = H1_RE.exec(line);
      if (m) {
        title = trim(m[1]);
        // The page title reaches Jekyll and Quarto front matter, and layouts print it.
        if (TITLE_MARKUP_RE.test(title)) err("title-markup", lineno);
        continue;
      }
      err("no-h1", lineno);
      title = "";
    }

    if (FENCE_RE.test(trim(line))) {
      inFence = !inFence;
      fenceStart = lineno;
      if (current !== null && !skipping) err("stray-text", lineno);
      else if (current === null) intro.push(line);
      continue;
    }
    if (inFence) {
      if (current === null) intro.push(line);
      else if (!skipping) err("stray-text", lineno);
      continue;
    }

    const h2 = H2_RE.exec(line);
    if (h2) {
      lastField = null;
      h2Lines.push(lineno);
      const m = ENTRY_HEADING_RE.exec(h2[1]);
      const um = m ? null : UNRELEASED_HEADING_RE.exec(h2[1]);
      if (!m && !um) {
        err("bad-heading", lineno);
        current = null;
        skipping = true;
        continue;
      }
      skipping = false;
      const date: string | null = m ? m[1] : null;
      const etitle = trim(m ? m[2] : um![1]);
      if (date === null) {
        if (entries.some((e) => e.unreleased)) err("duplicate-unreleased", lineno);
        else if (entries.length) err("unreleased-not-first", lineno);
      }
      current = {
        date,
        unreleased: date === null,
        title: etitle,
        anchor: githubSlug(`${date ?? "Unreleased"}: ${etitle}`),
        tags: [],
        summary: null,
        if_you_used_the_old_numbers: null,
        who_it_affects: null,
        mcp_version: null,
        notice_on: [],
        more_detail: null,
        updates: [],
        links: [],
        line: lineno,
        valid: true,
        _seen: new Set<string>(),
        _rawTags: null,
        _fieldLines: {},
        _updateLines: [],
      };
      if (date === null) {
        // waits for its release date; `check --release` fails while it is here
      } else if (!isRealDate(date)) err("bad-date", lineno);
      else if (date > day) err("future-date", lineno);
      if (TITLE_MARKUP_RE.test(etitle)) err("title-markup", lineno);
      if (EXAMPLE_TITLE_RE.test(etitle)) err("template-placeholder", lineno);
      else checkPlaceholders(etitle, lineno);
      entries.push(current);
      continue;
    }

    if (skipping) continue;

    if (current === null) {
      checkPlaceholders(line, lineno);
      const fm = FIELD_RE.exec(line);
      if (fm && Object.hasOwn(PREAMBLE_FIELDS, fm[1])) {
        const key = PREAMBLE_FIELDS[fm[1]];
        preamble[key] = trim(fm[2] ?? "");
        preambleLines[key] = lineno;
      }
      intro.push(line);
      continue;
    }

    if (!trim(line)) continue;
    if (DEEPER_RE.test(line) || H1_RE.test(line)) {
      err("stray-text", lineno);
      lastField = null;
      continue;
    }
    const fm = FIELD_RE.exec(line);
    if (fm) {
      const label = fm[1];
      const value = trim(fm[2] ?? "");
      checkPlaceholders(value, lineno);
      const um = UPDATE_LABEL_RE.exec(label);
      if (um) {
        const udate = um[1];
        if (!isRealDate(udate) || udate < (current.date ?? "") || udate > day) err("bad-update-date", lineno);
        if (!value) err("empty-field", lineno);
        current.updates.push({ date: udate, text: value });
        current._updateLines.push(lineno);
        lastField = "update";
        continue;
      }
      if (!Object.hasOwn(FIELDS, label)) {
        err("unknown-field", lineno);
        lastField = null;
        continue;
      }
      const key = FIELDS[label];
      if (current._seen.has(key)) {
        err("duplicate-field", lineno);
        lastField = null;
        continue;
      }
      current._seen.add(key);
      if (!value) err("empty-field", lineno);
      if (key === "tags") current._rawTags = [value, lineno];
      else if (key === "notice_on") current.notice_on = splitList(value);
      else {
        (current as unknown as Record<string, unknown>)[key] = value;
        current._fieldLines[key] = lineno;
      }
      lastField = key;
      continue;
    }
    if (CONT_RE.test(raw) && lastField !== null) {
      const extra = trim(line);
      checkPlaceholders(extra, lineno);
      if (lastField === "update") {
        const u = current.updates[current.updates.length - 1];
        u.text = trim(`${u.text} ${extra}`);
      } else if (lastField === "tags" && current._rawTags) {
        current._rawTags = [trim(`${current._rawTags[0]} ${extra}`), current._rawTags[1]];
      } else if (lastField === "notice_on") {
        current.notice_on.push(...splitList(extra));
      } else {
        const rec = current as unknown as Record<string, string | null>;
        rec[lastField] = trim(`${rec[lastField] ?? ""} ${extra}`);
      }
      continue;
    }
    err("stray-text", lineno);
    lastField = null;
  }

  if (inComment) err("unterminated-comment", commentStart);
  if (inFence) err("unterminated-fence", fenceStart); // GitHub shows everything after it as code
  if (title === null) {
    err("no-h1", 1);
    title = "";
  }

  const seenAnchors = new Set<string>();
  let prevDate: string | null = null;
  const out: Entry[] = [];
  for (const w of entries) {
    const { _seen, _rawTags, _fieldLines, _updateLines, ...e } = w;
    void _seen;
    const ln = e.line;
    if (_rawTags === null) {
      err("missing-tags", ln);
    } else {
      const [value, tln] = _rawTags;
      for (const t of splitList(value)) {
        if (!(TAGS as readonly string[]).includes(t)) err("bad-tag", tln);
        else if (e.tags.includes(t as Tag)) err("duplicate-tag", tln);
        else e.tags.push(t as Tag);
      }
    }
    if (!e.summary) err("missing-summary", ln);
    if (e.tags.includes("Correction")) {
      if (!e.tags.some((t) => SUBJECT_TAGS.includes(t))) err("correction-alone", ln);
      if (!e.if_you_used_the_old_numbers) err("missing-old-numbers", ln);
    } else if (e.notice_on.length) {
      err("notice-without-correction", ln);
    }
    if (e.tags.includes("MCP") && !e.mcp_version) err("missing-mcp-version", ln);
    if (e.mcp_version && !SEMVER_RE.test(e.mcp_version)) err("bad-mcp-version", ln);
    if (seenAnchors.has(e.anchor)) err("duplicate-anchor", ln);
    seenAnchors.add(e.anchor);
    if (e.date !== null && prevDate && isRealDate(e.date) && isRealDate(prevDate) && e.date > prevDate) err("out-of-order", ln);
    if (e.date !== null && isRealDate(e.date)) prevDate = e.date;
    for (const key of ["summary", "if_you_used_the_old_numbers", "who_it_affects", "mcp_version", "more_detail"] as const) {
      const v = e[key];
      if (v && hasUnsafeLink(v)) err("unsafe-link", _fieldLines[key] ?? ln);
    }
    e.updates.forEach((u, k) => {
      if (hasUnsafeLink(u.text)) err("unsafe-link", _updateLines[k]);
    });
    const values = [e.summary, e.if_you_used_the_old_numbers, e.who_it_affects, e.mcp_version, e.more_detail]
      .filter((v): v is string => !!v);
    e.links = extractLinks([...values, ...e.updates.map((u) => u.text)]);
    out.push(e);
  }

  const hb = preamble.history_begins;
  let hbDate: string | null = null;
  if (hb === null) {
    err("missing-history-begins", 1);
  } else {
    const hm = HISTORY_RE.exec(hb);
    if (!hm || !isRealDate(hm[1])) {
      err("bad-history-begins", preambleLines.history_begins);
    } else {
      hbDate = hm[1];
      const dated = out.map((e) => e.date).filter((d): d is string => d !== null && isRealDate(d)).sort();
      if (dated.length && hbDate > dated[0]) err("history-after-entry", preambleLines.history_begins);
    }
  }

  // An entry is valid when no entry-level error falls between its heading and the next one.
  const bounds = [...h2Lines].sort((a, b) => a - b);
  for (const e of out) {
    const next = bounds.find((b) => b > e.line);
    const end = next ?? lines.length + 1;
    e.valid = !errors.some((x) => x.line >= e.line && x.line < end && !FILE_LEVEL_CODES.includes(x.code));
  }

  errors.sort((a, b) => (a.line - b.line) || (a.code < b.code ? -1 : a.code > b.code ? 1 : 0));
  while (intro.length && !trim(intro[0])) intro.shift();
  while (intro.length && !trim(intro[intro.length - 1])) intro.pop();
  return {
    title,
    history_begins: hbDate,
    data_refresh: preamble.data_refresh,
    intro: intro.join("\n"),
    entries: out,
    errors,
  };
}

// --------------------------------------------------------------------------- query

export const DEFAULT_LIMIT = 10;
export const MAX_LIMIT = 50;

export interface Query {
  since?: string;
  tag?: Tag;
  limit?: number;
}

/** Valid, released entries newest first (the file's order); an entry with any error, and the
 * "Unreleased" entry, are never returned.
 * `since` keeps an entry dated on or after it, or one
 * with an Update dated on or after it, so a later update to an old correction still shows. */
export function queryEntries(parsed: ParsedFile, q: Query = {}): { matching: Entry[]; returned: Entry[] } {
  const matching = parsed.entries.filter((e) => {
    if (!e.valid || e.unreleased || e.date === null) return false;
    if (q.tag && !e.tags.includes(q.tag)) return false;
    if (q.since && !(e.date >= q.since || e.updates.some((u) => u.date >= q.since!))) return false;
    return true;
  });
  return { matching, returned: matching.slice(0, q.limit ?? DEFAULT_LIMIT) };
}

// --------------------------------------------------------------------------- links

function repoBase(repoUrl: string): string {
  return repoUrl.replace(/\/+$/, "");
}

/** Where readers find the file: the site page if there is one, else the file on GitHub. */
export function whatsChangedUrl(config: BetanycServerConfig): string {
  return config.pageUrl ?? `${repoBase(config.repoUrl)}/blob/HEAD/WHATS-CHANGED.md`;
}

/** Make a link from the file absolute, or null for a link that must not be followed
 * (anything but http, https, mailto, a repo path or a #anchor). Absolute URLs stay; "#anchor" points into the
 * What's changed page; a path under siteBase.prefix goes to the site; any other relative path
 * goes to the file on GitHub. */
export function absoluteLink(url: string, config: BetanycServerConfig): string | null {
  if (!isSafeUrl(url)) return null;
  if (SCHEME_RE.test(url)) return url;
  if (url.startsWith("#")) return whatsChangedUrl(config) + url;
  const path = (url.startsWith("./") ? url.slice(2) : url).replace(/^\/+/, "");
  const sb = config.siteBase;
  if (sb) {
    const prefix = sb.prefix.replace(/^\/+|\/+$/g, "") + "/";
    if (path.startsWith(prefix)) return sb.url.replace(/\/+$/, "") + "/" + path.slice(prefix.length);
  }
  return `${repoBase(config.repoUrl)}/blob/HEAD/${path}`;
}

/** Rewrite every markdown link inside a field to its absolute form. */
function absolutizeText(text: string | null, config: BetanycServerConfig): string | null {
  if (text === null) return null;
  return text.replace(LINK_RE, (_m, t: string, u: string) => {
    const abs = absoluteLink(u, config);
    return abs === null ? t : `[${t}](${abs})`; // an unsafe link keeps its words, loses its target
  });
}

// --------------------------------------------------------------------------- about BetaNYC

/** Every fact below is sourced. Mission and history: platform/system/org-context.md
 * (Version A tagline; "founded in 2008; operating as BetaNYC since 2013"). "A project of the
 * Fund for the City of New York" is the LICENSE wording in engineering-standards.md. No tax or
 * 501(c)(3) wording, on purpose: BetaNYC is not itself the 501(c)(3), and a model paraphrasing a
 * sentence about it could say it is. Each URL returned 200 on a GET on 2026-11-12. Change these only from a source, and record the check in the standard. */
export const BETANYC_ABOUT = {
  built_by: "BetaNYC, a project of the Fund for the City of New York",
  about:
    "BetaNYC is a civic organization dedicated to improving lives in New York through civic design, technology, and data.",
  history: "Founded in 2008 as the NYC Open Government meetup; operating as BetaNYC since 2013.",
  support: "To support BetaNYC's work, give at https://www.beta.nyc/donate/.",
  links: {
    website: "https://www.beta.nyc/",
    about: "https://www.beta.nyc/about/",
    history: "https://www.beta.nyc/our-history/",
    events: "https://www.beta.nyc/events/",
    newsletter: "https://www.beta.nyc/newsletter/",
    get_involved: "https://www.beta.nyc/our-work/get-involved/",
    donate: "https://www.beta.nyc/donate/",
  },
} as const;

// --------------------------------------------------------------------------- tool definitions

const LINK_SCHEMA = {
  type: "object",
  properties: { text: { type: "string" }, url: { type: "string" } },
  required: ["text", "url"],
};

const NULLABLE_STRING = { type: ["string", "null"] };

const ENTRY_SCHEMA = {
  type: "object",
  properties: {
    date: { type: "string", description: "YYYY-MM-DD, the day the change went live" },
    title: { type: "string" },
    url: { type: "string", description: "Link to this entry" },
    tags: { type: "array", items: { type: "string", enum: [...TAGS] } },
    summary: NULLABLE_STRING,
    if_you_used_the_old_numbers: {
      type: ["string", "null"],
      description: "For corrections: what to re-check and how",
    },
    who_it_affects: NULLABLE_STRING,
    mcp_version: NULLABLE_STRING,
    more_detail: NULLABLE_STRING,
    updates: {
      type: "array",
      items: {
        type: "object",
        properties: { date: { type: "string" }, text: { type: "string" } },
        required: ["date", "text"],
      },
    },
    links: { type: "array", items: LINK_SCHEMA },
  },
  required: [
    "date", "title", "url", "tags", "summary", "if_you_used_the_old_numbers",
    "who_it_affects", "mcp_version", "more_detail", "updates", "links",
  ],
};

export const WHATS_CHANGED_TOOL: ToolDefinition = {
  name: "whats_changed",
  title: "What's changed",
  description:
    "What has changed in this server, its data and its website, newest first, from the project's WHATS-CHANGED.md: new tools and pages, new data, data fixes, and corrections when BetaNYC published something wrong. " +
    "Each correction says what to re-check if you used the old numbers. Call this before relying on a figure you got from this server earlier, or when a user asks whether something was fixed. " +
    "Filter with since (YYYY-MM-DD; also keeps older entries that have an update on or after that date) and tag (Site, Data, MCP or Correction).",
  inputSchema: {
    type: "object",
    properties: {
      since: {
        type: "string",
        pattern: "^\\d{4}-\\d{2}-\\d{2}$",
        description: "Only changes on or after this date, YYYY-MM-DD",
      },
      tag: {
        type: "string",
        description: "Only changes with this tag: Site, Data, MCP or Correction (any case; answers use these spellings). Correction lists every correction.",
      },
      limit: {
        type: "integer",
        minimum: 1,
        maximum: MAX_LIMIT,
        description: `Most entries to return (default ${DEFAULT_LIMIT}, max ${MAX_LIMIT})`,
      },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      server: {
        type: "object",
        properties: { name: { type: "string" }, version: { type: "string" } },
        required: ["name", "version"],
      },
      source: { type: "string", description: "Where to read the full history" },
      history_begins: NULLABLE_STRING,
      filters: {
        type: "object",
        properties: { since: NULLABLE_STRING, tag: NULLABLE_STRING, limit: { type: "integer" } },
        required: ["since", "tag", "limit"],
      },
      total_matching: { type: "integer" },
      returned: { type: "integer" },
      entries: { type: "array", items: ENTRY_SCHEMA },
      note: NULLABLE_STRING,
    },
    required: ["server", "source", "history_begins", "filters", "total_matching", "returned", "entries", "note"],
  },
  annotations: { title: "What's changed", readOnlyHint: true, openWorldHint: false },
};

export const ABOUT_BETANYC_TOOL: ToolDefinition = {
  name: "about_betanyc",
  title: "About BetaNYC and this server",
  description:
    "Who built this server and how to reach them: BetaNYC, a project of the Fund for the City of New York. " +
    "Returns what BetaNYC is, links to its events, newsletter and donation page, where to report a bug in this server or ask for a new feature (this server's GitHub issues), and this server's name and version.",
  inputSchema: { type: "object", properties: {}, additionalProperties: false },
  outputSchema: {
    type: "object",
    properties: {
      server: {
        type: "object",
        properties: {
          name: { type: "string" },
          version: { type: "string" },
          repository: { type: "string" },
          shared_module_version: { type: "string" },
        },
        required: ["name", "version", "repository", "shared_module_version"],
      },
      built_by: { type: "string" },
      about: { type: "string" },
      history: { type: "string" },
      support: { type: "string" },
      links: {
        type: "object",
        properties: Object.fromEntries(Object.keys(BETANYC_ABOUT.links).map((k) => [k, { type: "string" }])),
        required: Object.keys(BETANYC_ABOUT.links),
      },
      bugs_and_requests: {
        type: "object",
        properties: { issues: { type: "string" }, new_issue: { type: "string" } },
        required: ["issues", "new_issue"],
      },
      whats_changed: { type: "string" },
    },
    required: ["server", "built_by", "about", "history", "support", "links", "bugs_and_requests", "whats_changed"],
  },
  annotations: { title: "About BetaNYC and this server", readOnlyHint: true, openWorldHint: false },
};


// --------------------------------------------------------------------------- handlers

function textResult(text: string, structured: Record<string, unknown>): ToolResult {
  return { content: [{ type: "text", text }], structuredContent: structured };
}

function errorResult(text: string): ToolResult {
  return { content: [{ type: "text", text: `Error: ${text}` }], isError: true };
}

/** Reject unknown keys and wrong types by name, as the BetaNYC servers do (an ignored
 * parameter would answer a different question with real-looking results). */
function checkArgs(tool: string, args: unknown, allowed: string[]): Record<string, unknown> {
  if (args === undefined || args === null) return {};
  if (typeof args !== "object" || Array.isArray(args)) throw new Error(`${tool} takes an object of arguments.`);
  const rec = args as Record<string, unknown>;
  const bad = Object.keys(rec).filter((k) => !allowed.includes(k));
  if (bad.length) {
    throw new Error(
      `${tool} does not accept ${bad.map((k) => `'${k}'`).join(", ")}. ` +
        (allowed.length ? `Accepted parameters: ${allowed.join(", ")}. ` : `${tool} takes no parameters. `) +
        "Unknown parameters are rejected rather than ignored, because ignoring one would answer a different question.",
    );
  }
  return rec;
}

function parseQuery(args: unknown): Query {
  const a = checkArgs("whats_changed", args, ["since", "tag", "limit"]);
  const q: Query = {};
  if (a.since !== undefined) {
    if (typeof a.since !== "string" || !isRealDate(a.since)) {
      throw new Error("since must be a real date written YYYY-MM-DD, for example 2026-11-01.");
    }
    q.since = a.since;
  }
  if (a.tag !== undefined) {
    const t = typeof a.tag === "string" ? TAGS.find((x) => x.toLowerCase() === (a.tag as string).trim().toLowerCase()) : undefined;
    if (!t) throw new Error(`tag must be one of ${TAGS.join(", ")}.`);
    q.tag = t;
  }
  if (a.limit !== undefined) {
    if (typeof a.limit !== "number" || !Number.isInteger(a.limit) || a.limit < 1 || a.limit > MAX_LIMIT) {
      throw new Error(`limit must be a whole number from 1 to ${MAX_LIMIT}.`);
    }
    q.limit = a.limit;
  }
  return q;
}

type Loaded = { kind: "ok"; text: string } | { kind: "missing" } | { kind: "unreadable"; message: string };

function loadText(config: BetanycServerConfig): Loaded {
  if (typeof config.whatsChangedText === "string") return { kind: "ok", text: config.whatsChangedText };
  if (!config.whatsChangedPath) return { kind: "missing" };
  try {
    return { kind: "ok", text: readFileSync(config.whatsChangedPath, "utf8") };
  } catch (e) {
    const code = (e as { code?: string }).code;
    if (code === "ENOENT") return { kind: "missing" };
    return { kind: "unreadable", message: e instanceof Error ? e.message : String(e) };
  }
}

function plural(n: number, word: string): string {
  if (n === 1) return `${n} ${word}`;
  return `${n} ${word.endsWith("y") ? `${word.slice(0, -1)}ies` : `${word}s`}`;
}

/** The whats_changed handler. Pure apart from reading the file; `today` is for tests. */
export function handleWhatsChanged(config: BetanycServerConfig, args: unknown, today?: string): ToolResult {
  let q: Query;
  try {
    q = parseQuery(args);
  } catch (e) {
    return errorResult(e instanceof Error ? e.message : String(e));
  }
  const limit = q.limit ?? DEFAULT_LIMIT;
  const server = { name: config.serverName, version: config.version };
  const source = whatsChangedUrl(config);
  const issues = `${repoBase(config.repoUrl)}/issues`;
  const base = {
    server,
    source,
    filters: { since: q.since ?? null, tag: q.tag ?? null, limit },
  };

  const loaded = loadText(config);
  if (loaded.kind !== "ok") {
    const why = loaded.kind === "missing"
      ? `${config.serverName} ${config.version} has no WHATS-CHANGED.md yet, so there is no change history to show.`
      : `${config.serverName} ${config.version} could not read its WHATS-CHANGED.md (${loaded.message}).`;
    const note = `${why} Release notes for developers: ${repoBase(config.repoUrl)}/releases. Report a bug in this server or ask for a new feature: ${issues}.`;
    return textResult(note, { ...base, history_begins: null, total_matching: 0, returned: 0, entries: [], note });
  }

  const parsed = parseWhatsChanged(loaded.text, today);
  const { matching, returned } = queryEntries(parsed, q);
  const notes: string[] = [];
  if (!parsed.entries.some((e) => e.valid && !e.unreleased)) notes.push("The change history has no entries to show yet.");
  else if (!matching.length) notes.push("No change matches those filters.");
  if (matching.length > returned.length) {
    notes.push(`Showing ${returned.length} of ${matching.length}; raise limit (max ${MAX_LIMIT}) or narrow since to see more.`);
  }
  const unreadable = parsed.errors.filter((e) => e.code === "bad-heading").length +
    parsed.entries.filter((e) => !e.valid).length;
  if (unreadable) notes.push(`${plural(unreadable, "entry")} in the file ${unreadable === 1 ? "has" : "have"} errors and ${unreadable === 1 ? "is" : "are"} left out. Full file: ${source}`);
  const waiting = parsed.entries.filter((e) => e.unreleased && e.valid).length;
  if (waiting) notes.push(`${plural(waiting, "change")} not released yet ${waiting === 1 ? "is" : "are"} left out until ${waiting === 1 ? "its" : "their"} release date is set.`);
  const hidden = parsed.errors.find((e) => ["unterminated-comment", "unterminated-fence", "file-too-large"].includes(e.code));
  if (hidden) notes.push(`The file has a problem at line ${hidden.line} (${hidden.code}), so entries after it may be missing. Full file: ${source}`);
  const note = notes.length ? notes.join(" ") : null;

  const entries = returned.map((e) => ({
    date: e.date,
    title: e.title,
    url: `${source}#${e.anchor}`,
    tags: e.tags,
    summary: absolutizeText(e.summary, config),
    if_you_used_the_old_numbers: absolutizeText(e.if_you_used_the_old_numbers, config),
    who_it_affects: absolutizeText(e.who_it_affects, config),
    mcp_version: absolutizeText(e.mcp_version, config),
    more_detail: absolutizeText(e.more_detail, config),
    updates: e.updates.map((u) => ({ date: u.date, text: absolutizeText(u.text, config) ?? "" })),
    links: e.links.flatMap((l) => {
      const url = absoluteLink(l.url, config);
      return url === null ? [] : [{ text: l.text, url }];
    }),
  }));

  const filterWords = [q.tag ? `tagged ${q.tag}` : "", q.since ? `since ${q.since}` : ""].filter(Boolean).join(", ");
  const head = [
    `What's changed in ${config.serverName} ${config.version}, newest first.` +
      (filterWords ? ` ${plural(matching.length, "change")} ${filterWords}.` : ` ${plural(matching.length, "change")} in all.`),
    parsed.history_begins ? `This history begins ${parsed.history_begins}; earlier corrections may be missing.` : "",
    `Full history: ${source}`,
  ].filter(Boolean);
  const blocks = entries.map((e) => {
    const lines = [`${e.date}: ${e.title} [${e.tags.join(", ")}]`];
    if (e.summary) lines.push(`What changed: ${e.summary}`);
    if (e.if_you_used_the_old_numbers) lines.push(`If you used the old numbers: ${e.if_you_used_the_old_numbers}`);
    if (e.who_it_affects) lines.push(`Who it affects: ${e.who_it_affects}`);
    if (e.mcp_version) lines.push(`MCP version: ${e.mcp_version}`);
    if (e.more_detail) lines.push(`More detail: ${e.more_detail}`);
    for (const u of e.updates) lines.push(`Update ${u.date}: ${u.text}`);
    lines.push(`Link: ${e.url}`);
    return lines.join("\n");
  });
  const text = [head.join("\n"), ...blocks, note ?? ""].filter(Boolean).join("\n\n");
  return textResult(text, {
    ...base,
    history_begins: parsed.history_begins,
    total_matching: matching.length,
    returned: entries.length,
    entries,
    note,
  });
}

/** The about_betanyc handler. */
export function handleAboutBetanyc(config: BetanycServerConfig, args: unknown): ToolResult {
  try {
    checkArgs("about_betanyc", args, []);
  } catch (e) {
    return errorResult(e instanceof Error ? e.message : String(e));
  }
  const repo = repoBase(config.repoUrl);
  const L = BETANYC_ABOUT.links;
  const structured = {
    server: {
      name: config.serverName,
      version: config.version,
      repository: repo,
      shared_module_version: SHARED_MODULE_VERSION,
    },
    built_by: BETANYC_ABOUT.built_by,
    about: BETANYC_ABOUT.about,
    history: BETANYC_ABOUT.history,
    support: BETANYC_ABOUT.support,
    links: { ...L },
    bugs_and_requests: { issues: `${repo}/issues`, new_issue: `${repo}/issues/new` },
    whats_changed: whatsChangedUrl(config),
  };
  const text = [
    `${config.serverName} ${config.version} was built by ${BETANYC_ABOUT.built_by}.`,
    `${BETANYC_ABOUT.about} ${BETANYC_ABOUT.history} More: ${L.about}`,
    `Events and workshops: ${L.events}\nNewsletter: ${L.newsletter}\nJoin the community: ${L.get_involved}`,
    BETANYC_ABOUT.support,
    `Report a bug in this server or ask for a new feature: ${repo}/issues (new issue: ${repo}/issues/new)`,
    `What's changed in this server: ${structured.whats_changed}`,
  ].join("\n\n");
  return textResult(text, structured);
}

// --------------------------------------------------------------------------- about data
//
// DATA-SOURCES.json: one file per repo with the facts about where its data comes from. The
// about_data tool answers from it; whats_changed.py `about-data catalog` writes the DCAT-US 3.0
// data.json and Croissant 1.1 croissant.json from the same file, so the three cannot disagree.
// The reader below and parse_data_sources() in whats_changed.py walk the same spec in the same
// order and give the same output (shared fixtures in fixtures/data-sources/).
// Standard: platform/system/about-data-standard.md.

export const DATA_SOURCES_FORMAT = "betanyc-data-sources/1";
export const DATA_SOURCES_FILE = "DATA-SOURCES.json";
const DS_MAX_STRING = 5_000;
/** A source_name is one dataset or document's name: at most this many characters (room for a
 * long official title), and no ";" (a list of several names breaks "Built from: {source}
 * ({publisher})"). 1.4.0. */
export const DS_SOURCE_NAME_MAX = 160;
const DS_ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const DS_URL_RE = /^https?:\/\/[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+(?::[0-9]{1,5})?(?:[/?#][A-Za-z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?$/;
const DS_REPO_RE = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
/** The leading lookahead rejects a "mailto:" prefix in any case: the catalog adds it. */
const DS_EMAIL_RE = /^(?![Mm][Aa][Ii][Ll][Tt][Oo]:)[A-Za-z0-9_~!$&'()*+,;=:.-]+@[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+$/;
const DS_DATE_RE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
const DS_TOOL_RE = /^[A-Za-z0-9_.-]{1,128}$/;
const DS_ANCHOR_RE = /^[a-z0-9-]{1,200}$/;
const DS_SHA256_RE = /^[0-9a-f]{64}$/;
const DS_MIME_RE = /^[a-z0-9!#$&^_.+-]+\/[a-z0-9!#$&^_.+-]+$/;
const DS_PATH_RE = /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))[A-Za-z0-9_./-]+$/;
/** The template's placeholders: any REPLACE, and the BetaNYC/REPO repo name. */
const DS_PLACEHOLDER_RE = /REPLACE|BetaNYC\/REPO(?![A-Za-z0-9_-])/;
const DS_KEY_CHAR_RE = /^[A-Za-z0-9_$-]$/;
/** An unpaired UTF-16 surrogate (Python reads the same text as a lone surrogate code point). */
const DS_SURROGATE_RE = /[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/;
const DS_MAX_DEPTH = 64;
/** Package pages and repos are where a server is obtained, not a hosted endpoint. */
const DS_NOT_ENDPOINT_RE = /^https?:\/\/(?:www\.)?(?:npmjs\.com|github\.com)(?:[/?#]|$)/i;
/** The placeholder contact address from files written before BetaNYC named its monitored
 * address (lab@beta.nyc, 2026-11-13; about-data-standard.md § 1). `--release` refuses it, and
 * about_data never shows it as a contact. */
export const DS_CONTACT_PLACEHOLDER = "contact-not-yet-named@example.invalid";
export const DS_STEPS = ["cleaned", "filtered", "reshaped", "fields-removed", "address-matched", "merged", "counted", "curated"] as const;
/** ISO 19115 maintenance frequency codes, as DCAT-US 3.0 lists them for accrualPeriodicity. */
export const DS_FREQUENCIES = [
  "continual", "daily", "weekly", "fortnightly", "monthly", "quarterly", "biannually",
  "annually", "asNeeded", "irregular", "notPlanned", "unknown",
] as const;
const DS_FRESHNESS = ["live", "file", "hook", "copied"] as const;
const DS_DATA_TYPES = ["Boolean", "Date", "Time", "DateTime", "Float", "Integer", "Text"] as const;
/** The three tools BetaNYC is adding to each of its servers (the What's changed and about-data
 * standards require them). They are about BetaNYC, not data, so need no source. */
export const SHARED_TOOL_NAMES: readonly string[] = ["whats_changed", "about_betanyc", "about_data"];

type Spec =
  | { kind: "obj"; required: boolean; fields: [string, Spec][] }
  | { kind: "list"; required: boolean; item: Spec; min: number }
  | { kind: "enum"; required: boolean; values: readonly string[] }
  | { kind: string; required: boolean };

const f = (kind: string, required = true): Spec => ({ kind, required });
const obj = (fields: [string, Spec][], required = true): Spec => ({ kind: "obj", required, fields });
const list = (item: Spec, required = false, min = 0): Spec => ({ kind: "list", required, item, min });
const en = (values: readonly string[], required = true): Spec => ({ kind: "enum", required, values });

/** Same fields, order and kinds as DS_SPEC in whats_changed.py. */
const DS_SPEC: Spec = obj([
  ["$schema", f("str", false)],
  ["format", en([DATA_SOURCES_FORMAT])],
  ["server", obj([
    ["name", f("str")],
    ["title", f("str")],
    ["description", f("str")],
    ["kind", en(["mcp", "site"])],
    ["repository", f("repo")],
    ["homepage", f("url", false)],
    ["documentation_url", f("url", false)],
    ["endpoint_urls", list(f("url"))],
    ["whats_changed_url", f("url", false)],
    ["license", obj([["name", f("str")], ["url", f("url")]])],
    ["package_url", f("url", false)],
    ["contact_email", f("email")],
    ["keywords", list(f("str"))],
  ])],
  ["sources", list(obj([
    ["id", f("id")],
    ["title", f("str")],
    ["what", f("str")],
    ["source_name", f("source-name")],
    ["publisher", obj([["name", f("publisher-name")], ["url", f("url", false)]])],
    ["source_url", f("url")],
    ["official", f("bool")],
    ["how_gathered", f("str")],
    ["changes", obj([["changed", f("bool")], ["steps", list(en(DS_STEPS))], ["detail", f("str", false)]])],
    ["verify_at", f("url")],
    ["freshness", obj([
      ["kind", en(DS_FRESHNESS)],
      ["path", f("path", false)],
      ["field", f("str", false)],
      ["key", f("str", false)],
    ])],
    ["update_frequency", en(DS_FREQUENCIES, false)],
    ["coverage", obj([
      ["start", f("date", false)],
      ["end", f("date", false)],
      ["geography", f("str")],
      ["known_gaps", list(f("str"))],
    ])],
    ["terms", obj([
      ["license_name", f("str", false)],
      ["license_url", f("url", false)],
      ["terms_url", f("url", false)],
      ["credit_line", f("str", false)],
    ])],
    ["report_errors", obj([["upstream_url", f("url")], ["upstream_email", f("email", false)], ["upstream_name", f("str", false)]])],
    ["tools", list(f("tool"))],
    ["caveats", list(f("str"))],
    ["corrections", list(f("anchor"))],
  ]), true, 1)],
  ["published_data", obj([
    ["name", f("str")],
    ["description", f("str")],
    ["url", f("url")],
    ["license", obj([["name", f("str")], ["url", f("url")]])],
    ["date_published", f("date")],
    ["version", f("str", false)],
    ["cite_as", f("str", false)],
    ["live", f("bool")],
    ["files", list(obj([
      ["id", f("id")],
      ["name", f("str")],
      ["description", f("str")],
      ["content_url", f("url")],
      ["encoding_format", f("mime")],
      ["sha256", f("sha", false)],
      ["derived_from", list(f("id"), true, 1)],
      ["fields", list(obj([
        ["name", f("str")],
        ["description", f("str")],
        ["data_type", en(DS_DATA_TYPES)],
        ["column", f("str", false)],
        ["json_path", f("str", false)],
      ]), true, 1)],
    ]), true, 1)],
  ], false)],
]);

export interface DataSourcesError {
  code: string;
  path: string;
}

/** A source, normalized: every optional field present (null or []). */
export interface DataSource {
  id: string | null;
  title: string | null;
  what: string | null;
  source_name: string | null;
  publisher: { name: string | null; url: string | null } | null;
  source_url: string | null;
  official: boolean | null;
  how_gathered: string | null;
  changes: { changed: boolean | null; steps: string[]; detail: string | null } | null;
  verify_at: string | null;
  freshness: { kind: string | null; path: string | null; field: string | null; key: string | null } | null;
  update_frequency: string | null;
  coverage: { start: string | null; end: string | null; geography: string | null; known_gaps: string[] } | null;
  terms: { license_name: string | null; license_url: string | null; terms_url: string | null; credit_line: string | null } | null;
  report_errors: { upstream_url: string | null; upstream_email: string | null; upstream_name: string | null } | null;
  tools: string[];
  caveats: string[];
  corrections: string[];
  /** False when any error falls inside this source. Invalid sources are never shown. */
  valid: boolean;
}

export interface DataSourcesDoc {
  format: string | null;
  server: Record<string, any> | null;
  sources: DataSource[];
  published_data: (Record<string, any> & { valid: boolean }) | null;
}

export interface DataSourcesParse {
  doc: DataSourcesDoc | null;
  errors: DataSourcesError[];
}

const codePoints = (s: string) => [...s].length;

function dsIsDate(s: string): boolean {
  if (!DS_DATE_RE.test(s)) return false;
  const [y, m, d] = s.split("-").map(Number);
  if (y < 1) return false;
  const dt = new Date(Date.UTC(2000, m - 1, d));
  dt.setUTCFullYear(y);
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
}

/** An unknown key as it appears in an error path: one "?" per unsafe character (code point). */
function dsKey(k: string): string {
  return [...k].map((c) => (DS_KEY_CHAR_RE.test(c) ? c : "?")).slice(0, 64).join("");
}

/** The path part of a URL (after the host, before ? or #). */
function urlPath(url: string): string {
  const m = /^https?:\/\/[^/?#]*([^?#]*)/.exec(url);
  return m ? m[1] : "";
}

/** Characters (code points), the unit Python's len() counts. */
function charCount(s: string): number {
  let n = s.length;
  for (let i = 0; i < s.length - 1; i++) {
    const c = s.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff) {
      const d = s.charCodeAt(i + 1);
      if (d >= 0xdc00 && d <= 0xdfff) {
        n--;
        i++;
      }
    }
  }
  return n;
}

function depthExceeds(value: unknown, limit: number): boolean {
  const stack: [unknown, number][] = [[value, 1]];
  while (stack.length) {
    const [v, d] = stack.pop()!;
    if (v !== null && typeof v === "object") {
      if (d > limit) return true;
      for (const x of Array.isArray(v) ? v : Object.values(v)) stack.push([x, d + 1]);
    }
  }
  return false;
}

function walk(spec: Spec, value: unknown, path: string, errors: DataSourcesError[]): unknown {
  const bad = (code: string) => errors.push({ code, path });
  if (spec.kind === "obj") {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      bad("wrong-type");
      return null;
    }
    const rec = value as Record<string, unknown>;
    const fields = (spec as { fields: [string, Spec][] }).fields;
    const known = fields.map(([k]) => k);
    for (const k of Object.keys(rec)) {
      if (!known.includes(k)) errors.push({ code: "unknown-key", path: path ? `${path}.${dsKey(k)}` : dsKey(k) });
    }
    const out: Record<string, unknown> = {};
    for (const [k, sub] of fields) {
      const p = path ? `${path}.${k}` : k;
      if (!Object.hasOwn(rec, k) || rec[k] === null) {
        if (sub.required) errors.push({ code: "missing", path: p });
        out[k] = sub.kind === "list" ? [] : null;
        continue;
      }
      out[k] = walk(sub, rec[k], p, errors);
    }
    return out;
  }
  if (spec.kind === "list") {
    const { item, min } = spec as { item: Spec; min: number };
    if (!Array.isArray(value)) {
      bad("wrong-type");
      return [];
    }
    if (value.length < min) bad("empty");
    return value.map((v, i) => walk(item, v, `${path}[${i}]`, errors));
  }
  if (spec.kind === "bool") {
    if (typeof value !== "boolean") {
      bad("wrong-type");
      return null;
    }
    return value;
  }
  if (typeof value !== "string") {
    bad("wrong-type");
    return null;
  }
  const k = spec.kind;
  let code: string | null = null;
  if (!trim(value)) code = "empty";
  else if (codePoints(value) > DS_MAX_STRING) code = "too-long";
  else if (CONTROL_RE.test(value)) code = "control-character";
  else if (DS_SURROGATE_RE.test(value)) code = "lone-surrogate";
  else if (DS_PLACEHOLDER_RE.test(value)) code = "placeholder";
  else if (k === "enum" && !(spec as { values: readonly string[] }).values.includes(value)) code = "bad-enum";
  else if (k === "url" && (!DS_URL_RE.test(value) || DOT_SEGMENT_RE.test(urlPath(value)))) code = "bad-url";
  else if (k === "repo" && !DS_REPO_RE.test(value)) code = "bad-repo";
  else if (k === "email" && !DS_EMAIL_RE.test(value)) code = "bad-email";
  else if (k === "date" && !dsIsDate(value)) code = "bad-date";
  else if (k === "id" && !(codePoints(value) <= 64 && DS_ID_RE.test(value))) code = "bad-id";
  else if (k === "tool" && !DS_TOOL_RE.test(value)) code = "bad-tool";
  else if (k === "anchor" && !DS_ANCHOR_RE.test(value)) code = "bad-anchor";
  else if (k === "sha" && !DS_SHA256_RE.test(value)) code = "bad-sha256";
  else if (k === "mime" && !DS_MIME_RE.test(value)) code = "bad-mime";
  else if (k === "path" && !DS_PATH_RE.test(value)) code = "bad-path";
  else if (k === "source-name" && (value.includes(";") || codePoints(value) > DS_SOURCE_NAME_MAX)) code = "bad-source-name";
  else if (k === "publisher-name" && /[()]/.test(value)) code = "bad-publisher-name";
  if (code) {
    bad(code);
    return null;
  }
  return value;
}

function compact(v: unknown): unknown {
  if (Array.isArray(v)) return v.filter((x) => x !== null).map(compact);
  if (v !== null && typeof v === "object") {
    return Object.fromEntries(Object.entries(v as Record<string, unknown>).map(([k, x]) => [k, compact(x)]));
  }
  return v;
}

/** Parse DATA-SOURCES.json. Never throws: problems come back in `errors` ({code, path}); each
 * source and the published_data block say whether they are `valid`. `doc` is null only when the
 * text is not one JSON object. Same output as `whats_changed.py about-data json`. */
export function parseDataSources(input: string): DataSourcesParse {
  if (input.length > MAX_CHARS && charCount(input) > MAX_CHARS) {
    return { doc: null, errors: [{ code: "file-too-large", path: "" }] };
  }
  const text = input.startsWith("\ufeff") ? input.slice(1) : input;
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch (e) {
    return { doc: null, errors: [{ code: e instanceof RangeError ? "too-deep" : "json-syntax", path: "" }] };
  }
  if (depthExceeds(raw, DS_MAX_DEPTH)) return { doc: null, errors: [{ code: "too-deep", path: "" }] };
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return { doc: null, errors: [{ code: "not-object", path: "" }] };
  }
  const errors: DataSourcesError[] = [];
  const doc = walk(DS_SPEC, raw, "", errors) as Record<string, any>;
  delete doc.$schema;
  const err = (code: string, path: string) => errors.push({ code, path });
  const server = doc.server ?? {};
  ((server.endpoint_urls ?? []) as (string | null)[]).forEach((u, k) => {
    if (u !== null && DS_NOT_ENDPOINT_RE.test(u)) err("not-an-endpoint", `server.endpoint_urls[${k}]`);
  });

  const seen = new Set<string>();
  const byUrl = new Map<string, string>();
  (doc.sources as (Record<string, any> | null)[]).forEach((s, i) => {
    if (s === null) return;
    const p = `sources[${i}]`;
    if (s.id !== null) {
      if (s.id === "all") err("reserved-id", `${p}.id`);
      else if (seen.has(s.id)) err("duplicate-id", `${p}.id`);
      seen.add(s.id);
    }
    const ch = s.changes;
    if (ch && ch.changed !== null) {
      if (ch.changed && (!ch.steps.length || ch.detail === null)) err("changes-mismatch", `${p}.changes`);
      if (ch.changed === false && ch.steps.length) err("changes-mismatch", `${p}.changes`);
    }
    const fr = s.freshness;
    if (fr && fr.kind !== null) {
      const want = ({ live: [], file: ["path", "field"], hook: ["key"], copied: ["key"] } as Record<string, string[]>)[fr.kind];
      const have = ["path", "field", "key"].filter((k) => fr[k] !== null);
      if (have.join(",") !== want.join(",")) err("freshness-fields", `${p}.freshness`);
    }
    const cov = s.coverage;
    if (cov && cov.start && cov.end && cov.start > cov.end) err("date-order", `${p}.coverage`);
    const t = s.terms;
    if (t && !(t.license_name || t.license_url || t.terms_url)) err("terms-missing", `${p}.terms`);
    if (s.source_url) {
      // Sources sharing a source_url share one upstream Dataset in data.json, so every field
      // that reaches it must agree.
      const mine = JSON.stringify([s.source_name, s.publisher, s.verify_at, s.update_frequency, s.terms, s.report_errors]);
      const prev = byUrl.get(s.source_url);
      if (prev === undefined) byUrl.set(s.source_url, mine);
      else if (prev !== mine) err("source-conflict", `${p}.source_url`);
    }
  });

  const pub = doc.published_data;
  if (pub !== null && typeof pub === "object") {
    const fileIds = new Set<string>();
    (pub.files as (Record<string, any> | null)[]).forEach((file, j) => {
      if (file === null) return;
      const p = `published_data.files[${j}]`;
      if (file.id !== null) {
        if (fileIds.has(file.id)) err("duplicate-id", `${p}.id`);
        fileIds.add(file.id);
      }
      (file.derived_from as (string | null)[]).forEach((ref, k) => {
        if (ref !== null && !seen.has(ref)) err("unknown-source", `${p}.derived_from[${k}]`);
      });
      if (pub.live === false && file.sha256 === null) err("sha256-required", `${p}.sha256`);
      const names = new Set<string>();
      (file.fields as (Record<string, any> | null)[]).forEach((fld, m) => {
        if (fld === null) return;
        const fp = `${p}.fields[${m}]`;
        if (fld.name !== null) {
          if (names.has(fld.name)) err("duplicate-id", `${fp}.name`);
          names.add(fld.name);
        }
        if ((fld.column === null) === (fld.json_path === null)) err("field-extract", fp);
      });
    });
  }
  // Every node with an @id in data.json must have its own (same order and paths as
  // parse_data_sources() in whats_changed.py; the later claim is the error).
  const nodes = new Map<string, string>([["https://www.beta.nyc/", "org:BetaNYC"]]);
  const claim = (id: string | null | undefined, key: string, path: string) => {
    if (!id) return;
    const prev = nodes.get(id);
    if (prev === undefined) nodes.set(id, key);
    else if (prev !== key) err("id-collision", path);
  };
  const srcs = doc.sources as (Record<string, any> | null)[];
  if (server.repository) {
    srcs.forEach((s, i) => {
      if (s !== null && s.id !== null) claim(`${server.repository}/blob/HEAD/${DATA_SOURCES_FILE}#${s.id}`, "derived:" + s.id, `sources[${i}].id`);
    });
    if ((server.endpoint_urls ?? []).length) claim(server.repository, "service", "server.repository");
  }
  srcs.forEach((s, i) => {
    if (s === null) return;
    claim(s.source_url, "upstream:" + (s.source_url ?? ""), `sources[${i}].source_url`);
    if (s.publisher && s.publisher.url) claim(s.publisher.url, "org:" + (s.publisher.name ?? ""), `sources[${i}].publisher.url`);
  });
  if (pub !== null && typeof pub === "object") claim(pub.url, "published", "published_data.url");
  if (pub !== null && typeof pub === "object") {
    pub.valid = !errors.some((e) => e.path === "published_data" || e.path.startsWith("published_data."));
  }
  (doc.sources as (Record<string, any> | null)[]).forEach((s, i) => {
    if (s === null) return;
    const pre = `sources[${i}]`;
    s.valid = !errors.some((e) => e.path === pre || e.path.startsWith(pre + "."));
  });
  errors.sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : a.code < b.code ? -1 : a.code > b.code ? 1 : 0));
  return { doc: compact(doc) as DataSourcesDoc, errors };
}

/** parseDataSources() for raw file bytes: invalid UTF-8 is a clean error ("bad-encoding"). */
export function parseDataSourcesBytes(data: Uint8Array): DataSourcesParse {
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(data);
  } catch {
    return { doc: null, errors: [{ code: "bad-encoding", path: "" }] };
  }
  return parseDataSources(text);
}

/** The server's tools that no source lists (the three shared tools excepted), and tools a source
 * lists that the server does not have. Same as tool_coverage() in whats_changed.py. */
export function toolCoverage(doc: DataSourcesDoc | null, toolNames: readonly string[]): { without_source: string[]; unknown: string[] } {
  const listed = new Set<string>();
  for (const s of doc?.sources ?? []) for (const t of s.tools) listed.add(t);
  const have = new Set(toolNames);
  const sort = (a: string[]) => a.sort((x, y) => (x < y ? -1 : x > y ? 1 : 0));
  return {
    without_source: sort([...have].filter((t) => !listed.has(t) && !SHARED_TOOL_NAMES.includes(t))),
    unknown: sort([...listed].filter((t) => !have.has(t))),
  };
}

/** For each MCP's own test suite: throws, naming them, when a tool has no source in
 * DATA-SOURCES.json, when a source lists a tool the server lacks, or when the file has errors.
 *
 *   import { assertEveryToolExplained } from "../dist/betanyc-tools.js";
 *   test("every tool says where its data comes from", () =>
 *     assertEveryToolExplained(readFileSync("DATA-SOURCES.json", "utf8"), TOOLS.map((t) => t.name)));
 */
export function assertEveryToolExplained(dataSourcesText: string, toolNames: readonly string[]): void {
  const parsed = parseDataSources(dataSourcesText);
  const problems: string[] = [];
  if (parsed.errors.length) {
    problems.push(`${DATA_SOURCES_FILE} has errors: ${parsed.errors.map((e) => `${e.code} at ${e.path || "(file)"}`).join("; ")}`);
  }
  const cov = toolCoverage(parsed.doc, toolNames);
  if (cov.without_source.length) problems.push(`no source lists these tools: ${cov.without_source.join(", ")}`);
  if (cov.unknown.length) problems.push(`sources list tools this server does not have: ${cov.unknown.join(", ")}`);
  if (problems.length) throw new Error(`about_data: ${problems.join(". ")}.`);
}

/** Add this to the server's `instructions` (new Server(..., { instructions })), so the AI app
 * knows to call about_data and how to word curated facts. createBetanycTools returns it too. */
export const BETANYC_INSTRUCTIONS =
  "When someone asks where an answer's data comes from, how current or accurate it is, whether it is official, " +
  "or how to check, cite, or correct it, call about_data (with a topic for one kind of data or one tool) and answer " +
  "from it, naming the source and its publisher. about_data gives each source one of three answers on whether it is " +
  "official. \"Publisher: … BetaNYC did not modify it.\" means it is the publisher's own record. " +
  "\"BetaNYC modified this data\" means this copy is not the official record; say what BetaNYC did, name the official " +
  "record and give its link. \"BetaNYC produced this\" means BetaNYC built or collected it, and it is not an official " +
  "record either. Never call data official when BetaNYC modified or produced it. For who built this server, call " +
  "about_betanyc; for recent fixes and corrections, call whats_changed.";

export const ABOUT_DATA_TOOL: ToolDefinition = {
  name: "about_data",
  title: "Where this server's data comes from",
  description:
    "Where this server's data comes from and how far to trust it. For each kind of data: who publishes it and a link, " +
    "whether it is an official record (only data its publisher published and BetaNYC did not modify is; data BetaNYC " +
    "modified or produced is not), how it was gathered, what BetaNYC did to it (for example cleaned it, matched it to " +
    "addresses, joined it with other data, or counted it), how current it is on this server, what it covers and what is " +
    "missing, the terms of use and the credit line to print, where to check a figure at the official record, where to " +
    "report an error (to BetaNYC when BetaNYC modified or produced the data, to the publisher for the original records, " +
    "and to this server's issues for a bug), which tools use it, and corrections that touched it. " +
    "Call it whenever someone asks where an answer comes from, how current or accurate it is, or how to check or cite it. " +
    "topic narrows it to one kind of data, or to the data behind one tool (give the tool's name). For who built this server, use about_betanyc.",
  inputSchema: {
    type: "object",
    properties: {
      topic: {
        type: "string",
        description: "One kind of data (a source id), or a tool name for the data behind that tool. Any case. Default: all.",
      },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      server: {
        type: "object",
        properties: { name: { type: "string" }, version: { type: "string" } },
        required: ["name", "version"],
      },
      source_file: { type: "string", description: "DATA-SOURCES.json on GitHub" },
      topic: NULLABLE_STRING,
      topics: { type: "array", items: { type: "string" } },
      sources: {
        type: "array",
        items: {
          type: "object",
          properties: {
            topic: { type: "string" },
            title: { type: "string" },
            what: { type: "string" },
            source: { type: "string" },
            publisher: { type: "string" },
            source_url: { type: "string" },
            official: { type: "boolean", description: "The source is an official publisher's record (false: BetaNYC produced it)" },
            figures_official: {
              type: "boolean",
              description: "True only when the source is official and BetaNYC did not modify it. False means this copy is not the official record, because BetaNYC modified it or produced it",
            },
            how_gathered: { type: "string" },
            changed_by_betanyc: {
              type: "object",
              properties: {
                changed: { type: "boolean" },
                steps: { type: "array", items: { type: "string" } },
                detail: NULLABLE_STRING,
              },
              required: ["changed", "steps", "detail"],
            },
            as_of: { type: "string", description: "How current this data is on this server" },
            as_of_status: {
              type: "string",
              enum: ["live", "read", "copied", "not-fetched", "unavailable", "unreadable"],
              description: "read: a checked date from this server. unavailable: none given. unreadable: given, but not a usable date",
            },
            update_frequency: NULLABLE_STRING,
            coverage: {
              type: "object",
              properties: {
                start: NULLABLE_STRING,
                end: NULLABLE_STRING,
                geography: { type: "string" },
                known_gaps: { type: "array", items: { type: "string" } },
              },
              required: ["start", "end", "geography", "known_gaps"],
            },
            terms: {
              type: "object",
              properties: {
                license_name: NULLABLE_STRING,
                license_url: NULLABLE_STRING,
                terms_url: NULLABLE_STRING,
                credit_line: NULLABLE_STRING,
              },
              required: ["license_name", "license_url", "terms_url", "credit_line"],
            },
            verify_at: { type: "string" },
            report_errors: {
              type: "object",
              properties: {
                in_the_data: { type: "string", description: "The publisher's page for data errors" },
                in_the_data_email: NULLABLE_STRING,
                in_the_data_name: {
                  type: "string",
                  description: "Who handles reports at in_the_data: the publisher, the organization named in the file when someone else runs the route (for example a city's open data team), or BetaNYC",
                },
                in_the_data_handled_by: {
                  type: "string",
                  enum: ["publisher", "betanyc"],
                  description: "Who fixes errors at in_the_data: the publisher, or BetaNYC when the route is BetaNYC's own",
                },
                in_these_figures: {
                  type: ["string", "null"],
                  description: "When BetaNYC modified or produced the data: where to report an error in it to BetaNYC (this server's issues). Null for data its publisher published and BetaNYC did not modify",
                },
                in_this_server: { type: "string", description: "This server's GitHub issues" },
              },
              required: ["in_the_data", "in_the_data_email", "in_the_data_name", "in_the_data_handled_by", "in_these_figures", "in_this_server"],
            },
            tools: { type: "array", items: { type: "string" } },
            caveats: { type: "array", items: { type: "string" } },
            corrections: {
              type: "array",
              items: {
                type: "object",
                properties: { date: NULLABLE_STRING, title: NULLABLE_STRING, url: { type: "string" } },
                required: ["date", "title", "url"],
              },
            },
          },
          required: [
            "topic", "title", "what", "source", "publisher", "source_url", "official", "figures_official", "how_gathered",
            "changed_by_betanyc", "as_of", "as_of_status", "update_frequency", "coverage", "terms", "verify_at",
            "report_errors", "tools", "caveats", "corrections",
          ],
        },
      },
      catalog: {
        type: "object",
        properties: { data_json: NULLABLE_STRING, croissant_json: NULLABLE_STRING },
        required: ["data_json", "croissant_json"],
      },
      who_built_this: { type: "string", description: "Call about_betanyc for who built this server" },
      contact_email: {
        type: ["string", "null"],
        description: "BetaNYC's monitored address for questions and error reports about this data, from DATA-SOURCES.json. Null when the file names none yet",
      },
      left_out: {
        type: "array",
        description: "Sources in the file that this server cannot show, and why",
        items: {
          type: "object",
          properties: {
            topic: NULLABLE_STRING,
            reason: { type: "string", enum: ["newer-feature", "errors"] },
          },
          required: ["topic", "reason"],
        },
      },
      note: NULLABLE_STRING,
    },
    required: ["server", "source_file", "topic", "topics", "sources", "catalog", "who_built_this", "contact_email", "left_out", "note"],
  },
  annotations: { title: "Where this server's data comes from", readOnlyHint: true, openWorldHint: false },
};

type LoadedDs = { kind: "ok"; parsed: DataSourcesParse } | { kind: "missing" } | { kind: "unreadable"; message: string };

function loadDataSources(config: BetanycServerConfig): LoadedDs {
  if (typeof config.dataSourcesText === "string") return { kind: "ok", parsed: parseDataSources(config.dataSourcesText) };
  if (!config.dataSourcesPath) return { kind: "missing" };
  try {
    return { kind: "ok", parsed: parseDataSourcesBytes(readFileSync(config.dataSourcesPath)) };
  } catch (e) {
    if ((e as { code?: string }).code === "ENOENT") return { kind: "missing" };
    return { kind: "unreadable", message: e instanceof Error ? e.message : String(e) };
  }
}

/** The package root that freshness `file` paths are relative to: dataRoot, else the folder
 * holding DATA-SOURCES.json. */
function dataRoot(config: BetanycServerConfig): URL | null {
  const asDirUrl = (p: string | URL): URL => {
    const u = typeof p === "string" ? pathToFileURL(p) : p;
    return u.href.endsWith("/") ? u : new URL(u.href + "/");
  };
  if (config.dataRoot) return asDirUrl(config.dataRoot);
  if (config.dataSourcesPath) {
    const u = typeof config.dataSourcesPath === "string" ? pathToFileURL(config.dataSourcesPath) : config.dataSourcesPath;
    return new URL(".", u);
  }
  return null;
}

const AS_OF_RE = /^([0-9]{4}-[0-9]{2}-[0-9]{2})(?:T([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.[0-9]{1,9})?)?([Zz]|[+-][0-9]{2}:[0-9]{2}))?$/;
/** How far ahead of this machine's clock a freshness value may be before it is not believed. */
export const AS_OF_SKEW_MS = 24 * 60 * 60 * 1000;

/** Today's date in New York (YYYY-MM-DD), where BetaNYC's data is published. */
function newYorkDate(now: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" })
    .formatToParts(now);
  const get = (t: string) => parts.find((p) => p.type === t)!.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

/** A freshness value is used only when it is an ISO 8601 date (YYYY-MM-DD) or date-time with a
 * zone (YYYY-MM-DDThh:mm[:ss[.fff]](Z|z|+hh:mm)), is a real day and time (a leap second, :60, is
 * rejected), and is not in the future beyond one day's allowance: a date against today's date in
 * New York, a date-time against now. Anything else is reported as unreadable, never passed on. */
export function isUsableAsOf(v: unknown, now: Date): v is string {
  if (typeof v !== "string" || v.length > 40) return false;
  const m = AS_OF_RE.exec(v);
  if (!m || !dsIsDate(m[1])) return false;
  if (m[2] === undefined) {
    const t = new Date(`${newYorkDate(now)}T00:00:00Z`);
    t.setUTCDate(t.getUTCDate() + 1);
    return m[1] <= t.toISOString().slice(0, 10);
  }
  if (Number(m[2]) > 23 || Number(m[3]) > 59 || (m[4] !== undefined && Number(m[4]) > 59)) return false;
  const t = Date.parse(v.replace(/z$/, "Z"));
  return Number.isFinite(t) && t <= now.getTime() + AS_OF_SKEW_MS;
}

type AsOfStatus = "live" | "read" | "copied" | "not-fetched" | "unavailable" | "unreadable";
type AsOf = { as_of: string; as_of_status: AsOfStatus };
type HookOutcome = { kind: "none" } | { kind: "threw" } | { kind: "async" } | { kind: "timeout" } | { kind: "value"; value: unknown };

function hookFor(config: BetanycServerConfig, key: string): FreshnessHook | undefined {
  const hooks = config.freshness;
  const h = hooks && Object.hasOwn(hooks, key) ? hooks[key] : undefined;
  return typeof h === "function" ? h : undefined;
}

const isThenable = (v: unknown): v is PromiseLike<unknown> =>
  v !== null && typeof v === "object" && typeof (v as { then?: unknown }).then === "function";

function syncOutcome(config: BetanycServerConfig, key: string): HookOutcome {
  const h = hookFor(config, key);
  if (!h) return { kind: "none" };
  try {
    const v = h();
    if (isThenable(v)) {
      Promise.resolve(v).catch(() => undefined); // never an unhandled rejection
      return { kind: "async" };
    }
    return { kind: "value", value: v };
  } catch {
    return { kind: "threw" };
  }
}

async function asyncOutcome(config: BetanycServerConfig, key: string): Promise<HookOutcome> {
  const h = hookFor(config, key);
  if (!h) return { kind: "none" };
  try {
    return { kind: "value", value: await h() };
  } catch {
    return { kind: "threw" };
  }
}

function fromValue(v: unknown, where: string, now: Date, copied: boolean): AsOf {
  if (v !== null && typeof v === "object" && (v as { notFetched?: unknown }).notFetched === true) {
    return { as_of: "not fetched yet on this server (it downloads this data when first asked)", as_of_status: "not-fetched" };
  }
  if (v === null || v === undefined || (typeof v === "string" && !trim(v))) {
    return { as_of: `unavailable: ${where} has no readable date for it`, as_of_status: "unavailable" };
  }
  if (!isUsableAsOf(v, now)) return { as_of: `unknown: ${where} did not give a usable date`, as_of_status: "unreadable" };
  return copied
    ? { as_of: `copied from the source on ${v} and built into this server`, as_of_status: "copied" }
    : { as_of: v, as_of_status: "read" };
}

/** How current one source is on this running server. Read from a build artifact, a hook, or a
 * date kept in code beside copied text; never typed into DATA-SOURCES.json; checked before it is
 * repeated (isUsableAsOf). */
function asOf(s: DataSource, config: BetanycServerConfig, now: Date, outcome: (key: string) => HookOutcome): AsOf {
  const off = config.unavailableSources;
  if (off && Object.hasOwn(off, s.id!) && typeof off[s.id!] === "string" && trim(off[s.id!])) {
    return { as_of: `not available on this server: ${trim(off[s.id!])}`, as_of_status: "unavailable" };
  }
  const fr = s.freshness!;
  if (fr.kind === "live") return { as_of: "live: fetched from the source when you ask", as_of_status: "live" };
  if (fr.kind === "hook" || fr.kind === "copied") {
    const o = outcome(fr.key!);
    if (o.kind === "none") return { as_of: "not reported by this server", as_of_status: "unavailable" };
    if (o.kind === "threw") return { as_of: "unknown: the server could not read it", as_of_status: "unreadable" };
    if (o.kind === "timeout") return { as_of: "unavailable: the server did not report it in time", as_of_status: "unavailable" };
    if (o.kind === "async") {
      return { as_of: "unavailable: this server reads it asynchronously; its about_data must be called with callAsync", as_of_status: "unavailable" };
    }
    return fromValue(o.value, "the server", now, fr.kind === "copied");
  }
  const root = dataRoot(config);
  if (!root) return { as_of: "unknown: no data folder is configured", as_of_status: "unavailable" };
  let data: unknown;
  try {
    data = JSON.parse(readFileSync(new URL(fr.path!, root), "utf8"));
  } catch (e) {
    const missing = (e as { code?: string }).code === "ENOENT";
    return missing
      ? { as_of: `${fr.path} is missing from this install`, as_of_status: "unavailable" }
      : { as_of: `unknown: ${fr.path} could not be read`, as_of_status: "unreadable" };
  }
  const v = data !== null && typeof data === "object" && !Array.isArray(data) && Object.hasOwn(data, fr.field!)
    ? (data as Record<string, unknown>)[fr.field!] : undefined;
  return fromValue(v, fr.path!, now, false);
}

function dsFileUrl(config: BetanycServerConfig): string {
  return `${repoBase(config.repoUrl)}/blob/HEAD/${DATA_SOURCES_FILE}`;
}

const ROUTE_URL_RE = /^https?:\/\/([A-Za-z0-9.-]+)(?::[0-9]{1,5})?([/?#].*)?$/;
/** A "." or ".." path segment, literal or percent-encoded. Such URLs are bad-url in check, and
 * never count as BetaNYC's: github.com/BetaNYC/x/../../evil resolves somewhere else. */
const DOT_SEGMENT_RE = /(?:^|\/)(?:\.|%2e){1,2}(?:\/|$)/i;

/** True when an error-report URL is BetaNYC's own (a BetaNYC repo, its issues, beta.nyc, or a
 * BetaNYC GitHub Pages site on betanyc.github.io), so the route is worded as reporting to BetaNYC.
 * Same as route_is_betanyc() in whats_changed.py. */
export function routeIsBetanyc(url: string): boolean {
  const m = ROUTE_URL_RE.exec(url ?? "");
  if (!m) return false;
  const host = m[1].toLowerCase();
  const path = (m[2] ?? "").split(/[?#]/)[0];
  if (DOT_SEGMENT_RE.test(path)) return false;
  if (host === "beta.nyc" || host.endsWith(".beta.nyc")) return true;
  if (host === "betanyc.github.io") return true; // BetaNYC's GitHub Pages sites (1.3.7)
  if (host === "github.com" || host === "www.github.com") return path.split("/")[1]?.toLowerCase() === "betanyc";
  return false;
}

/** Plain words for each step, for the "modified" answer. Every step in DS_STEPS has one (a test
 * checks). Same table as DS_STEP_WORDS in whats_changed.py. Before 1.4.0, reshaped and
 * fields-removed (DS_FORMAT_ONLY_STEPS) kept "Official record: yes"; from 1.4.0 any step at all
 * means BetaNYC modified the data, so this copy is not the official record. */
export const DS_STEP_WORDS: Readonly<Record<string, string>> = {
  cleaned: "cleaned it",
  filtered: "left some records out",
  reshaped: "reshaped it",
  "fields-removed": "left some fields out",
  "address-matched": "matched addresses to places",
  merged: "joined it with other data",
  counted: "counted or added up records",
  curated: "read it from the published document and checked it",
};

/** What BetaNYC did, in plain words, in the file's order, Oxford comma: "reshaped it and counted
 * or added up records", but "read it from the published document and checked it, and reshaped it". Same as what_was_done() in whats_changed.py. */
export function whatWasDone(steps: readonly string[]): string {
  const words = [...new Set(steps)].map((st) => (Object.hasOwn(DS_STEP_WORDS, st) ? DS_STEP_WORDS[st] : st));
  // Two steps join with " and ", unless a step's own words contain " and " (1.4.0).
  if (words.length <= 1 || (words.length === 2 && !words.some((w) => w.includes(" and ")))) return words.join(" and ");
  return `${words.slice(0, -1).join(", ")}, and ${words[words.length - 1]}`;
}

/** The three answers to "is this data official?" (1.4.0). */
export type OfficialKind = "published-as-is" | "modified-by-betanyc" | "produced-by-betanyc";

/** Which answer a source gets: produced by BetaNYC when it is not official; modified by BetaNYC
 * when BetaNYC took any step at all; else published as is. Same as official_kind() in
 * whats_changed.py. */
export function officialKind(official: boolean, changed: boolean, steps: readonly string[] = []): OfficialKind {
  if (!official) return "produced-by-betanyc";
  return changed || steps.length > 0 ? "modified-by-betanyc" : "published-as-is";
}

/** True when a source's publisher is BetaNYC itself: the name "BetaNYC" (any case), or a URL that
 * routeIsBetanyc() accepts. Same as publisher_is_betanyc() in whats_changed.py (1.3.7). */
export function publisherIsBetanyc(name: string, url: string | null = null): boolean {
  return trim(name ?? "").toLowerCase() === "betanyc" || (typeof url === "string" && routeIsBetanyc(url));
}

/** A name as the "already names the publisher" check compares it: trimmed, lower case, runs of
 * spaces as one, and "New York City" read as "NYC". Same as _name_key() in whats_changed.py. */
function nameKey(s: string): string {
  return trim(s).toLowerCase().replace(/ +/g, " ").replace(/(?<![a-z0-9])new york city(?![a-z0-9])/g, "nyc");
}

/** The source part of the modified ("Official record:") and produced ("Built from:") answers:
 * the source's name, then the publisher's full name in parentheses. The publisher is left out
 * when it is BetaNYC or the source's name already names it (1.3.7). A publisher name never has
 * parentheses (the readers reject it, bad-publisher-name), so they never nest. Same as
 * built_from() in whats_changed.py. */
export function builtFrom(sourceName: string, publisher: string, publisherUrl: string | null = null): string {
  if (publisherIsBetanyc(publisher, publisherUrl)) return sourceName;
  if (nameKey(sourceName).includes(nameKey(publisher))) return sourceName;
  return `${sourceName} (${publisher})`;
}

export interface OfficialWordingInput {
  official: boolean;
  changed: boolean;
  steps?: readonly string[];
  publisher: string;
  publisherUrl?: string | null;
  sourceName: string;
  sourceUrl: string;
}

/** The one answer to "is this data official?" (1.4.0). Same words as official_wording() in
 * whats_changed.py. Every answer names the source (its name), its publisher and a link (Noel,
 * 2026-11-15). No period after a link: some apps take it into the link. */
export function officialWording(s: OfficialWordingInput): string {
  const steps = s.steps ?? [];
  const kind = officialKind(s.official, s.changed, steps);
  if (kind === "produced-by-betanyc") {
    return `BetaNYC produced this. It is not an official record. Built from: ${builtFrom(s.sourceName, s.publisher, s.publisherUrl ?? null)}, ${s.sourceUrl}`;
  }
  if (kind === "modified-by-betanyc") {
    return `BetaNYC modified this data: ${whatWasDone(steps)}. This copy should not be considered the official record. Official record: ${builtFrom(s.sourceName, s.publisher, s.publisherUrl ?? null)}, ${s.sourceUrl}`;
  }
  return `Publisher: ${s.publisher}. BetaNYC did not modify it. Source: ${s.sourceName}, ${s.sourceUrl}`;
}

/** Error codes a newer module's file gives an older reader: a value (a step, a freshness kind)
 * or a field it does not know yet. */
const NEWER_FEATURE_CODES = ["bad-enum", "unknown-key"];

/** The invalid sources, in file order, each with why: "newer-feature" when every error in it is
 * an unknown value or field (the file was written for a newer module), else "errors". */
function leftOutSources(parsed: DataSourcesParse): { topic: string | null; reason: "newer-feature" | "errors" }[] {
  const byIndex = new Map<number, string[]>();
  for (const e of parsed.errors) {
    const m = /^sources\[(\d+)\](\.|$)/.exec(e.path);
    if (!m) continue;
    const i = Number(m[1]);
    if (e.path === `sources[${i}]` && e.code === "wrong-type") {
      byIndex.set(i, ["not-an-object"]); // dropped from the doc; never shown
      continue;
    }
    if (byIndex.get(i)?.[0] === "not-an-object") continue;
    byIndex.set(i, [...(byIndex.get(i) ?? []), e.code]);
  }
  const invalid = (parsed.doc?.sources ?? []).filter((s) => !s.valid);
  const indices = [...byIndex.entries()].filter(([, c]) => c[0] !== "not-an-object").sort((a, b) => a[0] - b[0]);
  return invalid.map((s, k) => {
    const codes = indices[k]?.[1] ?? [];
    return { topic: s.id, reason: codes.length && codes.every((c) => NEWER_FEATURE_CODES.includes(c)) ? "newer-feature" : "errors" };
  });
}

/** BetaNYC's contact address from the file's server block, or null when it is missing, invalid,
 * or still the placeholder: a placeholder is never shown as if it were monitored (nyc-council-mcp#77). */
function contactEmail(parsed: DataSourcesParse): string | null {
  const v = parsed.doc?.server?.contact_email;
  if (typeof v !== "string" || !trim(v) || v === DS_CONTACT_PLACEHOLDER) return null;
  if (parsed.errors.some((e) => e.path === "server.contact_email" || e.path === "server")) return null;
  return trim(v);
}

/** The about_data handler. Reads DATA-SOURCES.json (and WHATS-CHANGED.md for corrections) on
 * every call, so a rebuilt data file shows at once. Only a bad argument is an error. */
export function handleAboutData(config: BetanycServerConfig, args: unknown, now: Date = new Date()): ToolResult {
  return aboutData(config, args, now, (key) => syncOutcome(config, key));
}

/** handleAboutData for servers with async freshness hooks: awaits every hook first. */
/** How long callAsync waits for one freshness hook before reporting it as unavailable. */
export const ABOUT_DATA_HOOK_TIMEOUT_MS = 3000;

/** handleAboutData for servers with async freshness hooks. Runs only the hooks of the sources in
 * this answer, each raced against hookTimeoutMs (default ABOUT_DATA_HOOK_TIMEOUT_MS), so a hook
 * that never settles cannot hang the tool. */
export async function handleAboutDataAsync(config: BetanycServerConfig, args: unknown, now: Date = new Date()): Promise<ToolResult> {
  const keys = new Set<string>();
  aboutData(config, args, now, (key) => {
    keys.add(key);
    return { kind: "none" };
  });
  const ms = config.hookTimeoutMs ?? ABOUT_DATA_HOOK_TIMEOUT_MS;
  const outcomes = new Map<string, HookOutcome>();
  await Promise.all([...keys].map(async (k) => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const timeout = new Promise<HookOutcome>((res) => {
      timer = setTimeout(() => res({ kind: "timeout" }), ms);
      (timer as { unref?: () => void }).unref?.();
    });
    outcomes.set(k, await Promise.race([asyncOutcome(config, k), timeout]));
    clearTimeout(timer);
  }));
  return aboutData(config, args, now, (key) => outcomes.get(key) ?? { kind: "none" });
}

function aboutData(config: BetanycServerConfig, args: unknown, now: Date, outcome: (key: string) => HookOutcome): ToolResult {
  let topic: string | null = null;
  try {
    const a = checkArgs("about_data", args, ["topic"]);
    if (a.topic !== undefined) {
      if (typeof a.topic !== "string") throw new Error("topic must be a string: a kind of data or a tool name.");
      if (a.topic.length > 128) throw new Error("topic must be a source id or a tool name, 128 characters at most.");
      topic = trim(a.topic).toLowerCase() || null;
      if (topic === "all") topic = null;
    }
  } catch (e) {
    return errorResult(e instanceof Error ? e.message : String(e));
  }
  const repo = repoBase(config.repoUrl);
  const issues = `${repo}/issues`;
  const who = `Call about_betanyc for who built ${config.serverName} and how to reach them.`;
  const base = {
    server: { name: config.serverName, version: config.version },
    source_file: dsFileUrl(config),
    who_built_this: who,
    contact_email: null as string | null,
  };
  const catalog = {
    data_json: config.catalogUrls?.dataJson ?? null,
    croissant_json: config.catalogUrls?.croissantJson ?? null,
  };

  const loaded = loadDataSources(config);
  const parsed = loaded.kind === "ok" ? loaded.parsed : null;
  if (!parsed || !parsed.doc) {
    const why = loaded.kind === "missing"
      ? `${config.serverName} ${config.version} has no ${DATA_SOURCES_FILE} yet, so it cannot say source by source where its data comes from.`
      : loaded.kind === "unreadable"
        ? `${config.serverName} ${config.version} could not read its ${DATA_SOURCES_FILE} (${loaded.message}).`
        : `${config.serverName} ${config.version} has a ${DATA_SOURCES_FILE} that cannot be read (${parsed!.errors.map((e) => e.code).join(", ")}).`;
    const note = `${why} Each tool's own answer may name its source. Report a bug in this server or ask for a new feature: ${issues}. ${who}`;
    return textResult(note, { ...base, topic, topics: [], sources: [], catalog, left_out: [], note });
  }

  const doc = parsed.doc;
  base.contact_email = contactEmail(parsed);
  const usable = doc.sources.filter((s) => s.valid);
  const leftOut = leftOutSources(parsed);
  const topics = usable.map((s) => s.id!);
  let picked = usable;
  if (topic !== null) {
    picked = usable.filter((s) => s.id === topic);
    if (!picked.length) picked = usable.filter((s) => s.tools.some((t) => t.toLowerCase() === topic));
    if (!picked.length) {
      return errorResult(`No data topic or tool named ${JSON.stringify(topic)}. Topics: ${topics.join(", ") || "(none)"}. A tool name also works.`);
    }
  }

  // Corrections: anchors in DATA-SOURCES.json resolved against WHATS-CHANGED.md.
  const wcUrl = config.pageUrl ?? doc.server?.whats_changed_url ?? whatsChangedUrl(config);
  const wcLoaded = loadText(config);
  const wcEntries = new Map<string, Entry>();
  if (wcLoaded.kind === "ok") {
    for (const e of parseWhatsChanged(wcLoaded.text).entries) if (e.valid && !e.unreleased) wcEntries.set(e.anchor, e);
  }
  let unresolved = 0;

  const out = picked.map((s) => {
    const fresh = asOf(s, config, now, outcome);
    const corrections = s.corrections.map((anchor) => {
      const e = wcEntries.get(anchor);
      if (!e) unresolved++;
      return { date: e?.date ?? null, title: e?.title ?? null, url: `${wcUrl}#${anchor}` };
    });
    return {
      topic: s.id!,
      title: s.title!,
      what: s.what!,
      source: s.source_name!,
      publisher: s.publisher!.name!,
      source_url: s.source_url!,
      official: s.official!,
      figures_official: officialKind(s.official!, s.changes!.changed!, s.changes!.steps) === "published-as-is",
      how_gathered: s.how_gathered!,
      changed_by_betanyc: { changed: s.changes!.changed!, steps: s.changes!.steps, detail: s.changes!.detail },
      ...fresh,
      update_frequency: s.update_frequency,
      coverage: { ...s.coverage! } as { start: string | null; end: string | null; geography: string; known_gaps: string[] },
      terms: { ...s.terms! },
      verify_at: s.verify_at!,
      report_errors: {
        in_the_data: s.report_errors!.upstream_url!,
        in_the_data_email: s.report_errors!.upstream_email,
        in_the_data_name: routeIsBetanyc(s.report_errors!.upstream_url!) ? "BetaNYC" : (s.report_errors!.upstream_name ?? s.publisher!.name!),
        in_the_data_handled_by: (routeIsBetanyc(s.report_errors!.upstream_url!) ? "betanyc" : "publisher") as "betanyc" | "publisher",
        in_these_figures: officialKind(s.official!, s.changes!.changed!, s.changes!.steps) === "published-as-is" ? null : issues,
        in_this_server: issues,
      },
      tools: s.tools,
      caveats: s.caveats,
      corrections,
    };
  });

  const notes: string[] = [];
  const bad = doc.sources.length - usable.length;
  const newer = leftOut.filter((l) => l.reason === "newer-feature");
  if (newer.length) {
    notes.push(`${plural(newer.length, "source")} (${newer.map((l) => l.topic ?? "unnamed").join(", ")}) ${newer.length === 1 ? "uses" : "use"} a feature newer than this server's shared module (${SHARED_MODULE_VERSION}), so ${newer.length === 1 ? "it is" : "they are"} not shown; the server needs a newer copy of betanyc-tools.ts. Full file: ${base.source_file}`);
  }
  const other = bad - newer.length;
  if (other > 0) notes.push(`${plural(other, "source")} in ${DATA_SOURCES_FILE} ${other === 1 ? "has" : "have"} errors and ${other === 1 ? "is" : "are"} left out. Full file: ${base.source_file}`);
  if (!usable.length && !bad) notes.push(`${DATA_SOURCES_FILE} lists no sources yet.`);
  if (unresolved) notes.push(`${plural(unresolved, "correction")} could not be found in WHATS-CHANGED.md; the links still point where the entry should be.`);
  const note = notes.length ? notes.join(" ") : null;

  const head = [
    topic === null
      ? `Where the data in ${config.serverName} ${config.version} comes from: ${plural(out.length, "source")}.`
      : `Where the data in ${config.serverName} ${config.version} comes from, for '${topic}'.`,
    "Each source gives one of three answers on whether it is official. Only \"Publisher: … BetaNYC did not modify it\" is an official record. Data BetaNYC modified or produced is not. Repeat the answer when you use the data.",
    `Full list: ${base.source_file}`,
  ];
  const blocks = out.map((s, i) => {
    const lines = [
      `${s.title} [topic: ${s.topic}]`,
      `What it is: ${s.what}`,
      officialWording({
        official: s.official, changed: s.changed_by_betanyc.changed, steps: s.changed_by_betanyc.steps,
        publisher: s.publisher, publisherUrl: picked[i].publisher!.url ?? null, sourceName: s.source, sourceUrl: s.source_url,
      }),
      `How it is gathered: ${s.how_gathered}`,
      s.changed_by_betanyc.changed
        ? `Modified by BetaNYC (${s.changed_by_betanyc.steps.join(", ")}): ${s.changed_by_betanyc.detail}`
        : "Modified by BetaNYC: no, passed on as published.",
      `How current on this server: ${s.as_of}` + (s.update_frequency ? ` (the source updates: ${s.update_frequency})` : ""),
      `Covers: ${s.coverage.geography}` +
        (s.coverage.start || s.coverage.end ? `, ${s.coverage.start ?? "the beginning"} to ${s.coverage.end ?? "now"}` : "") + ".",
    ];
    for (const g of s.coverage.known_gaps) lines.push(`Known gap: ${g}`);
    for (const c of s.caveats) lines.push(`Caveat: ${c}`);
    const t = s.terms;
    const termBits = [t.license_name, t.license_url, t.terms_url ? `terms: ${t.terms_url}` : null].filter(Boolean);
    if (termBits.length) lines.push(`Terms of use: ${termBits.join(", ")}`);
    if (t.credit_line) lines.push(`Credit line: ${t.credit_line}`);
    lines.push(`Check a figure at the source: ${s.verify_at}`);
    const re = s.report_errors;
    const email = re.in_the_data_email ? ` (${re.in_the_data_email})` : "";
    lines.push(
      (re.in_the_data_handled_by === "betanyc"
        ? `Report an error in the data to BetaNYC: ${re.in_the_data}`
        : re.in_these_figures
          ? `Report an error in the data to BetaNYC: ${re.in_these_figures}; an error in the original records to ${re.in_the_data_name}: ${re.in_the_data}${email}`
          : `Report an error in the data to ${re.in_the_data_name}: ${re.in_the_data}${email}`) +
        `. Report a bug in this server or ask for a new feature: ${re.in_this_server}`,
    );
    if (s.tools.length) lines.push(`Tools that use it: ${s.tools.join(", ")}`);
    for (const c of s.corrections) lines.push(`Correction: ${c.date ? `${c.date}: ` : ""}${c.title ?? "(entry not found)"} ${c.url}`);
    return lines.join("\n");
  });
  const contactLine = base.contact_email ? `Questions or error reports about this data, to BetaNYC: ${base.contact_email}` : "";
  const tail = [catalog.data_json ? `Catalog (DCAT-US 3.0): ${catalog.data_json}` : "", catalog.croissant_json ? `Croissant: ${catalog.croissant_json}` : "", contactLine, who]
    .filter(Boolean).join("\n");
  const text = [head.join("\n"), ...blocks, tail, note ?? ""].filter(Boolean).join("\n\n");
  return textResult(text, { ...base, topic, topics, sources: out, catalog, left_out: leftOut, note });
}

export const BETANYC_TOOLS: readonly ToolDefinition[] = [WHATS_CHANGED_TOOL, ABOUT_BETANYC_TOOL, ABOUT_DATA_TOOL];
export const BETANYC_TOOL_NAMES: readonly string[] = BETANYC_TOOLS.map((t) => t.name);

/** Wire the three tools into a server. Throws at startup on a bad config, so a mistake shows
 * when the server starts, not when a user calls the tool.
 *
 *   const betanyc = createBetanycTools({ serverName, version, repoUrl,
 *     whatsChangedPath: new URL("../WHATS-CHANGED.md", import.meta.url),
 *     dataSourcesPath: new URL("../DATA-SOURCES.json", import.meta.url) });
 *   export const TOOLS = [ ...existingTools, ...betanyc.tools ];
 *   new Server({ name, version }, { capabilities: { tools: {} }, instructions: `${own} ${betanyc.instructions}` });
 *   // first line of callTool():
 *   if (betanyc.handles(name)) return betanyc.call(name, args);
 */
export function createBetanycTools(config: BetanycServerConfig): {
  tools: ToolDefinition[];
  instructions: string;
  handles: (name: string) => boolean;
  call: (name: string, args: unknown) => ToolResult;
  /** Like call, but awaits async freshness hooks. Use it when any hook is async. */
  callAsync: (name: string, args: unknown) => Promise<ToolResult>;
} {
  const problems: string[] = [];
  if (!config.serverName?.trim()) problems.push("serverName is empty");
  if (!config.version?.trim()) problems.push("version is empty");
  if (!/^https:\/\/github\.com\/[^/\s]+\/[^/\s]+\/?$/.test(config.repoUrl ?? "")) {
    problems.push(`repoUrl must look like https://github.com/BetaNYC/<repo> (got ${JSON.stringify(config.repoUrl)})`);
  }
  if (config.whatsChangedPath === undefined && config.whatsChangedText === undefined) {
    problems.push("give whatsChangedPath or whatsChangedText");
  }
  // A readable DATA-SOURCES.json must describe this server, and link corrections to the same
  // What's changed page the server uses, or about_data and data.json would disagree.
  let topics: string[] = [];
  const ds = loadDataSources(config);
  if (ds.kind === "ok") {
    const doc = ds.parsed.doc;
    const server = doc?.server;
    if (server) {
      if (typeof server.repository === "string" && repoBase(server.repository) !== repoBase(config.repoUrl ?? "")) {
        problems.push(`${DATA_SOURCES_FILE} server.repository is ${server.repository}, but repoUrl is ${config.repoUrl}`);
      }
      if ((server.whats_changed_url ?? null) !== (config.pageUrl ?? null)) {
        problems.push(`${DATA_SOURCES_FILE} server.whats_changed_url (${server.whats_changed_url ?? "not set"}) must equal pageUrl (${config.pageUrl ?? "not set"})`);
      }
    }
    topics = (doc?.sources ?? []).filter((s) => s.valid).map((s) => s.id!);
  }
  for (const [id, reason] of Object.entries(config.unavailableSources ?? {})) {
    if (typeof reason !== "string" || !trim(reason)) problems.push(`unavailableSources.${id} needs a reason`);
    else if (ds.kind === "ok" && !topics.includes(id)) problems.push(`unavailableSources names ${id}, which is not a source in ${DATA_SOURCES_FILE}`);
  }
  if (problems.length) throw new Error(`betanyc-tools: ${problems.join("; ")}`);
  const tools = BETANYC_TOOLS.map((t) => ({ ...t }));
  if (topics.length) {
    const i = tools.findIndex((t) => t.name === "about_data");
    tools[i] = { ...tools[i], description: `${tools[i].description} Topics on this server: ${topics.join(", ")}.` };
  }
  return {
    tools,
    instructions: BETANYC_INSTRUCTIONS,
    handles: (name) => BETANYC_TOOL_NAMES.includes(name),
    call: (name, args) =>
      name === "whats_changed" ? handleWhatsChanged(config, args)
        : name === "about_betanyc" ? handleAboutBetanyc(config, args)
          : name === "about_data" ? handleAboutData(config, args)
            : errorResult(`Unknown tool: ${name}`),
    callAsync: async (name, args) =>
      name === "about_data" ? handleAboutDataAsync(config, args)
        : name === "whats_changed" ? handleWhatsChanged(config, args)
          : name === "about_betanyc" ? handleAboutBetanyc(config, args)
            : errorResult(`Unknown tool: ${name}`),
  };
}

// --------------------------------------------------------------------------- helpers for a server's own tools (1.5.0)

// Small helpers so every BetaNYC server labels, sources and fails its OWN tools the same way.
// None of them change the three shared tools above.

/** The annotations every BetaNYC tool carries: it only reads (readOnlyHint: true), and says
 * whether it reaches outside (openWorldHint: true when it calls a live outside API, false when
 * it answers from bundled or local data). For the SDK's high-level registerTool:
 *   server.registerTool("search_spending", { ..., annotations: readOnlyAnnotations(true, "Search spending") }, cb) */
export function readOnlyAnnotations(openWorld: boolean, title?: string): ToolAnnotations {
  if (typeof openWorld !== "boolean") throw new Error("readOnlyAnnotations: openWorld must be true or false");
  return { ...(title ? { title } : {}), readOnlyHint: true, openWorldHint: openWorld };
}

type Annotatable = { name: string; title?: string; annotations?: ToolAnnotations };

/** A tool's title for people: its own title, else its name with "_" as spaces, capitalized. */
function titleFor(t: Annotatable): string {
  const s = t.title?.trim() || t.name.replace(/_/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** A copy of a server's tool list with `annotations` filled for the low-level TOOLS array:
 * readOnlyHint true, the openWorldHint the caller gives, and a title when there is none.
 * `openWorld` is one value for every tool, or one per tool name. A tool that already declares
 * both hints (the three shared tools do) needs no entry and passes through as is. Throws on a
 * tool with no openWorld value, a name the list does not have, a tool that declares
 * readOnlyHint false, or an openWorldHint that disagrees with the caller's.
 *   export const TOOLS = annotateTools([...domainTools, ...betanyc.tools],
 *     { search_bills: false, search_legislation_live: true }); */
export function annotateTools<T extends Annotatable>(
  tools: readonly T[],
  openWorld: boolean | Readonly<Record<string, boolean>>,
): (T & { annotations: ToolAnnotations })[] {
  const per = typeof openWorld === "boolean" ? null : openWorld;
  const problems: string[] = [];
  if (per) {
    const names = new Set(tools.map((t) => t.name));
    for (const k of Object.keys(per)) if (!names.has(k)) problems.push(`${k} is not in the tool list`);
  }
  const out = tools.map((t) => {
    const a = t.annotations ?? {};
    const given = per ? (Object.hasOwn(per, t.name) ? per[t.name] : undefined) : openWorld;
    if (a.readOnlyHint === false) problems.push(`${t.name} declares readOnlyHint false`);
    if (given !== undefined && typeof given !== "boolean") problems.push(`${t.name}: openWorld must be true or false`);
    if (given !== undefined && typeof a.openWorldHint === "boolean" && a.openWorldHint !== given) {
      problems.push(`${t.name} declares openWorldHint ${a.openWorldHint}, but ${given} was given`);
    }
    const hint = typeof a.openWorldHint === "boolean" ? a.openWorldHint : given;
    if (given === undefined && typeof hint !== "boolean") problems.push(`${t.name} has no openWorld value`);
    return { ...t, annotations: { ...a, title: a.title || titleFor(t), readOnlyHint: true, openWorldHint: hint as boolean } };
  });
  if (problems.length) throw new Error(`annotateTools: ${problems.join("; ")}`);
  return out;
}

/** For each MCP's own test suite: throws, naming them, when a tool lacks readOnlyHint or
 * openWorldHint (a boolean each). Takes the TOOLS array, or tools/list from an SDK client.
 *   test("every tool is annotated", () => assertEveryToolAnnotated(TOOLS)); */
export function assertEveryToolAnnotated(tools: readonly { name: string; annotations?: ToolAnnotations }[]): void {
  const bad = tools.flatMap((t) => {
    const a = t.annotations ?? {};
    const missing = [
      typeof a.readOnlyHint === "boolean" ? "" : "readOnlyHint",
      typeof a.openWorldHint === "boolean" ? "" : "openWorldHint",
    ].filter(Boolean);
    return missing.length ? [`${t.name} (no ${missing.join(" or ")})`] : [];
  });
  if (bad.length) throw new Error(`Tools without annotations: ${bad.join(", ")}. Use annotateTools() or readOnlyAnnotations().`);
}

export interface ProvenanceInput {
  /** The dataset or document's name, as in DATA-SOURCES.json source_name. */
  sourceName: string;
  /** Its publisher's full name. */
  publisher: string;
  /** A link a person can open: the dataset page, record page or document (http or https). */
  sourceUrl: string;
  /** "live": fetched from the source for this answer (as of = asOf, else now). "snapshot": a
   * copy built into or downloaded by the server (as of = the copy's date, required). */
  kind: "live" | "snapshot";
  /** An ISO 8601 date or date-time with a zone (isUsableAsOf). */
  asOf?: string | null;
}

/** The plain object half of a provenance block. Same field names as about_data's sources. */
export interface Provenance {
  source: string;
  publisher: string;
  source_url: string;
  as_of: string | null;
  /** "retrieved" (live), "snapshot" (a copy's date), or "unknown" (no usable date). */
  as_of_kind: "retrieved" | "snapshot" | "unknown";
}

/** The source block for one answer: who published the data, a link, and how current it is, as
 * a plain-text line and an object. A date that isUsableAsOf() rejects (garbled, or in the
 * future) is never passed on: it reads "as of: unknown". Throws on an empty name or publisher,
 * or a link that is not http(s), so a mistake shows in the server's tests.
 *   const p = provenance({ sourceName: "City Record Online", publisher: "NYC DCAS", sourceUrl, kind: "live" });
 *   return { content: [{ type: "text", text: `${body}\n\n${p.text}` }] }; */
export function provenance(input: ProvenanceInput, now: Date = new Date()): { text: string; provenance: Provenance } {
  const name = trim(input.sourceName ?? "");
  const publisher = trim(input.publisher ?? "");
  const url = trim(input.sourceUrl ?? "");
  if (!name || !publisher) throw new Error("provenance: sourceName and publisher are required");
  if (!/^https?:\/\/[^\s/?#]+[^\s]*$/i.test(url)) throw new Error(`provenance: sourceUrl must be an http(s) link (got ${JSON.stringify(input.sourceUrl)})`);
  if (input.kind !== "live" && input.kind !== "snapshot") throw new Error('provenance: kind must be "live" or "snapshot"');
  const raw = input.asOf ?? (input.kind === "live" ? now.toISOString() : null);
  const usable = isUsableAsOf(raw, now);
  const asOf = usable ? (raw as string) : null;
  const kind: Provenance["as_of_kind"] = !usable ? "unknown" : input.kind === "live" ? "retrieved" : "snapshot";
  const when = kind === "retrieved" ? `As of ${asOf} (fetched from the source for this answer).`
    : kind === "snapshot" ? `As of ${asOf} (the date of the copy this server answers from).`
      : "As of: unknown (this server has no usable date for it).";
  // No period after the link: some apps take it into the link.
  const text = `Source: ${builtFrom(name, publisher)}. ${when} Link: ${url}`;
  return { text, provenance: { source: name, publisher, source_url: url, as_of: asOf, as_of_kind: kind } };
}

/** Most characters of an upstream error body that toolError passes on. */
export const UPSTREAM_BODY_MAX = 500;

/** Lines that look like a JavaScript or Python stack frame. */
const STACK_LINE_RE = /^\s*(?:at\s+\S.*|File\s+".*",\s+line\s+\d+.*|Traceback \(most recent call last\):.*)$/;

function scrub(text: string, secrets: readonly string[]): string {
  let s = text.split(/\r?\n/).filter((l) => !STACK_LINE_RE.test(l)).join("\n");
  for (const v of secrets) s = s.split(v).join("[redacted]");
  return s;
}

/** An isError result from a plain sentence (what went wrong, what to try), plus an optional
 * upstream body cut to UPSTREAM_BODY_MAX characters. Stack-frame lines are dropped, and every
 * secret value given (an API key, a token; also its URL-encoded form) is replaced by
 * "[redacted]" in both, before the cut, so no part of a key survives it.
 *   catch (e) { return toolError("The Legistar API did not answer. Try again in a minute.",
 *     { upstreamBody: body, secrets: [process.env.LEGISTAR_TOKEN] }); } */
export function toolError(
  message: string,
  opts: { upstreamBody?: string | null; secrets?: readonly (string | null | undefined)[] } = {},
): ToolResult {
  const secrets = [...new Set((opts.secrets ?? []).flatMap((v) =>
    typeof v === "string" && v ? [v, encodeURIComponent(v)] : []))].sort((a, b) => b.length - a.length);
  const msg = trim(scrub(String(message ?? ""), secrets)) || "The tool failed.";
  const body = typeof opts.upstreamBody === "string" ? trim(scrub(opts.upstreamBody, secrets)) : "";
  if (!body) return errorResult(msg);
  const cp = [...body];
  const cut = cp.length > UPSTREAM_BODY_MAX ? `${cp.slice(0, UPSTREAM_BODY_MAX).join("")}… (cut at ${UPSTREAM_BODY_MAX} characters)` : body;
  return errorResult(`${msg}\nThe source said: ${cut}`);
}

/** The size, in characters, of a server's tools/list (JSON of its tools) plus its instructions:
 * what the model reads every turn. Each server's test caps it, and records any raise with a date
 * and reason (the nyc-311-mcp test/tool-size.test.mjs pattern; same measure, so its budget holds).
 *   assert.ok(toolListSize(TOOLS, INSTRUCTIONS) <= 47_000); */
export function toolListSize(tools: readonly object[], instructions = ""): number {
  return JSON.stringify(tools).length + instructions.length;
}
