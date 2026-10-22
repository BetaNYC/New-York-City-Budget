import { describe, expect, test } from "vitest";

import * as R from "../../src/review/queue.js";

const items = [
  { family: "capital_sd", fiscal_year: 2027, review_id: "a", severity: "warn", dollars: 10, pdf_page: 4, check_id: "C9", suggested_decision: "accepted_as_printed", suggested_note: "keep" },
  { family: "schedule_c", fiscal_year: 2027, review_id: "b", severity: "critical", dollars: 5, pdf_page: 9, check_id: "H8", suggested_decision: "" },
  { family: "terms", fiscal_year: 2027, review_id: "c", severity: "warn", dollars: 0, pdf_page: 2, check_id: "T7", suggested_decision: "accepted_as_printed" },
  { family: "capital_sd", fiscal_year: 2027, review_id: "d", severity: "warn", dollars: 900, pdf_page: 66, check_id: "C3", suggested_decision: "needs_info" },
];
const NOW = new Date("2026-10-21T08:00:00Z");

describe("the queue", () => {
  test("severity first, then dollars, largest first", () => {
    expect(R.sortQueue(items).map((i) => i.review_id)).toEqual(["b", "d", "a", "c"]);
  });
  test("filters by family, year, check, severity and open/decided", () => {
    const dec = { [R.itemKey(items[0])]: { decision: "accepted_as_printed" } };
    expect(R.filterQueue(items, { family: "capital_sd" }).map((i) => i.review_id)).toEqual(["a", "d"]);
    expect(R.filterQueue(items, { check_id: "T7" }).map((i) => i.review_id)).toEqual(["c"]);
    expect(R.filterQueue(items, { severity: "critical" }).map((i) => i.review_id)).toEqual(["b"]);
    expect(R.filterQueue(items, { state: "decided" }, dec).map((i) => i.review_id)).toEqual(["a"]);
    expect(R.filterQueue(items, { state: "open" }, dec)).toHaveLength(3);
    expect(R.filterQueue(items, { fiscal_year: 2026 })).toHaveLength(0);
    expect(R.progress(items, dec)).toEqual({ total: 4, decided: 1, committed: 0, open: 3, needs_info: 0 });
  });
});

describe("decision buttons", () => {
  const opts = { by: "Noel Hidalgo", now: NOW };
  test("keep as printed", () => {
    expect(R.decide("keep", items[0], { ...opts, note: "fine" })).toMatchObject({ decision: "accepted_as_printed", note: "fine", decided_by: "Noel Hidalgo", decided_at: "2026-10-21T08:00:00.000Z" });
  });
  test("accept suggestion copies the suggested decision, and needs one", () => {
    expect(R.decide("suggestion", items[3], opts).decision).toBe("needs_info");
    expect(R.decide("suggestion", items[0], opts).note).toBe("Suggestion accepted: keep");
    expect(() => R.decide("suggestion", items[1], opts)).toThrow(/no suggested decision/);
  });
  test("accepting a page-image suggestion keeps what the page shows in the note (#209)", () => {
    const it = { family: "schedule_c", fiscal_year: 2023, review_id: "42eba5fef74a", severity: "warn", check_id: "H5.anchors",
      suggested_decision: "read_from_page_image", suggested_note: 'page shows ein: "87-0753479" (text layer "87 0753479")' };
    const d = R.decide("suggestion", it, opts);
    expect(d.decision).toBe("read_from_page_image");
    // code/page_image.py reads the value from anywhere in the note.
    expect(d.note).toMatch(/page shows ein: "87-0753479"/);
    expect(R.suggestionLabel(it)).toBe("Accept suggestion → use what the page shows");
  });
  test("change to… records parser_bug with the value", () => {
    expect(R.decide("change", items[0], { ...opts, change: "HR CC0168", note: "see p.47" })).toMatchObject({ decision: "parser_bug", note: "change to: HR CC0168 — see p.47" });
    expect(() => R.decide("change", items[0], opts)).toThrow(/change to/);
  });
  test("a name is required", () => {
    expect(() => R.decide("keep", items[0], { now: NOW })).toThrow(/name/);
  });
});

describe("rows decided in the repository are closed", () => {
  const committed = { ...items[1], decision: "source_error", decision_note: "PDF self-error" };
  const all = [items[0], committed, items[2], items[3]];
  test("they count as decided and show their decision", () => {
    expect(R.isCommitted(committed)).toBe(true);
    expect(R.decisionOf(committed, {})).toEqual({ decision: "source_error", note: "PDF self-error", committed: true });
    expect(R.filterQueue(all, { state: "open" }).map((i) => i.review_id)).toEqual(["a", "c", "d"]);
    expect(R.progress(all, {})).toMatchObject({ decided: 1, committed: 1, open: 3 });
  });
  test("a browser decision never overrides or re-exports them", () => {
    const dec = { [R.itemKey(committed)]: R.decide("keep", committed, { by: "X", now: NOW }) };
    expect(R.decisionOf(committed, dec).decision).toBe("source_error");
    expect(R.toDecisionsCsv(all, dec, "schedule_c", 2027)).toBe("review_id,decision,note,decided_by,decided_at\n");
  });
});

describe("buttons say what they record, and why they are off", () => {
  test("Accept suggestion names its decision", () => {
    expect(R.suggestionLabel({ suggested_decision: "accepted_as_printed" })).toBe("Accept suggestion → keep as printed");
    expect(R.suggestionLabel({ suggested_decision: "source_error" })).toBe("Accept suggestion → source error");
    expect(R.suggestionLabel({ suggested_decision: "needs_info" })).toBe("Accept suggestion → needs more information");
    expect(R.suggestionLabel({ suggested_decision: "" })).toBe("Accept suggestion (none for this item)");
  });
  test("no name: every button is off, with the reason; then each button's own reason", () => {
    for (const k of ["keep", "suggestion", "needs_info", "change"]) expect(R.blockedReason(k, items[0], { by: " " })).toMatch(/Enter your name first/);
    expect(R.blockedReason("keep", items[0], { by: "Noel" })).toBeNull();
    expect(R.blockedReason("suggestion", items[1], { by: "Noel" })).toMatch(/no suggested decision/);
    expect(R.blockedReason("change", items[0], { by: "Noel" })).toMatch(/right value/);
    expect(R.blockedReason("change", items[0], { by: "Noel", change: "X" })).toBeNull();
  });
  test("the store key and the decision shape do not change (saved decisions survive)", () => {
    expect(R.STORE_KEY).toBe("nycb-review-decisions-v1");
    expect(R.NAME_KEY).toBe("nycb-review-reviewer");
    expect(Object.keys(R.decide("keep", items[0], { by: "N", now: NOW })).sort()).toEqual(["decided_at", "decided_by", "decision", "family", "fiscal_year", "note", "review_id"]);
  });
});

describe("decisions CSV", () => {
  const dec = {
    [R.itemKey(items[0])]: R.decide("keep", items[0], { by: "Noel", note: 'has, comma and "quotes"', now: NOW }),
    [R.itemKey(items[3])]: R.decide("needs_info", items[3], { by: "Noel", now: NOW }),
    [R.itemKey(items[1])]: R.decide("keep", items[1], { by: "Noel", now: NOW }),
  };
  test("export: the exact header, one family and year, queue order, RFC 4180 quoting", () => {
    const csv = R.toDecisionsCsv(items, dec, "capital_sd", 2027);
    expect(csv).toBe(
      "review_id,decision,note,decided_by,decided_at\n" +
        "d,needs_info,,Noel,2026-10-21T08:00:00.000Z\n" +
        'a,accepted_as_printed,"has, comma and ""quotes""",Noel,2026-10-21T08:00:00.000Z\n'
    );
    expect(R.toDecisionsCsv(items, {}, "terms", 2027)).toBe("review_id,decision,note,decided_by,decided_at\n");
  });
  test("import round-trips an export, and reports what it cannot take", () => {
    const csv = R.toDecisionsCsv(items, dec, "capital_sd", 2027) + "zzz,accepted_as_printed,,Noel,2026-10-21\nc,fixed,,Noel,2026-10-21\n";
    const { decisions, errors } = R.importDecisions(csv, items);
    expect(Object.keys(decisions).sort()).toEqual([R.itemKey(items[0]), R.itemKey(items[3])].sort());
    expect(decisions[R.itemKey(items[0])].note).toBe('has, comma and "quotes"');
    expect(errors).toHaveLength(2);
    expect(R.importDecisions("a,b\n1,2\n", items).errors[0]).toMatch(/header/);
  });
  test("parseCsv handles CRLF, a BOM and quoted line breaks", () => {
    expect(R.parseCsv('﻿a,b\r\n"x\ny",2\r\n')).toEqual([["a", "b"], ["x\ny", "2"]]);
  });
});

describe("the browser store", () => {
  test("load and save, and survive junk", () => {
    const m = new Map();
    const storage = { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) };
    expect(R.loadStore(storage)).toEqual({});
    R.saveStore(storage, { x: { decision: "needs_info" } });
    expect(R.loadStore(storage)).toEqual({ x: { decision: "needs_info" } });
    m.set(R.STORE_KEY, "{not json");
    expect(R.loadStore(storage)).toEqual({});
  });
});
