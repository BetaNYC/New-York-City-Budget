/**
 * Tests for the Legistar adopting-session link (issue #31).
 *
 * Three layers:
 *   1. buildMeetingUrl (pure) — the OData EventId → working MeetingDetail URL.
 *   2. pickAdoptingEvent (pure) — matter history → adopting City Council event,
 *      asserted against REAL captured Legistar payloads (test/fixtures/), so the
 *      extraction is checked against the documented wire shape, not a guess.
 *   3. get_legistar_link end-to-end through the MCP protocol — emits the working
 *      MeetingDetail link and never the broken LegislationDetail.aspx?ID= link.
 */
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { server } from "../dist/server.js";
import { buildMeetingUrl } from "../dist/db.js";
import { pickAdoptingEvent } from "../scripts/enrich-crosswalk.mjs";

const FIX = join(dirname(fileURLToPath(import.meta.url)), "fixtures");
const fixture = (matterId) =>
  JSON.parse(readFileSync(join(FIX, `histories-${matterId}.json`), "utf8"));

// ---- 1. buildMeetingUrl -----------------------------------------------------

test("buildMeetingUrl builds the working MeetingDetail URL from an EventId", () => {
  assert.equal(
    buildMeetingUrl(22592),
    "https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID=22592&GID=61"
  );
  // Stored crosswalk value is a string — must work identically.
  assert.equal(
    buildMeetingUrl("14178"),
    "https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID=14178&GID=61"
  );
});

test("buildMeetingUrl returns null for empty/absent EventId (no link, never a wrong one)", () => {
  assert.equal(buildMeetingUrl(""), null);
  assert.equal(buildMeetingUrl(null), null);
  assert.equal(buildMeetingUrl(undefined), null);
  assert.equal(buildMeetingUrl("   "), null);
});

// ---- 2. pickAdoptingEvent against real captured payloads ---------------------

test("pickAdoptingEvent picks EventId 22592 for Res 0540-2026 (matter 79146)", () => {
  const ev = pickAdoptingEvent(fixture(79146));
  assert.equal(ev.event_id, 22592);
  assert.equal(ev.body, "City Council");
  assert.equal(ev.action, "Approved, by Council");
  assert.equal(ev.datetime, "2026-06-30T17:05:00");
});

test("pickAdoptingEvent picks EventId 14178 for Res 0763-2015 (matter 54745)", () => {
  const ev = pickAdoptingEvent(fixture(54745));
  assert.equal(ev.event_id, 14178);
  assert.equal(ev.datetime, "2015-06-26T18:00:00");
});

test("pickAdoptingEvent returns null when no City Council adoption event exists", () => {
  assert.equal(pickAdoptingEvent([]), null);
  assert.equal(pickAdoptingEvent(null), null);
  // A committee-only approval must NOT be treated as the adoption.
  assert.equal(
    pickAdoptingEvent([
      {
        MatterHistoryActionName: "Approved by Committee",
        MatterHistoryActionBodyName: "Committee on Finance",
        MatterHistoryPassedFlag: 1,
        MatterHistoryEventId: 22597,
      },
    ]),
    null
  );
});

// ---- 3. get_legistar_link end-to-end ----------------------------------------

let client;
before(async () => {
  const [c, s] = InMemoryTransport.createLinkedPair();
  await server.connect(s);
  client = new Client({ name: "legistar-link-test", version: "0" }, { capabilities: {} });
  await client.connect(c);
});
after(async () => {
  await client.close();
});

async function callText(name, args = {}) {
  const res = await client.callTool({ name, arguments: args });
  assert.ok(!res.isError, `${name} error: ${JSON.stringify(res.content)}`);
  return res.content.map((c) => c.text).join("\n");
}

test("get_legistar_link emits the working MeetingDetail link, not the broken LegislationDetail link", async () => {
  // FY2027 Schedule C = Res 0540-2026, enriched to adopting EventId 22592.
  const out = await callText("get_legistar_link", {
    fiscal_year: 2027,
    document_type: "schedule_c",
  });
  assert.match(
    out,
    /MeetingDetail\.aspx\?LEGID=22592&GID=61/,
    "expected the working adopting-meeting link"
  );
  assert.doesNotMatch(
    out,
    /LegislationDetail\.aspx\?ID=/,
    "the broken bill-detail URL must not be surfaced as a citation"
  );
  assert.match(out, /adopting session: City Council/);
});

test("no crosswalk row anywhere surfaces the broken LegislationDetail.aspx?ID= link", async () => {
  // Sweep every fiscal year; the broken scheme must never appear in tool output.
  for (let fy = 2008; fy <= 2027; fy++) {
    const res = await client.callTool({
      name: "get_legistar_link",
      arguments: { fiscal_year: fy },
    });
    const out = res.content.map((c) => c.text).join("\n");
    assert.doesNotMatch(
      out,
      /LegislationDetail\.aspx\?ID=/,
      `FY${fy} output leaked the broken LegislationDetail link`
    );
  }
});
