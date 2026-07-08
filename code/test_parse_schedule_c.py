#!/usr/bin/env python3
"""
Regression tests for parse_schedule_c.py across the FY2016-FY2024 range that reconciles.

Reparses from the in-repo source PDFs and asserts each year's category reconciliation meets
its known ratio (so a parser change that silently drops line items or mislabels categories is
caught). Also pins the FY2018 ToC-detection fix: FY18's contents page is headed 'Contents'
(not 'Table of Contents'), which previously yielded 0 categories.

Run: pytest code/test_parse_schedule_c.py
"""
import os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# (prefix, source PDF, expected exact-category count, total categories)
YEARS = [
    ("fy16", "source/FY16/fy2016-skedcf.pdf", 24, 26),
    ("fy17", "source/FY17/FY17-Schedule-C.pdf", 24, 27),
    ("fy18", "source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf", 24, 27),
    ("fy19", "source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf", 27, 28),
    ("fy20", "source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf", 27, 28),
    ("fy21", "source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf", 25, 26),
    ("fy22", "source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf", 24, 26),
    ("fy23", "source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf", 26, 26),
    ("fy24", "source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf", 24, 26),
]


def _reconcile(src):
    """Reparse and return (exact_count, total_categories, ncats_from_toc)."""
    import parse_schedule_c as P
    pages = P.load_pages(os.path.join(REPO, src))
    maxp = max(pages)
    cats = P.derive_categories(pages)
    body_lo = 6
    for pn in sorted(pages):
        if pn > 2 and __import__("re").search(r'(?i)agency\s+initiative\s+amount', pages[pn]):
            body_lo = max(6, pn - 1); break
    apxA = P.first_heading_page(pages, "Appendix A")
    body_hi = apxA or maxp + 1
    _inits, recon, _n = P.parse_initiatives(pages, body_lo, body_hi, cats)
    from collections import defaultdict
    isum = defaultdict(int)
    for c, ag, nm, amt in _inits:
        isum[c] += amt
    exact = sum(1 for c in cats if isum.get(c, 0) == (recon.get(c) or 0) and (recon.get(c) or 0))
    return exact, len(cats), len(cats)


@pytest.mark.parametrize("prefix,src,exact,total", YEARS)
def test_reconciliation_ratio(prefix, src, exact, total):
    if not os.path.exists(os.path.join(REPO, src)):
        pytest.skip(f"source PDF missing: {src}")
    got_exact, ncats, _ = _reconcile(src)
    assert ncats >= total, f"{prefix}: only {ncats} categories from ToC (expected >= {total})"
    assert got_exact >= exact, f"{prefix}: {got_exact} categories reconcile exact (expected >= {exact})"


def test_fy27_west_side_work_coalition_survives(tmp_path):
    """Regression: a real FCNY Schedule C award -- Speaker's Initiative ->
    'Fund for the City of New York, Inc. - West Side Work Coalition', $125,000, DYCD
    (source PDF p.274, EIN 13-2612524) -- was silently dropped from the FY27 CSV.

    Root cause: a repeated page-break column header ('Sponsor Legal Name of Organization -
    Program Name Tax ID Amount Agency Purpose of Funds') bled into the award's organization
    buffer, and the header-junk filter in main() then deleted the ENTIRE row rather than
    stripping the header fragment. The parser must retain the award. See DATA-ANOMALIES.md.

    Driven end-to-end via subprocess so the header-junk filter and per-EIN backfill in main()
    are exercised (not just parse_awards)."""
    import csv, subprocess
    src = os.path.join(REPO, "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf")
    if not os.path.exists(src):
        pytest.skip("FY27 source PDF missing")
    subprocess.run(
        [sys.executable, os.path.join(HERE, "parse_schedule_c.py"), src,
         "--outdir", str(tmp_path), "--prefix", "fy27"],
        check=True, capture_output=True, cwd=REPO,
    )
    with open(os.path.join(tmp_path, "fy27_schedule_c_awards.csv")) as f:
        rows = list(csv.DictReader(f))

    # The dropped award is back, with correct EIN / amount / agency / program / category.
    west = [r for r in rows
            if r["ein"] == "132612524" and "West Side Work Coalition" in r["program"]]
    assert len(west) == 1, "West Side Work Coalition FCNY award missing from parsed awards"
    w = west[0]
    assert w["amount"] == "125000"
    assert w["agency"] == "DYCD"
    assert "Speaker" in w["category"]

    # FCNY (EIN 13-2612524) Schedule C main-body passthrough: 37 awards totaling $3,357,714
    # (was 36 / $3,232,714 before the fix dropped the $125,000 West Side row).
    fcny = [r for r in rows if r["ein"] == "132612524"]
    assert len(fcny) == 37, f"expected 37 FCNY awards, got {len(fcny)}"
    assert sum(int(r["amount"]) for r in fcny) == 3357714

    # No surviving award may carry repeated column-header text in its organization -- that was the
    # signature of the bled-in header the filter used to delete whole rows.
    junk = [r for r in rows
            if "legal name of organization" in r["organization"].lower()
            or "sponsor legal" in r["organization"].lower()]
    assert not junk, f"{len(junk)} awards still carry header-junk organizations"


def test_fy18_toc_contents_heading():
    """FY18's contents page is headed 'Contents' (not 'Table of Contents'). The ToC-detection
    regex must find it, or the whole year silently yields 0 categories."""
    import parse_schedule_c as P
    src = os.path.join(REPO, "source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf")
    if not os.path.exists(src):
        pytest.skip("FY18 source PDF missing")
    cats = P.derive_categories(P.load_pages(src))
    assert len(cats) >= 25, f"FY18 ToC detection recovered only {len(cats)} categories"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
