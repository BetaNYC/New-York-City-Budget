#!/usr/bin/env python3
"""
Tests for reconcile_disclosure_schedule_c.py -- the (EIN, amount) multiset join between the
Council's expense disclosure and the Schedule C award files, and the #57 blocker-2 verdict.

Synthetic cases pin the join's rules; corpus cases pin the numbers DATA-ANOMALIES.md quotes.
Each docstring says what result would FAIL the test.

Run: pytest code/test_reconcile_disclosure_schedule_c.py
"""
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import reconcile_disclosure_schedule_c as R  # noqa: E402


def _d(ein, amount, stream="initiative", status="cleared", row=2):
    return dict(key=(ein, Decimal(amount)), amount=Decimal(amount), stream=stream,
                status=status, row=row, ein=ein, name="X", source=stream)


def _sc(ein, amount, member=""):
    return {"ein": ein, "amount": str(amount), "member": member,
            "_key": (ein, Decimal(amount))}


def _sc_set(**streams):
    out = {k: [] for k in R.PUBLISHED + R.SIDECARS}
    out.update(streams)
    return out


# ---------------------------------------------------------------- the join

def test_multiset_counts_duplicates():
    """FAILS if a key printed three times in the disclosure and twice in Schedule C yields
    anything but two matches and one unmatched disclosure row (a set join would say 1 or 3)."""
    disc = [_d("111111111", 5000, row=r) for r in (2, 3, 4)]
    m, un, _ = R.match_year(disc, _sc_set(body=[_sc("111111111", 5000)] * 2), R.PUBLISHED)
    assert len(m) == 2 and sum(len(v) for v in un.values()) == 0


def test_key_is_ein_and_amount_never_ein_alone():
    """FAILS if a Schedule C row matches a disclosure row with the same EIN but a different
    amount (the FCNY fiscal-sponsor EIN would then match everything)."""
    disc = [_d("132612524", 5000)]
    m, un, _ = R.match_year(disc, _sc_set(body=[_sc("132612524", 7500)]), R.PUBLISHED)
    assert m == {} and len(un["body"]) == 1


def test_member_is_never_part_of_the_key():
    """FAILS if the sponsoring member (export-time roster in the disclosure) blocks a match."""
    disc = [_d("111111111", 5000)]
    m, _, _ = R.match_year(disc, _sc_set(body=[_sc("111111111", 5000, member="Someone")]),
                           R.PUBLISHED)
    assert len(m) == 1


def test_ambiguous_allocation_is_counted_not_hidden():
    """FAILS if, when one Schedule C row could be either a cleared or a pending disclosure row,
    the choice is not flagged as ambiguous."""
    disc = [_d("111111111", 5000, status="cleared", row=2),
            _d("111111111", 5000, status="pending", row=3)]
    m, _, amb = R.match_year(disc, _sc_set(body=[_sc("111111111", 5000)]), R.PUBLISHED)
    assert len(m) == 1 and amb == {0, 1}


def test_appendix_file_claims_its_own_stream_first():
    """FAILS if appendix B (Local) takes an initiative-stream disclosure row while a Local row
    with the same key is free."""
    disc = [_d("111111111", 5000, stream="initiative", row=2),
            _d("111111111", 5000, stream="local", row=3)]
    m, _, _ = R.match_year(disc, _sc_set(appendix_b=[_sc("111111111", 5000)]), R.PUBLISHED)
    assert m == {1: "appendix_b"}


def test_stream_of():
    """FAILS if a Speaker's Initiative row (either apostrophe) or a named initiative lands in an
    appendix stream, or the three appendix streams are not recognized."""
    assert [R.stream_of(s) for s in ("Local", "Aging", "Youth", "Speaker's Initiative",
                                     "Speaker’s Initiative", "Food Pantries")] == \
        ["local", "aging", "youth", "speaker", "speaker", "initiative"]


# ---------------------------------------------------------------- blocker 2

def test_blocker2_detects_a_subset():
    """FAILS if a body that re-prints its appendix rows is not called SUBSET."""
    disc = [_d(f"1000000{i:02d}", 5000, stream="local", row=i) for i in range(10)]
    rows = [_sc(f"1000000{i:02d}", 5000) for i in range(10)]
    b = R.blocker2(disc, _sc_set(body=list(rows), appendix_b=list(rows)))
    assert b["double"] == 10 and b["body_only_app"] == 10 and R.verdict(b) == "SUBSET"


def test_blocker2_additive():
    """FAILS if separate body and appendix designations are not called ADDITIVE."""
    disc = [_d("100000001", 5000, stream="initiative"), _d("100000002", 5000, stream="local")]
    b = R.blocker2(disc, _sc_set(body=[_sc("100000001", 5000)],
                                 appendix_b=[_sc("100000002", 5000)]))
    assert R.verdict(b) == "ADDITIVE" and b["double"] == 0


def test_blocker2_ignores_keys_the_disclosure_lacks():
    """FAILS if a key in both body and appendix that the disclosure does not carry at all is
    counted as double-listed (the disclosure cannot speak to it)."""
    disc = [_d("100000001", 5000, stream="initiative")]
    b = R.blocker2(disc, _sc_set(body=[_sc("999999999", 1)], appendix_b=[_sc("999999999", 1)]))
    assert b["double"] == 0 and b["unconfirmed_shared_keys"] == 1


# ---------------------------------------------------------------- the corpus

def _years():
    if not hasattr(_years, "cache"):
        _years.cache = {y["fy"]: y for y in R.analyse()}
    return _years.cache


def test_fy2027_appendices_are_additive_to_the_row():
    """FAILS if any FY2027 appendix row only matches a designation the body already claimed,
    or if the appendix dollars stop equalling the disclosure's Local/Aging/Youth dollars."""
    y = _years()[2027]
    b = y["blocker2"]
    assert R.verdict(b) == "ADDITIVE"
    assert y["app_matched_after_body"] == b["app_rows"] == 3860
    assert b["app_amount"] == b["disc_app_all"] == Decimal(49799000)


def test_no_year_is_a_subset():
    """FAILS if the appendices of any year with appendix rows read as a subset of the body."""
    for fy, y in _years().items():
        b = y["blocker2"]
        if b is None:
            continue
        assert R.verdict(b) in ("ADDITIVE", "ADDITIVE (with exceptions)", "NO APPENDIX ROWS"), fy
        if b["app_rows"]:
            assert y["app_matched_after_body"] >= 0.96 * b["app_rows"], fy  # README quotes 96%


def test_fy2027_gap_is_city_ein_pool_money_checked_not_assumed():
    """Pins the FY2027 gap DATA-ANOMALIES quotes. FAILS if the unmatched set changes: 64 rows,
    60 of them on the City's own EIN, all 60 Pending."""
    y = _years()[2027]
    u = y["unmatched_disc"]
    city = [d for d in u if d["ein"] == R.CITY_EIN]
    assert len(u) == 64 and len(city) == 60
    assert all(d["status"] == "pending" for d in city)
    assert sum(d["amount"] for d in city) == Decimal(50508586)
    assert sorted(r["_key"][1] for r in y["unmatched_sc_rows"]["body"]) == \
        [Decimal(14999), Decimal(44999)]


def test_fy2013_fy2014_have_nothing_to_match():
    """FAILS if FY2013/FY2014 report coverage that cannot exist (no Schedule C award files)."""
    for fy in (2013, 2014):
        assert sum(c["matched_rows"] for c in _years()[fy]["cells"]) == 0


def test_circular_sidecar_is_never_counted_as_coverage():
    """FAILS if rows matched only through the disclosure-built appendix sidecar leak into the
    published-set or with-absorbed columns."""
    for y in _years().values():
        for c in y["cells"]:
            assert c["matched_rows"] <= c["matched_rows_with_absorbed"]
            assert c["matched_rows_with_absorbed"] + c["circular_rows"] <= c["disc_rows"]


def test_committed_outputs_are_current():
    """FAILS if data/DISCLOSURE-COVERAGE.md or the coverage CSV differs from a fresh run."""
    files, _ = R.outputs()
    for path, text in files.items():
        with open(path, encoding="utf-8", newline="") as f:
            assert f.read() == text, path
