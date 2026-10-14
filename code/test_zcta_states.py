#!/usr/bin/env python3
"""
Tests for zcta_states.py -- the Census 2020 ZCTA table and the disclosure ZIP check (GitHub #70).

The derivation is tested on a small file written in the record layout the Census Bureau
documents (18 pipe-separated columns, header row, blank ZCTA fields for a county with no ZCTA),
never on the 6.8 MB download, which is not committed. The ZIP rules are tested case by case on
the shapes the disclosure actually holds, and pinned on the committed CSVs.

Each docstring says what result would FAIL the test. Run: pytest code/test_zcta_states.py
"""
import collections
import csv
import glob
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import zcta_states as Z  # noqa: E402 -- after the sys.path insert


def _rel(records):
    """A relationship file in the documented layout: header + records of (zcta, county)."""
    out = ["﻿" + "|".join(Z.LAYOUT)]
    for z, county in records:
        r = [""] * len(Z.LAYOUT)
        if z:
            r[Z.LAYOUT.index("GEOID_ZCTA5_20")] = z
        r[Z.LAYOUT.index("GEOID_COUNTY_20")] = county
        out.append("|".join(r))
    return io.StringIO("\n".join(out) + "\n")


def test_derive_follows_the_documented_examples():
    """The Census explanation's own examples: ZCTA 54932 wholly in county 55039 (WI); ZCTA 06331
    in counties 09011 and 09015 (both CT, so one state); county 01003 with no ZCTA. FAILS if the
    blank-ZCTA record becomes a ZCTA, if the two-county ZCTA is listed twice, or if the leading
    zero of 06331 is lost."""
    z, n, nz = Z.derive(_rel([("54932", "55039"), ("06331", "09011"), ("06331", "09015"),
                              ("", "01003")]))
    assert z == {"54932": {"WI"}, "06331": {"CT"}}
    assert (n, nz) == (4, 3)
    assert Z.table_text(z) == "zcta,states\n06331,CT\n54932,WI\n"


def test_derive_lists_every_state_a_zcta_crosses():
    """FAILS if a ZCTA whose counties lie in two states keeps only one of them."""
    z, _, _ = Z.derive(_rel([("10001", "36061"), ("10001", "34003")]))
    assert Z.table_text(z) == "zcta,states\n10001,NJ;NY\n"


@pytest.mark.parametrize("bad", [
    lambda: io.StringIO("GEOID_ZCTA5_20|GEOID_COUNTY_20\n10001|36061\n"),   # undocumented layout
    lambda: _rel([("1001", "36061")]),                                        # 4-digit ZCTA
    lambda: _rel([("10001", "99001")]),                                       # unknown state FIPS
])
def test_derive_stops_on_anything_off_layout(bad):
    """FAILS if a header that is not the documented 18 columns, a ZCTA that is not 5 digits, or
    a county whose state FIPS is not in the Census table is read instead of stopping."""
    with pytest.raises(ValueError):
        Z.derive(bad())


ZCTAS = {"10001": frozenset({"NY"}), "02446": frozenset({"MA"}), "07083": frozenset({"NJ"}),
         "06108": frozenset({"CT"}), "11217": frozenset({"NY"})}


@pytest.mark.parametrize("raw,state,expected", [
    ("10001", "NY", ("10001", "valid")),
    ("10001-1234", "New York", ("10001", "valid")),
    ("10001 - 1234", "New YorkNY", ("10001", "valid")),
    ("100011234", "ny", ("10001", "valid")),
    ("10001", "Brooklyn", ("10001", "valid")),          # state unreadable: existence only
    ("11217", "NC", ("11217", "state_mismatch")),       # FY2013 rows 404-406
    ("10008", "NY", ("10008", "not_a_zcta")),           # a PO-box ZIP: not verified, not fake
    ("2446", "MA", ("02446", "padded")),                # Brookline, lost leading zero
    ("2446", "MassachusettsMA", ("02446", "padded")),
    ("7083", "NY", ("", "invalid")),                    # FY2014 row 2347, Bronx: 07083 is NJ
    ("6108", "New York", ("", "invalid")),              # 06108 is CT; the row says New York
    ("2446", "", ("", "invalid")),                      # no state to check the padding against
    ("1004", "NY", ("", "invalid")),                    # 01004 is no ZCTA
    ("#N/A", "", ("", "invalid")),                      # issue #71: an Excel error is no ZIP
    ("N/A", "NY", ("", "invalid")),
    ("0", "NY", ("", "invalid")),
    ("10001-", "NY", ("10001", "trimmed")),             # a ragged ZIP+4, in-state ZCTA
    ("11217-11217", "NY", ("11217", "trimmed")),
    ("10001-000", "New YorkNY", ("10001", "trimmed")),
    ("11217 - 20", "NY", ("11217", "trimmed")),
    ("11217-", "NC", ("", "invalid")),                  # ZCTA in another state: not trimmed
    ("10001-", "", ("", "invalid")),                    # no state to check against
    ("10001-", "Brooklyn", ("", "invalid")),            # state unreadable: not trimmed
    ("10008-", "NY", ("", "invalid")),                  # first five are no ZCTA
    ("11217=1020", "NY", ("", "invalid")),              # not the hyphenated form
    ("11217 ZipCode2: 3929", "NY", ("", "invalid")),
    ("112171", "NY", ("", "invalid")),                  # six digits: a typo, not ZIP+4
    ("www.mind-builders.org", "NY", ("", "invalid")),
    ("", "NY", ("", "blank")),
])
def test_classify_zip(raw, state, expected):
    """Issue #70. FAILS if a 4-digit ZIP is padded when the padded ZCTA does not exist or is in
    another state (or the row names no state), if '#N/A' or '0' gets a status other than
    invalid, if a non-ZCTA ZIP is called invalid rather than not_a_zcta, if a ZIP+4 loses
    its five digits, or if a ragged ZIP+4 is trimmed when its five digits are not a ZCTA in the
    row's own state (or the row names no state), or is not trimmed when they are."""
    assert Z.classify_zip(raw, state, ZCTAS) == expected


def test_row_state_reads_only_what_it_can_name():
    """FAILS if 'New YorkNY' is not read as NY, or if a borough, a mismatched run-together
    ('New YorkNJ') or 'N/A' is read as a state."""
    assert Z.row_state("New YorkNY") == "NY" and Z.row_state(" ny ") == "NY"
    assert Z.row_state("Massachusetts") == "MA"
    for s in ("Brooklyn", "New YorkNJ", "N/A", "NY10024", ""):
        assert Z.row_state(s) == "", s


def test_committed_table_is_well_formed_and_matches_the_manifest():
    """FAILS if data/reference/zcta2020_states.csv is unsorted, holds a non-ZCTA or an unknown
    state code, or its row count is not MANIFEST.csv's derived_rows (33,791), or if the manifest
    lost the source's URL or sha256."""
    assert Z.check() == []
    m = Z.read_manifest()[0]
    assert m["url"].startswith("https://www2.census.gov/") and len(m["sha256"]) == 64
    assert int(m["derived_rows"]) == 33791


def test_committed_zip_statuses_issue_70():
    """Corpus pin, from the committed disclosure CSVs. FAILS if the ZIP status counts move, if a
    published postal_code was rewritten (zip must be derivable from it), or if any '#N/A' ZIP
    is not invalid, or if the ragged ZIP+4 values trimmed (issue #70 follow-up) are not exactly
    the seven hyphenated forms below."""
    c, trimmed = collections.Counter(), collections.Counter()
    for f in glob.glob(os.path.join(os.path.dirname(HERE), "data", "fy*", "expense_disclosure",
                                    "*_awards.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                c[r["zip_status"]] += 1
                if r["postal_code"] == "#N/A":
                    assert r["zip_status"] == "invalid" and r["zip"] == "", r
                if r["zip_status"] == "padded":
                    assert r["zip"] == "0" + r["postal_code"], r
                elif r["zip"]:
                    assert r["postal_code"].startswith(r["zip"]), r
                if r["zip_status"] == "trimmed":
                    assert Z._RAGGED.fullmatch(r["postal_code"]), r
                    trimmed[r["postal_code"]] += 1
    assert dict(c) == {"valid": 127343, "blank": 10834, "not_a_zcta": 1073, "invalid": 232,
                       "state_mismatch": 29, "padded": 13, "trimmed": 32}
    assert dict(trimmed) == {"11203-": 24, "10027-000": 2, "10037-999": 2, "11217-11217": 1,
                             "11204-11204": 1, "10033-10033": 1, "11102-20": 1}
