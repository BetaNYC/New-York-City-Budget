/**
 * Comparing two fiscal years, as pure functions: the diff of two keyed sums, and the diff of two
 * years' Terms and Conditions. The queries that feed them are in ./queries.js.
 *
 * Words used on screen:
 *   new        only in year B          dropped    only in year A
 *   increased  in both, more in B      decreased  in both, less in B
 *   same       in both, equal amounts (to the cent)
 * Amounts are compared in cents, so a float sum's last digit never turns "same" into "changed".
 */

export const STATUSES = ["new", "dropped", "increased", "decreased", "same"];
export const STATUS_LABEL = { new: "New", dropped: "Dropped", increased: "Increased", decreased: "Decreased", same: "Same" };

const cents = (v) => Math.round(Number(v ?? 0) * 100);

/**
 * a, b: [{ key, label, amount, n }] for year A and year B (one row per key).
 * Returns { rows: [{ key, label, a, b, a_n, b_n, delta, status }], summary: { status: {count, a, b} } }.
 * A key in neither is impossible; a null amount counts as 0 only inside a year that has the key.
 */
export function diffKeyed(a, b) {
  const map = new Map();
  for (const r of a) map.set(r.key, { key: r.key, label: r.label ?? r.key, a: Number(r.amount ?? 0), a_n: Number(r.n ?? 0), b: null, b_n: 0 });
  for (const r of b) {
    const m = map.get(r.key) ?? { key: r.key, label: r.label ?? r.key, a: null, a_n: 0 };
    m.b = Number(r.amount ?? 0);
    m.b_n = Number(r.n ?? 0);
    if (!m.label && r.label) m.label = r.label;
    map.set(r.key, m);
  }
  const rows = [];
  for (const m of map.values()) {
    let status;
    if (m.a === null) status = "new";
    else if (m.b === null) status = "dropped";
    else if (cents(m.b) > cents(m.a)) status = "increased";
    else if (cents(m.b) < cents(m.a)) status = "decreased";
    else status = "same";
    rows.push({ ...m, delta: (m.b ?? 0) - (m.a ?? 0), status });
  }
  const summary = Object.fromEntries(STATUSES.map((s) => [s, { count: 0, a: 0, b: 0 }]));
  for (const r of rows) {
    summary[r.status].count += 1;
    summary[r.status].a += r.a ?? 0;
    summary[r.status].b += r.b ?? 0;
  }
  return { rows, summary };
}

/** Largest change first (absolute), then label; optionally one status only. */
export function sortDiff(rows, status = "") {
  return rows
    .filter((r) => !status || r.status === status)
    .sort((x, y) => Math.abs(y.delta) - Math.abs(x.delta) || String(x.label).localeCompare(String(y.label)) || String(x.key).localeCompare(String(y.key)));
}

// ---------------------------------------------------------------- Terms and Conditions

/** Condition text for comparison: case, spacing, punctuation and the year numbers ignored. */
export const normText = (s) =>
  String(s ?? "")
    .toLowerCase()
    .replace(/\b(19|20)\d{2}\b/g, "<yr>")
    .replace(/[^a-z0-9<>]+/g, " ")
    .trim();

/** The agencies and units a condition names, as a key: "042:001;042:002" (order-free). */
export const unitKey = (c) =>
  String(c.units_of_appropriation || c.budget_lines || c.agency_code || "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean)
    .sort()
    .join(";");

/**
 * Pair year A's conditions with year B's:
 *   same     the text is the same once year numbers are ignored (normText)
 *   changed  not the same text, but the same agencies and units (unitKey), paired in printed order
 *   removed  in A only        added    in B only
 * Each condition is used once. Returns [{ status, a, b }] in B's order, then removed ones.
 */
export function diffTerms(aConds, bConds) {
  const usedA = new Set();
  const out = [];
  const pairs = new Map();
  const byText = new Map();
  aConds.forEach((c, i) => {
    const k = normText(c.condition_text);
    if (!byText.has(k)) byText.set(k, []);
    byText.get(k).push(i);
  });
  bConds.forEach((c, j) => {
    const cands = (byText.get(normText(c.condition_text)) ?? []).filter((i) => !usedA.has(i));
    if (cands.length) {
      usedA.add(cands[0]);
      pairs.set(j, { status: "same", i: cands[0] });
    }
  });
  const byUnits = new Map();
  aConds.forEach((c, i) => {
    if (usedA.has(i)) return;
    const k = unitKey(c);
    if (!byUnits.has(k)) byUnits.set(k, []);
    byUnits.get(k).push(i);
  });
  bConds.forEach((c, j) => {
    if (pairs.has(j)) return;
    const cands = (byUnits.get(unitKey(c)) ?? []).filter((i) => !usedA.has(i));
    if (cands.length && unitKey(c)) {
      usedA.add(cands[0]);
      pairs.set(j, { status: "changed", i: cands[0] });
    }
  });
  bConds.forEach((c, j) => {
    const p = pairs.get(j);
    out.push(p ? { status: p.status, a: aConds[p.i], b: c } : { status: "added", a: null, b: c });
  });
  aConds.forEach((c, i) => {
    if (!usedA.has(i)) out.push({ status: "removed", a: c, b: null });
  });
  return out;
}

export const TERMS_STATUSES = ["added", "removed", "changed", "same"];
