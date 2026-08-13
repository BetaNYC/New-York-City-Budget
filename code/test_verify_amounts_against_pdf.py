#!/usr/bin/env python3
"""
Tests for verify_amounts_against_pdf.py — corroborating amounts against the adopted PDF.

This script's whole value is that a `pdf_confirms` means something. A version that confirms
everything is worse than no check at all, because it launders an unverified number as verified. The
first version did exactly that: it accepted any line under the EIN and returned 440 of 440.

So the tests here are mostly about what must NOT confirm:

1. An amount printed nowhere against that EIN must never confirm. This is the mechanism test — if
   it ever fails, every other result in the file is meaningless.
2. An amount that *is* under the EIN but on a line naming nobody we recognise must not be promoted
   past `pdf_confirms_weak` when that EIN spans many lines. One EIN in FY2021 is printed on 483
   lines; against that, "the number is in there somewhere" is nearly free.
3. A line naming us pins the match even when the EIN spans many lines — otherwise a fiscal
   sponsor's grantees could never be confirmed at all, and the check would be useless where it is
   needed most.

Run: pytest code/test_verify_amounts_against_pdf.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import verify_amounts_against_pdf as V  # noqa: E402

# One printed page, in the shape poppler emits with -layout: organization, EIN, amount on one line.
PAGE = [
    "Brooklyn Book Bodega                        47-1234567          $12,500",
    "Fund for the City of New York               13-2612524          $40,000",
    "Fund for the City of New York               13-2612524          $75,000",
    "Levin Grace Family Services, Inc.           20-2765775          $5,000  DYCD",
]


def run(rows, page=PAGE):
    """verify() against a fixed page instead of a real PDF."""
    orig = V.pdf_lines
    V.pdf_lines = lambda fy: page
    try:
        return V.verify(rows)
    finally:
        V.pdf_lines = orig


def row(ein, amount, org, verdict="ein_absent"):
    return dict(file="data/fy21/schedule_c/x.csv", line="2", fiscal_year="2021", ein=ein,
                organization=org, our_amount=str(amount), verdict=verdict,
                nearest_disclosure_amount="", delta="", belongs_to_ein="", org_text_merged="")


def test_amount_absent_from_the_ein_never_confirms():
    """The mechanism test. $99,999 is not printed against this EIN, so no verdict may confirm it."""
    (r,) = run([row("471234567", 99999, "Brooklyn Book Bodega")])
    assert r["pdf_verdict"] == "pdf_contradicts", r
    assert "12500" in str(r["pdf_amounts"])


def test_ein_absent_from_the_document_is_not_a_confirmation():
    (r,) = run([row("999999999", 12500, "Nowhere Inc.")])
    assert r["pdf_verdict"] == "pdf_ein_absent"


def test_single_line_ein_confirms():
    """One line all year carrying both EIN and amount — nothing to be ambiguous about."""
    (r,) = run([row("471234567", 12500, "Brooklyn Book Bodega")])
    assert r["pdf_verdict"] == "pdf_confirms"


def test_multi_line_ein_without_our_name_is_only_weak():
    """A fiscal sponsor's EIN carries many awards. Finding our amount among them corroborates the
    figure but does not say which printed row is ours, so it must not read as settled."""
    (r,) = run([row("132612524", 75000, "Some Grantee We Cannot Find")])
    assert r["pdf_verdict"] == "pdf_confirms_weak"
    assert int(r["pdf_ein_lines"]) == 2


def test_multi_line_ein_with_our_name_confirms():
    """Otherwise every fiscally-sponsored award would be unverifiable — the case that matters most."""
    (r,) = run([row("132612524", 75000, "Fund for the City of New York")])
    assert r["pdf_verdict"] == "pdf_confirms"


def test_leading_wrapped_column_does_not_break_the_name_match():
    """-layout wraps the council-member column onto the front of a row: FY2027's Selfhelp line
    reads 'Lee Selfhelp Community Services...'. A prefix-anchored match would miss every one."""
    (r,) = run([row("202765775", 5000, "Grace Family Services, Inc.")])
    assert r["pdf_verdict"] == "pdf_confirms"


def test_script_writes_no_data_file():
    """It reports; it must never repair. audit_amounts.py holds the same line for the same reason.

    Scanned with the module docstring removed — that prose says "--apply" while explaining why
    there isn't one, and a test that trips over its own documentation is a test nobody keeps.
    """
    src = open(os.path.join(HERE, "verify_amounts_against_pdf.py"), encoding="utf-8").read()
    src = src.split('"""', 2)[-1]
    assert '"--apply"' not in src and "'--apply'" not in src
    for name in ("data/fy", "org_name_recovery_crosswalk"):
        assert name not in src, f"writes to {name}?"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
