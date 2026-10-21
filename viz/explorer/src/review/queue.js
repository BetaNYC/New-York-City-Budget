/**
 * The review screen's logic, as pure functions: the queue, its order and filters, what each
 * decision button records, and the decisions CSV (export and import).
 *
 * A decisions file is a person's answers to a family's review queue (PLAN.md §5.3), in exactly
 * the shape of research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv:
 *   review_id,decision,note,decided_by,decided_at
 * The site is static, so decisions live in this browser (localStorage) until the reviewer exports
 * the file and commits it; code/validate_review_decisions.py checks it.
 */

export const DECISIONS_HEADER = ["review_id", "decision", "note", "decided_by", "decided_at"];
export const DECISIONS = ["source_error", "parser_bug", "accepted_as_printed", "needs_info"];
export const DECISION_LABEL = {
  accepted_as_printed: "kept as printed",
  source_error: "the PDF's own error",
  parser_bug: "our reading is wrong",
  needs_info: "needs more information",
};
/** What a decision records, as a button says it ("Accept suggestion → keep as printed"). */
export const DECISION_ACTION = {
  accepted_as_printed: "keep as printed",
  source_error: "source error",
  parser_bug: "our reading is wrong",
  needs_info: "needs more information",
};

/** The "Accept suggestion" button's label: it names the decision it will record. */
export const suggestionLabel = (item) =>
  DECISIONS.includes(item?.suggested_decision) ? `Accept suggestion → ${DECISION_ACTION[item.suggested_decision]}` : "Accept suggestion (none for this item)";

/**
 * Why a decision button cannot be used yet, before it is clicked (null = it can). The name comes
 * first: every decision records it as decided_by.
 */
export function blockedReason(kind, item, { by = "", change = "" } = {}) {
  if (!String(by).trim()) return "Enter your name first (at the top of the queue): it is recorded as decided_by.";
  if (kind === "suggestion" && !DECISIONS.includes(item?.suggested_decision)) return "This item has no suggested decision.";
  if (kind === "change" && !String(change).trim()) return "Type the right value first.";
  return null;
}

const SEVERITY_RANK = { critical: 0, warn: 1 };

export const itemKey = (it) => `${it.family}|${it.fiscal_year}|${it.review_id}`;

/**
 * Decided in the repository: the family's committed decisions file already answers this row (its
 * review CSV carries the decision, so pdf_review.decision is set). Such a row is closed: the
 * screen shows the recorded decision and takes no new one.
 */
export const isCommitted = (it) => DECISIONS.includes(it.decision);

/** The decision that stands for a row: the committed one, else this browser's. */
export const decisionOf = (it, decisions) =>
  isCommitted(it) ? { decision: it.decision, note: it.decision_note ?? "", committed: true } : decisions[itemKey(it)] ?? null;

/** Severity (critical first), then dollar impact (largest first), then family, page, id. */
export function sortQueue(items) {
  return [...items].sort(
    (a, b) =>
      (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9) ||
      Number(b.dollars ?? 0) - Number(a.dollars ?? 0) ||
      String(a.family).localeCompare(String(b.family)) ||
      Number(a.pdf_page ?? 0) - Number(b.pdf_page ?? 0) ||
      String(a.review_id).localeCompare(String(b.review_id))
  );
}

/** Filters: family, fiscal_year, check_id, severity, state ("open" | "decided" | ""). */
export function filterQueue(items, f, decisions = {}) {
  return items.filter(
    (it) =>
      (!f.family || it.family === f.family) &&
      (f.fiscal_year == null || f.fiscal_year === "" || Number(it.fiscal_year) === Number(f.fiscal_year)) &&
      (!f.check_id || it.check_id === f.check_id) &&
      (!f.severity || it.severity === f.severity) &&
      (!f.state || (f.state === "decided") === Boolean(decisionOf(it, decisions)))
  );
}

/**
 * What a button records. kind: "keep" | "suggestion" | "change" | "needs_info".
 * "change to…" means our parsed value is wrong, so it records parser_bug with the correct value
 * in the note ("change to: …"); the note the reviewer typed follows.
 */
export function decide(kind, item, { note = "", change = "", by = "", now = new Date() } = {}) {
  const n = note.trim();
  let decision;
  let text = n;
  if (kind === "keep") decision = "accepted_as_printed";
  else if (kind === "needs_info") decision = "needs_info";
  else if (kind === "suggestion") {
    if (!DECISIONS.includes(item.suggested_decision)) throw new Error("This item has no suggested decision.");
    decision = item.suggested_decision;
    text = n || `Suggestion accepted: ${item.suggested_note ?? ""}`.trim();
  } else if (kind === "change") {
    const c = change.trim();
    if (!c) throw new Error('Say what the value should be ("change to…").');
    decision = "parser_bug";
    text = `change to: ${c}${n ? ` — ${n}` : ""}`;
  } else throw new Error(`unknown decision kind ${kind}`);
  if (!by.trim()) throw new Error("Enter your name first (decided_by).");
  return {
    review_id: item.review_id,
    family: item.family,
    fiscal_year: Number(item.fiscal_year),
    decision,
    note: text,
    decided_by: by.trim(),
    decided_at: now.toISOString(),
  };
}

// ---------------------------------------------------------------- CSV

const quote = (v) => {
  const s = String(v ?? "");
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

/**
 * This browser's decisions for one family and year as a decisions CSV, in queue order. Rows
 * already decided in the repository are left out: their committed lines stay as they are, and
 * code/validate_review_decisions.py --add merges this file into the committed one.
 */
export function toDecisionsCsv(items, decisions, family, fiscalYear) {
  const lines = [DECISIONS_HEADER.join(",")];
  for (const it of sortQueue(items)) {
    if (it.family !== family || Number(it.fiscal_year) !== Number(fiscalYear) || isCommitted(it)) continue;
    const d = decisions[itemKey(it)];
    if (!d) continue;
    lines.push(DECISIONS_HEADER.map((c) => quote(d[c])).join(","));
  }
  return lines.join("\n") + "\n";
}

/** RFC 4180 CSV -> array of string arrays. */
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let q = false;
  const s = String(text).replace(/^﻿/, "");
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (q) {
      if (ch === '"' && s[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (ch === '"') q = false;
      else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && s[i + 1] === "\n") i++;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else cell += ch;
  }
  if (cell !== "" || row.length) {
    row.push(cell);
    rows.push(row);
  }
  return rows.filter((r) => r.some((c) => c.trim() !== ""));
}

/**
 * A decisions CSV -> decisions keyed like the store, for the queue items it names. Unknown ids,
 * bad decision values and a wrong header are reported and skipped, never guessed.
 */
export function importDecisions(text, items) {
  const rows = parseCsv(text);
  const errors = [];
  const out = {};
  if (!rows.length) return { decisions: out, errors: ["The file is empty."] };
  const header = rows[0];
  if (header.join(",") !== DECISIONS_HEADER.join(",")) {
    return { decisions: out, errors: [`The header is "${header.join(",")}"; a decisions file starts "${DECISIONS_HEADER.join(",")}".`] };
  }
  const byId = new Map();
  for (const it of items) byId.set(it.review_id, it);
  rows.slice(1).forEach((r, i) => {
    const d = Object.fromEntries(DECISIONS_HEADER.map((c, k) => [c, r[k] ?? ""]));
    const it = byId.get(d.review_id);
    const line = i + 2;
    if (!it) return errors.push(`Line ${line}: review_id ${d.review_id} is not in this build's queue.`);
    if (!DECISIONS.includes(d.decision)) return errors.push(`Line ${line}: decision "${d.decision}" is not one of ${DECISIONS.join(", ")}.`);
    out[itemKey(it)] = { ...d, family: it.family, fiscal_year: Number(it.fiscal_year) };
  });
  return { decisions: out, errors };
}

// ---------------------------------------------------------------- the browser's store

export const STORE_KEY = "nycb-review-decisions-v1";
export const NAME_KEY = "nycb-review-reviewer";

export function loadStore(storage) {
  try {
    const v = JSON.parse(storage?.getItem(STORE_KEY) ?? "{}");
    return v && typeof v === "object" ? v : {};
  } catch {
    return {};
  }
}

export function saveStore(storage, decisions) {
  storage?.setItem(STORE_KEY, JSON.stringify(decisions));
}

/** Counts for the header: total, decided (committed + this browser), open, needs_info. */
export function progress(items, decisions) {
  const decided = items.filter((it) => decisionOf(it, decisions));
  return {
    total: items.length,
    decided: decided.length,
    committed: items.filter(isCommitted).length,
    open: items.length - decided.length,
    needs_info: decided.filter((it) => decisionOf(it, decisions).decision === "needs_info").length,
  };
}
