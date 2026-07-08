#!/usr/bin/env python3
"""
Regression tests for parse_schedule_c_fy15.py — the standalone FISCAL 2015 Schedule C parser.

FY2015 breaks the shared parser's positional block->category mapping (its ToC leads with two
narrative sections, so every summary block gets mislabeled by two positions). This variant maps
each block to its immediately-preceding category heading. The tests pin:
  * adjacent-heading mapping labels all 24 summary blocks correctly (not shifted);
  * every reconcilable category reconciles EXACT (24/24) against its printed TOTAL;
  * the three FY15 line-item formatting artifacts the shared segmenter drops are captured
    (a 'Council Initiatives' initiative name; a '$ 100,000' space-after-$ amount; a bare
    no-$ '2,100,000' amount) — each verified to sum to the printed category TOTAL;
  * FY2015 IS an award/EIN-level year (EIN-anchored award rows, all 9-digit).

Reparses from the in-repo source PDF. Run: pytest code/test_parse_schedule_c_fy15.py
"""
import os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SRC = os.path.join(REPO, "source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf")


def _parse():
    import parse_schedule_c_fy15 as F
    import parse_schedule_c as P
    import re
    pages = P.load_pages(SRC)
    maxp = max(pages)
    cats = P.derive_categories(pages)
    body_lo = 6
    for pn in sorted(pages):
        if pn > 2 and re.search(r'(?i)agency\s+initiative\s+amount', pages[pn]):
            body_lo = max(6, pn - 1); break
    apxA = P.first_heading_page(pages, "Appendix A")
    body_hi = apxA or maxp + 1
    roster = P.build_roster(pages, body_lo, maxp + 1)
    inits, recon, nblocks = F.parse_initiatives_fy15(pages, body_lo, body_hi, cats)
    awards = P.parse_awards(pages, body_lo, body_hi, cats, roster)
    return cats, inits, recon, nblocks, awards


@pytest.mark.skipif(not os.path.exists(SRC), reason="FY15 source PDF missing")
def test_all_reconcilable_categories_exact():
    """24 summary blocks, and each block's line-item sum == its printed TOTAL (24/24 exact)."""
    from collections import defaultdict
    _cats, inits, recon, nblocks, _awards = _parse()
    assert nblocks == 24, f"expected 24 summary blocks, got {nblocks}"
    isum = defaultdict(int)
    for c, _ag, _nm, amt in inits:
        isum[c] += amt
    reconcilable = [c for c in recon if recon[c]]
    assert len(reconcilable) == 24
    exact = sum(1 for c in reconcilable if isum.get(c, 0) == recon[c])
    assert exact == 24, f"only {exact}/24 categories reconcile exact"


@pytest.mark.skipif(not os.path.exists(SRC), reason="FY15 source PDF missing")
def test_adjacent_heading_labels_not_shifted():
    """The positional bug labeled block 0 (Anti-Gun Violence, $6.7M) as 'FROM BUDGET RESPONSE...'
    and pushed real categories off the end as 0/0. Adjacent-heading mapping must fix that."""
    _cats, _inits, recon, _n, _awards = _parse()
    # narrative front-matter entries must carry NO summary total
    assert recon.get("FROM BUDGET RESPONSE TO ADOPTION: NEW PRIORITIES REFLECTED IN THE FISCAL 2015 BUDGET", 0) == 0
    assert recon.get("INTRODUCTION", 0) == 0
    # the two real no-block categories also carry no total
    assert recon.get("BOROUGHWIDE NEEDS", 0) == 0
    assert recon.get("HEALTH SERVICES AND PREVENTION", 0) == 0
    # real categories carry their correct printed totals
    assert recon.get("ANTI-GUN VIOLENCE INITIATIVE") == 6_700_000
    assert recon.get("ANTI-POVERTY INITIATIVE") == 2_800_000
    assert recon.get("YOUTH AND COMMUNITY DEVELOPMENT") == 45_560_000


@pytest.mark.skipif(not os.path.exists(SRC), reason="FY15 source PDF missing")
def test_three_line_item_artifacts_recovered():
    """The three artifacts that made CUNY/HOUSING/YOUTH under-count in the shared parser must be
    captured here, so those categories reconcile exact."""
    from collections import defaultdict
    _cats, inits, recon, _n, _awards = _parse()
    isum = defaultdict(int)
    for c, _ag, _nm, amt in inits:
        isum[c] += amt
    for cat in ("CUNY", "HOUSING", "YOUTH AND COMMUNITY DEVELOPMENT"):
        assert isum.get(cat, 0) == recon.get(cat), f"{cat}: {isum.get(cat)} != printed {recon.get(cat)}"
    # the specific recovered rows
    cuny = [nm for c, _ag, nm, amt in inits if c == "CUNY" and amt == 500_000]
    assert any("Council Initiatives" in nm for nm in cuny), "CUNY 'Council Initiatives' $500k row not recovered"
    youth500k = [amt for c, _ag, _nm, amt in inits if c == "YOUTH AND COMMUNITY DEVELOPMENT" and amt == 2_100_000]
    assert youth500k, "YOUTH bare-amount $2,100,000 row not recovered"


def test_trailing_amount_helper():
    """Unit-test the amount tolerance directly (no PDF needed)."""
    import parse_schedule_c_fy15 as F
    assert F.trailing_amount("HPD Assn for Neighborhood and Housing Development $ 100,000")[1] == 100_000
    assert F.trailing_amount("DYCD Youth Action Build Initiative 2,100,000")[1] == 2_100_000
    assert F.trailing_amount("CUNY Results Based Accountability for Council Initiatives $500,000")[1] == 500_000
    assert F.trailing_amount("Some wrapped initiative name with no amount") is None
    # a bare small integer / year must NOT be read as an amount (must be comma-grouped)
    assert F.trailing_amount("Program funded in 2015") is None


@pytest.mark.skipif(not os.path.exists(SRC), reason="FY15 source PDF missing")
def test_fy15_is_award_ein_level():
    """FY2015 (unlike FY09-FY14) carries EIN-anchored award tables; every EIN is 9 digits."""
    _cats, _inits, _recon, _n, awards = _parse()
    assert len(awards) > 600, f"expected >600 award rows, got {len(awards)}"
    for r in awards:
        e = r["ein"].replace("-", "")
        assert e.isdigit() and len(e) == 9, f"malformed EIN {r['ein']!r}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
