/**
 * Whole-word matching for the free-text filters (GitHub #259).
 *
 * Every text filter matches a folded substring (src/fold.ts). A short term then matches inside
 * unrelated words: "AI" found "Jamaica" and "AIDS". So a filter can also match whole words: the
 * term matches only where the character just before it and the character just after it (in the
 * folded text) are not a letter or a digit, or are the start or end of the text. "AI" matches
 * "AI Training Program", "(AI)", "AI-powered" and "BetaNYC's AI", never "Jamaica" or "AIDS".
 * Folding (case, accents, curly quotes, dashes) is the same as for a substring, and nothing is a
 * wildcard: % and _ are literal characters either way.
 *
 * The default (SHORT_TERM): a term of 1 to 3 letters and digits, after folding and trimming,
 * matches whole words; a longer term keeps substring matching, so "Fellow" still finds
 * "Fellowship" and "BetaNYC" still finds "BetaNYC's". A term with no letter or digit at all ("%",
 * "_") stays a substring: word edges mean nothing for it. A tool's `whole_word` argument, when
 * given, overrides the default for every text filter in that call, either way.
 *
 * The matching runs in SQL, through the word_match() function registerTextFunctions() puts on a
 * connection (the same way fold() is registered), so the totals cover exactly the rows shown.
 */
import type { Database as DB } from "better-sqlite3";
import { fold } from "./fold.js";

/** Terms with at most this many letters and digits match whole words by default. */
export const SHORT_TERM = 3;

const ALNUM = /[\p{L}\p{N}]/u;
const ALNUM_G = /[\p{L}\p{N}]/gu;

/** How many letters and digits a term has once folded (the default's measure). */
export function alnumCount(term: string): number {
  return (fold(term).match(ALNUM_G) ?? []).length;
}

/**
 * Whether a filter value matches whole words: the caller's explicit choice when given, else the
 * default (1 to SHORT_TERM letters and digits).
 */
export function useWholeWord(term: string, explicit?: boolean): boolean {
  if (explicit != null) return explicit;
  const n = alnumCount(term);
  return n > 0 && n <= SHORT_TERM;
}

/**
 * Whether `term` occurs in `text` as a whole word. Both must already be folded. Every occurrence
 * is tried, so "ai" is found in "jamaica ai" after the miss inside "jamaica".
 */
export function containsWord(text: string, term: string): boolean {
  if (term === "") return false;
  for (let at = text.indexOf(term); at !== -1; at = text.indexOf(term, at + 1)) {
    const before = at === 0 ? "" : text[at - 1];
    const after = text[at + term.length] ?? "";
    if (!ALNUM.test(before) && !ALNUM.test(after)) return true;
  }
  return false;
}

/**
 * Put fold() and word_match() on a connection. word_match(text, term) folds `text` and is 1 when
 * the already-folded `term` occurs in it as a whole word.
 */
export function registerTextFunctions(db: DB): void {
  db.function("fold", { deterministic: true }, (v: unknown) => fold(v == null ? "" : String(v)));
  db.function("word_match", { deterministic: true }, (v: unknown, q: unknown) =>
    v == null ? 0 : containsWord(fold(String(v)), String(q ?? "")) ? 1 : 0
  );
}

/** One filter matched as whole words, for the answer's note. */
export interface WordFilter {
  filter: string;
  value: string;
}

/**
 * The answer's one line when any filter matched as whole words, or "" when none did. `explicit`
 * is the call's whole_word argument.
 */
export function wholeWordNote(filters: WordFilter[], explicit?: boolean): string {
  if (!filters.length) return "";
  const list = filters.map((f) => `${f.filter} ${JSON.stringify(f.value.trim())}`).join(", ");
  return explicit
    ? `Matched as whole words (whole_word is true): ${list}. Pass whole_word: false to match inside longer words too.`
    : `Matched as whole words, because a term of ${SHORT_TERM} or fewer letters and digits does by default: ${list}. Pass whole_word: false to match inside longer words too (e.g. "AI" in "Jamaica").`;
}
