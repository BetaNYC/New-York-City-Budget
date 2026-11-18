/**
 * The evaluation set (eval/questions.json, #345): at least ten realistic questions, each with its
 * known answer and where that answer was worked out from, all passing against the shipped index
 * and pretest's PDF tables. Each test says what result would make it FAIL.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runEval } from "../eval/run.mjs";

const { questions } = JSON.parse(readFileSync(new URL("../eval/questions.json", import.meta.url), "utf8"));

test("the set has at least ten questions, each with a check and its source", () => {
  // FAILS if the set shrinks below ten, or a question has no check or no record of its answer's source.
  assert.ok(questions.length >= 10, `${questions.length} questions`);
  assert.equal(new Set(questions.map((q) => q.id)).size, questions.length, "duplicate id");
  for (const q of questions) {
    assert.ok(q.q && q.tool && q.args, q.id);
    assert.ok(q.contains?.length, `${q.id} checks nothing`);
    assert.ok(q.from, `${q.id} does not say where its answer came from`);
  }
});

test("every question gets its known answer", async () => {
  // FAILS if an answer changes, a tool errors, or a PDF question is skipped (pretest builds the tables).
  const results = await runEval();
  const bad = results.filter((r) => r.result !== "pass");
  assert.deepEqual(bad, []);
});
