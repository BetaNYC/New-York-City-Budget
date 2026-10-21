#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2026 (GitHub #103), run from
config/capital_sd/fy2026.toml and config/terms/fy2026.toml. FY2027 stays covered by
code/test_review_capital_sd.py.

Both re-read the committed PDFs under source/FY26/. Golden rows are read off the rendered pages
by a person (pp.4, 19, 35, 56, 70, 81 of the capital book; pp.2, 8, 15, 27 of the T&C).

Run: pytest code/test_review_fy26_capital_terms.py
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
    out = cap.run(str(tmp_path_factory.mktemp("cap26")), do_ink=False, fy=2026)
    yield out
    cap.configure(2027)


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_config_page_map_and_columns(capital):
    assert cap.FYS == ("fy2026", "fy2027", "fy2028", "fy2029")
    assert cap.pages_of("summary") == [65]
    assert cap.pages_of("part3") == list(range(78, 87))


def test_counts_and_totals(capital):
    rows, totals, _ = capital
    assert sum(r["part"] == "I" for r in rows) == 1259
    assert sum(r["part"] == "II" for r in rows) == 197
    assert len(totals) == 33
    assert all(t["status"] == "OK" for t in totals)
    p1 = next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")
    assert p1["printed_fy2026"] == 779320000


def test_golden_rows(capital):
    rows, _, _ = capital
    r = row(rows, "I", "AG NC1273")                   # p.4, title wraps to a second line
    assert (r["title"], r["fy2026"], r["sponsor"]) == \
        ("HOMECREST COMMUNITY SERVICES COMMUNITY CENTER", 2525000, "SPEAKER, BRANNAN")
    r = row(rows, "I", "E CN1572")                    # p.19: the PDF prints no "B:" here
    assert (r["title"], r["building_code"], r["school_code"]) == \
        ("NEW HEIGHTS MIDDLE SCHOOL LAB K391", "", "K722")


def test_unmapped_tab_glyph_kept_raw_read_as_space(capital):
    rows, _, _ = capital
    r = row(rows, "I", "E CN1588")                    # p.35
    assert "(cid:9)" in r["title_raw"]
    assert r["title"] == "P.S.350 NEW DIRECTION TECH UPGRADES"
    assert (r["building_code"], r["school_code"]) == ("S410", "X350")


def test_edit_after_export_and_two_reads(capital):
    rows, _, review = capital
    e = row(rows, "I", "P CN1114")                    # p.56: ", POWERS" typed in later
    assert e["sponsor"] == "SPEAKER, LEE, POWERS" and "edited_after_export" in e["flags"]
    assert row(rows, "I", "P CN1542")["sponsor"] == "LEE"
    assert not [x for x in review.rows if x["check_id"] == "C5.geom_vs_stream"
                and x["severity"] == "critical"]


def test_negative_amount_in_part2_and_part3(capital):
    rows, _, _ = capital
    assert row(rows, "II", "PV MA0005")["fy2026"] == -183000   # p.70 prints -183,000
    assert cap.money("$(183,000)") == -183000                   # p.81 prints $(183,000)
    assert cap.money("-183,000") == -183000 and cap.money("1,183,000") == 1183000


def test_part2_only_rows(capital):
    rows, _, review = capital
    p1 = {r["sub_id"] for r in rows if r["part"] == "I"}
    only = [r for r in rows if r["part"] == "II" and r["sub_id"] not in p1]
    mm = [r for r in only if r["sub_id"].split(" ")[1].startswith("MM")]
    assert len(only) == 42 and len(mm) == 39
    assert sum(r["fy2026"] for r in mm) == 62073000
    crit = sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C3.part2_only")
    assert crit == ["PV MA0005", "PV MA0007", "PV MA0022"]


def test_ink_check_sees_a_dropped_word_and_digit():
    cap.configure(2026)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            page = pdf.pages[3]
            words = cap.page_words(page)
            gray = cap.render_gray(cap.PDF, 4)
            allw = {w["wid"] for w in words}
            assert cap.ink_regions(gray, words, allw, page)[0] == []
            word = next(w for w in words if w["text"] == "HOMECREST")
            regs = cap.ink_regions(gray, words, allw - {word["wid"]}, page)[0]
            assert regs and all(word["x0"] - 2 <= r["bbox_pt"][0] and r["bbox_pt"][2] <= word["x1"] + 2
                                for r in regs)      # one region per letter, all inside the word
            zero = next(w for w in words if w["text"] == "0")
            assert len(cap.ink_regions(gray, words, allw - {zero["wid"]}, page)[0]) == 1
    finally:
        cap.configure(2027)


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc26")), do_ink=False, fy=2026)
    yield out
    terms.configure(2027)


def test_terms_numbering_and_units(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 69))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    assert rows[4]["units_of_appropriation"] == "030:001"      # #5 prints "Units of Appropriation"
    assert rows[66]["units_of_appropriation"] == "260:311; 260:312; 056:001"
    assert rows[38]["budget_lines"] == "HB‐" "0278 – All Projects"   # U+2010 kept as printed


def test_terms_page_header_is_furniture(tc):
    rows, _ = tc
    assert not any("Page " in r["condition_text"] and " of 29" in r["condition_text"] for r in rows)


def test_fsr_superscript_ordinals_stay_in_place(tmp_path):
    terms.configure(2026)
    try:
        review = cap.Review(tag="test")
        with pdfplumber.open(terms.PDF) as pdf:
            fsr, _ = terms.fsr_table(pdf, review, [])
    finally:
        terms.configure(2027)
    dates = [r["issue_date"].replace("\xa0", " ") for r in fsr]    # the PDF prints a no-break space
    assert dates == ["October 2nd", "November 5th", "December 9th", "February 11th", "April 8th",
                     "May 26th"]
