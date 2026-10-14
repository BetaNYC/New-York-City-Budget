/**
 * enrich-crosswalk.mjs — add the adopting City Council session to each confirmed
 * crosswalk row, so get_legistar_link can emit a WORKING Legistar link.
 *
 * WHY: the crosswalk's stored `legistar_url`
 * (LegislationDetail.aspx?ID={MatterId}&GUID={MatterGuid}) resolves to "Invalid
 * parameters!" — NYC runs two Legistar backends and the OData MatterId/GUID are
 * NOT the public website's ids, with no formula between them (see issue #31).
 * The *meeting* URL scheme, however, DOES accept the OData EventId:
 *   https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID={EventId}&GID=61
 * (GID=61 verified term-stable, 2015 & 2026 — issue #31). So we precompute, per
 * confirmed row, the EventId of the meeting where the matter was adopted.
 *
 * SOURCE OF THE EventId: the matter's Legistar OData history. The adopting event
 * is the history row that is the final City Council adoption:
 *   MatterHistoryActionName === "Approved, by Council"
 *   MatterHistoryActionBodyName === "City Council"
 *   MatterHistoryPassedFlag === 1
 * → its MatterHistoryEventId. (Predicate verified live 2026-07-16 against
 * MatterId 79146 → EventId 22592 and MatterId 54745 → EventId 14178: exactly one
 * matching history row each. See test/fixtures/histories-*.json.)
 *
 * Legistar OData WebAPI (endpoints/fields reused from the sibling nyc-council-mcp
 * `src/legistar.ts`, which is exercised live in production):
 *   base:      https://webapi.legistar.com/v1/nyc
 *   auth:      ?token=<LEGISTAR_TOKEN>   (free NYC read token)
 *   matter:    GET /matters?$filter=MatterFile eq '<file>'&$top=1   → [{ MatterId, ... }]
 *   histories: GET /matters/{MatterId}/histories?$orderby=MatterHistoryActionDate desc
 *
 * IDEMPOTENT & RESUMABLE: rows already carrying adopting_event_id are skipped, and
 * the CSV is rewritten after every newly-enriched matter — a killed run resumes
 * where it stopped. Throttled ~1 req/sec; 429s are honored with backoff.
 *
 * Usage:
 *   LEGISTAR_TOKEN=... node scripts/enrich-crosswalk.mjs [--csv <path>] [--limit N] [--throttle ms]
 * Register a free token: https://council.nyc.gov/legislation/api/
 */
import { parse } from "csv-parse/sync";
import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CSV = join(__dirname, "..", "..", "data", "combined", "legistar_crosswalk.csv");

const BASE_URL = "https://webapi.legistar.com/v1/nyc";
export const MEETING_GID = "61"; // verified term-stable constant, issue #31

// New columns appended to the crosswalk (order stable for a clean diff).
export const ADOPTING_COLUMNS = [
  "adopting_event_id",
  "adopting_body",
  "adopting_action",
  "adopting_datetime",
];

/** OData string-literal escape: single quotes are doubled (no URL-encoding — URL does that). */
function odataString(v) {
  return String(v).replace(/'/g, "''");
}

/**
 * Pick the final City Council adoption event from a matter's Legistar histories.
 * Returns { event_id, body, action, datetime } or null when the matter has no
 * such event (e.g. filed, or committee-only) — a null link, never a wrong one.
 * Pure: unit-tested against captured fixtures.
 */
export function pickAdoptingEvent(histories) {
  const hits = (histories ?? []).filter(
    (h) =>
      h.MatterHistoryActionName === "Approved, by Council" &&
      h.MatterHistoryActionBodyName === "City Council" &&
      h.MatterHistoryPassedFlag === 1 &&
      h.MatterHistoryEventId != null
  );
  if (hits.length === 0) return null;
  // histories arrive ordered by action date desc; the most recent adoption is the
  // authoritative one if a matter were ever re-adopted. Verified: exactly one hit.
  const h = hits[0];
  return {
    event_id: h.MatterHistoryEventId,
    body: h.MatterHistoryActionBodyName,
    action: h.MatterHistoryActionName,
    datetime: h.MatterHistoryActionDate ?? "",
  };
}

/** Full working meeting URL for an adopting event id (mirror of db.ts buildMeetingUrl, for reporting). */
export function meetingUrl(eventId) {
  return eventId
    ? `https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID=${eventId}&GID=${MEETING_GID}`
    : null;
}

async function legistarFetch(url, { retries = 3 } = {}) {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(url);
    if (res.status === 429 && attempt < retries) {
      const wait = Number(res.headers.get("retry-after")) * 1000 || 2000 * (attempt + 1);
      console.error(`  429 rate-limited; backing off ${wait}ms`);
      await sleep(wait);
      continue;
    }
    if (!res.ok) throw new Error(`Legistar ${res.status} ${res.statusText}`);
    return res.json();
  }
}

async function getMatterId(token, fileNumber) {
  const u = new URL(`${BASE_URL}/matters`);
  u.searchParams.set("token", token);
  u.searchParams.set("$filter", `MatterFile eq '${odataString(fileNumber)}'`);
  u.searchParams.set("$top", "1");
  const rows = await legistarFetch(u.toString());
  return rows.length ? rows[0].MatterId : null;
}

async function getHistories(token, matterId) {
  const u = new URL(`${BASE_URL}/matters/${matterId}/histories`);
  u.searchParams.set("token", token);
  u.searchParams.set("$orderby", "MatterHistoryActionDate desc");
  return legistarFetch(u.toString());
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** RFC4180 field: quote if it contains comma, quote, CR or LF; double internal quotes. */
function csvField(v) {
  const s = v == null ? "" : String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function toCsv(header, rows) {
  const lines = [header.map(csvField).join(",")];
  for (const r of rows) lines.push(header.map((h) => csvField(r[h])).join(","));
  return lines.join("\r\n") + "\r\n"; // CRLF + trailing newline, matching the source file
}

async function main() {
  const flag = (name, def) => {
    const i = process.argv.indexOf(name);
    return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : def;
  };
  const csvPath = flag("--csv", DEFAULT_CSV);
  const limit = Number(flag("--limit", "0")) || Infinity;
  const throttle = Number(flag("--throttle", "1100"));
  const token = process.env.LEGISTAR_TOKEN;
  if (!token) {
    console.error("FATAL: LEGISTAR_TOKEN is not set. Register a free token at https://council.nyc.gov/legislation/api/");
    process.exit(1);
  }

  const rows = parse(readFileSync(csvPath, "utf8"), { columns: true, skip_empty_lines: true });
  const header = [...Object.keys(rows[0])];
  for (const c of ADOPTING_COLUMNS) if (!header.includes(c)) header.push(c);
  for (const r of rows) for (const c of ADOPTING_COLUMNS) if (!(c in r)) r[c] = "";

  const stats = { confirmed: 0, alreadyDone: 0, enriched: 0, noAdoptingEvent: 0, unresolved: 0, skippedStatus: 0 };
  const deferred = [];
  const matterCache = new Map(); // matter number -> { event_id, body, action, datetime } | null | undefined(error)

  let processed = 0;
  for (const r of rows) {
    if (r.status !== "confirmed") {
      stats.skippedStatus++;
      continue;
    }
    stats.confirmed++;
    if (r.adopting_event_id) {
      stats.alreadyDone++;
      continue;
    }
    const num = (r.legistar_matter_number || "").trim();
    if (!num) {
      stats.unresolved++;
      deferred.push(`${r.fiscal_year} ${r.document_type}: no matter number`);
      continue;
    }
    if (processed >= limit) break;

    let result = matterCache.get(num);
    if (result === undefined) {
      try {
        const matterId = await getMatterId(token, num);
        await sleep(throttle);
        if (matterId == null) {
          matterCache.set(num, "ERR:not-found");
          result = "ERR:not-found";
        } else {
          const hist = await getHistories(token, matterId);
          await sleep(throttle);
          result = pickAdoptingEvent(hist);
          matterCache.set(num, result);
          console.error(
            `  ${num} (matter ${matterId}) -> ${result ? `event ${result.event_id} (${result.datetime})` : "NO adopting City Council event"}`
          );
        }
      } catch (e) {
        matterCache.set(num, `ERR:${e.message}`);
        result = `ERR:${e.message}`;
      }
      processed++;
    }

    if (typeof result === "string") {
      stats.unresolved++;
      deferred.push(`${r.fiscal_year} ${r.document_type} ${num}: ${result}`);
      continue;
    }
    if (result === null) {
      stats.noAdoptingEvent++;
      deferred.push(`${r.fiscal_year} ${r.document_type} ${num}: no City Council adoption event`);
      continue;
    }
    r.adopting_event_id = String(result.event_id);
    r.adopting_body = result.body;
    r.adopting_action = result.action;
    r.adopting_datetime = result.datetime;
    stats.enriched++;
    writeFileSync(csvPath, toCsv(header, rows)); // write-after-each → resumable
  }

  console.error("\n=== enrichment summary ===");
  console.error(JSON.stringify(stats, null, 2));
  if (deferred.length) {
    console.error(`\ndeferred / unresolved (${deferred.length}):`);
    for (const d of deferred) console.error(`  - ${d}`);
  }
}

// Only run when invoked directly (not when imported by tests).
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
