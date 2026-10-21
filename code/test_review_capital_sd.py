#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py (FY2027 review, GitHub #102).

Both re-read the committed PDFs under source/FY27/, so they always run. Golden rows are read off
the rendered pages by a person (pp.40, 47, 56, 24, 30).

Run: pytest code/test_review_capital_sd.py
"""
import os
import sys

import pdfplumber
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402
import review_terms as terms     # noqa: E402


@pytest.fixture(scope="module")
def capital(tmp_path_factory):
    rows, totals, review = cap.run(str(tmp_path_factory.mktemp("cap")), do_ink=False)
    return rows, totals, review


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_counts_and_totals(capital):
    rows, totals, _ = capital
    assert sum(r["part"] == "I" for r in rows) == 1213
    assert sum(r["part"] == "II" for r in rows) == 178
    assert len(totals) == 28
    assert all(t["status"] == "OK" for t in totals)


def test_titles_printed_above_their_row_p40(capital):
    rows, _, _ = capital
    # The title sits on the line above the SUB ID; a line reader gives it to the row before.
    assert row(rows, "I", "HD CC1047")["title"] == "FIRST ATLANTIC TERMINAL"
    assert row(rows, "I", "HD CC1050")["title"] == "CHLDC YEAR 15 AFFORDABLE HOUSING REHABILITATION"
    assert row(rows, "I", "HD CC1044")["title"] == \
        "RISEBORO COMMUNITY PARTNERSHIP MONTROSE MESEROLE AFFORDABLE HOUSING"


def test_rows_the_old_parser_lost(capital):
    rows, _, _ = capital
    r = row(rows, "I", "HR CC0168")
    assert (r["budget_line"], r["fy2027"], r["sponsor"]) == ("HR DN917", 250000, "ABREU")
    assert row(rows, "I", "HD CC0707")["fy2027"] == 300000
    assert row(rows, "I", "HD CC0863")["fy2027"] == 300000


def test_p56_misprint_kept_as_printed(capital):
    rows, _, review = capital
    r = row(rows, "I", "PV CC0989")
    assert r["fy2030"] is None and r["sponsor"] == "SPEAKER, THOMAS-HENRY"
    assert row(rows, "I", "PV CC1110")["sponsor"] == "SPEAKER, MANHATTAN DELEGATION 0"
    assert any(x["check_id"] == "C6.amount_cells" and x["sub_id"] == "PV CC0989" for x in review.rows)


def test_codes_and_edits(capital):
    rows, _, _ = capital
    r = row(rows, "I", "E CC0002")
    assert (r["building_code"], r["school_code"]) == ("M276", "M276")
    e = row(rows, "I", "HR CC1065")
    assert e["sponsor"] == "SPEAKER, BANKS, LOUIS, ZHUANG"
    assert "edited_after_export" in e["flags"]
    assert row(rows, "II", "HR CC1065")["sponsor"] == "SPEAKER, BANKS"


def test_ma_rows_only_in_part2(capital):
    rows, _, _ = capital
    ma = [r for r in rows if r["sub_id"].split(" ")[1].startswith("MA")]
    assert len(ma) == 30 and {r["part"] for r in ma} == {"II"}
    assert sum(r["fy2027"] for r in ma) == 70987000


def test_no_unresolved_stream_disagreement(capital):
    _, _, review = capital
    assert not [x for x in review.rows if x["check_id"] == "C5.geom_vs_stream"
                and x["severity"] == "critical"]


def test_ink_check_sees_a_dropped_row_and_digit():
    with pdfplumber.open(cap.PDF) as pdf:
        page = pdf.pages[46]
        words = cap.page_words(page)
        gray = cap.render_gray(cap.PDF, 47)
        allw = {w["wid"] for w in words}
        assert cap.ink_regions(gray, words, allw, page)[0] == []
        zero = next(w for w in words if w["text"] == "0")
        assert len(cap.ink_regions(gray, words, allw - {zero["wid"]}, page)[0]) == 1


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    return terms.run(str(tmp_path_factory.mktemp("tc")), do_ink=False)


def test_terms_numbering_and_units(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 76))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    r64 = rows[63]
    assert r64["agency_code"] == "071; 806; 069; 858"
    assert r64["units_of_appropriation"] == \
        "071:100; 071:101; 071:200; 806:001; 806:014; 069:101; 069:201; 858:002; 858:010"
    assert rows[32]["budget_lines"].startswith("HD-0206")


def test_terms_text_has_no_split_words(tc):
    rows, _ = tc
    assert "unit of appropriation number 001" in rows[0]["condition_text"]
    assert "bias incidents" in rows[0]["condition_text"]
    vocab = {w.lower() for r in rows for w in terms.re.findall(r"[A-Za-z]+", r["condition_text"])}
    assert terms.split_words([r["condition_text"] for r in rows], vocab) == 0
