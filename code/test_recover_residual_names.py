#!/usr/bin/env python3
"""
Tests for recover_residual_names.py.

Two layers:
  1. Unit tests on the decision logic — the unanimity rule, the absorbed-text reader, the defect
     classifier, the member-bleed filter. These are where a wrong name would come from.
  2. Two behavioural guarantees that the module's whole value rests on, exercised against the real
     repo: --dry-run writes NOTHING (a dry run that touched the crosswalk once recorded 16
     substitutions the data never received), and the crosswalk ACCUMULATES rather than being
     overwritten (it is the only record that the original text ever existed).

Run: python3 code/test_recover_residual_names.py
 or: pytest code/test_recover_residual_names.py
"""
import csv
import hashlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import recover_residual_names as R  # noqa: E402


# ---------------------------------------------------------------- the unanimity rule
def test_needs_two_sources():
    """One witness is never enough, however confident."""
    assert R.resolve({"council_disclosure": {"Safe Horizon"}}, "prose") is None


def test_two_agreeing_sources_resolve():
    got = R.resolve({"council_disclosure": {"Safe Horizon, Inc."},
                     "transparency_reso": {"Safe Horizon"}}, "Funds will be used to")
    assert got is not None
    name, sources = got
    assert name == "Safe Horizon, Inc."          # council wins the spelling
    assert sources == ["council_disclosure", "transparency_reso"]


def test_disagreement_is_a_stop():
    assert R.resolve({"council_disclosure": {"Safe Horizon"},
                      "transparency_reso": {"Her Justice"}}, "prose") is None


def test_internally_ambiguous_source_vetoes_rather_than_abstains():
    """The fiscal-sponsor case, and the single most important line in the module. EIN 13-2612524
    carries 229 names in this corpus; if a source keyed on (EIN, amount) returns several DIFFERENT
    organizations then that key does not identify this award, so no source keyed the same way may
    be trusted on this row either. Two other sources agreeing does not rescue it."""
    assert R.resolve({"council_disclosure": {"Alpha Fund", "Beta Trust"},
                      "transparency_reso": {"Alpha Fund"},
                      "corpus_other_year": {"Alpha Fund"}}, "prose") is None


def test_suffix_variants_are_not_a_disagreement():
    """canon() exists so 'X Corporation' and 'X Corporation, The' stop looking like two orgs."""
    got = R.resolve({"council_disclosure": {"Carnegie Hall Corporation, The"},
                     "corpus_other_year": {"Carnegie Hall Corporation"}}, "prose")
    assert got and got[0] == "Carnegie Hall Corporation, The"


def test_never_overwrites_a_field_that_already_leads_with_the_name():
    """FY21's appendices append a program label the validator misreads as prose. The name was not
    lost, so overwriting would DELETE the trailing text — a normalisation, not a recovery."""
    original = "Entertainers for Education Alliance, Inc. -I Will Graduate Program"
    assert R.resolve({"council_disclosure": {"Entertainers For Education Alliance, Inc."},
                      "corpus_other_year": {"Entertainers for Education Alliance, Inc."}},
                     original) is None


def test_more_corroborated_spelling_wins_over_the_longer_one():
    got = R.resolve({"council_disclosure": {"New Heritage Theatre Group, Inc.",
                                            "New Heritage Theatre Group, Inc., The"},
                     "transparency_reso": {"New Heritage Theatre Group, Inc."},
                     "corpus_other_year": {"New Heritage Theatre Group, Inc."}}, "prose")
    assert got and got[0] == "New Heritage Theatre Group, Inc."


# ---------------------------------------------------------------- absorbed text (S4)
def test_absorbed_tail_reads_the_name_after_the_last_dollar_figure():
    assert R.absorbed_tail("Her Justice 13-3688519 * $100,000 Safe Horizon") == "Safe Horizon"


def test_absorbed_tail_refuses_a_prose_tail():
    """The FY2018 shape runs on into purpose text; a purpose is not a name."""
    assert R.absorbed_tail("Brooklyn Arts Council, Inc. 237072915 * $10,500.00 Funds will be "
                           "used to run the program") == ""


def test_absorbed_tail_empty_without_a_dollar_figure():
    assert R.absorbed_tail("Coalition of Institutionalized Aged and Disabled") == ""


# ---------------------------------------------------------------- classification and hygiene
def test_classify_matches_the_validator_precedence():
    assert R.classify("") == "empty"
    assert R.classify("Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders") == "org_merged"
    assert R.classify("Funds will be used to support the program") == "org_prose"
    assert R.classify("Safe Horizon, Inc.") is None
    # org_merged outranks org_prose when a row is both.
    assert R.classify("Funding to support X 13-3931074 * $1") == "org_merged"


def test_member_bleed_names_are_not_usable_evidence():
    R._SURNAMES = {"gjonaj", "lander"}
    assert R.has_member_bleed("Gjonaj HANAC, Inc.")
    assert not R.has_member_bleed("HANAC, Inc.")
    assert not R.has_member_bleed("Gjonaj")            # a bare token is not an org at all
    assert not R.is_clean_name("Lander New York Memory Center")
    R._SURNAMES = set()


# ---------------------------------------------------------------- behavioural guarantees
def _fingerprint(paths):
    h = {}
    for p in paths:
        with open(p, "rb") as fh:
            h[p] = hashlib.sha256(fh.read()).hexdigest()
    return h


def test_dry_run_writes_nothing_at_all():
    """The hard rule. A dry run must not touch a single byte — not the award CSVs, not the
    crosswalk. This is a regression test for a real bug: a dry run that appended to the audit
    trail recorded 16 substitutions the data never received."""
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        watched = sorted(R.award_files()) + [R.CROSSWALK]
        watched = [p for p in watched if os.path.exists(p)]
        before = _fingerprint(watched)
        assert R.main(["--dry-run"]) == 0
        assert _fingerprint(watched) == before, "--dry-run modified a file"
    finally:
        os.chdir(cwd)


def test_crosswalk_accumulates_and_never_drops_a_prior_entry():
    cols = R.CROSSWALK_FIELDS
    old = {c: "" for c in cols}
    old.update(file="data/fy16/schedule_c/a.csv", line="7", ein="131234567", amount="1000",
               defect="org_prose", source="council_disclosure", match_key="ein+amount",
               original_organization="Funds will be used", recovered_organization="Alpha, Inc.")
    new = dict(old, line=9, original_organization="To provide services",
               recovered_organization="Beta, Inc.")
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            os.makedirs(os.path.dirname(R.CROSSWALK))
            with open(R.CROSSWALK, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerow(old)
            assert R.append_crosswalk([new]) == 2
            rows = list(csv.DictReader(open(R.CROSSWALK, newline="", encoding="utf-8")))
            assert [r["line"] for r in rows] == ["7", "9"]          # sorted, prior kept
            assert rows[0]["original_organization"] == "Funds will be used"
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print(f"ok  {name}")
    print(f"\n{len(fns)} passed")
