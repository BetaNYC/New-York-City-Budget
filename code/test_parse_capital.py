#!/usr/bin/env python3
"""
Regression tests for the FY25/FY26/FY27 capital parsers.

Two layers:
  1. Invariants on the committed output CSVs (always run) — schema, no column bleed, and the
     hard reconciliation facts (FY26 grand totals tie exactly; the one negative adjustment).
  2. Re-parse from the source PDF when it is present (skipped in CI / on machines without the
     iCloud source tree) — asserts FY26 reconciles 31/31 and both grand totals match.

FY27 (parse_capital.py) locks the non-city column-bleed fix: 'PV MA#### PV 0N####' non-city
grantee rows must parse as sponsorless data rows, never as agency headers (the pre-fix bug leaked
a whole mis-parsed row's text into the `agency` field of the CITY rows that followed). Its source
PDF is committed under source/FY27/, so the FY27 re-parse layer always runs here.

Run: pytest code/test_parse_capital.py   (or: python code/test_parse_capital.py)
"""
import csv, os, sys, subprocess
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FY26_CSV = os.path.join(REPO, "data", "fy26", "capital", "fy26_capital_projects.csv")
# FY25 canonical capital is now the Council-additions supporting-detail book (Parts I+II),
# directly comparable to FY26/FY27. The old broad appropriation-changes extract was renamed to
# fy25_capital_changes_appropriation.csv (kept for provenance).
FY25_CSV = os.path.join(REPO, "data", "fy25", "capital", "fy25_capital_projects.csv")
FY25_NONCITY_CSV = os.path.join(REPO, "data", "fy25", "capital",
                                "fy25_capital_noncity_by_entity.csv")
FY25_APPROP_CSV = os.path.join(REPO, "data", "fy25", "capital",
                               "fy25_capital_changes_appropriation.csv")
FY27_CSV = os.path.join(REPO, "data", "fy27", "capital", "fy27_capital_projects.csv")
# FY27 + FY25-detail source PDFs are committed in-repo (unlike FY26, whose source lives in the
# iCloud tree), so their re-parse layers always run here.
FY27_PDF = os.path.join(REPO, "source", "FY27",
    "Supporting-Detail-for-FY2027-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254.V4.pdf")
FY25_DETAIL_PDF = os.path.join(REPO, "source", "FY25",
    "Supporting-Detail-for-FY2025-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254-Council-Version-24.07.17.pdf")

FY27_COLS = ["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3", "fy4",
             "sponsor", "title", "building_code", "school_code"]
BORO = set("MXKQRA")

# Source PDFs (iCloud tree; absent in CI). Set via env to override.
SRC = os.environ.get("NYC_BUDGET_SRC",
    "/Users/noneck/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "Apple Notes/INBOX/NYC Budget FY 27/Source Documents")
FY26_PDF = os.path.join(SRC, "FY 26", "Fiscal-2026-Capital-Budget-Supporting-Details-1.pdf")
FY25_PDF = os.path.join(SRC, "FY 25", "Fiscal-2025-Capital-Changes.pdf")
AWARDS = [os.path.join(REPO, "data", fy, "schedule_c", f"{fy}_schedule_c_awards.csv")
          for fy in ("fy25", "fy26", "fy27")]


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------- layer 1: committed-CSV invariants ----------

@pytest.mark.skipif(not os.path.exists(FY26_CSV), reason="fy26 output not generated")
def test_fy26_schema_and_columns():
    rows = _rows(FY26_CSV)
    assert rows and list(rows[0].keys()) == FY27_COLS
    for r in rows:
        assert r["part"] in ("I", "II")
        assert r["agency"] and r["title"]
        assert r["boro"] in BORO
        assert len(r["budget_line"].split()) == 2   # 'AG CN0584'
        assert len(r["sub_id"].split()) == 2         # 'AG D001'
        # no wide/negative amount bled into the title
        for tok in r["title"].split():
            assert not tok.lstrip("-").replace(",", "").isdigit() or len(tok) < 7


@pytest.mark.skipif(not os.path.exists(FY26_CSV), reason="fy26 output not generated")
def test_fy26_grand_totals_tie_exactly():
    rows = _rows(FY26_CSV)
    def part(p):
        rs = [r for r in rows if r["part"] == p]
        return sum(int(r["fy1"]) for r in rs), len(rs)
    assert part("I") == (779_320_000, 1259)    # printed 'TOTALS FOR ALL (1259 PROJECTS)'
    assert part("II") == (203_243_000, 197)    # printed 'TOTALS FOR ALL (197 PROJECTS)'


@pytest.mark.skipif(not os.path.exists(FY26_CSV), reason="fy26 output not generated")
def test_fy26_negative_adjustment_present():
    # PV MA0005 is a -183,000 FY2026 adjustment; missing it desyncs Cultural Institutions.
    rows = _rows(FY26_CSV)
    neg = [r for r in rows if int(r["fy1"]) < 0]
    assert len(neg) == 1 and neg[0]["budget_line"] == "PV MA0005" and neg[0]["fy1"] == "-183000"


@pytest.mark.skipif(not os.path.exists(FY25_CSV), reason="fy25 output not generated")
def test_fy25_detail_schema_and_columns():
    """FY25 canonical capital is now the Council-additions detail — same 13-col schema as
    FY26/FY27, Parts I+II, clean columns (no boro/amount bleed)."""
    rows = _rows(FY25_CSV)
    assert rows and list(rows[0].keys()) == FY27_COLS   # exact FY26/FY27 schema, no 'action'
    for r in rows:
        assert r["part"] in ("I", "II")
        assert r["agency"] and r["title"]
        assert r["boro"] in BORO
        assert len(r["budget_line"].split()) == 2        # e.g. 'ED NC128'
        assert len(r["sub_id"].split()) == 2             # e.g. 'AG DN06Y'
        for tok in r["title"].split():                   # no wide amount bled into title
            assert not tok.lstrip("-").replace(",", "").isdigit() or len(tok) < 7


@pytest.mark.skipif(not os.path.exists(FY25_CSV), reason="fy25 output not generated")
def test_fy25_detail_grand_totals_tie_exactly():
    rows = _rows(FY25_CSV)
    def part(p):
        rs = [r for r in rows if r["part"] == p]
        return sum(int(r["fy1"]) for r in rs), len(rs)
    assert part("I") == (775_000_000, 1327)     # printed 'TOTALS FOR ALL (1327 PROJECTS)' — $775M
    assert part("II") == (158_992_000, 181)     # printed 'TOTALS FOR ALL (181 PROJECTS)'


@pytest.mark.skipif(not os.path.exists(FY25_NONCITY_CSV), reason="fy25 non-city sidecar not generated")
def test_fy25_noncity_sidecar_reconciles():
    """Part III (by non-city entity) is a cross-tab of Part II: budget-line rows sum to the same
    $158,992,000 grand total."""
    rows = _rows(FY25_NONCITY_CSV)
    assert rows and list(rows[0].keys()) == ["organization", "budget_line", "fy1", "fy2", "fy3", "fy4"]
    assert sum(int(r["fy1"]) for r in rows) == 158_992_000
    for r in rows:
        assert r["organization"] and r["budget_line"]


@pytest.mark.skipif(not os.path.exists(FY25_APPROP_CSV), reason="fy25 appropriation book not present")
def test_fy25_appropriation_book_preserved():
    """The old broad appropriation-changes extract must survive the rename (provenance), keeping
    its FY25-only 'action' column and empty boro/sub_id/sponsor."""
    rows = _rows(FY25_APPROP_CSV)
    assert rows and "action" in rows[0]
    for r in rows:
        assert r["part"] == "I"
        assert r["boro"] == "" and r["sub_id"] == "" and r["sponsor"] == ""


# ---------- layer 2: re-parse from source PDF (skipped without the PDFs) ----------

@pytest.mark.skipif(not os.path.exists(FY26_PDF), reason="FY26 source PDF not available")
def test_fy26_reparse_reconciles_31_of_31(tmp_path):
    import parse_capital_fy26 as P
    roster = P.load_roster(AWARDS)
    projects, subtotals = P.parse(FY26_PDF, roster)
    for p in projects:
        p["sponsor"] = p.get("sponsor", "")
    from collections import defaultdict
    got = defaultdict(int); cnt = defaultdict(int)
    for p in projects:
        got[(p["part"], p["agency"])] += p["fy1"]; cnt[(p["part"], p["agency"])] += 1
    ok = sum(1 for st in subtotals
             if got[(st["part"], st["agency"])] == st["fy1"]
             and cnt[(st["part"], st["agency"])] == st["projects"])
    assert (ok, len(subtotals)) == (31, 31)


@pytest.mark.skipif(not os.path.exists(FY25_PDF), reason="FY25 appropriation-book PDF not available")
def test_fy25_appropriation_reparse_block_count():
    import parse_capital_fy25 as P
    projects = P.parse(FY25_PDF)
    assert len(projects) == 149
    assert all(p["part"] == "I" for p in projects)


@pytest.mark.skipif(not os.path.exists(FY25_DETAIL_PDF), reason="FY25 detail source PDF not available")
def test_fy25_detail_reparse_reconciles(tmp_path):
    """Re-parse the committed FY25 Council-additions detail book: 30/30 agency subtotals tie,
    both grand totals tie ($775M/1327 for Part I; $158,992,000/181 for Part II), and Part III's
    non-city entity cross-tab reconciles to the same $158,992,000 as Part II."""
    import parse_capital_fy25_detail as P
    import pdfplumber
    roster = P.load_roster(AWARDS)
    with pdfplumber.open(FY25_DETAIL_PDF) as pdf:
        projects, subtotals, grand = P.parse_detail(pdf, roster)
        p3_rows, p3_entities, p3_grand = P.parse_part3(pdf)
    from collections import defaultdict
    got = defaultdict(int); cnt = defaultdict(int)
    for p in projects:
        got[(p["part"], p["agency"])] += p["fy1"]; cnt[(p["part"], p["agency"])] += 1
    ok = sum(1 for st in subtotals
             if got[(st["part"], st["agency"])] == st["fy1"]
             and cnt[(st["part"], st["agency"])] == st["projects"])
    assert (ok, len(subtotals)) == (30, 30)
    assert grand["I"] == {"fy1": 775_000_000, "projects": 1327}
    assert grand["II"] == {"fy1": 158_992_000, "projects": 181}
    # Part I grand total == printed; summed projects match per part
    assert sum(p["fy1"] for p in projects if p["part"] == "I") == 775_000_000
    assert sum(p["fy1"] for p in projects if p["part"] == "II") == 158_992_000
    # Part III cross-tab: every entity reconciles, and the grand total matches Part II
    assert p3_entities and all(e["got"] == e["total_fy1"] for e in p3_entities)
    assert sum(r["fy1"] for r in p3_rows) == 158_992_000 == p3_grand["fy1"] == grand["II"]["fy1"]


# ---------- FY27 (parse_capital.py) — non-city column-bleed regression ----------

@pytest.mark.skipif(not os.path.exists(FY27_CSV), reason="fy27 output not generated")
def test_fy27_agency_never_polluted():
    """The exact bug this fix closes: every `agency` value is a clean agency name — no digit,
    no leaked 'PV MA#### ... amounts ... ORG' mis-parsed row. Would fail on the pre-fix CSV
    (52 polluted rows)."""
    rows = _rows(FY27_CSV)
    assert rows and list(rows[0].keys()) == FY27_COLS
    for r in rows:
        assert not any(ch.isdigit() for ch in r["agency"]), \
            f"digit in agency (leaked mis-parsed row): {r['agency']!r}"
        assert "PV " not in r["agency"], f"leaked code string in agency: {r['agency']!r}"
        assert r["part"] in ("I", "II") and r["agency"]
        assert len(r["budget_line"].split()) == 2 and len(r["sub_id"].split()) == 2


def test_fy27_noncity_MA_row_is_data_row_not_agency_header():
    """Unit-level lock (no PDF): a 'PV MA#### PV 0N####' non-city row must parse as ONE
    sponsorless data row under the current agency, not be mistaken for an agency header."""
    import parse_capital as P
    line = "PV MA1002 PV 0N957 K 1,500,000 0 0 0 NOEL POINTER FOUNDATION"
    pages = {1: "II.\nCULTURAL INSTITUTIONS\n" + line}
    projects, subtotals = P.parse(pages)
    assert len(projects) == 1, "MA/0N non-city row must be captured as a project"
    p = projects[0]
    assert p["part"] == "II" and p["agency"] == "CULTURAL INSTITUTIONS"
    assert p["budget_line"] == "PV MA1002" and p["sub_id"] == "PV 0N957"
    assert (p["fy1"], p["fy2"], p["fy3"], p["fy4"]) == (1_500_000, 0, 0, 0)
    assert p["title"] == "NOEL POINTER FOUNDATION"
    assert p["_noncity"] is True   # flags the sponsor-splitter to leave the org title intact


@pytest.mark.skipif(not os.path.exists(FY27_PDF), reason="FY27 source PDF not available")
def test_fy27_reparse_recovers_noncity_and_reconciles(tmp_path):
    """Re-parse the committed FY27 PDF: no polluted agency, the 30 non-city (MA/0N) grantee
    rows are recovered as sponsorless projects, and reconciliation holds at 24/26 (>= the
    pre-fix 23/26 — must not regress)."""
    import parse_capital as P
    pages = P.load_pages(FY27_PDF)
    projects, subtotals = P.parse(pages)
    assert not any(any(ch.isdigit() for ch in p["agency"]) for p in projects)
    noncity = [p for p in projects if p.get("_noncity")]
    assert len(noncity) == 30 and all(p["sponsor"] == "" for p in noncity)
    from collections import defaultdict
    got = defaultdict(int); cnt = defaultdict(int)
    for p in projects:
        got[(p["part"], p["agency"])] += p["fy1"]; cnt[(p["part"], p["agency"])] += 1
    ok = sum(1 for st in subtotals
             if got[(st["part"], st["agency"])] == st["fy1"]
             and cnt[(st["part"], st["agency"])] == st["projects"])
    assert (ok, len(subtotals)) == (24, 26)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(pytest.main([__file__, "-v"]))
