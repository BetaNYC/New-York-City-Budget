"""data/council_questions.csv: the questions to Council Finance (decisions #209, epic #190).

The MCP and the explorer read it (mcp/src/questions.ts) to say, on each review row a question
covers, whether the question is a draft, sent (and when) or answered. These tests keep the file
loadable and honest: the columns, the statuses, ISO dates that fit the status, and review ids that
exist in a promoted review file, each in at most one question.
"""
import csv
import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "council_questions.csv"
COLUMNS = ["question_id", "review_ids", "issue", "sent_on", "answered_on", "answer", "status"]
STATUSES = {"draft", "sent", "answered"}
# The question ids the code names (mcp/src/questions.ts MA_SERIES_QUESTION, BOROUGH_CODES_QUESTION).
NAMED = {"capital-ma-series", "capital-borough-codes-a-c"}

csv.field_size_limit(10**9)


def _rows():
    with QUESTIONS.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        assert r.fieldnames == COLUMNS, r.fieldnames
        return list(r)


def _review_rows():
    out = {}
    for p in sorted((ROOT / "data").glob("fy*/pdf/*/*_review.csv")):
        with p.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out[r["review_id"]] = (p, r)
    return out


def _iso(s):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", s), s
    return dt.date.fromisoformat(s)


def test_columns_ids_and_statuses():
    rows = _rows()
    assert rows, "premise: the file holds the questions"
    ids = [r["question_id"] for r in rows]
    assert len(ids) == len(set(ids)), "a question_id is listed twice"
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", i) for i in ids), ids
    assert NAMED <= set(ids)
    for r in rows:
        assert r["status"] in STATUSES, r
        assert r["issue"] == "" or re.fullmatch(r"[1-9]\d*", r["issue"]), r


def test_dates_are_iso_and_fit_the_status():
    today = dt.date.today()
    for r in _rows():
        q = r["question_id"]
        if r["status"] == "draft":
            assert r["sent_on"] == r["answered_on"] == r["answer"] == "", f"{q}: a draft has no dates or answer"
            continue
        sent = _iso(r["sent_on"])
        assert sent <= today, f"{q}: sent_on is in the future"
        if r["status"] == "sent":
            assert r["answered_on"] == r["answer"] == "", f"{q}: a sent question has no answer yet"
        else:
            answered = _iso(r["answered_on"])
            assert sent <= answered <= today, f"{q}: answered_on"
            assert r["answer"].strip(), f"{q}: an answered question records its answer"


def test_review_ids_exist_and_are_in_one_question():
    reviews = _review_rows()
    assert len(reviews) > 1000, "premise: the promoted review files were read"
    seen = {}
    for r in _rows():
        for rid in filter(None, (s.strip() for s in r["review_ids"].split(";"))):
            assert rid in reviews, f"{r['question_id']}: review id {rid} is in no data/fy*/pdf/*/*_review.csv"
            assert rid not in seen, f"{rid} is in {seen[rid]} and {r['question_id']}"
            seen[rid] = r["question_id"]


def test_every_ma_series_review_row_is_in_the_ma_question():
    # Decided in #209: needs_info in every year, one question to Council Finance.
    ma = {rid for rid, (_, r) in _review_rows().items() if r["check_id"] == "C3.ma_series"}
    assert len(ma) >= 7, "premise: one MA-series item per capital year"
    row = next(r for r in _rows() if r["question_id"] == "capital-ma-series")
    assert set(row["review_ids"].split(";")) == ma


def test_every_ask_council_finance_suggestion_has_a_question():
    # A needs_info suggestion that says to ask Council Finance must be covered by a question.
    covered = {rid for r in _rows() for rid in r["review_ids"].split(";") if rid}
    with (ROOT / "data" / "pdf_review_suggestions.csv").open(newline="", encoding="utf-8") as f:
        ask = {s["review_id"] for s in csv.DictReader(f)
               if s["suggested_decision"] == "needs_info" and "Council Finance" in s["suggested_note"]}
    assert ask, "premise: some suggestions ask Council Finance"
    assert ask <= covered, sorted(ask - covered)
