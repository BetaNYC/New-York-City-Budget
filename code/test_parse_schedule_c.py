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
