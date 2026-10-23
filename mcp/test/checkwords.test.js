/**
 * The plain words for check codes (src/checkwords.ts) and for questions to Council Finance
 * (src/questions.ts), both shared with the explorer through dist/. FAILS if a check code in any
 * promoted file (data/fy* /pdf/**: a review file's check_id or a row's flags) has no plain
 * sentence, if a sentence reads like a code, or if a question's status is worded wrong.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "csv-parse/sync";
import { CHECK_WORDS, UNKNOWN_CHECK, checkWords, flagWords, otherFlagWords, plainReviewNote } from "../dist/checkwords.js";
import {
  BOROUGH_CODES_QUESTION,
  MA_SERIES_QUESTION,
  decisionWithQuestion,
  STILL_CHECKING,
  inPart2Series,
  seriesWords,
  questionById,
  questionWords,
  questionsByReviewId,
} from "../dist/questions.js";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** Every CSV under data/fyNN/pdf/. */
function pdfCsvs() {
  const out = [];
  const walk = (d) => {
    for (const f of readdirSync(d)) {
      const p = join(d, f);
      if (statSync(p).isDirectory()) walk(p);
      else if (f.endsWith(".csv")) out.push(p);
    }
  };
  for (const fy of readdirSync(join(REPO, "data")).filter((d) => /^fy\d\d$/.test(d))) {
    try {
      walk(join(REPO, "data", fy, "pdf"));
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
    }
  }
  return out;
}

test("every check code in data/fy*/pdf/ has a plain sentence", () => {
  const codes = new Map();
  for (const p of pdfCsvs()) {
    for (const r of parse(readFileSync(p, "utf8"), { columns: true, bom: true, relax_column_count: false })) {
      const found = [...String(r.check_id ?? "").split(";"), ...String(r.flags ?? "").split(";")].map((s) => s.trim()).filter(Boolean);
      for (const c of found) if (!codes.has(c)) codes.set(c, p.slice(REPO.length + 1));
    }
  }
  assert.ok(codes.size >= 100, `premise: the promoted files were read (${codes.size} codes)`);
  const missing = [...codes].filter(([c]) => !(c in CHECK_WORDS)).map(([c, p]) => `${c} (${p})`);
  assert.deepEqual(missing, [], "add a sentence to mcp/src/checkwords.ts CHECK_WORDS");
});

test("each sentence is short and plain: one sentence or two, no codes, no severity words", () => {
  for (const [code, words] of Object.entries(CHECK_WORDS)) {
    assert.match(words, /^[A-Z"].*\.$/, `${code}: a sentence, capitalized, ending in a period`);
    assert.ok(words.length <= 140, `${code}: ${words.length} characters`);
    assert.doesNotMatch(words, /\b[A-Z]\d*\.[a-z_]+\b|_/, `${code}: reads like a code`);
    assert.doesNotMatch(words, /\b(critical|warn|severity|fraud|error by|wrong(ly)? (filed|claimed))\b/i, `${code}: a charge, not a description`);
  }
  assert.equal(checkWords("no.such_code"), UNKNOWN_CHECK);
  assert.equal(checkWords("W.fiscal_conduit"), "The PDF prints something in the fiscal-conduit column for this row, usually a group that receives the money for the one listed.");
});

test("flags and review notes in plain words", () => {
  assert.deepEqual(flagWords("W.amount_bare;W.amount_no_dollar;W.asterisk"), [CHECK_WORDS["W.amount_bare"], CHECK_WORDS["W.asterisk"]], "one sentence once");
  assert.deepEqual(flagWords(""), []);
  assert.equal(plainReviewNote({ check_id: "H8.lattice", field: "org;ein" }), `${CHECK_WORDS["H8.lattice"]} Part of the row: organization name, EIN.`);
  assert.equal(plainReviewNote({ check_id: "H8.lattice", field: "no_rule_at_top" }), CHECK_WORDS["H8.lattice"], "an unknown field is left out");
  const note = plainReviewNote({ check_id: "W.fiscal_conduit", field: "conduit" });
  assert.deepEqual(otherFlagWords("W.fiscal_conduit;W.amount_bare", [note]), [CHECK_WORDS["W.amount_bare"]], "a flag its note says is not said twice");
});

const Q = (o) => ({ question_id: "q", review_ids: "a;b", issue: null, sent_on: "", answered_on: "", answer: "", status: "draft", ...o });
const TODAY = new Date("2026-10-23T12:00:00Z");

test("a question's status, in the words both front ends show", () => {
  assert.equal(questionWords(Q({}), TODAY), "Open question (not yet sent)");
  assert.equal(questionWords(null, TODAY), "Still being checked");
  assert.equal(questionWords(Q({ status: "sent", sent_on: "2026-10-01" }), TODAY), "Question sent to Council Finance on 2026-10-01");
  assert.equal(questionWords(Q({ status: "sent", sent_on: "2026-09-23" }), TODAY), "Question sent to Council Finance on 2026-09-23, no answer yet", "30 days");
  assert.equal(questionWords(Q({ status: "sent", sent_on: "2026-09-24" }), TODAY), "Question sent to Council Finance on 2026-09-24", "29 days");
  assert.equal(
    questionWords(Q({ status: "answered", sent_on: "2026-09-01", answered_on: "2026-10-10", answer: "MA means a mayoral item." }), TODAY),
    "Council Finance answered on 2026-10-10: MA means a mayoral item."
  );
  assert.equal(decisionWithQuestion("", "", null, TODAY), "");
  assert.equal(decisionWithQuestion("needs_info", "", null, TODAY), STILL_CHECKING, "needs_info with no Council question");
  assert.equal(decisionWithQuestion("accepted_as_printed", "kept as printed", Q({}), TODAY), "kept as printed. Open question (not yet sent)");
  assert.equal(seriesWords(["MA"], Q({}), TODAY), 'the "MA" series, a question for Council Finance: Open question (not yet sent)');
  assert.equal(seriesWords(["MM", "MA", "MA"], Q({}), TODAY), 'the "MA"/"MM" series, a question for Council Finance: Open question (not yet sent)');
  const series = [{ fiscal_year: 2026, id_prefix: "MM", line_prefix: "0N" }, { fiscal_year: 2027, id_prefix: "MA", line_prefix: "0N" }];
  assert.equal(inPart2Series({ fiscal_year: 2026, sub_id: "PV MM0001", budget_line: "PV 0N06Z" }, series), true);
  assert.equal(inPart2Series({ fiscal_year: 2026, sub_id: "PV MA0022", budget_line: "PV 0N06Z" }, series), false, "FY2026's series is MM");
  assert.equal(inPart2Series({ fiscal_year: 2027, sub_id: "PV MA0005", budget_line: "PV MN07D" }, series), false, "not on a 0N line");
  assert.equal(inPart2Series({ fiscal_year: 2025, sub_id: "PV MA0005", budget_line: "PV 0N06Z" }, series), false, "no series for the year");
  const qs = [Q({ question_id: MA_SERIES_QUESTION })];
  assert.equal(questionById(qs, MA_SERIES_QUESTION)?.question_id, MA_SERIES_QUESTION);
  assert.equal(questionById(qs, BOROUGH_CODES_QUESTION), null);
  assert.equal(questionsByReviewId(qs).get("b")?.question_id, MA_SERIES_QUESTION);
});

test("data/council_questions.csv: nothing is marked sent that Noel has not sent", () => {
  // The seed is all drafts (2026-10-23). When Noel records a sent date, update this premise.
  const rows = parse(readFileSync(join(REPO, "data", "council_questions.csv"), "utf8"), { columns: true, bom: true });
  for (const id of [MA_SERIES_QUESTION, BOROUGH_CODES_QUESTION]) assert.ok(rows.some((r) => r.question_id === id), id);
  for (const r of rows) {
    if (r.status !== "draft") assert.match(r.sent_on, /^\d{4}-\d{2}-\d{2}$/, `${r.question_id}: a sent or answered question has its date`);
  }
});
