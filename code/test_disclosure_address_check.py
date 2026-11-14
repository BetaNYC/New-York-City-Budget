#!/usr/bin/env python3
"""Tests for disclosure_address_check.py (GitHub #247): disclosure mailing addresses checked
against PAD, offline. No PAD file is needed: the rules are tested on made-up addresses, and the
committed result is checked against the committed data. Each docstring says what would FAIL."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import disclosure_address_check as A  # noqa: E402


@pytest.mark.parametrize("raw,want", [
    ("WEST 45TH STREET", "W 45 ST"), ("Third Avenue", "3 AVE"), ("E. 137th St 2C", "E 137 ST"),
    ("8th Avenue 5", "8 AVE"), ("AVENUE P", "AVE P"), ("Broadway", "BROADWAY"),
    ("E 94 Streat", "E 94 ST"), ("Grand Concourse", "GRAND CONC"),
])
def test_street_normalization(raw, want):
    """FAILS if PAD's streets and ours stop normalizing alike (suffixes, directions, ordinals in
    digits or words, unit text after the type, a type that is the street's name)."""
    assert A.norm_street(raw) == want


@pytest.mark.parametrize("raw,num,street,rule", [
    ("123 West 45th Street, 2nd Floor", "123", "W 45 ST", "after_comma_dropped"),
    ("475 Riverside Drive#455", "475", "RIVERSIDE DR", "unit_dropped"),
    ("475 Riverside Drive Suite 300", "475", "RIVERSIDE DR", "unit_dropped"),
    ("SoBRO 555 Bergen Avenue", "555", "BERGEN AVE", "name_before_number"),
    ("104-30 Roosevelt Avenue", "104-30", "ROOSEVELT AVE", None),
])
def test_address_split(raw, num, street, rule):
    """FAILS if the house number or street is misread, or a cleanup rule goes unrecorded."""
    n, s, rules = A.split_address(raw)
    assert (n, s) == (num, street)
    assert (rule in rules) if rule else rules == []


@pytest.mark.parametrize("raw", ["PO Box 123", "", "Avenue", "123 Street"])
def test_no_key_without_a_number_and_a_street(raw):
    """FAILS if a PO box, a blank, or a street that is only a type ('123 Street') gets a key."""
    assert A.split_address(raw)[:2] == (None, None)


def row(**kw):
    base = {"fiscal_year": "2018", "source_row": "7", "zip_status": "ambiguous_extra_digit",
            "zip": "", "zip_candidates": "10458;10465;10468", "postal_code": "104658",
            "city": "Bronx", "address1": "1 Main St"}
    return dict(base, **kw)


def test_borough_from_city_then_zip_never_mixed():
    """FAILS if a Queens neighborhood city blocks the ZIP rule, or candidates in two boroughs
    give one."""
    assert A.borough_of(row()) == ("2", "city")
    assert A.borough_of(row(city="Jamaica", zip_candidates="11434;11435")) == ("4", "zip")
    assert A.borough_of(row(city="Somewhere", zip_candidates="10011;11215")) == ("", "")
    assert A.borough_of(row(city="Outside of NYC", zip_status="state_mismatch", zip="08701",
                            zip_candidates="")) == ("", "")


def test_decide_settles_only_one_address_whose_zip_agrees():
    """FAILS if a row is settled with zero or several PAD addresses, or with a ZIP that is not a
    candidate (ambiguous) or not the printed ZIP (state mismatch)."""
    amb = row()
    assert A.decide(amb, [("10468", "2032")])[:3] == ("repaired_by_address", A.decide(amb, [("10468", "2032")])[1], "10468")
    assert A.decide(amb, [("10451", "2032")])[0] == "left"
    assert A.decide(amb, [])[0] == "left"
    assert A.decide(amb, [("10458", "1"), ("10468", "2")])[0] == "left"
    assert A.decide(amb, None)[0] == "left"
    sm = row(zip_status="state_mismatch", zip="10128", zip_candidates="", postal_code="10128")
    assert A.decide(sm, [("10128", "1")])[0] == "nyc_address_confirmed"
    assert A.decide(sm, [("10005", "1")])[0] == "left"


def test_apply_changes_only_a_settled_row_and_refuses_a_stale_check():
    """FAILS if a 'left' check changes a row, a settled one does not, or a check that no longer
    fits the row is applied instead of stopping the build."""
    c = {"fiscal_year": "2018", "source_row": "7", "zcta_status": "ambiguous_extra_digit",
         "result": "repaired_by_address", "pad_zip": "10468"}
    assert A.apply("", "ambiguous_extra_digit", "10458;10465;10468", c) == ("10468", "repaired_by_address", "10458;10465;10468")
    assert A.apply("", "ambiguous_extra_digit", "10458;10468", dict(c, result="left")) == ("", "ambiguous_extra_digit", "10458;10468")
    assert A.apply("", "ambiguous_extra_digit", "10458;10468", None) == ("", "ambiguous_extra_digit", "10458;10468")
    with pytest.raises(ValueError):
        A.apply("", "ambiguous_extra_digit", "10458;10465", c)            # not a candidate
    with pytest.raises(ValueError):
        A.apply("10001", "valid", "", c)                                  # the row changed
    s = {"fiscal_year": "2018", "source_row": "8", "zcta_status": "state_mismatch",
         "result": "nyc_address_confirmed", "pad_zip": "10128"}
    assert A.apply("10128", "state_mismatch", "", s) == ("10128", "nyc_address_confirmed", "")
    with pytest.raises(ValueError):
        A.apply("10129", "state_mismatch", "", s)


# ---------------------------------------------------------------- the committed result

def test_committed_check_is_current_and_follows_its_rules():
    """FAILS if data/disclosure_address_check.csv misses or adds a row to check, a printed value
    changed since the check, a settled row does not follow from one PAD match, or the PAD
    version or file hash is missing."""
    assert A.check() == []


def test_committed_check_never_settles_without_one_match():
    """FAILS if any settled row has other than exactly one PAD match."""
    for c in A.load().values():
        if c["result"] != "left":
            assert c["pad_matches"] == "1", c
            assert c["result"] == A.SETTLED[c["zcta_status"]], c


def test_the_dataset_carries_the_settled_statuses():
    """FAILS if the per-year CSVs and the committed check disagree on a row's status or zip."""
    import csv
    import glob
    have = A.load()
    seen = 0
    for f in glob.glob(os.path.join(A.ROOT, "data", "fy*", "expense_disclosure", "*_expense_awards.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                c = have.get((r["fiscal_year"], r["source_row"]))
                if c is None:
                    assert r["zip_status"] not in A.SETTLED.values(), r["source_row"]
                    continue
                seen += 1
                want = c["zcta_status"] if c["result"] == "left" else c["result"]
                assert r["zip_status"] == want, (c["fiscal_year"], c["source_row"])
                if c["result"] == "repaired_by_address":
                    assert r["zip"] == c["pad_zip"]
    assert seen == len(have)
