#!/usr/bin/env python3
"""
Tests for code/validate_review_decisions.py and code/build_review_suggestions.py.

Run: pytest code/test_review_decisions.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_review_suggestions as brs  # noqa: E402
import validate_review_decisions as vrd  # noqa: E402

REVIEW = [{"review_id": "aaa", "check_id": "C1", "pdf_page": "4"},
          {"review_id": "bbb", "check_id": "C2", "pdf_page": "5"},
          {"review_id": "ccc", "check_id": "C3", "pdf_page": "6"}]


def dec(rid, decision="accepted_as_printed", by="Noel Hidalgo", at="2026-10-21"):
    return {"review_id": rid, "decision": decision, "note": "", "decided_by": by, "decided_at": at}


def test_valid_and_open():
    res = vrd.validate(REVIEW, vrd.HEADER, [dec("aaa"), dec("bbb", "needs_info", at="2026-10-21T09:30:00Z")])
    assert res["errors"] == []
    assert [r["review_id"] for r in res["open"]] == ["ccc"]
    assert res["needs_info"] == ["bbb"]


def test_every_problem_is_listed():
    res = vrd.validate(REVIEW, ["review_id", "decision"], [
        dec("zzz"), dec("aaa", "fixed"), dec("aaa"), dec("bbb", by=" "), dec("ccc", at="21/10/2026")])
    text = "\n".join(res["errors"])
    assert "header is review_id,decision" in text
    assert "zzz" in text and "not in the review CSV" in text
    assert "'fixed'" in text
    assert "also on line" in text
    assert "decided_by is blank" in text
    assert "not an ISO date" in text


def test_cli_exit_codes(tmp_path):
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    d = tmp_path / "decisions.csv"
    with open(d, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vrd.HEADER)
        w.writeheader()
        w.writerow(dec("aaa"))
    assert vrd.main(["--review", str(rv), "--decisions", str(d)]) == 0
    assert vrd.main(["--review", str(rv), "--decisions", str(d), "--complete"]) == 2
    with open(d, "a", newline="") as f:
        csv.writer(f).writerow(["nope", "accepted_as_printed", "", "x", "2026-10-21"])
    assert vrd.main(["--review", str(rv), "--decisions", str(d)]) == 1


def test_committed_decision_files_are_valid():
    # The header-only files committed for each FY2027 family, and the Schedule C one.
    pairs = [
        ("data/fy27/pdf/schedule_c/fy27_sc_review.csv", "research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv"),
        ("data/fy27/pdf/capital_sd/fy27_capital_sd_review.csv", "research/2026-10-20-fy27-capital-terms-review/data/fy27_capital_sd_review_decisions.csv"),
        ("data/fy27/pdf/terms/fy27_terms_review.csv", "research/2026-10-20-fy27-capital-terms-review/data/fy27_terms_review_decisions.csv"),
        ("data/fy26/pdf/capital_sd/fy26_capital_sd_review.csv", "research/2026-10-21-fy26-capital-terms-review/data/fy26_capital_sd_review_decisions.csv"),
        ("data/fy26/pdf/terms/fy26_terms_review.csv", "research/2026-10-21-fy26-capital-terms-review/data/fy26_terms_review_decisions.csv"),
        ("data/fy26/pdf/schedule_c/fy26_sc_review.csv", "research/2026-10-21-fy26-schedule-c-review/data/fy26_sc_review_decisions.csv"),
        ("data/fy26/pdf/transparency/fy26_tr_review.csv", "research/2026-10-21-fy26-transparency-review/data/fy26_tr_review_decisions.csv"),
    ]
    for review, decisions in pairs:
        assert vrd.main(["--review", os.path.join(REPO, review), "--decisions", os.path.join(REPO, decisions)]) == 0, decisions


def test_suggestions_cover_every_review_row_and_are_committed():
    text, rows = brs.build()
    with open(brs.OUT, encoding="utf-8") as f:
        assert f.read() == text, "run code/build_review_suggestions.py --write"
    n = 0
    for (fy, fam), rel in brs.REVIEW_FILES.items():
        with open(os.path.join(REPO, rel), newline="", encoding="utf-8") as f:
            n += sum(1 for _ in csv.DictReader(f))
    assert len(rows) == n
    assert {r["suggested_decision"] for r in rows} <= set(brs.DECISIONS) | {""}
    # Only Schedule C rows may be blank, and only where its REVIEW.md suggests nothing.
    assert {r["family"] for r in rows if not r["suggested_decision"]} <= {"schedule_c", "transparency"}
    by = {r["review_id"]: r for r in rows}
    assert by["d68b985e6c58"]["suggested_decision"] == "source_error"
    assert by["01375b88b4c3"]["suggested_decision"] == "accepted_as_printed"


def test_merge_adds_new_and_never_overwrites(tmp_path):
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    committed = tmp_path / "decisions.csv"
    committed.write_text(vrd.to_csv([dec("aaa", "source_error")]))
    export = tmp_path / "export.csv"
    export.write_text(vrd.to_csv([dec("aaa", "source_error"), dec("bbb")]))
    assert vrd.main(["--review", str(rv), "--decisions", str(committed), "--add", str(export), "--write"]) == 0
    _, rows = vrd.read(str(committed))
    assert [(r["review_id"], r["decision"]) for r in rows] == [("aaa", "source_error"), ("bbb", "accepted_as_printed")]
    # A conflicting decision is a problem and nothing is written.
    export.write_text(vrd.to_csv([dec("aaa", "accepted_as_printed"), dec("ccc")]))
    before = committed.read_text()
    assert vrd.main(["--review", str(rv), "--decisions", str(committed), "--add", str(export), "--write"]) == 1
    assert committed.read_text() == before


def test_accept_as_printed_is_never_needs_info():
    # A suggestion whose note says "Accept as printed" (the REVIEW.md's own words) must not be
    # needs_info: clicking "Accept suggestion" would record something the note does not say.
    _, rows = brs.build()
    bad = [(r["review_id"], r["suggested_note"]) for r in rows
           if "accept as printed" in r["suggested_note"].lower() and r["suggested_decision"] == "needs_info"]
    assert bad == []
    by = {r["review_id"]: r for r in rows}
    assert by["549bba9337ee"]["suggested_decision"] == "accepted_as_printed"
    assert "Council Finance" in by["549bba9337ee"]["suggested_note"]
    for rid in ("0a4bc5e267ec", "138c84722a95", "5f578772c9b9"):   # FY2026, same wording
        assert by[rid]["suggested_decision"] == "accepted_as_printed", rid
    # Real unknowns stay needs_info: FY2027 E CC0598 and E CC1245.
    assert by["1191bd798416"]["suggested_decision"] == "needs_info"
    assert by["4ce0ec50aa88"]["suggested_decision"] == "needs_info"
