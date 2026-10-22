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


def test_fy25_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2025" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "104" and y["status"] == "reviewed" and y["rows"] == "3555"
    assert y["printed_totals_tied"] == "3/3"
    assert y["source_pdf"] == "source/FY25/transparency-resolutions/"
    rs = rows(built["data/fy25/pdf/transparency/fy25_tr_rows.csv"])
    assert len(rs) == 3555 and all(r["resolution_date"] for r in rs)
    dates = {r["resolution_seq"]: r["resolution_date"] for r in rs}
    assert dates["1"] == "2024-08-15" and dates["13"] == "2025-06-30"
    # Reso 04 (2024-10-23) has no resolution number on record; every other row has one.
    assert {r["resolution_seq"] for r in rs if not r["resolution_number"].startswith("Res ")} == {"4"}
    rev = {r["review_id"]: r for r in rows(built["data/fy25/pdf/transparency/fy25_tr_review.csv"])}
    for r in rs:
        if r["review_id"]:
            assert r["review_id"] in rev and rev[r["review_id"]]["check_id"] in r["flags"].split(";")
    # Reso 07 p.30: "01/" shows in the * column; the staff note past the table is hidden.
    r = next(r for r in rs if r["row_id"] == "fy25-tr07-p030-r003")
    assert r["prequal_printed"] == "01/" and r["prequal_pending"] == "0"
    assert r["hidden_text"].startswith("prequal: 22; DCLA: We checked")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "13-3682472" in t and "Midori" in t


def test_fy24_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2024" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "105" and y["status"] == "reviewed" and y["rows"] == "3303"
    assert y["printed_totals_tied"] == "n/a"
    assert y["source_pdf"] == "source/FY24/transparency-resolutions/"
    rs = rows(built["data/fy24/pdf/transparency/fy24_tr_rows.csv"])
    assert len(rs) == 3303
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs)
    # Reso 01 p.3 is /Rotate 90: the promoted box is on the unrotated page and holds its row.
    r = next(r for r in rs if r["row_id"] == "fy24-tr01-p003-r001")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert t == ("Marte Society of the Third Street Music School Settlement - Third Street Partners "
                 "13-5596825 DCLA ($5,000) 126 003")
    # An upright page needs no turn: Reso 02 p.11, the clipped "Staten Island Delegatio".
    r = next(r for r in rs if r["row_id"] == "fy24-tr02-p011-r001")
    assert r["member"] == "Staten Island Delegatio" and r["hidden_text"] == "member: n"
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "81-0728516" in t and "South Shore" in t


def test_fy23_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2023" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "106" and y["status"] == "reviewed" and y["rows"] == "8424"
    assert y["printed_totals_tied"] == "n/a"
    assert y["source_pdf"] == "source/FY23/transparency-resolutions/"
    rs = rows(built["data/fy23/pdf/transparency/fy23_tr_rows.csv"])
    assert len(rs) == 8424
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs)
    # Reso 08 p.32: chart #25's first page prints "(continued)"; its rows are kept.
    r = next(r for r in rs if r["row_id"] == "fy23-tr08-p032-r001")
    assert r["chart_number"] == "25" and r["amount"] == "-1000000"
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert t == "Legal Aid Society ** 13-5562265 MOCJ ($1,000,000) 098 002"


def test_fy22_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2022" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "107" and y["status"] == "reviewed" and y["rows"] == "7918"
    assert y["printed_totals_tied"] == "n/a"
    rs = rows(built["data/fy22/pdf/transparency/fy22_tr_rows.csv"])
    assert len(rs) == 7918
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs)
    assert sum(1 for r in rs if r["action"] == "listed" and r["amount"] == "") == 91
    # Reso 02 p.29: the media box starts at (-8.39, -8.39); the promoted box is on the page as
    # rendered, so in PDF space it is offset by the box's origin.
    r = next(r for r in rs if r["row_id"] == "fy22-tr02-p029-r001")
    doc = pdfium.PdfDocument(os.path.join(REPO, r["source_pdf"]))
    try:
        pg = doc[int(r["pdf_page"]) - 1]
        mb = pg.get_mediabox()
        x0, top, x1, bottom = (float(v) for v in r["bbox_pt"].split(","))
        t = pg.get_textpage().get_text_bounded(left=x0 + mb[0], bottom=mb[3] - bottom,
                                               right=x1 + mb[0], top=mb[3] - top)
    finally:
        doc.close()
    assert t == ("Gennaro Outstanding Renewal Enterprises, Inc. - E-Waste Collection - Council "
                 "District 24 13-3320984 DYCD ($10,000) 260 005")



def test_fy21_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2021" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "108" and y["status"] == "reviewed" and y["rows"] == "4500"
    assert y["printed_totals_tied"] == "n/a"
    rs = {r["row_id"]: r for r in rows(built["data/fy21/pdf/transparency/fy21_tr_rows.csv"])}
    assert len(rs) == 4500
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs.values())
    assert sum(1 for r in rs.values() if r["action"] == "listed" and r["amount"] == "") == 28
    # Reso 02 p.29: the row under the one with no EIN; Reso 01 p.126: a portrait "Beating
    # Hearts" page (no agency, no amount).
    r = rs["fy21-tr02-p029-r021"]
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]) == (
        "Adams Bartlett Foundation, The - Council District 28 ** 90-0952784 DYCD $10,000 260 005")
    r = rs["fy21-tr01-p126-r001"]
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]) == (
        "Koslowitz Ronald McDonald House of Long Island, Inc. 11-2764747")


def test_fy20_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2020" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "109" and y["status"] == "reviewed" and y["rows"] == "5396"
    assert y["printed_totals_tied"] == "n/a"
    rs = {r["row_id"]: r for r in rows(built["data/fy20/pdf/transparency/fy20_tr_rows.csv"])}
    assert len(rs) == 5396
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs.values())
    assert sum(1 for r in rs.values() if r["action"] == "listed" and r["amount"] == "") == 73
    # Reso 01 p.70 ("Chart #35:") and Reso 06 p.25 ("CHART #:", read as chart #16): rows on
    # pages whose captions the reader rewrites.
    r = rs["fy20-tr01-p070-r001"]
    assert r["chart_number"] == "35"
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]).startswith(
        "Local Borelli Columcille Cultural Center, Inc. 13-3909562 DYCD ($2,500) Funds will be")
    r = rs["fy20-tr06-p025-r001"]
    assert r["chart_number"] == "16"
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]).startswith(
        "Youth Richards Jewish Community Council of the")

def test_fy19_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2019" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "110" and y["status"] == "reviewed" and y["rows"] == "7207"
    assert y["printed_totals_tied"] == "n/a"
    rs = {r["row_id"]: r for r in rows(built["data/fy19/pdf/transparency/fy19_tr_rows.csv"])}
    assert len(rs) == 7207
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs.values())
    assert sum(1 for r in rs.values() if r["action"] == "listed" and r["amount"] == "") == 112
    r = rs["fy19-tr01-p018-r001"]
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]).startswith(
        "Van Bramer Jacob A. Riis Neighborhood Settlement, Inc. - Friends of Queensbridge Park 11-1729398")
    # Reso 01 p.108 prints "CHART 55" on chart #56's first page (T3.chart_number).
    r = rs["fy19-tr01-p108-r001"]
    assert r["chart_number"] == "56" and r["budget_fiscal_year"] == "2018"
    assert "Citywide Icahn School of Medicine at Mount Sinai 13-6171197" in boxed_text(
        r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    # Reso 07 p.27: an overfull cell, read as one block (T7.overfull).
    assert rs["fy19-tr07-p027-r017"]["org"].startswith("Greenwich House, Inc.")


def test_fy18_transparency(built):
    ys = [y for y in rows(built["data/pdf_years.csv"])
          if y["fiscal_year"] == "2018" and y["family"] == "transparency"]
    assert len(ys) == 1
    y = ys[0]
    assert y["issue"] == "111" and y["status"] == "reviewed" and y["rows"] == "5558"
    assert y["printed_totals_tied"] == "n/a"
    rs = {r["row_id"]: r for r in rows(built["data/fy18/pdf/transparency/fy18_tr_rows.csv"])}
    assert len(rs) == 5558
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rs.values())
    assert sum(1 for r in rs.values() if r["action"] == "listed" and r["amount"] == "") == 136
    # Reso 01 p.55 prints a header row with no labels (T4.blank_header).
    r = rs["fy18-tr01-p055-r001"]
    assert (r["org"], r["amount"]) == ("Rugby Family Services", "-3500")
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]) == (
        "Williams Rugby Family Services 11-3223904 DYCD ($3,500.00) 260 312")
    # A fiscal conduit (FY2018 only columns).
    r = rs["fy18-tr01-p013-r018"]
    assert (r["fiscal_conduit"], r["fiscal_conduit_ein"]) == ("Greater Ridgewood Youth Council, Inc.", "112518141")
    assert boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"]).endswith(
        "Greater Ridgewood Youth Council, Inc. 11-2518141 *")


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
