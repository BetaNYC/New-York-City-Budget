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
