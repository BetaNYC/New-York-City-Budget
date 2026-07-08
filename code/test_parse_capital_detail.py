#!/usr/bin/env python3
"""
Regression tests for parse_capital_detail.py — the §254 "Capital Project Detail" parser for
the fiscal years whose text layer pdfplumber extracts cleanly (FY2020, FY2022, FY2023, FY2024).

Two layers (mirrors test_parse_capital.py):
  1. Invariants on the committed output CSVs (always run) — FY27 schema, boro is a single
     letter, both code columns are two tokens, no wide amount bled into the title.
  2. Re-parse from the source PDFs and assert FULL agency-subtotal reconciliation. Unlike the
     FY25/FY26 capital tests (whose PDFs live in an external iCloud tree), these source PDFs are
     committed under source/ in this repo, so layer 2 always runs here.

Run: pytest code/test_parse_capital_detail.py
"""
import csv, os, re, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FY27_COLS = ["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3", "fy4",
             "sponsor", "title", "building_code", "school_code"]

# (prefix, source PDF, expected (reconciled, total) agency subtotals)
YEARS = [
    ("fy20", "source/FY20/Supporting-Detail-for-the-FY-2020-Changes-to-the-Executive-Capital-"
             "Budget-Adopted-by-the-City-Council-Pursuant-to-Section-254-2.pdf", (23, 23)),
    ("fy22", "source/FY22/FY22-Sec254-Capital-Supporting-Detail-Book.pdf", (32, 32)),
    ("fy23", "source/FY23/FY23-Sec254-Capital-Supporting-Detail-Book.pdf", (30, 30)),
    ("fy24", "source/FY24/FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf", (30, 30)),
]

AWARDS = [os.path.join(REPO, "data", fy, "schedule_c", f"{fy}_schedule_c_awards.csv")
          for fy in ("fy20", "fy22", "fy23", "fy24")]


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------- layer 1: committed-CSV invariants ----------

@pytest.mark.parametrize("prefix", [y[0] for y in YEARS])
def test_committed_schema_and_columns(prefix):
    csv_path = os.path.join(REPO, "data", prefix, "capital", f"{prefix}_capital_projects.csv")
    if not os.path.exists(csv_path):
        pytest.skip(f"{prefix} capital output not generated")
    rows = _rows(csv_path)
    assert rows and list(rows[0].keys()) == FY27_COLS
    for r in rows:
        assert r["part"] in ("I", "II", "III")
        assert r["agency"] and r["title"]
        assert len(r["boro"]) == 1 and r["boro"].isalpha()
        assert len(r["budget_line"].split()) == 2      # e.g. 'AG CN001'
        assert len(r["sub_id"].split()) == 2            # e.g. 'AG D001'
        # no printed amount bled into the title. Amounts are comma-grouped thousands
        # ('225,000'); bare title numbers (a 6-digit project id like '125382', a community
        # district '126') are legitimate and must NOT trip this guard — so key on the comma.
        for tok in r["title"].split():
            assert not re.match(r'^-?\d{1,3}(?:,\d{3})+$', tok), f"amount bled into title: {r}"


# ---------- layer 2: re-parse from committed source PDFs (always available here) ----------

@pytest.mark.parametrize("prefix,src,expected", YEARS)
def test_reparse_reconciles_fully(prefix, src, expected):
    src_path = os.path.join(REPO, src)
    if not os.path.exists(src_path):
        pytest.skip(f"source PDF missing: {src}")
    import parse_capital_detail as P
    projects, subtotals = P.parse(src_path)
    from collections import defaultdict
    got = defaultdict(int); cnt = defaultdict(int)
    for p in projects:
        got[(p["part"], p["agency"])] += p["fy1"]; cnt[(p["part"], p["agency"])] += 1
    ok = sum(1 for st in subtotals
             if got[(st["part"], st["agency"])] == st["fy1"]
             and cnt[(st["part"], st["agency"])] == st["projects"])
    assert (ok, len(subtotals)) == expected, \
        f"{prefix}: reconciled {ok}/{len(subtotals)}, expected {expected}"


def test_split_amounts_handles_title_trailing_number():
    """A title ending in punctuation-numbers ('NO. 4, 6, 7, 8, AND 9') must not have those
    tokens mistaken for the four amount columns — the amounts are the real trailing run."""
    import parse_capital_detail as P
    toks = "CROTONA PARKWAY MALLS NO. 4, 6, 7, 8, AND 9 2,000,000 0 0 0 FELIZ".split()
    title, amts, sponsor = P.split_amounts(toks)
    assert amts == [2_000_000, 0, 0, 0], amts
    assert sponsor == ["FELIZ"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
