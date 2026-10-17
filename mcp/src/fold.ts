/**
 * The one text-folding rule for substring filters, used on BOTH sides: build-index.mjs writes a
 * folded copy of each searchable text column (`<column>_fold`), and db.ts folds the query the same
 * way before matching it. SQLite's NOCASE folds ASCII only, so before 2026-10-16 "Women's" missed
 * "Women’s" and "Jewish Emigre" missed "Jewish Émigré" (red team S1).
 *
 * Steps: Unicode NFKD (splits accents off letters, turns full-width and compatibility forms into
 * their plain form), drop the combining marks and invisible format characters (zero-width space
 * and the like, which the parser already strips from the data), map curly quotes, primes, the
 * okina, guillemets and dashes to ASCII, lower-case, then map the few Latin letters NFKD leaves
 * whole (ł, ø, đ, æ, œ, ß, dotless ı), and collapse whitespace. Lower-casing comes before the letter
 * map so the capital sharp s (ẞ) becomes ß and then "ss".
 */
const LETTERS: Record<string, string> = {
  ł: "l", ø: "o", đ: "d", æ: "ae", œ: "oe", ß: "ss", ı: "i",
};

export function fold(s: string | null | undefined): string {
  return (s ?? "")
    .normalize("NFKD")
    .replace(/[\p{M}\p{Cf}]/gu, "")
    .replace(/[‘’‚‛′ʻʼ`´]/g, "'")
    .replace(/[“”„‟″«»]/g, '"')
    .replace(/[‐-―−]/g, "-")
    .toLowerCase()
    .replace(/[łøđæœßı]/g, (c) => LETTERS[c])
    .replace(/\s+/g, " ")
    .trim();
}
