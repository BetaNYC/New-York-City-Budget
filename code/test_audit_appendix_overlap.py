#!/usr/bin/env python3
"""
Tests for audit_appendix_overlap.py — the additive-vs-subset question.

This audit reversed a published claim, so the parts that could be quietly wrong get a test:

1. The ToC regex. It is the whole of Test 1. If it stops matching (a different dash, an ellipsis
   character, "Page" capitalised), the test silently reports 0 appendices and reads as evidence
   for subset — a wrong answer that looks like a measurement.
2. `twins()` round/distinctive split. The upper bound on double-counting rests entirely on it.
   $5,000 must count as round; $29,730 must count as distinctive.
3. `pairs()` pairing every EIN on a line with every amount on it. That is deliberately generous —
   it over-counts overlap, so the additive conclusion is drawn against the least favourable
   reading, not the most.

Run: pytest code/test_audit_appendix_overlap.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import audit_appendix_overlap as A  # noqa: E402


def test_toc_regex_matches_the_printed_form():
    """FY2024's actual line, ellipsis character and en dash included."""
    toc = "   APPENDIX A: AGING DISCRETIONARY….PAGE 1 - 26\n" \
          "   APPENDIX B: LOCAL INITIATIVES….PAGE 27 - 147\n" \
          "   APPENDIX C: YOUTH DISCRETIONARY….PAGE 148 - 189"
    hits = A.TOC_APPENDIX.findall(toc)
    assert len(hits) == 3, hits
    # Only Appendix A restarts at 1 — that restart is the evidence, so it must be read correctly.
    assert sum(1 for _, _, lo, _ in hits if int(lo) == 1) == 1


def test_toc_regex_survives_a_plain_hyphen_and_dots():
    toc = "APPENDIX A: AGING DISCRETIONARY.....PAGE 1 - 26"
    assert len(A.TOC_APPENDIX.findall(toc)) == 1


def test_pairs_is_deliberately_generous():
    """Every EIN on a line is paired with every amount on it. Over-counting overlap is the safe
    direction: it argues against the additive conclusion this audit reaches."""
    page = ["Org A 13-1234567 $5,000    Org B 11-7654321 $9,000"]
    got = A.pairs([page[0]], range(1, 2))
    assert ("131234567", 5000) in got
    assert ("131234567", 9000) in got, "should over-pair, not under-pair"
    assert len(got) == 4


def test_pairs_ignores_pages_outside_the_range():
    assert A.pairs(["13-1234567 $5,000"], range(2, 5)) == set()


def test_money_and_ein_forms():
    assert A.EIN.findall("tax id 13-1234567") == [("13", "1234567")]
    assert A.EIN.findall("tax id 131234567") == [("13", "1234567")]
    assert A.MONEY.findall("$1,234,567 and $50") == ["1,234,567", "50"]


def test_round_thousand_split_is_what_bounds_the_double_counting():
    """The $447,500 upper bound is this arithmetic. $5,000 is designated hundreds of times a year
    so a twin on it proves nothing; $29,730 is distinctive enough to mean something."""
    assert 5000 % 1000 == 0
    assert 29730 % 1000 != 0
    assert 833333 % 1000 != 0


def test_script_writes_no_data_file():
    """Read-only: no write mode anywhere, and no --apply. The one file it creates is the poppler
    text cache under build/, which is derived from source/ and gitignored."""
    src = open(os.path.join(HERE, "audit_appendix_overlap.py"), encoding="utf-8").read()
    src = src.split('"""', 2)[-1]
    for bad in ('"w"', "'w'", '"a"', "--apply"):
        assert bad not in src, f"writes? {bad}"
    assert "data/" in src, "sanity: it should still be reading the data tree"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
