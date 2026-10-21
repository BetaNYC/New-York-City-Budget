#!/usr/bin/env python3
"""
Tests for code/build_pdf_promoted.py: the committed data/fyNN/pdf/ files and data/pdf_years.csv
equal a fresh regeneration from the PDFs, and every table follows the row contract
(viz/explorer/INTEGRATION.md §1).

Run: pytest code/test_build_pdf_promoted.py
"""
import csv
import io
import os
import sys

import pypdfium2 as pdfium
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_pdf_promoted as bp  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return bp.build_all()


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_committed_files_equal_regeneration(built):
    for path, text in built.items():
        with open(os.path.join(REPO, path), encoding="utf-8") as f:
            assert f.read() == text, f"{path} drifted: run build_pdf_promoted.py --write"


def test_row_contract(built):
    for path, text in built.items():
        if path.endswith("pdf_years.csv"):
            continue
        rs = rows(text)
        assert rs, path
        for col in bp.CONTRACT if not path.endswith("_review.csv") else ["fiscal_year", "source_pdf", "pdf_sha256"]:
            assert col in rs[0], (path, col)
        fy = "20" + path.split("/")[1][2:]          # data/fyNN/...
        for r in rs:
            assert r["fiscal_year"] == fy
            assert os.path.exists(os.path.join(REPO, r["source_pdf"]))


def test_pdf_years(built):
    all_ys = rows(built["data/pdf_years.csv"])
    assert {y["status"] for y in all_ys} == {"reviewed"}
    y26 = {y["family"]: y for y in all_ys if y["fiscal_year"] == "2026"}
    assert set(y26) == {"schedule_c"}
    assert y26["schedule_c"]["rows"] == "9765" and y26["schedule_c"]["issue"] == "103"
    assert y26["schedule_c"]["printed_totals_tied"] == "24/25"
    ys = {y["family"]: y for y in all_ys if y["fiscal_year"] == "2027"}
    assert set(ys) == {"capital_sd", "schedule_c", "terms"}
    assert ys["capital_sd"]["rows"] == "1391" and ys["capital_sd"]["printed_totals_tied"] == "28/28"
    assert ys["terms"]["rows"] == "75"
    assert ys["schedule_c"]["rows"] == "9979" and ys["schedule_c"]["printed_totals_tied"] == "25/25"
    for y in ys.values():
        assert y["issue"] == "102"


def test_counts(built):
    assert len(rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_orgs.csv"])) == 127
    assert len(rows(built["data/fy27/pdf/terms/fy27_terms_units.csv"])) == 269
    totals = rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_totals.csv"])
    assert all(t["status"] == "OK" for t in totals if t["status"])


def test_unrotate():
    # p.40 'H' at display (206.41, 38.68, 214.72, 50.20) on a /Rotate 90 page shown 792 x 612;
    # pdfium's unrotated glyph box is x 39.5-47.8, y-from-top 578.2-584.8.
    assert bp.unrotate("206.41,38.68,214.72,50.20", 90, 792, 612) == "38.68,577.28,50.20,585.59"
    assert bp.unrotate("1,2,3,4", 0, 612, 792) == "1.00,2.00,3.00,4.00"


def boxed_text(pdf, page, bbox):
    doc = pdfium.PdfDocument(os.path.join(REPO, pdf))
    try:
        pg = doc[page - 1]
        h = pg.get_mediabox()[3]
        x0, top, x1, bottom = (float(v) for v in bbox.split(","))
        return pg.get_textpage().get_text_bounded(left=x0, bottom=h - bottom, right=x1, top=h - top)
    finally:
        doc.close()


def test_bbox_covers_the_row(built):
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_projects.csv"])}
    r = proj[("I", "HR CC0168")]
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "HR CC0168" in t and "ALI FORNEY" in t and "ABREU" in t and "HR CC1253" not in t
    c = rows(built["data/fy27/pdf/terms/fy27_terms_conditions.csv"])[0]
    t = boxed_text(c["source_pdf"], int(c["pdf_page"]), c["bbox_pt"])
    assert t.startswith("1. City University of New York (042)") and "2. City" not in t


def test_flags_link_to_review(built):
    proj = rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_projects.csv"])
    rev = {r["review_id"]: r for r in rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_review.csv"])}
    flagged = [r for r in proj if r["flags"]]
    assert flagged
    for r in flagged:
        ids = r["review_id"].split(";")
        assert all(i in rev for i in ids)
        assert set(r["flags"].split(";")) == {rev[i]["check_id"] for i in ids}
