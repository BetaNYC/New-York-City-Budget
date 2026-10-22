"""
Tests for the transparency-resolution reader (code/transreso/, code/parse_transparency_v2.py).

Unit tests use synthetic characters. Golden rows read single FY2026 pages straight from the
PDFs in source/ and compare with values written down by looking at the rendered page (not
copied from parser output). Snapshot tests read the committed outputs in the review folder.

Run: pytest code/test_transreso.py
"""
import csv
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schedc.config import ROOT  # noqa: E402
from transreso import reader, structure  # noqa: E402
import parse_transparency_v2 as ptv  # noqa: E402

CFG = ptv.load_config(2026)
OUT = os.path.join(ROOT, CFG["review_dir"], "data")
PDF = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG["resolutions"]}


def ch(text, x0, x1, top=10.0, color=(0.0,)):
    return dict(text=text, x0=x0, x1=x1, top=top, bottom=top + 8, non_stroking_color=color)


# --- unit ---------------------------------------------------------------------------------------
def test_runs_break_on_gap_line_and_colour():
    cs = [ch("a", 0, 5), ch("b", 5, 10), ch("c", 20, 25), ch("d", 25, 30, top=30),
          ch("e", 30, 35, top=30, color=(1.0, 0.0, 0.0))]
    assert ["".join(c["text"] for c in r) for r in reader.runs(cs)] == ["ab", "c", "d", "e"]


def test_runs_cross_cell_edge_only_without_gap():
    # Clipped text continues the word with no gap; a new cell's text starts after padding.
    cell = lambda c: 0 if c["x0"] < 10 else 1
    clipped = [ch("a", 5, 9.9), ch("b", 9.9, 14)]
    padded = [ch("a", 5, 9), ch("b", 10.5, 14)]
    assert len(reader.runs(clipped, cell=cell)) == 1
    assert len(reader.runs(padded, cell=cell)) == 2


def test_parse_amount_and_ein():
    assert structure.parse_amount("$5,000") == 5000
    assert structure.parse_amount("($37,000)") == -37000
    for bad in ("($5,000", "$5,000)", "5,000", "nt $5,000", "$5,00"):
        assert structure.parse_amount(bad) is None
    assert structure.parse_ein("13-6400434") == ("136400434", "hyphen")
    assert structure.parse_ein("131641068") == ("131641068", "no_hyphen")
    assert structure.parse_ein("") == ("", "blank")
    assert structure.parse_ein("of2 G3-r7e1") == ("", "odd")


def test_caption_regex():
    m = structure.CAPTION.match("CHART #1: Local Initiatives - Fiscal 2026 (continued)")
    assert m.groups()[:3] == ("1", "Local Initiatives", "2026") and m.group(4)
    m = structure.CAPTION.match("CHART #11: Chamber on the Go and Small Business Assistance- Fiscal 2026")
    assert m.group(2) == "Chamber on the Go and Small Business Assistance" and m.group(3) == "2026"
    m = structure.CAPTION.match("CHART #49: Operation Backpack")
    assert m.group(2) == "Operation Backpack" and m.group(3) is None


# --- golden rows, read off the rendered pages -----------------------------------------------------
def _row(seq, page, row_index):
    p = reader.read_pdf(PDF[seq], CFG["x_tolerance"], CFG["run_gap_pt"], pages=[page])[0]
    t = p["tables"][0]
    labels = [h["label"] for h in t["header"]]
    r = next(r for r in t["rows"] if r["row_index"] == row_index)
    return p, {labels[j]: c for j, c in r["cols"].items()}, r


def test_golden_reso01_p3_first_row():
    _, c, _ = _row(1, 3, 1)
    assert c["Member"]["text_raw"] == "Zhuang"
    assert c["Organization - Program"]["text_raw"] == "Department of Youth and Community Development"
    assert c["EIN Number"]["text_raw"] == "13-6400434"
    assert c["Amount"]["text_raw"] == "($37,000)" and c["Amount"]["red"] == c["Amount"]["nchars"]
    assert (c["Agy #"]["text_raw"], c["U/A"]["text_raw"]) == ("260", "005")


def test_golden_clipped_org_reso08_p19():
    # The page shows "...Modern History of Polan"; the rest is hidden under the EIN cell.
    p, c, _ = _row(8, 19, 2)
    assert c["Organization - Program"]["text_raw"].endswith("Modern History of Polan")
    assert c["Organization - Program"]["hidden"] == "d, Inc. - Stories of Greenpoint"
    assert c["EIN Number"]["text_raw"] == "23-7164776"
    assert c["Agency"]["text_raw"] == "DYCD" and c["Amount"]["text_raw"] == "$5,000"
    assert len(p["clipped"]) == 2


def test_golden_clipped_source_reso02_p110():
    _, c, _ = _row(2, 110, 1)
    assert c["Source"]["text_raw"] == "Speaker's Initiat"
    assert c["Member"]["text_raw"] == "Speaker"
    assert c["Organization - Program"]["text_raw"] == "Fortune Society, Inc., The - Fordham Plaza"


def test_golden_spanning_source_member_reso01_p91():
    # No rule between Source and Member in the data rows: the source text runs across both.
    _, c, r = _row(1, 91, 1)
    assert c["Source"]["text_raw"] == "Unaccompanied Minors and\nFamilies"
    assert c["Member"]["text_raw"] == ""
    assert c["Amount"]["text_raw"] == "($420,000)"
    assert "spanning_cell:Source+Member" in r["flags"]


def test_golden_made_purpose_cell_reso03_p81():
    _, c, r = _row(3, 81, 8)
    assert " ".join(c["Purpose of Funds"]["text_raw"].split()) == (
        "This allocation supports the use of art as a means to engage, organize, and mobilize "
        "communities in the public awareness and conflict mediation surrounding gun violence.")
    assert c["Purpose of Funds"]["how"] == "made" and c["Amount"]["text_raw"] == "$18,000"
    assert "made_cell:Purpose of Funds" in r["flags"]


# --- snapshot of the committed review run ----------------------------------------------------------
def _read(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        pytest.skip(f"{name} not built")
    return list(csv.DictReader(open(path, encoding="utf-8")))


def test_snapshot_rows_and_contract():
    rows = _read("fy26_tr_rows.csv")
    assert len(rows) == 4952
    for col in ptv.CONTRACT + ["resolution_seq", "resolution_number", "resolution_date"]:
        assert col in rows[0]
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    assert len({r["row_id"] for r in rows}) == len(rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 994, "2": 1655, "3": 845, "4": 491, "5": 303, "6": 193, "7": 80,
                  "8": 94, "9": 141, "10": 156}


def test_snapshot_checks_pass():
    path = os.path.join(OUT, "fy26_tr_checks.txt")
    if not os.path.exists(path):
        pytest.skip("checks not built")
    txt = open(path, encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt


def test_snapshot_review_sorted():
    rv = _read("fy26_tr_review.csv")
    sev = {"critical": 0, "warn": 1}
    keys = [(sev[r["severity"]], -int(r["dollar_impact"] or 0)) for r in rv]
    assert keys == sorted(keys)


# --- FY2025 (#104) --------------------------------------------------------------------------------
CFG25 = ptv.load_config(2025)
OUT25 = os.path.join(ROOT, CFG25["review_dir"], "data")
PDF25 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG25["resolutions"]}


def _row25(seq, page, row_index):
    p = reader.read_pdf(PDF25[seq], CFG25["x_tolerance"], CFG25["run_gap_pt"], pages=[page])[0]
    t = p["tables"][0]
    labels = [h["label"] for h in t["header"]]
    r = next(r for r in t["rows"] if r["row_index"] == row_index)
    return p, {labels[j]: c for j, c in r["cols"].items()}, r


def test_caption_without_colon():
    # FY2025 Reso 11 p.6 prints "CHART #4 Anti-Poverty" with no colon.
    m = structure.CAPTION.match("CHART #4 Anti-Poverty - Fiscal 2025")
    assert m.groups()[:3] == ("4", "Anti-Poverty", "2025")


def test_golden_fy25_staff_note_past_star_column_reso07_p30():
    # The page shows "01/" in the `*` column (no drawn cell); the note runs past the table's
    # right rule and off the page.
    p, c, r = _row25(7, 30, 3)
    assert c["*"]["text_raw"] == "01/" and c["*"]["how"] == "made"
    assert c["*"]["hidden"].startswith("22; DCLA: We checked Midori")
    assert c["EIN Number"]["text_raw"] == "13-3682472" and c["Amount"]["text_raw"] == "($5,000)"
    assert "made_cell:*" in r["flags"]
    assert sum(1 for x in p["clipped"] if x["table"] == -1) == 2


def test_golden_fy25_no_ein_reso08_p13():
    _, c, _ = _row25(8, 13, 7)
    assert c["Member"]["text_raw"] == "Salamanca"
    assert c["EIN Number"]["text_raw"] == "" and c["Amount"]["text_raw"] == "($15,000)"


def test_golden_fy25_member_borough_header_reso08_p12():
    p = reader.read_pdf(PDF25[8], CFG25["x_tolerance"], CFG25["run_gap_pt"], pages=[12])[0]
    assert p["tables"][0]["header"][0]["label"] == "Member/Borough"
    assert structure.LABELS["Member/Borough"] == "member"


def _read25(name):
    path = os.path.join(OUT25, name)
    if not os.path.exists(path):
        pytest.skip(f"{name} not built")
    return list(csv.DictReader(open(path, encoding="utf-8")))


def test_snapshot_fy25_rows_and_contract():
    rows = _read25("fy25_tr_rows.csv")
    assert len(rows) == 3555
    for col in ptv.CONTRACT + ["resolution_seq", "resolution_number", "resolution_date"]:
        assert col in rows[0]
    assert all(r["resolution_date"] for r in rows)
    # Reso 04 has no resolution number (not printed, not in Legistar's 2026-07-07 pass).
    assert {r["resolution_seq"] for r in rows if not r["resolution_number"]} == {"4"}
    assert len({r["row_id"] for r in rows}) == len(rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 738, "2": 1108, "3": 213, "4": 27, "5": 260, "6": 188, "7": 340,
                  "8": 165, "9": 107, "10": 7, "11": 142, "12": 174, "13": 86}


def test_snapshot_fy25_checks_pass():
    path = os.path.join(OUT25, "fy25_tr_checks.txt")
    if not os.path.exists(path):
        pytest.skip("checks not built")
    txt = open(path, encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 3,555 of 3,555" in txt


# --- FY2024 (#105) --------------------------------------------------------------------------------
CFG24 = ptv.load_config(2024)
OUT24 = os.path.join(ROOT, CFG24["review_dir"], "data")
PDF24 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG24["resolutions"]}


def test_runs_break_on_overlap_past_clip_gap():
    # FY2024 Reso 02 p.11: a clipped "n" ends 0.95 pt after the next cell's text begins.
    cell = lambda c: 0 if c["x0"] < 125 else 1
    cs = [ch("o", 117.45, 122.99), ch("n", 122.99, 128.53), ch("S", 127.58, 134.22),
          ch("o", 134.18, 139.72)]
    assert ["".join(c["text"] for c in r) for r in reader.runs(cs, cell=cell)] == ["on", "So"]


def test_golden_fy24_clipped_borough_reso02_p11():
    p = reader.read_pdf(PDF24[2], CFG24["x_tolerance"], CFG24["run_gap_pt"], pages=[11])[0]
    t = p["tables"][0]
    labels = [h["label"] for h in t["header"]]
    c = {labels[j]: x for j, x in next(r for r in t["rows"] if r["row_index"] == 1)["cols"].items()}
    assert c["Borough"]["text_raw"] == "Staten Island Delegatio" and c["Borough"]["hidden"] == "n"
    assert c["Organization - Program"]["text_raw"] == "South Shore District Management Association, Inc."
    assert c["EIN Number"]["text_raw"] == "81-0728516" and c["Amount"]["text_raw"] == "($14,000)"


def test_golden_fy24_rotated_page_reso01_p3():
    # /Rotate 90; the label under the chart is "Page\xa01" (no-break space).
    p = reader.read_pdf(PDF24[1], CFG24["x_tolerance"], CFG24["run_gap_pt"], pages=[3])[0]
    assert p["rotation"] == 90 and (p["width"], p["height"]) == (792.0, 612.0)
    assert any(structure.PAGE_LABEL.match(ln["text"]) and ln["text"].endswith("1") for ln in p["lines"])


def test_snapshot_fy24_rows_and_checks():
    path = os.path.join(OUT24, "fy24_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy24 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 3303
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 790, "2": 955, "3": 327, "4": 283, "5": 214, "6": 127, "7": 370,
                  "8": 161, "9": 76}
    txt = open(os.path.join(OUT24, "fy24_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 3,303 of 3,303" in txt


# --- FY2023 (#106) --------------------------------------------------------------------------------
CFG23 = ptv.load_config(2023)
OUT23 = os.path.join(ROOT, CFG23["review_dir"], "data")
PDF23 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG23["resolutions"]}


def test_caption_variants_fy23():
    # Reso 01 p.81: no "#"; Reso 01 p.66 and Reso 09 pp.21-25: "FY 2023"; Reso 03 p.20: a typo.
    m = structure.CAPTION.match("CHART 41: Neighborhood Development Grant Initiative - Fiscal 2022")
    assert m.groups()[:3] == ("41", "Neighborhood Development Grant Initiative", "2022")
    m = structure.CAPTION.match("CHART #26: Financial Empowerment for NYC's Renters - FY 2023")
    assert m.groups()[:3] == ("26", "Financial Empowerment for NYC's Renters", "2023")
    m = structure.CAPTION.match("CHART #8: A Greener NYC - Fiscal 2023 (cpntinued)")
    assert m.groups()[:3] == ("8", "A Greener NYC", "2023") and m.group(4)


def test_footnote_variants_fy23():
    assert structure.footnote_of("*** Correction and/or Reversal of a change made in a previous "
                                 "Transparency Resolution.") == "***"
    assert structure.footnote_of("** Requires a budget modification for the changes to take effect.") == "**"
    assert structure.footnote_of("Page 1") is None


def _build23(seq, page):
    p = reader.read_pdf(PDF23[seq], CFG23["x_tolerance"], CFG23["run_gap_pt"], pages=[page])[0]
    res = next(r for r in CFG23["resolutions"] if r["seq"] == seq)
    return structure.build(res, [p], CFG23["x_tolerance"], 2023)


def test_golden_fy23_continued_first_page_reso08_p32():
    # The first page of chart #25 prints "(continued)"; both rows are kept, chart #25 starts here.
    p = reader.read_pdf(PDF23[8], CFG23["x_tolerance"], CFG23["run_gap_pt"], pages=[31, 32])
    res = next(r for r in CFG23["resolutions"] if r["seq"] == 8)
    S = structure.build(res, p, CFG23["x_tolerance"], 2023)
    assert [f["check_id"] for f in S["flags"]] == ["T3.continued_start"]
    rs = [r for r in S["rows"] if r["chart_number"] == 25]
    assert [(r["org"], r["org_marker"], r["ein"], r["agency"], r["amount"]) for r in rs] == [
        ("Legal Aid Society", "**", "135562265", "MOCJ", -1000000),
        ("Legal Aid Society", "**", "135562265", "DYCD", 1000000)]


def test_golden_fy23_empty_drawn_row_reso01_p67():
    # The last drawn row under chart #27 (Stabilizing NYC) prints nothing: counted, not a row.
    S = _build23(1, 67)
    assert S["empty_rows"] == [dict(resolution_seq=1, pdf_page=67, row_index=22)]
    assert S["rows"][-1]["org"] == "Woodside on the Move, Inc." and S["rows"][-1]["amount"] == 160000


def test_golden_fy23_clipped_org_reso01_p85():
    # "… Summer Day Camp & Enrichm" shows; "ent Academy" is hidden under the EIN cell.
    S = _build23(1, 85)
    r = next(r for r in S["rows"] if r["row_index"] == 7)
    assert r["org"].endswith("Summer Day Camp & Enrichm") and r["hidden_text"] == "org: ent Academy"
    assert (r["member"], r["ein"], r["amount"]) == ("Hudson", "112870465", -4000)


def test_snapshot_fy23_rows_and_checks():
    path = os.path.join(OUT23, "fy23_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy23 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 8424
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 1782, "2": 1752, "3": 1569, "4": 815, "5": 428, "6": 435, "7": 202,
                  "8": 561, "9": 144, "10": 256, "11": 137, "12": 208, "13": 25, "14": 110}
    txt = open(os.path.join(OUT23, "fy23_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 8,424 of 8,424" in txt


# --- FY2022 (#107) --------------------------------------------------------------------------------
CFG22 = ptv.load_config(2022)
OUT22 = os.path.join(ROOT, CFG22["review_dir"], "data")
PDF22 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG22["resolutions"]}


def _build22(seq, pages, **kw):
    ps = reader.read_pdf(PDF22[seq], CFG22["x_tolerance"], CFG22["run_gap_pt"], pages=pages, **kw)
    res = next(r for r in CFG22["resolutions"] if r["seq"] == seq)
    return structure.build(res, ps, CFG22["x_tolerance"], 2022)


def test_amount_with_cents_fy22():
    # Reso 03 chart #48 prints "$20,290.00"; only ".00" is read.
    assert structure.parse_amount("$20,290.00") == 20290
    assert structure.parse_amount("($150.00)") == -150
    assert structure.parse_amount("$1.50") is None


def test_golden_fy22_no_amount_chart_reso03_p94():
    # "Beating Hearts": Member | Organization | EIN Number | *, and a note under the table.
    S = _build22(3, [94])
    assert [f["check_id"] for f in S["flags"]] == ["T4.no_amount"]
    r = S["rows"][0]
    assert (r["member"], r["org"], r["ein"], r["amount"], r["action"], r["chart_kind"]) == (
        "Adams", "Hope Church", "811270080", None, "listed", "no_amount")
    assert S["chart_notes"][0]["lines"][0].startswith("***Staten Island Heart Society, Inc. has received $350,000")


def test_golden_fy22_page_origin_reso02_p23():
    # The media box starts at (-8.39, -8.39); the text layer counts from there.
    p = reader.read_pdf(PDF22[2], CFG22["x_tolerance"], CFG22["run_gap_pt"], pages=[23])[0]
    assert p["origin"] == [-8.39, -8.39]
    assert ptv.shift_box([10.0, 20.0, 30.0, 40.0], p["origin"]) == [18.39, 28.39, 38.39, 48.39]


def test_golden_fy22_overlaid_text_reso09_p38():
    # Only on the named page: "Funding to go support …" drawn over the EIN is hidden.
    S = _build22(9, [38], overlay_pages=[38])
    r = next(r for r in S["rows"] if r["row_index"] == 3)
    assert (r["ein_printed"], r["ein"], r["amount"]) == ("13-4170389", "134170389", -5000)
    assert r["hidden_text"].startswith("ein: Funding to go support the creation")
    assert any(f.startswith("overlaid_text") for f in r["row_flags"])
    S = _build22(9, [38])                       # not named: read as before, EIN garbled
    assert next(r for r in S["rows"] if r["row_index"] == 3)["ein_format"] == "odd"


def test_golden_fy22_continued_wrong_number_reso07_p34():
    S = _build22(7, [32, 33, 34])
    assert [f["check_id"] for f in S["flags"]] == ["T3.continued_number"]
    assert {r["chart_number"] for r in S["rows"] if r["pdf_page"] == 34} == {22}


def test_snapshot_fy22_rows_and_checks():
    path = os.path.join(OUT22, "fy22_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy22 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 7918
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    assert sum(1 for r in rows if r["action"] == "listed") == 91
    txt = open(os.path.join(OUT22, "fy22_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 7,917 of 7,918" in txt


# --- FY2021 (#108) --------------------------------------------------------------------------------
CFG21 = ptv.load_config(2021)
OUT21 = os.path.join(ROOT, CFG21["review_dir"], "data")
PDF21 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG21["resolutions"]}


def _build21(seq, pages):
    ps = reader.read_pdf(PDF21[seq], CFG21["x_tolerance"], CFG21["run_gap_pt"], pages=pages)
    res = next(r for r in CFG21["resolutions"] if r["seq"] == seq)
    return structure.build(res, ps, CFG21["x_tolerance"], 2021)


def test_footnote_variant_fy21():
    # FY2021's wording of the *** footnote (Reso 02-07, e.g. Reso 03 p.12).
    assert structure.footnote_of("*** Technical adjustment to designation made in a previous "
                                 "Transparency Resolution.") == "***"


def test_golden_fy21_technical_adjustment_reso03_p12():
    S = _build21(3, [12])
    assert not [f for f in S["flags"] if f["check_id"] in ("T6.furniture", "T11.markers")]
    rs = [r for r in S["rows"] if r["org_marker"] == "***"]
    assert [(r["org"], r["correction"], r["amount"]) for r in rs] == [
        ("City University of New York - Brooklyn College", 1, -5000),
        ("Research Foundation of the City University of New York - Council District 45", 1, 5000)]


def test_golden_fy21_no_amount_chart_reso01_p126():
    # "Beating Hearts" on a portrait page; the note says $175,000 (FY2022's say $350,000).
    S = _build21(1, [126])
    assert [f["check_id"] for f in S["flags"]] == ["T4.no_amount"]
    assert len(S["rows"]) == 18
    r = S["rows"][0]
    assert (r["member"], r["org"], r["ein"], r["amount"], r["action"], r["chart_kind"]) == (
        "Koslowitz", "Ronald McDonald House of Long Island, Inc.", "112764747", None, "listed",
        "no_amount")
    assert S["chart_notes"][0]["lines"][0].replace(" ", "").startswith(
        "***StatenIslandHeartSociety,Inc.hasreceived$175,000")


def test_golden_fy21_row_without_ein_reso02_p29():
    # Chart #9 (continued): a row with no member and no EIN, "Department of Cultural Affairs **"
    # DCLA ($10,000), above Bartlett Foundation $10,000 DYCD. Kept as printed.
    S = _build21(2, [28, 29])
    r = next(r for r in S["rows"] if r["pdf_page"] == 29 and r["row_index"] == 20)
    assert (r["member"], r["org"], r["org_marker"], r["ein"], r["agency"], r["amount"],
            r["agency_side"], r["row_flags"]) == (
        "", "Department of Cultural Affairs", "**", "", "DCLA", -10000, 0, ["ein_blank"])


def test_golden_fy21_continued_first_page_reso02_p20():
    S = _build21(2, [19, 20])
    assert [f["check_id"] for f in S["flags"]] == ["T3.continued_start"]
    assert [(r["chart_number"], r["amount"]) for r in S["rows"] if r["pdf_page"] == 20] == [
        (6, 80000), (6, 60000)]


def test_snapshot_fy21_rows_and_checks():
    path = os.path.join(OUT21, "fy21_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy21 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 4500
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 2432, "2": 709, "3": 255, "4": 184, "5": 232, "6": 218, "7": 315, "8": 155}
    assert sum(1 for r in rows if r["action"] == "listed") == 28
    txt = open(os.path.join(OUT21, "fy21_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 4,500 of 4,500" in txt


# --- FY2020 (#109) --------------------------------------------------------------------------------
CFG20 = ptv.load_config(2020)
OUT20 = os.path.join(ROOT, CFG20["review_dir"], "data")
PDF20 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG20["resolutions"]}


def _build20(seq, pages):
    ps = reader.read_pdf(PDF20[seq], CFG20["x_tolerance"], CFG20["run_gap_pt"], pages=pages)
    res = next(r for r in CFG20["resolutions"] if r["seq"] == seq)
    return structure.build(res, ps, CFG20["x_tolerance"], 2020)


def test_caption_variants_fy20():
    assert structure.normalise_caption("Chart #35: Purpose of Funds Changes - Fiscal 2020") == (
        "CHART #35: Purpose of Funds Changes - Fiscal 2020", ["'Chart' for 'CHART'"])
    assert structure.normalise_caption("Chart # 44: Purpose of Funds Changes - Fiscal 2020 (continued)") == (
        "CHART #44: Purpose of Funds Changes - Fiscal 2020 (continued)",
        ["'Chart' for 'CHART'", "a space after '#'"])
    assert structure.normalise_caption("CHART #16: SU-CASA (continued) - Fiscal 2020") == (
        "CHART #16: SU-CASA - Fiscal 2020 (continued)", ["'(continued)' before the fiscal year"])
    assert structure.normalise_caption("CHART #9: A Greener NYC - Fiscal 2021") == (
        "CHART #9: A Greener NYC - Fiscal 2021", [])
    m = structure.CAPTION.match("CHART #: Purpose of Funds Changes - Fiscal 2020 (continued)")
    assert m.groups()[:3] == ("", "Purpose of Funds Changes", "2020") and m.group(4)


def test_golden_fy20_lowercase_caption_reso01_p70():
    # "Chart #35:" over a Source | Member | ... | New Purpose of Funds chart.
    S = _build20(1, [70])
    assert [f["check_id"] for f in S["flags"]] == ["W.caption_format"]
    assert len(S["rows"]) == 18
    r = S["rows"][0]
    assert (r["source"], r["member"], r["org"], r["ein"], r["agency"], r["amount"], r["action"],
            r["chart_number"]) == ("Local", "Borelli", "Columcille Cultural Center, Inc.",
                                   "133909562", "DYCD", -2500, "purpose_from", 35)


def test_golden_fy20_continued_mid_caption_reso05_p32():
    S = _build20(5, [31, 32])
    assert [f["check_id"] for f in S["flags"]] == ["W.caption_format"]
    assert {(r["pdf_page"], r["chart_number"]) for r in S["rows"]} == {(31, 16), (32, 16)}


def test_golden_fy20_unnumbered_continued_reso06_p25():
    S = _build20(6, [24, 25, 26])
    assert [(f["check_id"], f["pdf_page"]) for f in S["flags"]] == [
        ("T3.continued_number", 25), ("T3.continued_number", 26)]
    assert {r["chart_number"] for r in S["rows"]} == {16}


def test_golden_fy20_school_header_reso03_p58():
    # Header "Organization - School" with no Member column.
    S = _build20(3, [58])
    assert S["flags"] == []
    r = S["rows"][0]
    assert (r["org"], r["org_marker"], r["ein"], r["agency"], r["amount"]) == (
        "East Flatbush Village, Inc. - Meyer Levin High School", "**", "800612019", "DCLA", -18000)


def test_snapshot_fy20_rows_and_checks():
    path = os.path.join(OUT20, "fy20_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy20 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 5396
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 1361, "2": 1270, "3": 1090, "4": 573, "5": 570, "6": 176, "7": 233, "8": 123}
    assert sum(1 for r in rows if r["action"] == "listed") == 73
    txt = open(os.path.join(OUT20, "fy20_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 5,396 of 5,396" in txt


# --- FY2019 (#110) --------------------------------------------------------------------------------
CFG19 = ptv.load_config(2019)
OUT19 = os.path.join(ROOT, CFG19["review_dir"], "data")
PDF19 = {r["seq"]: os.path.join(ROOT, r["pdf"]) for r in CFG19["resolutions"]}


def _build19(seq, pages):
    ps = reader.read_pdf(PDF19[seq], CFG19["x_tolerance"], CFG19["run_gap_pt"], pages=pages,
                         overfull_pages=ptv.overfull_pages(CFG19, seq))
    res = next(r for r in CFG19["resolutions"] if r["seq"] == seq)
    renumber = {e["pdf_page"]: (e["printed"], e["read_as"]) for e in CFG19["exceptions"]
                if e["check_id"] == "T3.chart_number" and e["resolution_seq"] == seq}
    return structure.build(res, ps, CFG19["x_tolerance"], 2019, renumber)


def _org19(S, page, row_index):
    return next(r["org_raw"] for r in S["rows"] if (r["pdf_page"], r["row_index"]) == (page, row_index))


def test_golden_fy19_overfull_cells_reso07_p27():
    # One-line rows whose organization wraps to two lines: the block is centred on the row and
    # drawn across its rules. Without the T7.overfull rule, row 17 reads "IGnrce.enwich House"
    # (row 16's "Inc." on top of its own first line) and row 22 loses "Aged" past the table.
    ps = reader.read_pdf(PDF19[7], 3.0, 3.0, pages=[27])
    assert ps[0]["overfull_chars"] > 0
    plain = {r["row_index"]: r["cols"] for r in ps[0]["tables"][0]["rows"]}
    assert plain[17][1]["text_raw"].startswith("IGnrce.enwich House")
    S = _build19(7, [25, 26, 27])
    assert _org19(S, 27, 16).endswith("Penn South Social Services,\nInc.")
    assert _org19(S, 27, 17).startswith("Greenwich House, Inc. - Judith C White")
    assert _org19(S, 27, 18).startswith("Midtown Management Group, Inc.")
    assert _org19(S, 27, 22).endswith("For The\nAged")
    # Rows drawn column by column, each line inside its own row, stay apart (Borough "Eugene").
    p27 = [r for r in S["rows"] if r["pdf_page"] == 27]
    assert [r["member"] for r in p27 if r["row_index"] in (1, 2, 3)] == ["Eugene"] * 3
    assert all(r["ein"] and r["amount"] for r in p27)
    assert sum(1 for r in p27 if any(f.startswith("overfull_cell") for f in r["row_flags"])) == 4


def test_golden_fy19_overfull_past_table_reso04_p49():
    # The last row's "67K" is drawn below the table's bottom rule.
    S = _build19(4, [48, 49])
    assert _org19(S, 49, 6) == "University Settlement Society of New York, Inc. - Public School\n67K"


def test_golden_fy19_chart_renumber_reso01_p108():
    S = _build19(1, [104, 108, 109])
    assert [(f["check_id"], f["pdf_page"]) for f in S["flags"]] == [("T3.chart_number", 108)]
    assert sorted({(c["chart_number"], c["fy_printed"], c["first_page"]) for c in S["charts"]}) == [
        (55, "2019", 104), (56, "2018", 108)]


def test_golden_fy19_caption_house_style():
    # Reso 01 prints "CHART 1:" on every page (caption_no_hash): no review item. Reso 10 prints
    # "CHART #n:", and its one "CHART 7:" (p.15) still is.
    assert _build19(1, [18])["flags"] == []
    assert [f["check_id"] for f in _build19(10, [15])["flags"]] == ["W.caption_format"]


def test_snapshot_fy19_rows_and_checks():
    path = os.path.join(OUT19, "fy19_tr_rows.csv")
    if not os.path.exists(path):
        pytest.skip("fy19 not built")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 7207
    assert all(r["resolution_date"] and r["resolution_number"].startswith("Res ") for r in rows)
    by = {}
    for r in rows:
        by[r["resolution_seq"]] = by.get(r["resolution_seq"], 0) + 1
    assert by == {"1": 1704, "2": 1604, "3": 1118, "4": 596, "5": 925, "6": 89, "7": 339,
                  "8": 349, "9": 285, "10": 131, "11": 67}
    assert sum(1 for r in rows if r["action"] == "listed") == 112
    # Reso 01 prints "dated July 17, 2018"; resolution_date is Legistar's 2018-07-18.
    r1 = [r for r in rows if r["resolution_seq"] == "1"]
    assert {r["resolution_date"] for r in r1} == {"2018-07-18"}
    assert not r1[0]["resolution_date_source"].startswith("printed")
    txt = open(os.path.join(OUT19, "fy19_tr_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "(PASS)" in txt and "agree on every field: 7,207 of 7,207" in txt
    assert "regions: 0 " in txt
