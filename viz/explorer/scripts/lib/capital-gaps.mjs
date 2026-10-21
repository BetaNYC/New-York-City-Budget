/**
 * Why a capital report year has no data, read from data/capital/README.md.
 *
 * The README's "Which source each year comes from" table is where the repo states its capital
 * gaps (FY2018: "**none**"). The explorer shows that reason verbatim rather than restating it,
 * so a change to the README reaches the site on the next build. A table the parser cannot find,
 * or a gap year the table does not explain, is a stop: the site must never show a gap without
 * its reason, or (worse) a missing year as $0.
 */

/** Rows of the "Which source each year comes from" table, as {years, source, why}. */
export function readSourceTable(readme) {
  const start = readme.indexOf("## Which source each year comes from");
  if (start < 0) throw new Error('data/capital/README.md: no "## Which source each year comes from" section');
  const rest = readme.slice(start).split("\n").slice(1);
  const end = rest.findIndex((l) => l.startsWith("## "));
  const lines = (end < 0 ? rest : rest.slice(0, end)).filter((l) => l.trim().startsWith("|"));
  // header, separator, then rows
  const rows = lines.slice(2).map((l) =>
    l
      .trim()
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((c) => c.trim())
  );
  if (rows.length === 0) throw new Error("data/capital/README.md: the source table has no rows");
  return rows.map(([yearsCell, source, why]) => ({ years: yearsOf(yearsCell), source, why }));
}

/** "FY2015, FY2016" -> [2015, 2016]; "FY2019–FY2025" -> 2019..2025. */
export function yearsOf(cell) {
  const out = [];
  for (const part of cell.split(",")) {
    const m = /FY(\d{4})\s*[–-]\s*FY(\d{4})/.exec(part);
    if (m) {
      for (let y = Number(m[1]); y <= Number(m[2]); y++) out.push(y);
      continue;
    }
    const one = /FY(\d{4})/.exec(part);
    if (one) out.push(Number(one[1]));
  }
  return out;
}

/**
 * The capital gap years between the first and last published report year, each with the README's
 * reason. `published` is CAPITAL_REPORT_YEARS from mcp/scripts/verify-index.mjs.
 */
export function capitalGaps(readme, published) {
  const table = readSourceTable(readme);
  const first = Math.min(...published);
  const last = Math.max(...published);
  const gaps = [];
  for (let y = first; y <= last; y++) {
    if (published.includes(y)) continue;
    const row = table.find((r) => r.years.includes(y));
    if (!row || !/\bnone\b/i.test(row.source)) {
      throw new Error(`data/capital/README.md: FY${y} is not a published capital year, but the source table does not say why`);
    }
    gaps.push({ year: y, reason: row.why.replace(/\*\*/g, "") });
  }
  return { first, last, gaps };
}
