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

/** The question about the capital book's "MA" ID series (rows printed only in Part II), every year. */
export const MA_SERIES_QUESTION = "capital-ma-series";
/** The question about borough codes A and C in the capital book (GitHub #227). */
export const BOROUGH_CODES_QUESTION = "capital-borough-codes-a-c";

const DAY = 86_400_000;
const ISO = /^\d{4}-\d{2}-\d{2}$/;

/** Whole days from an ISO date to `today` (UTC). */
const daysSince = (iso: string, today: Date) => Math.floor((today.getTime() - Date.parse(`${iso}T00:00:00Z`)) / DAY);

/**
 * A question's status in plain words:
 *   draft                           "Open question (not yet sent)"
 *   sent, under 30 days             "Question sent on <date>"
 *   sent, 30 days or more           "Question sent to Council Finance on <date>, no answer yet"
 *   answered                        "Council Finance answered on <date>: <answer>"
 * A question with no record (null) reads as a draft: nothing has been sent.
 */
export function questionWords(q: CouncilQuestion | null | undefined, today: Date = new Date()): string {
  if (!q || q.status === "draft") return "Open question (not yet sent)";
  if (q.status === "answered") {
    const when = q.answered_on && ISO.test(q.answered_on) ? ` on ${q.answered_on}` : "";
    return `Council Finance answered${when}: ${String(q.answer ?? "").trim() || "(answer not recorded)"}`;
  }
  if (q.status === "sent" && q.sent_on && ISO.test(q.sent_on)) {
    return daysSince(q.sent_on, today) >= QUESTION_WAIT_DAYS
      ? `Question sent to Council Finance on ${q.sent_on}, no answer yet`
      : `Question sent on ${q.sent_on}`;
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
 * reads as a question not yet sent.
 */
export function decisionWithQuestion(decision: string, decided: string, q: CouncilQuestion | null, today: Date = new Date()): string {
  if (q) return decision && decision !== "needs_info" ? `${decided}. ${questionWords(q, today)}` : questionWords(q, today);
  if (decision === "needs_info") return questionWords(null, today);
  return decided;
}

/** The "MA" series' label: one question to Council Finance covers every year's rows (#209). */
export const maSeriesWords = (q: CouncilQuestion | null, today: Date = new Date()) =>
  `the "MA" series, a question for Council Finance: ${questionWords(q, today)}`;
