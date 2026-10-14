#!/usr/bin/env python3
"""
Tests for build_member_crosswalk.py -- disclosure council_member -> Legistar person ID (#72).

Synthetic rosters carry exactly the hazards the real one has: two people whose surnames nest
(Levin / Levine, Won / Wong), a member who left and came back while another held the seat
(Charles and Inez Barron), Legistar's own initial-prefixed surnames ('R. Diaz, Sr.', 'D. Diaz'),
accents, a hyphenated surname printed by one half, and people with no recorded vote. The
committed crosswalk is then pinned against the committed roster extract and workbooks.

Each docstring says what result would FAIL the test. Run: pytest code/test_build_member_crosswalk.py
"""
import collections
import csv
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_member_crosswalk as B  # noqa: E402 -- after the sys.path insert


def _p(pid, full, first, last, years):
    ys = sorted(years)
    return B.Person({"person_id": str(pid), "full_name": full, "first_name": first,
                     "last_name": last,
                     "first_vote": f"{ys[0] - 1}-07-15" if ys else "",
                     "last_vote": f"{ys[-1]}-06-15" if ys else "",
                     "vote_fiscal_years": ";".join(map(str, ys))})


ROSTER = [
    _p(7567, "Stephen T. Levin", "Stephen T.", "Levin", range(2010, 2023)),
    _p(7634, "Mark Levine", "Mark", "Levine", range(2014, 2023)),
    _p(7816, "Julie Won", "Julie", "Won", range(2022, 2028)),
    _p(7900, "Phil Wong", "Phil", "Wong", (2026, 2027)),
    _p(5288, "Charles Barron", "Charles", "Barron", list(range(2004, 2015)) + [2022, 2023, 2024]),
    _p(7623, "Inez D. Barron", "Inez D.", "Barron", range(2014, 2023)),
    _p(7744, "Ruben Diaz, Sr.", "Ruben", "R. Diaz, Sr.", range(2018, 2023)),
    _p(7793, "Darma V. Diaz", "Darma", "D. Diaz", (2021, 2022)),
    _p(5267, "Ruben Diaz", "Ruben", "Diaz", ()),
    _p(7807, "Marjorie Velázquez", "Marjorie", "Velázquez", range(2022, 2026)),
    _p(6269, "Melissa Mark-Viverito", "Melissa", "Mark-Viverito", range(2006, 2019)),
    _p(7808, "Pierina Ana Sanchez", "Pierina", "Sanchez", range(2022, 2028)),
    _p(7897, "Justin E. Sanchez", "Justin E.", "Sanchez", (2026, 2027)),
    _p(7741, "Keith Powers", "Keith", "Powers", range(2018, 2027)),
    _p(7809, "Selvena N. Brooks-Powers", "Selvena N.", "Brooks-Powers", range(2021, 2028)),
]


def cls(value, fy):
    return B.classify(value, fy, ROSTER)


def test_levin_is_not_levine():
    """The issue's own example. FAILS if 'Levin' and 'Levine' in the same year resolve to the
    same person, or either to anyone but its own Legistar ID."""
    a, b = cls("Levin", 2016), cls("Levine", 2016)
    assert (a["council_member_type"], a["council_member_id"]) == ("member", "7567")
    assert (b["council_member_type"], b["council_member_id"]) == ("member", "7634")


def test_won_is_not_wong_and_an_export_time_name_is_flagged():
    """FAILS if 'Won' resolves to Wong, or if FY2025 'Wong' (the 2026 roster re-attributing
    Holden's rows; Wong first voted in FY2026) is typed a plain member rather than
    member_outside_fy -- or loses the ID that the name does identify."""
    assert cls("Won", 2025)["council_member_id"] == "7816"
    w = cls("Wong", 2025)
    assert (w["council_member_type"], w["council_member_id"]) == ("member_outside_fy", "7900")
    assert cls("Wong", 2026)["council_member_type"] == "member"


def test_a_member_who_left_and_returned_is_not_in_office_in_between():
    """Charles Barron voted FY2004-FY2014 and FY2022-FY2024; Inez Barron held the seat between.
    FAILS if a first-to-last span puts Charles in office in FY2018 (which made every Barron year
    ambiguous), or if the hand-over years FY2014 and FY2022, when both voted, are resolved."""
    assert cls("Barron", 2018)["council_member_id"] == "7623"
    assert cls("Barron", 2023)["council_member_id"] == "5288"
    for fy in (2014, 2022):
        r = cls("Barron", fy)
        assert (r["council_member_type"], r["council_member_id"]) == ("ambiguous", ""), fy
        assert "Charles Barron (5288)" in r["evidence"] and "Inez D. Barron (7623)" in r["evidence"]


def test_initials_and_legistar_prefixes():
    """FAILS if 'D. Diaz' does not reach Darma Diaz through Legistar's own 'D. Diaz' surname, if
    a bare 'Diaz' in a year both Diazes voted is guessed, if the no-vote 'Ruben Diaz' is ever a
    candidate, or if 'Sanchez, J' / 'J. Sanchez' / 'P. Sanchez' miss their initial."""
    assert cls("D. Diaz", 2021)["council_member_id"] == "7793"
    assert cls("Diaz", 2019)["council_member_id"] == "7744"
    amb = cls("Diaz", 2021)
    assert amb["council_member_type"] == "ambiguous" and amb["council_member_id"] == ""
    assert "excluded Ruben Diaz (5267): no recorded vote" in amb["evidence"]
    assert cls("Sanchez, J", 2026)["council_member_id"] == "7897"
    assert cls("J. Sanchez", 2027)["council_member_id"] == "7897"
    assert cls("P. Sanchez", 2027)["council_member_id"] == "7808"
    assert cls("Sanchez", 2025)["council_member_id"] == "7808"
    assert cls("Sanchez", 2026)["council_member_type"] == "ambiguous"


# ---------------------------------------------------------------- file conventions

def _addr(local_bronx=0, local_brooklyn=0, other=0):
    """Synthetic (source, city, zip) rows: Local-stream Bronx / Brooklyn grantees, plus rows from
    other streams (which the evidence must ignore)."""
    return ([("Local", "Bronx", "10451")] * local_bronx + [("Local", "Brooklyn", "11201")] * local_brooklyn
            + [("Youth", "Brooklyn", "11201")] * other)


def _diaz_inputs(**over):
    pairs = {(2019, "Diaz"): 5, (2021, "Diaz"): 10, (2021, "D. Diaz"): 8, (2022, "Diaz"): 3}
    addresses = {(2021, "Diaz"): _addr(local_bronx=6, local_brooklyn=1, other=9),
                 (2021, "D. Diaz"): _addr(local_brooklyn=5)}
    addresses.update(over)
    return pairs, addresses


def _by(rows):
    return {(r["fiscal_year"], r["council_member"]): r for r in rows}


def test_fy2021_bare_diaz_is_ruben_diaz_sr_by_file_convention():
    """Noel's 2026-10-13 decision. FAILS if FY2021 bare 'Diaz' maps to Darma Diaz (7793), stays
    ambiguous, maps to the no-vote 5267 record, or is not labeled file_convention; if 'D. Diaz'
    stops being Darma; or if the evidence is not the computed Local-stream address counts with
    the mailing-address caveat."""
    pairs, addresses = _diaz_inputs()
    r = _by(B.build(pairs, ROSTER, addresses))
    d = r[(2021, "Diaz")]
    assert (d["council_member_type"], d["council_member_id"]) == ("member", "7744")
    assert d["method"].startswith("file_convention")
    assert "Bronx 6 / Brooklyn 1" in d["evidence"] and "104xx 6 / 112xx 1" in d["evidence"]
    assert "not where services were delivered" in d["evidence"]
    assert r[(2021, "D. Diaz")]["council_member_id"] == "7793"


def test_file_convention_does_not_leak_to_other_years_or_values():
    """FAILS if the FY2021 rule reaches FY2022 'Diaz' (both Diazes voted in FY2022: still
    ambiguous), changes FY2019 'Diaz' from the generic rule, or labels any other row
    file_convention."""
    pairs, addresses = _diaz_inputs()
    r = _by(B.build(pairs, ROSTER, addresses))
    assert r[(2022, "Diaz")]["council_member_type"] == "ambiguous"
    assert r[(2022, "Diaz")]["council_member_id"] == ""
    assert r[(2019, "Diaz")] == {"fiscal_year": 2019, "council_member": "Diaz", "rows": 5,
                                 **B.classify("Diaz", 2019, ROSTER)}
    assert [k for k, v in r.items() if v["method"].startswith("file_convention")] == [(2021, "Diaz")]


@pytest.mark.parametrize("breaks", [
    "addresses_flip", "sibling_missing", "sibling_elsewhere", "no_addresses", "no_longer_ambiguous",
])
def test_file_convention_stops_when_its_premise_fails(breaks):
    """FAILS if the build applies the convention when the bare value's Local addresses stop
    pointing to the Bronx (or the sibling's to Brooklyn), when 'D. Diaz' is not printed that
    year, when 'D. Diaz' resolves to someone else, when no address evidence is passed, or when
    the generic rule no longer calls the value ambiguous."""
    pairs, addresses = _diaz_inputs()
    roster = ROSTER
    conventions = B.FILE_CONVENTIONS
    if breaks == "addresses_flip":
        addresses[(2021, "Diaz")] = _addr(local_bronx=1, local_brooklyn=6)
    elif breaks == "sibling_missing":
        del addresses[(2021, "D. Diaz")]
    elif breaks == "sibling_elsewhere":
        rule = dict(B.FILE_CONVENTIONS[(2021, "Diaz")], sibling="R. Diaz")
        conventions = {(2021, "Diaz"): rule}
        addresses[(2021, "R. Diaz")] = _addr(local_brooklyn=5)
    elif breaks == "no_addresses":
        addresses = None
    elif breaks == "no_longer_ambiguous":
        roster = [p for p in ROSTER if p.id != "7793"]
    with pytest.raises(ValueError):
        B.build(pairs, roster, addresses, conventions)


def test_accents_components_and_exact_surname_priority():
    """FAILS if 'Velazquez' misses 'Velázquez', if 'Viverito' misses Mark-Viverito, or if
    'Powers' is diluted by Brooks-Powers (an exact surname wins over a component)."""
    assert cls("Velazquez", 2023)["council_member_id"] == "7807"
    assert cls("Viverito", 2013)["council_member_id"] == "6269"
    assert cls("Powers", 2022)["council_member_id"] == "7741"
    assert cls("Brooks-Powers", 2022)["council_member_id"] == "7809"


SUFFIX_ROSTER = [
    _p(26, "Peter F. Vallone", "Peter F.", "Vallone", (2001,)),
    _p(5271, "Peter F. Vallone, Jr.", "Peter F.", "Vallone, Jr.", range(2004, 2014)),
    _p(7642, "Paul A. Vallone", "Paul A.", "Vallone", range(2014, 2023)),
    _p(5280, "James Sanders, Jr.", "James", "Sanders, Jr.", range(2004, 2013)),
    _p(5286, "Bill De Blasio", "Bill", "de Blasio", range(2004, 2011)),
    _p(7556, "The Public Advocate (Mr. de Blasio)", "Bill", "Mr. de Blasio", ()),
]


def test_printed_generational_suffix_must_match_legistar_issue_89():
    """FY2009-FY2011 print 'Vallone, Jr', 'Sanders, Jr'. FAILS if a suffixed value stays
    unresolved, resolves to a person whose Legistar name carries no suffix (Peter F. Vallone,
    Paul A. Vallone), or if the suffix is ignored and 'Vallone, Jr' in FY2014 (Peter Jr. out of
    office, Paul in) resolves to Paul."""
    r = B.classify("Vallone, Jr", 2009, SUFFIX_ROSTER)
    assert (r["council_member_type"], r["council_member_id"]) == ("member", "5271")
    assert "suffix Jr" in r["method"]
    assert B.classify("Sanders Jr.", 2009, SUFFIX_ROSTER)["council_member_id"] == "5280"
    r14 = B.classify("Vallone, Jr", 2014, SUFFIX_ROSTER)
    assert (r14["council_member_type"], r14["council_member_id"]) == ("member_outside_fy", "5271")
    assert B.classify("Vallone", 2014, SUFFIX_ROSTER)["council_member_id"] == "7642"
    nosuf = [_p(1, "Joe Doe", "Joe", "Doe", (2009,))]
    assert B.classify("Doe, Jr", 2009, nosuf)["council_member_type"] == "unresolved"


def test_surname_with_spaces_ignored_issue_89():
    """FY2009 prints 'DeBlasio'; Legistar has 'de Blasio'. FAILS if it stays unresolved, if the
    Public Advocate record (no recorded vote, 'Mr. de Blasio') is a candidate, or if an exact
    surname stops winning over the spaces-ignored form."""
    r = B.classify("DeBlasio", 2009, SUFFIX_ROSTER)
    assert (r["council_member_type"], r["council_member_id"]) == ("member", "5286")
    assert "spaces ignored" in r["method"]
    assert B.classify("de Blasio", 2009, SUFFIX_ROSTER)["method"].startswith("exact surname;")


@pytest.mark.parametrize("value,typ", [
    ("", "blank"), ("Speaker", "speaker"), ("Bronx Delegation", "delegation"),
    ("Brooklyn", "delegation"), ("SI Delegation", "delegation"),
    ("Brooklyn / Queens", "delegation"), ("Citywide", "citywide"), ("CD28", "district_label"),
    ("CD19", "district_label"), ("CC", "unresolved"), ("NA", "unresolved"),
])
def test_non_member_values_get_explicit_types_and_no_id(value, typ):
    """FAILS if a label that is not a person gets a person ID, or a type other than its own."""
    r = cls(value, 2014)
    assert (r["council_member_type"], r["council_member_id"]) == (typ, "")


# ---------------------------------------------------------------- the committed crosswalk

@pytest.fixture(scope="module")
def committed():
    with open(B.OUT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_committed_crosswalk_is_current():
    """FAILS if the committed crosswalk is not what the committed roster extract and workbooks
    produce today (a re-pull or a rule change without --write)."""
    pairs, addresses = B.disclosure_inputs()
    with open(B.OUT, encoding="utf-8") as f:
        assert B.text(B.build(pairs, B.load_roster(), addresses)) == f.read()


def test_committed_crosswalk_pins(committed):
    """Pins the outcome. FAILS if the counts by type move, if Levin and Levine ever share an
    ID, or if one ID is reached by two names in a year that differ beyond case and a
    generational suffix."""
    by = collections.Counter(r["council_member_type"] for r in committed)
    rows = collections.Counter()
    for r in committed:
        rows[r["council_member_type"]] += int(r["rows"])
    # FY2009, FY2011, FY2012 (#89 A2) added 154 member pairs (12,478 rows) and 10 unresolved
    # pairs (953 rows: CC, the two-letter borough codes BK/BX/MN/QN, and multi-member values).
    assert dict(by) == {"member": 912, "member_outside_fy": 3, "ambiguous": 3, "unresolved": 12,
                        "speaker": 14, "delegation": 93, "citywide": 8, "district_label": 5,
                        "blank": 18}
    assert rows["member"] == 113547 and rows["member_outside_fy"] == 341
    assert rows["ambiguous"] == 189 and rows["unresolved"] == 1196
    unresolved = {(r["fiscal_year"], r["council_member"]) for r in committed
                  if r["council_member_type"] == "unresolved"}
    assert {v for _, v in unresolved} >= {"CC", "BK", "BX", "MN", "QN", "NA"}
    old = {r["council_member"]: r["council_member_id"] for r in committed
           if r["fiscal_year"] == "2009"}
    assert (old["Vallone, Jr"], old["DeBlasio"], old["Addabbo, Jr"]) == ("5271", "5286", "5281")
    ids = {r["council_member"]: r["council_member_id"] for r in committed
           if r["council_member"] in ("Levin", "Levine")}
    assert ids == {"Levin": "7567", "Levine": "7634"}
    names = collections.defaultdict(set)
    for r in committed:
        if r["council_member_id"]:
            # FY2009 prints Thomas White, Jr. both as 'White' and 'White, Jr': one person.
            names[(r["fiscal_year"], r["council_member_id"])].add(
                B.split_suffix(B.fold(r["council_member"]))[0])
    assert all(len(v) == 1 for v in names.values()), {k: v for k, v in names.items() if len(v) > 1}


def test_committed_fy2021_diaz_file_convention(committed):
    """The committed crosswalk. FAILS if FY2021 'Diaz' (123 rows) is not Ruben Diaz, Sr. (7744)
    by file_convention, if 'D. Diaz' that year is not Darma (7793), if any other row is labeled
    file_convention, or if the evidence drifts from the counts the 2026-10-13 QA read from the
    committed FY2021 CSV (46 Local rows: Bronx 18, 104xx 17; D. Diaz 24 Local rows: Brooklyn 14,
    112xx 14)."""
    conv = [r for r in committed if r["method"].startswith("file_convention")]
    assert [(r["fiscal_year"], r["council_member"]) for r in conv] == [("2021", "Diaz")]
    d = conv[0]
    assert (d["council_member_type"], d["council_member_id"], d["rows"]) == ("member", "7744", "123")
    assert "'Diaz' 46 Local-stream rows: city Bronx 18 / Brooklyn 2, ZIP 104xx 17 / 112xx 2" in d["evidence"]
    assert "'D. Diaz' 24 Local-stream rows: city Bronx 0 / Brooklyn 14, ZIP 104xx 0 / 112xx 14" in d["evidence"]
    dd = [r for r in committed if (r["fiscal_year"], r["council_member"]) == ("2021", "D. Diaz")]
    assert [(r["council_member_type"], r["council_member_id"]) for r in dd] == [("member", "7793")]
