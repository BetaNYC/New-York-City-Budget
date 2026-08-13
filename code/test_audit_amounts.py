#!/usr/bin/env python3
"""
Tests for audit_amounts.py — the award-amount audit.

Three things here can be wrong in a way that is invisible in the output, so each gets a test:

1. `unshift()` — the disclosure left-shift repair. Too eager and it mangles good rows into
   nonsense EINs; too timid and FY2016's 272 shifted rows stay unreadable, which makes the audit
   report phantom defects against data that is fine. The boundary is a non-EMPTY non-numeric EIN
   slot, because FY2014 carries genuinely blank EINs that must NOT be treated as shifted.
2. `classify()` — verdict ordering. An exact figure under the same EIN must outrank an approximate
   one, and both must outrank any story about where the number came from. Get the order wrong and
   real divergences hide inside `rounding` or `neighbour_bleed`.
3. `--dry-run` writes NOTHING. A dry run that wrote to the audit trail once recorded 16
   substitutions the data never received.

Run: pytest code/test_audit_amounts.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import audit_amounts as A  # noqa: E402

# Header layout of funded_disclosure_FY2016.xlsx.
HDR = ["Source", "Council Member", "Legal Name of Organization Requesting Funding", "EIN",
       "Status", "Amount", "Agency", "Program Name"]
I_NAME = A.hidx(HDR, ("legal name",))
I_EIN = A.hidx(HDR, ("tax id", "ein"), exclude=("fc ein", "conduit"))


def test_header_lookup_skips_fiscal_conduit_columns():
    """A conduit EIN is the pass-through sponsor's, not the grantee's. Grabbing one would key an
    award to an organization that never received the money."""
    fy16 = ["Source", "Council Member", "Legal Name of Organization Requesting Funding", "EIN",
            "Status", "Amount", "Agency", "Fiscal Conduit", "FC EIN"]
    fy24 = ["MOCS ID#", "Fiscal Year", "Source", "Council Member", "Legal Name", "Tax ID",
            "Status", "Amount", "Fiscal Conduit", "Fiscal Conduit EIN"]
    assert fy16[A.hidx(fy16, ("tax id", "ein"), exclude=("fc ein", "conduit"))] == "EIN"
    assert fy24[A.hidx(fy24, ("tax id", "ein"), exclude=("fc ein", "conduit"))] == "Tax ID"
    # Substring matching is required: exact lookups silently miss the drifted headers.
    assert A.hidx(["Amount ($"], ("amount",)) == 0
    assert fy16[A.hidx(fy16, ("legal name",))].startswith("Legal Name of Organization")


def test_unshift_repairs_a_shifted_row():
    """The FY2016 shape: no council member, so every cell after Source sits one column early."""
    vals = ["6th Congregate Weekend Meal", "CityMeals on Wheels", "133634381", "Cleared",
            "600000", "DFTA", "", "355 Lexington Avenue"]
    out, did = A.unshift(list(vals), I_NAME, I_EIN)
    assert did is True
    d = dict(zip(HDR, out))
    assert d["Council Member"] == ""
    assert d["Legal Name of Organization Requesting Funding"] == "CityMeals on Wheels"
    assert d["EIN"] == "133634381"
    assert d["Status"] == "Cleared"
    assert A.money(d["Amount"]) == 600000
    assert d["Agency"] == "DFTA"


def test_unshift_leaves_well_formed_rows_alone():
    vals = ["Local", "Rivera", "Henry Street Settlement", "131562242", "Cleared", "5000",
            "DYCD", "After School"]
    out, did = A.unshift(list(vals), I_NAME, I_EIN)
    assert (out, did) == (vals, False)


def test_unshift_ignores_a_genuinely_blank_ein():
    """FY2014 row 45: '88th Precinct', no EIN on file. Not shifted — the name slot holds a NAME.
    And the mirror case: a blank EIN slot alone must never trigger the repair."""
    vals = ["Youth", "James", "88th Precinct", "", "Pending", "5000", "DYCD", ""]
    assert A.unshift(list(vals), I_NAME, I_EIN)[1] is False
    nine_but_blank = ["Youth", "James", "133634381", "", "Pending", "5000", "DYCD", ""]
    assert A.unshift(list(nine_but_blank), I_NAME, I_EIN)[1] is False


def _year(triples):
    """Build a Year from (ein, canonical_name, amount) triples."""
    y = A.Year()
    for ein, name, amt in triples:
        key = (ein, name)
        y.by_org[key][amt] += 1
        y.by_ein[ein][amt] += 1
        y.by_amt[amt].add(key)
        y.rows += 1
    return y


def test_classify_verdicts_and_their_precedence():
    y = _year([("131562242", "henrystreetsettlement", 5000),
               ("131562242", "henrystreetsettlementhouse", 12345),
               ("135562301", "nycmissionsociety", 833334),
               ("999999999", "loneholderofararefigure", 777777)])

    # exact: this (EIN, org) carries this amount
    assert A.classify(5000, "131562242", "henrystreetsettlement", y, set())[0] == "exact"

    # name_variant outranks rounding: an EXACT figure under the same EIN beats a near one.
    # 12345 is exact under a different spelling; 12346 would be within rounding of it.
    assert A.classify(12345, "131562242", "henrystreetsettlement", y, set())[0] == "name_variant"

    # rounding: nearest is within ROUND_TOL and nothing exact corroborates it
    v, near, _ = A.classify(833333, "135562301", "nycmissionsociety", y, set())
    assert (v, near) == ("rounding", 833334)
    assert abs(833333 - near) <= A.ROUND_TOL

    # neighbour_bleed: the figure is UNIQUELY held by another org printed nearby
    owner = ("999999999", "loneholderofararefigure")
    v, _, got = A.classify(777777, "131562242", "henrystreetsettlement", y, {owner})
    assert (v, got) == ("neighbour_bleed", owner)
    # ...and NOT flagged when that org is not a neighbour — proximity is the whole claim
    assert A.classify(777777, "131562242", "henrystreetsettlement", y,
                      set())[0] == "unconfirmed"

    # ein_absent vs unconfirmed: absence of evidence is reported as such, separately
    assert A.classify(5000, "000000000", "someorg", y, set())[0] == "ein_absent"
    assert A.classify(4242, "131562242", "henrystreetsettlement", y, set())[0] == "unconfirmed"

    # no key to join on
    assert A.classify(5000, "", "someorg", y, set())[0] == "no_key"
    assert A.classify(None, "131562242", "henrystreetsettlement", y, set())[0] == "no_key"


def test_a_common_amount_is_never_called_bleed():
    """$5,000 is held by hundreds of grantees a year. Adjacency proves nothing about a figure that
    is not uniquely owned, and calling it bleed would bury the handful of real cases."""
    y = _year([("111111111", "orga", 5000), ("222222222", "orgb", 5000)])
    assert A.classify(5000, "333333333", "orgc", y, {("111111111", "orga")})[0] == "ein_absent"


def test_dry_run_writes_absolutely_nothing():
    """The rule that already cost this repo a false audit trail. Run the real script with
    --dry-run against the real tree and assert every output is untouched."""
    watched = [os.path.join(REPO, p) for p in
               (A.REPORT, A.FINDINGS, "data/combined/org_name_recovery_crosswalk.csv")]
    before = [(os.path.exists(p), os.path.getmtime(p) if os.path.exists(p) else None,
               os.path.getsize(p) if os.path.exists(p) else None) for p in watched]

    r = subprocess.run([sys.executable, os.path.join(HERE, "audit_amounts.py"), "--dry-run"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "nothing written" in r.stdout

    after = [(os.path.exists(p), os.path.getmtime(p) if os.path.exists(p) else None,
              os.path.getsize(p) if os.path.exists(p) else None) for p in watched]
    assert before == after, f"--dry-run touched an output file: {watched}"


def test_audit_writes_only_its_own_two_outputs():
    """There is no --apply, and the only files opened for writing are the report and the findings
    CSV. The crosswalk is read for cross-checking and never written: it records substitutions
    APPLIED to the data, and this pass applies none. If someone adds a write path, this test is
    what should make them justify it in the report first."""
    src = open(os.path.join(HERE, "audit_amounts.py"), encoding="utf-8").read()
    assert not re.search(r'add_argument\(\s*"--(apply|fix|write)"', src)
    assert set(re.findall(r'open\(\s*([A-Za-z_][A-Za-z_0-9]*)\s*,\s*"w"', src)) == {"REPORT",
                                                                                    "FINDINGS"}
    assert not re.search(r'open\(\s*"[^"]*crosswalk[^"]*"\s*,\s*"w"', src)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
