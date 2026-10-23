/**
 * Questions to Council Finance (data/council_questions.csv; decisions #209, epic #190), worded ONE
 * way for both front ends: the MCP imports this module and the explorer imports the compiled
 * mcp/dist/questions.js (as it does rowlinks.js).
 *
 * A question covers one or more review rows (`review_ids`). Its `status` is draft (written, not
 * sent), sent (with `sent_on`) or answered (with `answered_on` and `answer`). Thirty days after
 * a question is sent with no answer, its rows are published as printed with the date (PLAN.md
 * "What closed means", rule 3).
 */

export interface CouncilQuestion {
  question_id: string;
  /** `;`-joined review ids. */
  review_ids: string;
  issue: number | string | null;
  sent_on: string | null;
  answered_on: string | null;
  answer: string | null;
  status: string;
}

export const QUESTION_STATUSES = ["draft", "sent", "answered"] as const;

/** Days after sending before an unanswered question's rows are published with the date. */
export const QUESTION_WAIT_DAYS = 30;

/** The question about the capital book's Part II-only ID series ("MA"; FY2026 "MM"), FY2018 and FY2022–FY2027. */
export const MA_SERIES_QUESTION = "capital-ma-series";
/** The question about borough codes A and C in the capital book (GitHub #227). */
export const BOROUGH_CODES_QUESTION = "capital-borough-codes-a-c";

const DAY = 86_400_000;
const ISO = /^\d{4}-\d{2}-\d{2}$/;

/** Whole days from an ISO date to `today` (UTC). */
const daysSince = (iso: string, today: Date) => Math.floor((today.getTime() - Date.parse(`${iso}T00:00:00Z`)) / DAY);

/** A needs_info entry no question covers: a person is still looking into it (not a Council question). */
export const STILL_CHECKING = "Still being checked";

/**
 * A question's status in plain words:
 *   draft                           "Open question (not yet sent)"
 *   sent, under 30 days             "Question sent to Council Finance on <date>"
 *   sent, 30 days or more           "Question sent to Council Finance on <date>, no answer yet"
 *   answered                        "Council Finance answered on <date>: <answer>"
 * No question (null): "Still being checked".
 */
export function questionWords(q: CouncilQuestion | null | undefined, today: Date = new Date()): string {
  if (!q) return STILL_CHECKING;
  if (q.status === "answered") {
    const when = q.answered_on && ISO.test(q.answered_on) ? ` on ${q.answered_on}` : "";
    return `Council Finance answered${when}: ${String(q.answer ?? "").trim() || "(answer not recorded)"}`;
  }
  if (q.status === "sent" && q.sent_on && ISO.test(q.sent_on)) {
    const sent = `Question sent to Council Finance on ${q.sent_on}`;
    return daysSince(q.sent_on, today) >= QUESTION_WAIT_DAYS ? `${sent}, no answer yet` : sent;
  }
  return "Open question (not yet sent)";
}

/** The questions, keyed by each review id they cover (a review id is in at most one question). */
export function questionsByReviewId(qs: readonly CouncilQuestion[]): Map<string, CouncilQuestion> {
  const out = new Map<string, CouncilQuestion>();
  for (const q of qs) {
    for (const id of String(q.review_ids ?? "").split(";").map((s) => s.trim()).filter(Boolean)) out.set(id, q);
  }
  return out;
}

/** One question by its id, or null. */
export const questionById = (qs: readonly CouncilQuestion[], id: string): CouncilQuestion | null =>
  qs.find((q) => q.question_id === id) ?? null;

/**
 * A review entry's decision with its question, in plain words. `decided` is the decision already
 * in words ("" when none is recorded). An entry a question covers shows the question's status;
 * a recorded decision other than needs_info comes first. A needs_info entry no question covers
 * reads "Still being checked".
 */
export function decisionWithQuestion(decision: string, decided: string, q: CouncilQuestion | null, today: Date = new Date()): string {
  if (q) return decision && decision !== "needs_info" ? `${decided}. ${questionWords(q, today)}` : questionWords(q, today);
  if (decision === "needs_info") return STILL_CHECKING;
  return decided;
}

// ---------------------------------------------------------------- the capital book's Part II series

/**
 * The project ID series a year's capital book prints only in Part II, from the reader's config
 * (config/capital_sd/fyYYYY.toml [part2_only], loaded as pdf_capital_sd_series): "MA" IDs on
 * "0N" budget lines in most years, "MM" in FY2026.
 */
export interface Part2Series {
  fiscal_year: number | bigint;
  id_prefix: string;
  line_prefix: string;
}

/** The part after the agency code: "PV MA0005" -> "MA0005". */
const afterAgency = (v: unknown) => String(v ?? "").trim().split(/\s+/)[1] ?? "";

/** Whether a book row is in its year's Part II series (as code/review_capital_sd.py tests it). */
export function inPart2Series(row: { fiscal_year?: unknown; sub_id?: unknown; budget_line?: unknown }, series: readonly Part2Series[]): boolean {
  const s = series.find((x) => Number(x.fiscal_year) === Number(row.fiscal_year));
  return !!s && afterAgency(row.sub_id).startsWith(s.id_prefix) && afterAgency(row.budget_line).startsWith(s.line_prefix);
}

/**
 * The series' label, with its question's status: 'the "MA" series, a question for Council Finance:
 * Open question (not yet sent)'; several years with different series read 'the "MA"/"MM" series'.
 */
export function seriesWords(prefixes: readonly string[], q: CouncilQuestion | null, today: Date = new Date()): string {
  const names = [...new Set(prefixes)].sort().map((p) => `"${p}"`).join("/");
  return `the ${names || '"MA"'} series, a question for Council Finance: ${questionWords(q, today)}`;
}
