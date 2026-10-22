#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2025 (GitHub #104), run from
config/capital_sd/fy2025.toml and config/terms/fy2025.toml. FY2026 and FY2027 stay covered by
code/test_review_fy26_capital_terms.py and code/test_review_capital_sd.py.

Both re-read the committed PDFs under source/FY25/. Golden rows are read off the rendered pages
by a person (pp.4, 50, 51, 74, 79 of the capital book; pp.2, 6, 19, 24 of the T&C).

Run: pytest code/test_review_fy25_capital_terms.py
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
    out = cap.run(str(tmp_path_factory.mktemp("cap25")), do_ink=False, fy=2025)
    yield out
    cap.configure(2027)


def rows_of(rows, part, sub_id):
    return [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]


def row(rows, part, sub_id):
    hits = rows_of(rows, part, sub_id)
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_config_page_map_and_columns(capital):
    assert cap.FYS == ("fy2025", "fy2026", "fy2027", "fy2028")
    assert cap.pages_of("summary") == [67]
    assert cap.pages_of("part1") == list(range(4, 67))
    assert cap.pages_of("part3") == list(range(79, 88))


def test_counts_and_totals(capital):
    rows, totals, review = capital
    assert sum(r["part"] == "I" for r in rows) == 1327
    assert sum(r["part"] == "II" for r in rows) == 181
    assert len(totals) == 32
    assert all(t["status"] == "OK" for t in totals)
    p1 = next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")
    assert p1["printed_fy2025"] == 775000000
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2.summary", "C4", "C6"))]


def test_summary_page_prints_a_space_after_the_dollar_sign():
    cap.configure(2025)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            s = cap.summary_page(pdf, None)          # p.67: "($ 75,000,000)"
    finally:
        cap.configure(2027)
    assert s == {"additions": 775000000, "rescindments": 75000000, "net": 700000000}


def test_golden_rows(capital):
    rows, _, _ = capital
    r = row(rows, "I", "ED NC037")                   # p.4, the title wraps to a second line
    assert (r["budget_line"], r["boro"], r["title"], r["fy2025"], r["sponsor"]) == \
        ("AG DN262", "Q", "MET COUNCIL FOOD NETWORK REFRIGERATED TRUCK", 90000, "SCHULMAN")


def test_sponsor_cell_wrapping_past_the_row_band(capital):
    rows, _, review = capital
    r = row(rows, "I", "HN CN017")                   # p.50: three sponsor lines
    assert r["sponsor"] == ("SPEAKER, DE LA ROSA, SANCHEZ, FELIZ, MANHATTAN DELEGATION, BLACK, "
                            "LATINO AND ASIAN CAUCUS")
    assert "sponsor_wrapped_below" in r["flags"]
    assert not [x for x in review.rows if x["severity"] == "critical" and x["check_id"].startswith("C5")]


def test_edit_split_by_font_change_is_joined(capital):
    rows, _, _ = capital
    r = row(rows, "I", "HO CN025")                   # p.51: the C of SCHULMAN is another subset
    assert r["sponsor"] == "SPEAKER, LEE, KRISHNAN, SCHULMAN"
    assert "edited_after_export" in r["flags"]


def test_ids_printed_twice_are_kept_and_flagged(capital):
    rows, _, review = capital
    twice = rows_of(rows, "I", "HN CN018")           # p.51, same ID and budget line, two projects
    assert sorted((r["title"], r["fy2025"]) for r in twice) == [
        ("HUNTER COLLEGE CAMPUS SCHOOL ROOF", 100000),
        ("LEHMAN COLLEGE FINE ARTS BUILDING NEW MEDIA LABS", 2000000)]
    assert sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C3.id_reused") == \
        ["E CN810", "ED NC128", "HN CN018", "HN CN020", "HN CN021", "HO CN019"]
    # Part II's ED NC128 (p.69, AG DN06Y) is compared with the Part I row on its own line (p.4).
    assert not [x for x in review.rows if x["check_id"] == "C3.part2_vs_part1"]


def test_part2_only_rows(capital):
    rows, _, review = capital
    p1 = {r["sub_id"] for r in rows if r["part"] == "I"}
    only = [r for r in rows if r["part"] == "II" and r["sub_id"] not in p1]
    ma = [r for r in only if r["sub_id"].split(" ")[1].startswith("MA")]
    assert len(only) == 40 and len(ma) == 39
    assert sum(r["fy2025"] for r in ma) == 57657000
    crit = [x["sub_id"] for x in review.rows if x["check_id"] == "C3.part2_only"]
    assert crit == ["PV CT001"]                      # p.74, 126 PV207APLO APOLLO THEATER
    assert row(rows, "II", "PV CT001")["fy2025"] == 2500000


def test_part3_third_export(capital):
    _, _, review = capital
    cap.configure(2025)                               # other tests reset the module to FY2027
    assert cap.BOLD_FONTS == frozenset({"CIDFont+F1"})   # pp.79-87: bold without "Bold"
    assert not [x for x in review.rows if x["part"] == "III"]


def test_workbook_mojibake_decoded_for_comparing_only(capital):
    _, _, review = capital
    cap.configure(2025)
    assert cap.wb_text("OssΘ") == "Ossé" and cap.wb_text("Cabßn") == "Cabán"
    assert cap.wb_text("CAF╔") == "CAFÉ" and cap.wb_text("SPEAKER") == "SPEAKER"
    assert not [x for x in review.rows if x["check_id"] in ("C9.workbook_title", "C9.workbook_sponsor")]
    assert [x["check_id"] for x in review.rows if x["check_id"] == "C9.workbook_text"] == \
        ["C9.workbook_text"]


def test_defaults_leave_other_years_alone():
    cap.configure(2026)
    try:
        assert cap.wb_text("OssΘ") == "OssΘ"          # no workbook_mojibake in FY2026
        assert cap.BOLD_FONTS == frozenset()
        w = [{"text": "GENNARO", "x0": 0, "x1": 10, "top": 0}, {"text": ",", "x0": 10, "x1": 12, "top": 0}]
        assert cap.line_text(w) == "GENNARO ,"       # join_touching_words is FY2025 only
    finally:
        cap.configure(2027)


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc25")), do_ink=False, fy=2025)
    yield out
    terms.configure(2027)


def test_terms_numbering_and_units(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 66))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    assert rows[0]["units_of_appropriation"] == "068:001; 068:002; 068:007; 068:008"   # p.2
    assert rows[63]["units_of_appropriation"] == "260:311; 260:312; 056:001"            # p.24
    assert len(rows[56]["agency_code"].split("; ")) == 11                              # #57, p.19


def test_terms_fsr_table_belongs_to_16(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[16]["condition_text"].endswith("for the following dates:")
    assert "FINANCIAL STATUS" not in by[16]["condition_text"]
    assert by[16]["page_boxes"].startswith("6:")


def test_terms_page_number_is_furniture(tc):
    rows, _ = tc
    assert not any(r["condition_text"].rstrip().endswith((" 6", " 19", " 24")) for r in rows)
