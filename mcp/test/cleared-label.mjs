/**
 * The Cleared-line label the server should print for a set of matched CSV rows, computed from the
 * committed CSVs (not the index): "(headline)" only when every matched year is ordinary, meaning
 * not an early snapshot (data/disclosure_years.csv) and not a year that prints status_norm =
 * other anywhere in the year (FY2011, FY2012). Per year, never per match (review S7, 2026-10-17).
 * Red team B1 / S4 (2026-10-16). Shared by the disclosure test files.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const YEARS = parse(readFileSync(join(REPO, "data", "disclosure_years.csv"), "utf8"), { columns: true, bom: true });
export const EARLY_YEARS = new Set(YEARS.filter((r) => r.early_snapshot === "yes").map((r) => Number(r.fiscal_year)));
const yy = (fy) => String(fy % 100).padStart(2, "0");
export const OTHER_YEARS = new Set(
  YEARS.filter((r) => r.loaded === "yes")
    .map((r) => Number(r.fiscal_year))
    .filter((fy) =>
      parse(readFileSync(join(REPO, "data", `fy${yy(fy)}`, "expense_disclosure", `fy${yy(fy)}_expense_awards.csv`), "utf8"), { columns: true, bom: true })
        .some((r) => r.status_norm === "other")
    )
);

export function clearedLabel(rows) {
  const years = [...new Set(rows.map((r) => Number(r.fiscal_year)))];
  const bad = years.filter((y) => EARLY_YEARS.has(y) || OTHER_YEARS.has(y));
  if (bad.length === 0) return "Cleared (headline):";
  if (years.length > 1) return "Cleared (mixes years that are not headline figures; see the per-year split):";
  if (EARLY_YEARS.has(years[0])) return "Cleared (early snapshot, not a headline):";
  return "Cleared (not a headline: this year prints other statuses; see the note below):";
}
