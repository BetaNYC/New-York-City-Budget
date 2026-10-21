"""
Tests for the Schedule C toolkit (code/schedc/, code/schedc_cv/, code/parse_schedule_c_v2.py).

Unit tests use synthetic input. Golden rows read single FY2027 pages straight from the PDF in
source/ and compare with values written down by reading the rendered page (not copied from
parser output). The snapshot tests read the committed outputs in the review folder (config `review_dir`).

Run: pytest code/test_schedc.py
"""
import csv
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schedc import config, disclosure, review, structure, vector  # noqa: E402

CFG = config.load(2027)
OUT = os.path.join(config.ROOT, CFG["review_dir"], "data")


# --- unit ---------------------------------------------------------------------------------------
def test_clean_text_rules():
    assert structure.clean_text("Home-\nDelivered Meals") == ("Home-Delivered Meals", ["wrap_hyphen"])
    assert structure.clean_text("Inc. -\nCouncil") == ("Inc. - Council", ["line_join"])
    assert structure.clean_text("a  b") == ("a b", ["ws_collapse"])
    assert structure.clean_text("plain") == ("plain", [])


def test_parse_amount_strict():
    assert structure.parse_amount("$5,000") == 5000
    assert structure.parse_amount("$135,000") == 135000
    for bad in ("5,000", "$5,00", "$5000,0", "-$5", "$ 5,000x"):
        assert structure.parse_amount(bad) is None


def test_statement_kinds_from_config():
    k = lambda t: structure.statement_kind(t, CFG)
    assert k("The Council has designated the following providers for Fiscal 2027:") == ("full", None, None)
    assert k("The Council will designate $275,000 post-adoption and has designated $4,225,000 "
             "to the following providers for Fiscal 2027:") == ("partial", 275000, 4225000)
    assert k("The Council will designate $750,000 post-adoption for Fiscal 2027.") == \
        ("reserve_only", 750000, None)
    assert k("The Council will designate $750,000 post-adoption for Fiscal 2027. Public Safety")[0] \
        == "unknown"


def test_chars_to_text_lines_and_gaps():
    c = lambda t, x0, top: dict(text=t, x0=x0, x1=x0 + 5, top=top, bottom=top + 10)
    chars = [c("a", 0, 0), c("b", 5, 0.5), c("c", 20, 0), c("d", 0, 14)]
    assert vector.chars_to_text(chars) == "ab c\nd"


def test_city_ein_name_rule():
    assert disclosure.name_ok("136400434", "Department of Education", "Department of Education - PS 1")
    assert not disclosure.name_ok("136400434", "Department of Parks and Recreation",
                                  "Department of Youth and Community Development")
    assert disclosure.name_ok("131111111", "Anything", "Something else")


def test_review_id_stable():
    assert review.review_id(2027, "H8.lattice", 463, 0, 6, "ein") == \
        review.review_id(2027, "H8.lattice", 463, 0, 6, "ein")
    assert review.review_id(2027, "H8.lattice", 463, 0, 6, "ein") != \
        review.review_id(2027, "H8.lattice", 463, 0, 7, "ein")


def test_ink_regions_find_a_dot():
    np = pytest.importorskip("numpy")
    from schedc_cv import ink
    m = np.zeros((200, 200), dtype=bool)
    assert ink.find_uncovered_regions(m, 16, 64, (0, 0)) == []
    m[50:60, 70:80] = True          # one 10x10 px glyph-sized blob
    regs = ink.find_uncovered_regions(m, 16, 64, (100, 1000))
    assert regs == [{"bbox": [170, 1050, 180, 1060], "ink_px": 100}]


# --- golden rows (read from the page images, 2026-10-20) -----------------------------------------
@pytest.fixture(scope="module")
def pages():
    return {p["page"]: p for p in vector.read_pdf(CFG["_pdf_abs"], pages={7, 205, 279, 306, 463})}


def _rows(pages, pns):
    return structure.build([pages[p] for p in pns], CFG)["awards"]


@pytest.mark.parametrize("pn,member,org,ein,amount,agency", [
    (279, "Felder", "Medicare Rights Center, Inc.", "133505372", 135000, "DFTA"),
    (7, "Joseph", "Access Justice Brooklyn, Inc. - Legal Assistance - Council District 40",
     "113155182", 5000, "DSS/HRA"),
    (306, "Brooks-Powers", "100 Suits for 100 Men, Inc. - Council District 31", "462971279", 7000, ""),
])
def test_golden_landscape_rows(pages, pn, member, org, ein, amount, agency):
    rows = [r for r in _rows(pages, [pn]) if r["ein"] == ein and r["amount"] == amount]
    assert len(rows) == 1
    r = rows[0]
    assert (r["member"] or r["sponsor"]) == member
    assert r["org"] == org
    assert r["agency"] == agency


def test_golden_portrait_rows_attach_to_box(pages):
    rows = _rows(pages, [205])
    amudim = [r for r in rows if r["org"] == "Amudim Community Resources, Inc."]
    assert len(amudim) == 1 and amudim[0]["ein"] == "470984801" and amudim[0]["amount"] == 50000
    assert amudim[0]["initiative"] == "Opioid Prevention and Treatment"
    aids = [r for r in rows if r["ein"] == "133562071"]
    assert {r["initiative"] for r in aids} == {"Peer Specialists Support"}
    assert sorted(r["amount"] for r in aids) == [75000, 125000]
    assert sum(r["amount"] for r in rows if r["initiative"] == "Opioid Prevention and Treatment") \
        == 3075000


def test_golden_p463_overflow_hyphen(pages):
    r = [r for r in _rows(pages, [463]) if r["award_id"] == "fy27-p463-t00-r006"][0]
    assert r["ein"] == "134113613" and "ein_overflow_hyphen" in r["row_flags"]


# --- snapshot of the committed outputs -----------------------------------------------------------
def _read(name):
    with open(os.path.join(OUT, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.skipif(not os.path.exists(OUT), reason="FY2027 outputs not built")
def test_snapshot_rows_and_total():
    rows = _read("fy27_sc_awards.csv")
    assert len(rows) == 9979
    assert sum(int(r["amount"]) for r in rows) == 655045412
    by = {}
    for r in rows:
        by[r["section"]] = by.get(r["section"], 0) + int(r["amount"])
    assert by == {"body": 605246412, "appendix_a": 5610000, "appendix_b": 36539000,
                  "appendix_c": 7650000}
    assert any(r["org"] == "Medicare Rights Center, Inc." and r["amount"] == "135000" for r in rows)


@pytest.mark.skipif(not os.path.exists(OUT), reason="FY2027 outputs not built")
def test_snapshot_checks_pass():
    txt = open(os.path.join(OUT, "fy27_sc_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "acceptance on p.279" in txt and "(PASS)" in txt
    assert "matched without the City-EIN name rule (the 2026-10-19 prototype's H17 floor, 9,859): 9,859" in txt
