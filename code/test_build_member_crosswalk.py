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


def test_accents_components_and_exact_surname_priority():
    """FAILS if 'Velazquez' misses 'Velázquez', if 'Viverito' misses Mark-Viverito, or if
    'Powers' is diluted by Brooks-Powers (an exact surname wins over a component)."""
    assert cls("Velazquez", 2023)["council_member_id"] == "7807"
    assert cls("Viverito", 2013)["council_member_id"] == "6269"
    assert cls("Powers", 2022)["council_member_id"] == "7741"
    assert cls("Brooks-Powers", 2022)["council_member_id"] == "7809"


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
    with open(B.OUT, encoding="utf-8") as f:
        assert B.text(B.build(B.disclosure_pairs(), B.load_roster())) == f.read()


def test_committed_crosswalk_pins(committed):
    """Pins the outcome. FAILS if the counts by type move, if Levin and Levine ever share an
    ID, or if one ID is reached by two names in a year that differ beyond case."""
    by = collections.Counter(r["council_member_type"] for r in committed)
    rows = collections.Counter()
    for r in committed:
        rows[r["council_member_type"]] += int(r["rows"])
    assert dict(by) == {"member": 757, "member_outside_fy": 3, "ambiguous": 4, "unresolved": 2,
                        "speaker": 14, "delegation": 75, "citywide": 5, "district_label": 5,
                        "blank": 15}
    assert rows["member"] == 100946 and rows["member_outside_fy"] == 341
    assert rows["ambiguous"] == 312 and rows["unresolved"] == 243
    ids = {r["council_member"]: r["council_member_id"] for r in committed
           if r["council_member"] in ("Levin", "Levine")}
    assert ids == {"Levin": "7567", "Levine": "7634"}
    names = collections.defaultdict(set)
    for r in committed:
        if r["council_member_id"]:
            names[(r["fiscal_year"], r["council_member_id"])].add(r["council_member"].lower())
    assert all(len(v) == 1 for v in names.values()), {k: v for k, v in names.items() if len(v) > 1}
