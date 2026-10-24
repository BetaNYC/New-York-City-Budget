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
        # FY2020's and FY2019's capital books print no Part III, so their orgs tables are header
        # only (the MCP loader reads the file for every capital year and accepts no rows).
        # Schedule C's sub-awards table is written every year; only FY2019 and FY2018 print a
        # list of sub-awards (the Jobs to Build On partners).
        if path in ("data/fy20/pdf/capital_sd/fy20_capital_sd_orgs.csv",
                    "data/fy19/pdf/capital_sd/fy19_capital_sd_orgs.csv") or (
                path.endswith("_sc_subawards.csv") and "/fy19/" not in path and "/fy18/" not in path):
            assert not rs and set(bp.CONTRACT) <= set(text.splitlines()[0].split(",")), path
            continue
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


def test_fy25_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2025" and y["family"] == "schedule_c")
    assert y["issue"] == "104" and y["status"] == "reviewed" and y["rows"] == "9579"
    assert y["printed_totals_tied"] == "24/25"
    aw = rows(built["data/fy25/pdf/schedule_c/fy25_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 471876698
    r = next(r for r in aw if r["award_id"] == "fy25-p169-t01-r001")   # Bronx Defenders
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Bronx Defenders" in t and "13-3931074" in t and "Brooklyn Defender" not in t


def test_fy24_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2024" and y["family"] == "schedule_c")
    assert y["issue"] == "105" and y["status"] == "reviewed" and y["rows"] == "9291"
    assert y["printed_totals_tied"] == "24/25"
    aw = rows(built["data/fy24/pdf/schedule_c/fy24_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 453858561
    # p.242's MediaBox starts at (-18.03, 17.97); bbox_pt is from its top-left corner.
    r = next(r for r in aw if r["pdf_page"] == "242" and r["ein"] == "133505372")
    doc = pdfium.PdfDocument(os.path.join(REPO, r["source_pdf"]))
    try:
        pg = doc[241]
        mx0, _, _, my1 = pg.get_mediabox()
        x0, top, x1, bottom = (float(v) for v in r["bbox_pt"].split(","))
        t = pg.get_textpage().get_text_bounded(left=mx0 + x0, bottom=my1 - bottom,
                                               right=mx0 + x1, top=my1 - top)
    finally:
        doc.close()
    assert "Medicare Rights Center" in t and "MercyFirst" not in t and "CBO Capacity" not in t


def test_fy23_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2023" and y["family"] == "schedule_c")
    assert y["issue"] == "106" and y["status"] == "reviewed" and y["rows"] == "5925"
    assert y["printed_totals_tied"] == "26/26"
    aw = rows(built["data/fy23/pdf/schedule_c/fy23_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 323063807
    assert sum(int(r["amount"]) for r in aw if r["section"] == "appendix_b") == 36539000
    # One of the two Local rows the old parse lost (DATA-ANOMALIES §19): its box holds it.
    r = next(r for r in aw if r["award_id"] == "fy23-p235-t00-r018")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Laundromat Project" in t and "Latinas" not in t


def test_fy22_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2022" and y["family"] == "schedule_c")
    assert y["issue"] == "107" and y["status"] == "reviewed" and y["rows"] == "5732"
    assert y["printed_totals_tied"] == "25/25"
    aw = rows(built["data/fy22/pdf/schedule_c/fy22_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 285155968
    # A row of the four-column table the old parse lost; its box holds it, not its neighbours.
    r = next(r for r in aw if r["award_id"] == "fy22-p084-t03-r001")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Society of the Educational" in t and "Heritage High School" in t and "Groove" not in t


def test_fy21_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2021" and y["family"] == "schedule_c")
    assert y["issue"] == "108" and y["status"] == "reviewed" and y["rows"] == "6179"
    assert y["printed_totals_tied"] == "26/26"
    aw = rows(built["data/fy21/pdf/schedule_c/fy21_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 262477792
    # A row of a table whose header is printed outside its rules; its box holds it.
    r = next(r for r in aw if r["award_id"] == "fy21-p045-t00-r002")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Instituto Arte Teatral" in t and "ID Studio" not in t


def test_fy20_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2020" and y["family"] == "schedule_c")
    assert y["issue"] == "109" and y["status"] == "reviewed" and y["rows"] == "7921"
    assert y["printed_totals_tied"] == "27/27"
    aw = rows(built["data/fy20/pdf/schedule_c/fy20_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 336750073
    # An Appendix A row printed with no "$" (#59); its box holds it, not its neighbours.
    r = next(r for r in aw if r["award_id"] == "fy20-p190-t00-r002")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Wellness Program" in t and "19,000" in t and "Abe Stark" not in t


def test_fy19_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2019" and y["family"] == "schedule_c")
    assert y["issue"] == "110" and y["status"] == "reviewed" and y["rows"] == "5995"
    assert y["printed_totals_tied"] == "27/27"
    aw = rows(built["data/fy19/pdf/schedule_c/fy19_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 248436176
    # An Appendix A row printed with no "$" (#59); its box holds it, not its neighbours.
    r = next(r for r in aw if r["award_id"] == "fy19-p133-t00-r002")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Holocaust Survivors" in t and "6,500" in t and "Senior Stars" not in t


def test_fy18_schedule_c(built):
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2018" and y["family"] == "schedule_c")
    assert y["issue"] == "111" and y["status"] == "reviewed" and y["rows"] == "5906"
    assert y["printed_totals_tied"] == "25/26"   # Community Development (p.38), named
    aw = rows(built["data/fy18/pdf/schedule_c/fy18_sc_awards.csv"])
    assert sum(int(r["amount"]) for r in aw) == 203804505
    # An Appendix A row printed with cents; its box holds it, not its neighbours.
    r = next(r for r in aw if r["award_id"] == "fy18-p131-t00-r002")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "19,000.00" in t and "Williams" in t and "100,500" not in t
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


def test_fy24_capital_and_terms(built):
    y24 = {y["family"]: y for y in rows(built["data/pdf_years.csv"]) if y["fiscal_year"] == "2024"}
    assert y24["capital_sd"]["rows"] == "1364" and y24["capital_sd"]["printed_totals_tied"] == "32/32"
    assert y24["terms"]["rows"] == "61" and y24["terms"]["printed_totals_tied"] == "n/a"
    assert {y24[f]["issue"] for f in ("capital_sd", "terms")} == {"105"}
    assert len(rows(built["data/fy24/pdf/capital_sd/fy24_capital_sd_orgs.csv"])) == 113
    assert len(rows(built["data/fy24/pdf/terms/fy24_terms_units.csv"])) == 187
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy24/pdf/capital_sd/fy24_capital_sd_projects.csv"])}
    assert proj[("II", "HL TA001")]["fy2024"] == "-40000" and "C3.part2_only" in proj[("II", "HL TA001")]["flags"]


def test_fy23_capital_and_terms(built):
    y23 = {y["family"]: y for y in rows(built["data/pdf_years.csv"]) if y["fiscal_year"] == "2023"}
    assert y23["capital_sd"]["rows"] == "1547" and y23["capital_sd"]["printed_totals_tied"] == "32/32"
    assert y23["terms"]["rows"] == "60" and y23["terms"]["printed_totals_tied"] == "n/a"
    assert {y23[f]["issue"] for f in ("capital_sd", "terms")} == {"106"}
    assert len(rows(built["data/fy23/pdf/capital_sd/fy23_capital_sd_orgs.csv"])) == 115
    assert len(rows(built["data/fy23/pdf/terms/fy23_terms_units.csv"])) == 158
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy23/pdf/capital_sd/fy23_capital_sd_projects.csv"])}
    assert proj[("I", "E CN136")]["fy2023"] == "150000" and "C9.workbook_no_amount" in proj[("I", "E CN136")]["flags"]
    assert proj[("I", "HA RR002")]["sponsor"] == "" and proj[("I", "HA RR002")]["boro"] == "A"


def test_fy22_capital_and_terms(built):
    y22 = {y["family"]: y for y in rows(built["data/pdf_years.csv"]) if y["fiscal_year"] == "2022"}
    assert y22["capital_sd"]["rows"] == "1641" and y22["capital_sd"]["printed_totals_tied"] == "34/34"
    assert y22["terms"]["rows"] == "50" and y22["terms"]["printed_totals_tied"] == "n/a"
    assert {y22[f]["issue"] for f in ("capital_sd", "terms")} == {"107"}
    assert len(rows(built["data/fy22/pdf/capital_sd/fy22_capital_sd_orgs.csv"])) == 122
    assert len(rows(built["data/fy22/pdf/terms/fy22_terms_units.csv"])) == 134
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy22/pdf/capital_sd/fy22_capital_sd_projects.csv"])}
    assert proj[("II", "PW MBP01")]["fy2022"] == "-72000" and "C3.part2_only" in proj[("II", "PW MBP01")]["flags"]
    assert proj[("I", "AG TANC1")]["fy2022"] == "331000"


def test_fy19_capital(built):
    proj = {r["sub_id"]: r for r in rows(built["data/fy19/pdf/capital_sd/fy19_capital_sd_projects.csv"])}
    assert len(rows(built["data/fy19/pdf/capital_sd/fy19_capital_sd_projects.csv"])) == 1625
    r = proj["CS NC001"]                                   # p.1: the CD codes and the key's names
    assert (r["sponsor_raw"], r["council_district"], r["sponsor"]) == ("00, 37", "00, 37", "Speaker, Espinal")
    assert proj["E CN403"]["boro"] == "k" and "C6.boro" in proj["E CN403"]["flags"]
    tot = rows(built["data/fy19/pdf/capital_sd/fy19_capital_sd_totals.csv"])
    assert [(t["kind"], t["printed_count"], t["printed_fy2019"], t["status"]) for t in tot] == \
        [("totals_for", "", "614910000", "OK")]           # p.54; no count, no summary page
    y = next(y for y in rows(built["data/pdf_years.csv"])
             if y["fiscal_year"] == "2019" and y["family"] == "capital_sd")
    assert (y["family"], y["issue"], y["rows"], y["printed_totals_tied"]) == ("capital_sd", "110", "1625", "1/1")


def test_fy18_capital_and_terms(built):
    proj = {(r["part"], r["sub_id"]): r for r in rows(built["data/fy18/pdf/capital_sd/fy18_capital_sd_projects.csv"])}
    assert len(proj) == 1718 and len(rows(built["data/fy18/pdf/capital_sd/fy18_capital_sd_orgs.csv"])) == 170
    assert proj[("II", "HH TA003")]["fy2018"] == "-100000" and "C3.part2_only" in proj[("II", "HH TA003")]["flags"]
    assert proj[("I", "E CN765")]["sponsor"] == "DISTRICT 28"                    # p.43, as printed
    tot = rows(built["data/fy18/pdf/capital_sd/fy18_capital_sd_totals.csv"])
    assert len(tot) == 35 and all(t["status"] == "OK" and t["kind"] == "totals_for" for t in tot)
    conds = rows(built["data/fy18/pdf/terms/fy18_terms_conditions.csv"])
    assert len(conds) == 33 and conds[1]["budget_lines"] == "All Project Lines – All Projects"
    fsr = rows(built["data/fy18/pdf/terms/fy18_terms_fsr_table.csv"])
    assert len(fsr) == 6 and fsr[-1]["report_content"] == "FY18 FSR update; FY19 Executive Budget Summary"
    ys = {y["family"]: y for y in rows(built["data/pdf_years.csv"]) if y["fiscal_year"] == "2018"}
    assert ys["capital_sd"]["printed_totals_tied"] == "35/35" and ys["terms"]["rows"] == "33"
    assert {y["issue"] for y in ys.values()} == {"111"}


# ------------------------------------------------------------------ W8 schema fields (#209, #217)

SC_YEARS = range(2018, 2028)
TR_YEARS = range(2018, 2027)


def _sc(built, fy, name="awards"):
    return rows(built[f"data/fy{fy % 100}/pdf/schedule_c/fy{fy % 100}_sc_{name}.csv"])


def test_new_fields_in_every_year(built):
    sc_new = ["program_or_subheading", "program_or_subheading_raw", "review_not_completed",
              "fiscal_conduit", "fiscal_conduit_ein", "fiscal_conduit_raw",
              "fiscal_conduit_ein_printed", "read_from_page_image"]
    for fy in SC_YEARS:
        hdr = built[f"data/fy{fy % 100}/pdf/schedule_c/fy{fy % 100}_sc_awards.csv"].splitlines()[0].split(",")
        assert hdr[-len(sc_new):] == sc_new, fy
    tr_new = ["fiscal_conduit", "fiscal_conduit_ein", "fiscal_conduit_raw", "fiscal_conduit_ein_printed",
              "amount_kind", "read_from_page_image"]
    for fy in TR_YEARS:
        hdr = built[f"data/fy{fy % 100}/pdf/transparency/fy{fy % 100}_tr_rows.csv"].splitlines()[0].split(",")
        assert hdr[-len(tr_new):] == tr_new, fy
    # Blank where the PDF prints none: conduits FY2018 only; the "*" FY2019 and FY2018 only.
    for fy in SC_YEARS:
        aw = _sc(built, fy)
        assert any(r["fiscal_conduit"] for r in aw) == (fy == 2018), fy
        assert any(r["review_not_completed"] for r in aw) == (fy in (2018, 2019)), fy
        # Only rows a person decided read_from_page_image (2026-10-22: FY2023 Laundromat Project).
        page = [r["review_id"] for r in aw if r["read_from_page_image"]]
        assert page == (["42eba5fef74a"] if fy == 2023 else []), fy
    for fy in TR_YEARS:
        rs = rows(built[f"data/fy{fy % 100}/pdf/transparency/fy{fy % 100}_tr_rows.csv"])
        assert any(r["fiscal_conduit"] or r["fiscal_conduit_ein_printed"] for r in rs) == (fy == 2018), fy
        page = [r["review_id"] for r in rs if r["read_from_page_image"]]
        assert page == (["68a35940ec45"] if fy == 2019 else []), fy     # Himalayan Elders, 2026-10-22


def test_fiscal_conduit_schedule_c_fy18(built):
    aw = _sc(built, 2018)
    fc = [r for r in aw if r["fiscal_conduit"] or r["fiscal_conduit_ein_printed"]]
    # 50 rows print something in the conduit column: 49 conduits (48 with an EIN; p.242 prints
    # "13-281380", 8 digits) and p.271's drafting note, which is not a conduit.
    assert len(fc) == 49 and all("W.fiscal_conduit" in r["flags"] for r in fc)
    assert sum(1 for r in fc if r["fiscal_conduit_ein"]) == 48
    # Only p.242 (no well-formed FC EIN) and p.271's note are review items; the 48 stored
    # conduits with an EIN are not.
    rv = {x["review_id"]: x for x in rows(built["data/fy18/pdf/schedule_c/fy18_sc_review.csv"])}
    assert {x["award_id"] for x in rv.values() if x["check_id"] == "W.fiscal_conduit"} == {
        "fy18-p242-t00-r011", "fy18-p271-t00-r014"}
    assert not any("fiscal_conduit" in r["row_flags"].split(";") for r in aw if r not in fc)
    r = next(r for r in aw if r["award_id"] == "fy18-p271-t00-r014")
    assert (r["fiscal_conduit"], r["fiscal_conduit_raw"]) == ("", "Please indicate the actuals\nschools.")
    assert "conduit_note" in r["row_flags"] and "W.fiscal_conduit" in r["flags"]
    r = next(r for r in aw if r["award_id"] == "fy18-p242-t00-r011")
    assert (r["fiscal_conduit_ein"], r["fiscal_conduit_ein_printed"]) == ("", "13-281380")
    assert "not an EIN" in rv["1361ec218029"]["what_to_check"]
    assert "not a conduit" in rv["f0d35523ca12"]["what_to_check"]
    # p.34 (test_schedc golden): Staten Island Hindu Temple through the JCC of Staten Island.
    r = next(r for r in aw if r["ein"] == "133981477" and r["amount"] == "4000")
    assert (r["fiscal_conduit"], r["fiscal_conduit_ein"]) == (
        "Jewish Community Center of Staten Island, Inc.", "135562256")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Staten Island Hindu Temple" in t and "135562256" in t     # printed with no hyphen


def test_review_not_completed_is_the_asterisk(built):
    for fy, n in ((2019, 304), (2018, 1504)):
        aw = _sc(built, fy)
        star = [r for r in aw if r["review_not_completed"] == "1"]
        assert len(star) == n, fy
        assert all("asterisk" in r["row_flags"].split(";") for r in star)
        assert all(r["review_not_completed"] in ("0", "") for r in aw if "asterisk" not in r["row_flags"].split(";"))
    # FY2019 p.13: 100 Suits for 100 Men prints "*" in its row.
    r = next(r for r in _sc(built, 2019) if r["pdf_page"] == "13" and r["ein"] == "462971279" and r["amount"] == "5000")
    assert r["review_not_completed"] == "1"


def test_program_or_subheading_out_of_purpose(built):
    # FY2018-FY2022 Art as a Catalyst for Change ("School" FY2018, "Program" after) and FY2021's
    # sub-headings (pp.70-72): in program_or_subheading; purpose keeps only a printed purpose.
    got = {fy: [r for r in _sc(built, fy) if r["program_or_subheading"]] for fy in SC_YEARS}
    # FY2019 p.94 r026 prints only "*" in its Program cell: no program, its mark recorded.
    assert {fy: len(v) for fy, v in got.items() if v} == {2018: 35, 2019: 36, 2020: 36, 2021: 103, 2022: 36}
    sub21 = [r for r in got[2021] if "subheading" in r["row_flags"].split(";")]
    assert len(sub21) == 67 and {r["program_or_subheading"] for r in sub21} == {
        "Technical Assistance", "Community Consultant Contracts", "Housing Preservation Initiative"}
    for fy, rs in got.items():
        for r in rs:
            assert r["purpose"] == "" and r["purpose_raw"] == "", (fy, r["award_id"])
            # The "*" is the row's mark (review_not_completed), not part of the school's name.
            assert not r["program_or_subheading"].endswith("*"), (fy, r["award_id"])
    starred = [r for fy in (2018, 2019) for r in _sc(built, fy)
               if r["program_or_subheading_raw"].rstrip().endswith("*")]
    assert len(starred) == 11 and all(r["review_not_completed"] == "1" for r in starred)
    r = next(r for r in starred if r["award_id"] == "fy19-p094-t00-r026")
    assert (r["program_or_subheading"], r["program_or_subheading_raw"]) == ("", "*")
    r = next(r for r in got[2022] if r["award_id"] == "fy22-p084-t03-r001")
    assert r["program_or_subheading"] == "Heritage High School"


def test_subawards_jobs_to_build_on(built):
    for fy, n_tables in ((2019, 2), (2018, 3)):
        subs = _sc(built, fy, "subawards")
        aw = {r["award_id"]: r for r in _sc(built, fy)}
        assert len(subs) == 28 and sum(int(r["amount"]) for r in subs) == 4463500, fy
        parents = {r["parent_award_id"] for r in subs}
        assert len(parents) == 1, fy
        p = aw[parents.pop()]
        assert p["ein"] == "133564313" and p["amount"] == "5154200" and "Jobs to Build On" in p["org"]
        # Not award rows, so in no award total: no award shares a sub-award's page and box.
        boxes = {(r["pdf_page"], r["bbox_pt"]) for r in aw.values()}
        assert not any((r["pdf_page"], r["bbox_pt"]) in boxes for r in subs)
        assert len({r["table_index"] + r["pdf_page"] for r in subs}) == n_tables
        assert all("K.side_list" in r["flags"].split(";") and r["review_id"] for r in subs)
        # Checked like awards: both grids (FY2019) or the pixels' row rules and columns (FY2018's
        # tables have no vertical rules; #193), and every EIN and amount read.
        assert {r["image_check"] for r in subs} == ({"agree"} if fy == 2019 else {"columns_agree"}), fy
        assert all(r["ein"] and r["amount"] for r in subs)
    # Award and category totals are main's (3af3c7c): sub-awards are counted in neither.
    CAT_TOTALS = {2019: 338301000, 2018: 330801000}   # category TOTAL lines, as on main
    for fy, awards_total in ((2019, 248436176), (2018, 203804505)):
        assert sum(int(r["amount"]) for r in _sc(built, fy)) == awards_total, fy
        cats = _sc(built, fy, "categories")
        assert sum(int(r["amount"]) for r in cats if r["line"] == "TOTAL") == CAT_TOTALS[fy], fy
    # A row whose service type wraps to a second ruled band (FY2019 p.105, "Placement").
    r = next(r for r in _sc(built, 2019, "subawards") if r["subaward_id"] == "fy19-sub-p105-t01-r012")
    assert (r["org"], r["amount"], r["service_type"]) == (
        "Members Assistance Program, Inc. (MAP)", "200000", "Occupational Training and Job Placement")
    t = boxed_text(r["source_pdf"], int(r["pdf_page"]), r["bbox_pt"])
    assert "Members Assistance" in t and "Placement" in t and "St. Nick" not in t
    # FY2018 prints "Amount" and "Service Type" in one header cell (p.106).
    r = next(r for r in _sc(built, 2018, "subawards") if r["org"] == "Henry Street Settlement")
    assert (r["amount"], r["service_type"], r["amount_printed"]) == ("273000", "Job Placement", "$273,000")


def test_no_dollar_amount_rows_are_marked_and_skipped(built):
    want = {2018: 136, 2019: 112, 2020: 73, 2021: 28, 2022: 91}
    for fy in TR_YEARS:
        yy = fy % 100
        rs = rows(built[f"data/fy{yy}/pdf/transparency/fy{yy}_tr_rows.csv"])
        nd = [r for r in rs if r["amount_kind"] == "no_dollar_amount"]
        assert len(nd) == want.get(fy, 0), fy
        assert {r["amount_kind"] for r in rs} <= {"dollar_amount", "no_dollar_amount"}
        assert all(r["amount"] == "" and r["chart_kind"] == "no_amount" for r in nd)
        assert all(r["amount"] != "" for r in rs if r["amount_kind"] == "dollar_amount"), fy
        # Every sum the promoted tables print skips them: each chart's sums equal its dollar rows'.
        for c in rows(built[f"data/fy{yy}/pdf/transparency/fy{yy}_tr_charts.csv"]):
            amts = [int(r["amount"]) for r in rs if r["resolution_seq"] == c["resolution_seq"]
                    and r["chart_number"] == c["chart_number"] and r["amount_kind"] == "dollar_amount"]
            assert int(c["net"]) == sum(amts) and int(c["positive_sum"]) == sum(a for a in amts if a > 0)


def _decide(path, review_id, note):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["review_id", "decision", "note", "decided_by", "decided_at"])
        w.writerow([review_id, "read_from_page_image", note, "test", "2026-10-22"])


def test_page_image_decision_reaches_the_row_and_the_disclosure(tmp_path):
    # The page-image rule (#209), end to end, with a throwaway decisions file (the committed ones
    # decide nothing yet): the reader uses the page's EIN, keeps the text layer's, flags the row,
    # and aligns the disclosure on the page's value. --no-cv: the image checks are not under test.
    import contextlib
    import parse_schedule_c_v2 as sc
    import parse_transparency_v2 as tr
    d = tmp_path / "sc23"
    d.mkdir()
    _decide(d / "fy23_sc_review_decisions.csv", "42eba5fef74a", 'page shows ein: "87-0753479"')
    with contextlib.redirect_stdout(io.StringIO()):
        assert sc.main(["--fy", "2023", "--no-cv", "--out", str(d)]) == 0
    r = next(r for r in rows(open(d / "fy23_sc_awards.csv", encoding="utf-8").read())
             if r["award_id"] == "fy23-p235-t00-r018")
    assert (r["ein"], r["ein_printed"], r["read_from_page_image"]) == ("870753479", "87 0753479", "ein")
    assert "ein_unreadable" not in r["row_flags"] and "ein_read_from_page_image" in r["row_flags"]
    assert "H5.anchors" in r["flags"]                   # still linked to its review item
    assert r["disclosure_status"] == "cleared"          # unmatched (pdf_value_unreadable) as printed
    d = tmp_path / "tr19"
    d.mkdir()
    _decide(d / "fy19_tr_review_decisions.csv", "68a35940ec45", 'page shows ein: "472383238"')
    with contextlib.redirect_stdout(io.StringIO()):
        assert tr.main(["--fy", "2019", "--no-cv", "--out", str(d)]) == 0
    r = next(r for r in rows(open(d / "fy19_tr_rows.csv", encoding="utf-8").read())
             if r["row_id"] == "fy19-tr03-p046-r016")
    assert (r["ein"], r["ein_printed"], r["read_from_page_image"]) == ("472383238", "472383238(cid:9)", "ein")
    assert r["ein_format"] == "page_image" and "ein_odd" not in r["row_flags"].split(";")
    assert r["disclosure_status"] == "matched"
