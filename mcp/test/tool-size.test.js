/**
 * A size budget for what the model reads every turn: the tools/list JSON plus the server
 * instructions (#342), measured with the shared module's toolListSize (the same measure as
 * nyc-311-mcp's test/tool-size.test.mjs). Each test says what result would make it FAIL.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { INSTRUCTIONS, TOOLS } from "../dist/server.js";
import { toolListSize } from "../dist/betanyc-tools.js";

// Measured 2026-11-18 at 49,958 characters (shared module 1.5.0, annotations added; about
// 12,500 tokens). The budget is that plus about 2%, so any growth is a decision, not drift.
// To raise it, add a dated line here with the new measure and the reason, and put text that
// several tools share in the server instructions rather than in each tool.
// Lowered 2026-11-18 (#344): the text-matching rule moved into the server instructions, said once
// instead of in six tool descriptions and six whole_word descriptions. Measured 45,244.
// 2026-11-18, review fixes (not a raise): each tool's own title and a self-contained one-line
// text-matching hint in each tool (some apps never show the instructions). Measured 46,392.
// 2026-11-19, second review (not a raise): one title reworded so no title is only the name's
// words ("Search the Council's Schedule C awards"). Measured 46,420.
const BUDGET_CHARS = 46_500;

test("tool definitions plus server instructions stay within the size budget", () => {
  // FAILS if the tool list or the instructions grow past the budget.
  const size = toolListSize(TOOLS, INSTRUCTIONS);
  assert.ok(size <= BUDGET_CHARS, `tools/list JSON + instructions is ${size} characters, over the ${BUDGET_CHARS} budget`);
});
