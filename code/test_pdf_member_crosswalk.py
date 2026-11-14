#!/usr/bin/env python3
"""
Tests for the PDF-table half of build_member_crosswalk.py (GitHub #51): the printed `member` of
the checked Schedule C and transparency tables -> a Legistar person ID per fiscal year, by the
same rules #72 uses for the disclosure (one classify(), one roster, no second method).

What #51 found, pinned here: 'Williams' is two people in different years, 'Sanchez' is printed
bare until FY2027 and then as 'J. Sanchez' / 'P. Sanchez', 'Levin' is not 'Levine', 'Won' is not
'Wong', 'Barron' in FY2022 cannot be told apart, and borough delegation labels stay delegations.

Each docstring says what result would FAIL the test. Run: pytest code/test_pdf_member_crosswalk.py
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
    _p(6267, "Daniel R. Garodnick", "Daniel R.", "Garodnick", range(2006, 2019)),
    _p(7808, "Pierina Ana Sanchez", "Pierina", "Sanchez", range(2022, 2028)),
    _p(7897, "Justin E. Sanchez", "Justin E.", "Sanchez", (2026, 2027)),
    _p(5288, "Charles Barron", "Charles", "Barron", list(range(2004, 2015)) + [2022, 2023, 2024]),
    _p(7623, "Inez D. Barron", "Inez D.", "Barron", range(2014, 2023)),
]


# ---------------------------------------------------------------- the rules, on synthetic rows

def test_a_resolution_naming_an_earlier_years_member_keeps_the_id_and_says_why():
    """A FY2019 resolution row that changes the FY2018 budget names Garodnick, who left in
    FY2018. FAILS if the row loses his ID, is called the disclosure's 'export-time roster', or
    does not say a resolution can change an earlier year's budget."""
    r = B.build_pdf({("transparency", 2019, "Garodnick"): 2}, ROSTER)[0]
    assert (r["council_member_type"], r["council_member_id"]) == ("member_outside_fy", "6267")
    assert "export-time" not in r["method"]
    assert "earlier year's budget" in r["method"]


def test_a_name_outside_its_year_says_why_in_the_pdf_words():
    """FAILS if a PDF row outside the person's service is explained as the disclosure's
    'export-time roster' (a PDF has no export), or loses its ID."""
    rows = B.build_pdf({("schedule_c", 2020, "Garodnick"): 1}, ROSTER)
    r = rows[0]
    assert r["council_member_type"] == "member_outside_fy" and r["council_member_id"] == "6267"
    assert "export-time" not in r["method"]
    assert "Schedule C prints the member at adoption" in r["method"]


def test_overlapping_terms_are_ambiguous_with_their_candidates_and_no_id():
    """FY2026 bare 'Sanchez' and FY2022 'Barron': two people with that surname voted in the year.
    FAILS if either gets an ID (a guess), or the row does not list both candidates."""
    rows = {(r["fiscal_year"], r["council_member"]): r
            for r in B.build_pdf({("schedule_c", 2026, "Sanchez"): 138,
                                  ("schedule_c", 2022, "Barron"): 45}, ROSTER)}
    s, b = rows[(2026, "Sanchez")], rows[(2022, "Barron")]
    for r, ids in ((s, "7808;7897"), (b, "5288;7623")):
        assert r["council_member_type"] == "ambiguous"
        assert r["council_member_id"] == ""
        assert r["candidate_ids"] == ids
        assert "not guessed" in r["method"]


def test_initials_split_the_two_sanchezes_and_join_pierina_across_labels():
    """FAILS if 'P. Sanchez' (FY2027) is not the person bare 'Sanchez' is in FY2023, or if
    'J. Sanchez' is."""
    rows = {(r["fiscal_year"], r["council_member"]): r["council_member_id"]
            for r in B.build_pdf({("schedule_c", 2023, "Sanchez"): 1,
                                  ("schedule_c", 2027, "P. Sanchez"): 1,
                                  ("schedule_c", 2027, "J. Sanchez"): 1}, ROSTER)}
    assert rows[(2023, "Sanchez")] == rows[(2027, "P. Sanchez")] == "7808"
    assert rows[(2027, "J. Sanchez")] == "7897"


@pytest.mark.parametrize("value,typ", [
    ("Brooklyn Delegation", "delegation"), ("Staten Island Delegation", "delegation"),
    ("Speaker", "speaker"), ("", "blank"), ("CD 22", "district_label"),
    ("Council District 2", "district_label"),
])
def test_labels_that_are_not_people_keep_their_type_and_no_id(value, typ):
    """FAILS if a delegation, the Speaker, a blank or a district label is given a person, or
    'Council District 2' (FY2026 transparency, a vacancy) is called an unknown name."""
    r = B.build_pdf({("transparency", 2026, value): 1}, ROSTER)[0]
    assert (r["council_member_type"], r["council_member_id"], r["candidate_ids"]) == (typ, "", "")


def test_the_district_label_rule_did_not_change_the_disclosure_crosswalk():
    """The district pattern now also reads 'Council District N'. FAILS if that changes the type
    of any value the disclosure prints (the committed disclosure crosswalk would go stale)."""
    for r in _read(B.OUT):
        if r["council_member_type"] != "district_label":
            assert B._DISTRICT.fullmatch(B.fold(r["council_member"])) is None, r


# ---------------------------------------------------------------- the committed crosswalk

def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def committed():
    return _read(B.PDF_OUT)


def test_committed_pdf_crosswalk_is_current():
    """FAILS if data/pdf_council_member_crosswalk.csv is not what the committed roster extract
    and the committed PDF tables give (run code/build_member_crosswalk.py --write)."""
    with open(B.PDF_OUT, encoding="utf-8") as f:
        assert f.read() == B.text(B.build_pdf(B.pdf_pairs(), B.load_roster()), B.PDF_FIELDS)


def test_committed_pdf_crosswalk_covers_every_served_row(committed):
    """FAILS if a (family, fiscal year, printed member) of a reviewed or closed family-year has
    no crosswalk row, or the row counts differ from the tables."""
    got = {(r["family"], int(r["fiscal_year"]), r["council_member"]): int(r["rows"]) for r in committed}
    assert got == dict(B.pdf_pairs())


def test_committed_ids_fit_their_types(committed):
    """FAILS if a row without a member type carries an ID, a member type lacks one, or an
    ambiguous row lists fewer than two candidates."""
    for r in committed:
        has = r["council_member_id"] != ""
        assert has == (r["council_member_type"] in B.ID_TYPES), r
        assert (r["candidate_ids"] != "") == (r["council_member_type"] == "ambiguous"), r
        if r["candidate_ids"]:
            assert len(r["candidate_ids"].split(";")) >= 2, r


def test_committed_issue_51_cases(committed):
    """The cases #51 names, on the real tables. FAILS if 'Williams' is one person across the
    years, 'Levin'/'Levine' or 'Won'/'Wong' share a person, FY2022 'Barron' or FY2026 'Sanchez'
    get an ID, or 'P. Sanchez' (FY2027) is not the FY2023 'Sanchez'."""
    by = collections.defaultdict(set)
    one = {}
    for r in committed:
        if r["council_member_id"]:
            by[r["council_member"]].add(r["council_member_id"])
        one[(r["family"], r["fiscal_year"], r["council_member"])] = r
    assert len(by["Williams"]) == 2
    assert not by["Levin"] & by["Levine"] and by["Levin"] and by["Levine"]
    assert not by["Won"] & by["Wong"] and by["Won"] and by["Wong"]
    assert one[("schedule_c", "2022", "Barron")]["council_member_type"] == "ambiguous"
    assert one[("schedule_c", "2026", "Sanchez")]["council_member_type"] == "ambiguous"
    assert one[("schedule_c", "2027", "P. Sanchez")]["council_member_id"] == one[("schedule_c", "2023", "Sanchez")]["council_member_id"]
    assert one[("schedule_c", "2027", "J. Sanchez")]["council_member_id"] not in ("", one[("schedule_c", "2023", "Sanchez")]["council_member_id"])


def test_committed_delegations_stay_delegations(committed):
    """#51 'Do NOT break these'. FAILS if a printed '... Delegation' value is not typed
    delegation, or carries an ID."""
    dl = [r for r in committed if r["council_member"].endswith(" Delegation")]
    assert dl
    for r in dl:
        assert (r["council_member_type"], r["council_member_id"]) == ("delegation", ""), r
