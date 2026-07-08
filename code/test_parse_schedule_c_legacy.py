#!/usr/bin/env python3
"""
Regression tests for parse_schedule_c_legacy.py — the FY2009-FY2014 early-era Schedule C
initiatives parser. These documents print a per-category TOTAL, so reconciliation is the gate.

Reparses from the in-repo source PDFs and asserts each year's category reconciliation meets its
known ratio. The two non-exact years (FY09, FY11) each have a single in-source arithmetic
inconsistency (listed items vs. the printed TOTAL disagree in the source), not an extraction
error, so their expected exact-count is one short of total.

Run: pytest code/test_parse_schedule_c_legacy.py
"""
import os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# (prefix, source PDF, expected exact categories, total categories)
YEARS = [
    ("fy09", "source/FY09/fy09-Schedule-C-final.pdf", 21, 22),
    ("fy10", "source/FY10/fy_2010_sched_c_final.pdf", 21, 21),
    ("fy11", "source/FY11/fy2011-C2011.pdf", 18, 19),
    ("fy12", "source/FY12/fy2012-skedcfinal.pdf", 16, 16),
    ("fy13", "source/FY13/fy2013-FY-2013-Schedule-C-Merge-Final1.pdf", 17, 17),
    ("fy14", "source/FY14/fy2014-skedc.pdf", 17, 17),
]


def _reconcile(src):
    import parse_schedule_c_legacy as P
    from collections import defaultdict
    inits, recon, order = P.parse(P.load_pages(os.path.join(REPO, src)))
    isum = defaultdict(int)
    for c, ag, nm, amt in inits:
        isum[c] += amt
    exact = sum(1 for c in order if isum.get(c, 0) == (recon.get(c) or 0) and (recon.get(c) or 0))
    return exact, len(order), len(inits)


@pytest.mark.parametrize("prefix,src,exact,total", YEARS)
def test_reconciliation_ratio(prefix, src, exact, total):
    if not os.path.exists(os.path.join(REPO, src)):
        pytest.skip(f"source PDF missing: {src}")
    got_exact, ncats, nrows = _reconcile(src)
    assert ncats == total, f"{prefix}: {ncats} categories (expected {total})"
    assert got_exact >= exact, f"{prefix}: {got_exact}/{ncats} exact (expected >= {exact})"
    assert nrows > 0


def test_row_regex_edge_cases():
    """Two real early-era amount artifacts the parser must survive:
      * a comma-split amount  '$1,499, 254'   (FY13 CCRB) -> normalized to 1,499,254
      * an amount glued to text '(Harvest Home)$60,000' (FY12 Social Services) -> 60,000
    """
    import re, parse_schedule_c_legacy as P
    s = re.sub(r'(?<=\d),\s+(?=\d)', ',', "CCRB Administrative Prosecution Unit $1,499, 254")
    m = P.ROW.match(s)
    assert m and P.money(m.group(2)) == 1_499_254
    m2 = P.ROW.match("DYCD Expand Low-Income Farmer’s Markets (Harvest Home)$60,000")
    assert m2 and P.money(m2.group(2)) == 60_000


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
