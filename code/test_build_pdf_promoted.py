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
        fy = "20" + path.split("/")[1][2:]
        for r in rs:
            assert r["fiscal_year"] == fy, path
            assert os.path.exists(os.path.join(REPO, r["source_pdf"]))


def test_pdf_years(built):
    all_years = rows(built["data/pdf_years.csv"])
    assert {y["status"] for y in all_years} == {"reviewed"}
    tr = [y for y in all_years if y["fiscal_year"] == "2026" and y["family"] == "transparency"]
    assert len(tr) == 1
    assert tr[0]["issue"] == "103" and tr[0]["status"] == "reviewed" and tr[0]["rows"] == "4952"
    assert tr[0]["printed_totals_tied"] == "8/8"
    assert tr[0]["source_pdf"] == "source/FY26/transparency-resolutions/"
    ys = {y["family"]: y for y in all_years if y["fiscal_year"] == "2027"}
    y26 = {y["family"]: y for y in all_years if y["fiscal_year"] == "2026"}
    assert set(y26) == {"capital_sd", "schedule_c", "terms", "transparency"}
    assert y26["schedule_c"]["rows"] == "9765" and y26["schedule_c"]["issue"] == "103"
    assert y26["schedule_c"]["printed_totals_tied"] == "24/25"
    assert set(ys) == {"capital_sd", "schedule_c", "terms"}
    assert ys["capital_sd"]["rows"] == "1391" and ys["capital_sd"]["printed_totals_tied"] == "28/28"
    assert ys["terms"]["rows"] == "75"
    assert ys["schedule_c"]["rows"] == "9979" and ys["schedule_c"]["printed_totals_tied"] == "25/25"
    for y in ys.values():
        assert y["issue"] == "102"
    y26 = {y["family"]: y for y in all_years if y["fiscal_year"] == "2026"}
    assert y26["capital_sd"]["rows"] == "1456" and y26["capital_sd"]["printed_totals_tied"] == "33/33"
    assert y26["terms"]["rows"] == "68"
    for y in y26.values():
        assert y["issue"] == "103"


def test_counts(built):
    assert len(rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_orgs.csv"])) == 127
    assert len(rows(built["data/fy27/pdf/terms/fy27_terms_units.csv"])) == 269
    totals = rows(built["data/fy27/pdf/capital_sd/fy27_capital_sd_totals.csv"])
    assert all(t["status"] == "OK" for t in totals if t["status"])
    assert len(rows(built["data/fy26/pdf/capital_sd/fy26_capital_sd_orgs.csv"])) == 151
    assert len(rows(built["data/fy26/pdf/terms/fy26_terms_units.csv"])) == 245
    totals = rows(built["data/fy26/pdf/capital_sd/fy26_capital_sd_totals.csv"])
    assert all(t["status"] == "OK" for t in totals if t["status"])
    assert sum(t["kind"] == "summary" for t in totals) == 3 and \
        {t["pdf_page"] for t in totals if t["kind"] == "summary"} == {"65"}


def test_transparency_rows_carry_resolution(built):
    rs = rows(built["data/fy26/pdf/transparency/fy26_tr_rows.csv"])
    assert len(rs) == 4952
    dates = {r["resolution_seq"]: r["resolution_date"] for r in rs}
    assert dates["1"] == "2025-08-14" and dates["10"] == "2026-06-30"
    assert all(r["resolution_number"].startswith("Res ") for r in rs)
    rev = {r["review_id"]: r for r in rows(built["data/fy26/pdf/transparency/fy26_tr_review.csv"])}
    for r in rs:
        if r["review_id"]:
            assert r["review_id"] in rev and rev[r["review_id"]]["check_id"] in r["flags"].split(";")
    # The clipped Pilsudski row (Reso 08 p.19): what shows is kept, the rest is in hidden_text.
    r = next(r for r in rs if r["row_id"] == "fy26-tr08-p019-r002")
    assert r["org"].endswith("Modern History of Polan") and r["hidden_text"] == "org: d, Inc. - Stories of Greenpoint"
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "23-7164776" in t and "Restler" in t and "Banks" not in t


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


def test_bbox_covers_the_row_fy26(built):
    # Parts I/II upright (p.70), Part III rotated /Rotate 90 (p.81): both boxes hold their row.
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy26/pdf/capital_sd/fy26_capital_sd_projects.csv"])}
    r = proj[("II", "PV MA0005")]
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "PV MA0005" in t and "-183,000" in t and "EVENT STUDIO UPGRADE" in t
    o = next(o for o in rows(built["data/fy26/pdf/capital_sd/fy26_capital_sd_orgs.csv"])
             if o["budget_line"] == "PV MN07D")
    assert o["fy2026"] == "-183000" and o["pdf_page"] == "81"
    t = boxed_text(o["source_pdf"], int(o["pdf_page"]), o["bbox_pt"])
    assert "PV MN07D" in t and "(183,000" in t      # pdfium reads the rotated row out of order
    t = boxed_text(o["source_pdf"], int(o["org_pdf_page"]), o["org_bbox_pt"])
    assert "MANHATTAN COMMUNITY ACCESS CORPORATION" in t


def test_flags_link_to_review(built):
    for fy in ("fy27", "fy26"):
        proj = rows(built[f"data/{fy}/pdf/capital_sd/{fy}_capital_sd_projects.csv"])
        rev = {r["review_id"]: r for r in rows(built[f"data/{fy}/pdf/capital_sd/{fy}_capital_sd_review.csv"])}
        flagged = [r for r in proj if r["flags"]]
        assert flagged
        for r in flagged:
            ids = r["review_id"].split(";")
            assert all(i in rev for i in ids)
            assert set(r["flags"].split(";")) == {rev[i]["check_id"] for i in ids}


def test_fy25_capital_and_terms(built):
    y25 = {y["family"]: y for y in rows(built["data/pdf_years.csv"]) if y["fiscal_year"] == "2025"}
    assert y25["capital_sd"]["rows"] == "1508" and y25["capital_sd"]["printed_totals_tied"] == "32/32"
    assert y25["terms"]["rows"] == "65" and y25["terms"]["printed_totals_tied"] == "n/a"
    assert {y25[f]["issue"] for f in ("capital_sd", "terms")} == {"104"}
    assert len(rows(built["data/fy25/pdf/capital_sd/fy25_capital_sd_orgs.csv"])) == 129
    assert len(rows(built["data/fy25/pdf/terms/fy25_terms_units.csv"])) == 234
    # FY2025 prints 6 IDs on two rows each: both rows carry the C3.id_reused flag.
    proj = rows(built["data/fy25/pdf/capital_sd/fy25_capital_sd_projects.csv"])
    twice = [r for r in proj if r["part"] == "I" and r["sub_id"] == "HN CN018"]
    assert len(twice) == 2 and all("C3.id_reused" in r["flags"] for r in twice)
    rev = {r["review_id"]: r for r in rows(built["data/fy25/pdf/capital_sd/fy25_capital_sd_review.csv"])}
    for r in proj:
        if r["flags"]:
            ids = r["review_id"].split(";")
            assert set(r["flags"].split(";")) == {rev[i]["check_id"] for i in ids}
