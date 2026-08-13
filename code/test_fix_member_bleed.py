#!/usr/bin/env python3
"""
Tests for fix_member_bleed.py — peeling a bled council-member surname off an organization name.

Runs against a tiny synthetic tree (a hand-built xlsx plus two CSVs, no PDFs), because what has to
be proven is the DECISION, not the parsing: which rows get stripped, which are left alone, and
that a dry run writes nothing at all.

Run:  python3 code/test_fix_member_bleed.py      (no pytest in this environment)
      pytest code/test_fix_member_bleed.py       (also works where it is installed)
"""
import contextlib
import csv
import io
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fix_member_bleed as M  # noqa: E402

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
AWARD_HDR = ["category", "initiative", "award_type", "member", "organization", "program",
             "ein", "amount", "agency", "purpose"]


def _xlsx(path, header, rows):
    """Minimal xlsx: a shared-string table and one sheet. Enough for M.read_workbook, which opens
    only xl/sharedStrings.xml and xl/worksheets/sheet1.xml."""
    strings, index = [], {}

    def sid(s):
        if s not in index:
            index[s] = len(strings)
            strings.append(s)
        return index[s]

    body = []
    for r in [header] + rows:
        cells = []
        for v in r:
            if isinstance(v, int):
                cells.append(f"<c><v>{v}</v></c>")
            else:
                cells.append(f'<c t="s"><v>{sid(str(v))}</v></c>')
        body.append("<row>" + "".join(cells) + "</row>")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/sharedStrings.xml",
                   f'<sst xmlns="{NS}">' + "".join(f"<si><t>{s}</t></si>" for s in strings)
                   + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml",
                   f'<worksheet xmlns="{NS}"><sheetData>' + "".join(body)
                   + "</sheetData></worksheet>")


def _awards(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(AWARD_HDR)
        for member, org, ein, amt in rows:
            w.writerow(["Cat", "Init", "member_item", member, org, "", ein, amt, "DYCD", ""])


def build_tree(root):
    """One award year to repair (fy16) and one clean year (fy17) that supplies corpus evidence."""
    _awards(f"{root}/data/fy16/schedule_c/fy16_schedule_c_awards.csv", [
        # ln 2  bled surname, disclosure confirms the remainder            -> FIX
        ("", "Eugene 71st Precinct Community Council, Inc.", "043784543", 5500),
        # ln 3  borough leads a REAL name, disclosure confirms as printed  -> KEEP
        ("Gutierrez", "Brooklyn Book Bodega, Inc.", "111111111", 1000),
        # ln 4  two disclosure spellings of ONE name (canon-equal)         -> FIX
        ("Speaker", "Chin Asian Americans for Equality", "222222222", 2000),
        # ln 5  two genuinely different disclosure names for the key       -> LEAVE
        ("Speaker", "Johnson Church of Holy Apostles", "333333333", 3000),
        # ln 6  real org, surname-shaped first word, no disclosure row     -> LEAVE
        ("Manhattan", "Hudson Guild", "444444444", 4000),
        # ln 7  no disclosure row, but our own corpus carries the INVERSE
        #       defect for this EIN ('Hudson' in member, 'Guild' in org).
        #       Trusting our own output here truncates a real name.        -> LEAVE
        ("Speaker", "Hudson Guild", "135562989", 5000),
        # ln 8  co-sponsor list bled in, disclosure confirms the remainder -> FIX
        ("", "Brannan, Lander, Maisel Brooklyn Alliance, Inc.", "777777777", 7000),
        # ln 9  the list halts at a non-surname, so nothing confirms       -> LEAVE
        ("", "Brannan, ACME, Lander Brooklyn Alliance, Inc.", "777777777", 7000),
    ])
    _awards(f"{root}/data/fy17/schedule_c/fy17_schedule_c_awards.csv", [
        # The inverse defect: the parser put the org's first word into `member`. These rows are
        # what made a corpus-based fallback unsafe, and are kept here so a future reviver of that
        # idea trips over the counterexample.
        ("Hudson", "Guild", "135562989", 28986),
        ("Hudson", "Guild", "135562989", 100000),
        # The surname set is derived from the `member` column, so a surname only becomes peelable
        # once it appears there — exactly as in the real corpus, where the bled row itself has
        # lost its member and a sibling row still carries it.
        ("Eugene", "Alpha Center", "900000001", 1),
        ("Chin", "Beta House", "900000002", 1),
        ("Johnson", "Gamma Trust", "900000003", 1),
        ("Mealy", "Delta Fund", "900000004", 1),
        ("Brannan", "Epsilon Trust", "900000005", 1),
        ("Lander", "Zeta House", "900000006", 1),
        ("Maisel", "Eta Works", "900000007", 1),
    ])
    _xlsx(f"{root}/source/expense-funding-disclosure/funded_disclosure_FY2016.xlsx",
          ["Legal Name", "Tax ID", "Amount", "FC EIN"], [
              ["71st Precinct Community Council, Inc.", "04-3784543", 5500, ""],
              ["Brooklyn Book Bodega, Inc.", "11-1111111", 1000, ""],
              ["Asian Americans for Equality", "22-2222222", 2000, ""],
              ["Asian Americans For Equality, Inc.", "22-2222222", 2000, ""],
              ["Church of Holy Apostles", "33-3333333", 3000, ""],
              ["Holy Apostles Soup Kitchen", "33-3333333", 3000, ""],
              ["Brooklyn Alliance, Inc.", "77-7777777", 7000, ""],
          ])


def _plan(root):
    fixes, stats, _ = M.plan(f"{root}/data", f"{root}/source/expense-funding-disclosure")
    return {(x["file"].split("/")[-1], x["line"]): x for x in fixes}, stats


def test_decisions():
    root = tempfile.mkdtemp()
    try:
        build_tree(root)
        got, stats = _plan(root)
        F = "fy16_schedule_c_awards.csv"

        assert got[(F, 2)]["recovered_organization"] == "71st Precinct Community Council, Inc."
        assert got[(F, 2)]["source"] == "council_disclosure"
        assert "removed=Eugene" in got[(F, 2)]["match_key"]
        assert "@FY2016" in got[(F, 2)]["match_key"], "same-year disclosure should be preferred"
        assert got[(F, 2)]["_member"] == "Eugene", \
            "an empty member must inherit the surname, not lose it"
        assert got[(F, 4)]["_member"] is None, "an existing member is never overwritten"
        assert "member<-" not in got[(F, 4)]["match_key"]

        assert (F, 3) not in got, "a borough that opens a real name must never be peeled"
        assert stats["confirmed_as_printed"] >= 1

        assert got[(F, 4)]["recovered_organization"] == "Asian Americans for Equality", \
            "two spellings of one name are one candidate, not a conflict"

        assert (F, 5) not in got, "two different names for the key is not a unique resolution"
        assert stats["disclosure_disagrees"] == 2   # ln 5, and the partial peel on ln 9

        assert (F, 6) not in got, "no evidence either way means leave the row flagged"

        assert (F, 7) not in got, \
            "our own rows are not evidence about our own defects — this is the Hudson Guild trap"

        assert got[(F, 8)]["recovered_organization"] == "Brooklyn Alliance, Inc."
        assert got[(F, 8)]["match_key"].split("removed=")[1].split("|")[0] == \
            "Brannan, Lander, Maisel"
        assert got[(F, 8)]["_member"] is None, "a co-sponsor list is never written to `member`"

        assert (F, 9) not in got, "a partially-peeled sponsor list must confirm against nothing"
        assert len(got) == 3, f"expected exactly 3 fixes, got {sorted(got)}"
        assert stats["unresolved"] == 2             # ln 6 and ln 7, both "Hudson Guild"

        # Reversibility by string arithmetic: original == removed + whitespace + recovered.
        for x in got.values():
            removed = x["match_key"].split("removed=")[1].split("|member<-")[0]
            org, rec = x["original_organization"], x["recovered_organization"]
            assert org.endswith(rec) and org[:-len(rec)].strip() == removed
    finally:
        shutil.rmtree(root)


def test_dry_run_writes_nothing():
    """The bug this guards: a dry run that appended to the crosswalk recorded 16 substitutions the
    data never received. --dry-run must leave every byte on disk untouched, crosswalk included."""
    root = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        build_tree(root)
        os.makedirs(f"{root}/data/combined", exist_ok=True)
        with open(f"{root}/{M.CROSSWALK}", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=M.CROSSWALK_FIELDS)
            w.writeheader()
            w.writerow({k: "prior" for k in M.CROSSWALK_FIELDS} | {"line": "2"})

        def snapshot():
            out = {}
            for dp, _, fns in os.walk(root):
                for fn in fns:
                    p = os.path.join(dp, fn)
                    out[p] = open(p, "rb").read()
            return out

        os.chdir(root)
        before = snapshot()
        with contextlib.redirect_stdout(io.StringIO()):
            assert M.main(["--dry-run"]) == 0
        assert snapshot() == before, "--dry-run modified something on disk"

        # ...and the real run does write, and the crosswalk ACCUMULATES rather than overwrites.
        with contextlib.redirect_stdout(io.StringIO()):
            assert M.main([]) == 0
        rows = list(csv.DictReader(open(M.CROSSWALK, newline="", encoding="utf-8")))
        assert sum(1 for r in rows if r["file"] == "prior") == 1, "prior entry was dropped"
        assert sum(1 for r in rows if r["defect"] == "member_bleed") == 3
        # every crosswalk entry is verifiable against the data it claims to have changed
        assert "_member" not in rows[0], "the private member hint must not leak into the crosswalk"
        for r in rows:
            if r["defect"] != "member_bleed":
                continue
            row = list(csv.DictReader(open(r["file"], newline="", encoding="utf-8")))[
                int(r["line"]) - 2]
            assert row["organization"] == r["recovered_organization"]
            if "member<-" in r["match_key"]:
                assert row["member"] == r["match_key"].split("member<-")[1]
        # ln 2 had no member and gains one; ln 4's "Speaker" survives untouched.
        fy16 = list(csv.DictReader(
            open("data/fy16/schedule_c/fy16_schedule_c_awards.csv", newline="", encoding="utf-8")))
        assert fy16[0]["member"] == "Eugene"
        assert fy16[2]["member"] == "Speaker"
    finally:
        os.chdir(cwd)
        shutil.rmtree(root)


def test_peel_and_surname_set():
    surnames = {"Eugene", "De La Rosa", "Rosa", "Brooklyn", "Powers", "Brooks-Powers",
                "Brannan", "Lander", "Maisel", "Ampry-Samuel", "Cornegy", "Dromm"}
    assert M.peel("Eugene 71st Precinct Community Council", surnames) == (
        "Eugene", "71st Precinct Community Council")
    assert M.peel("De La Rosa Community League", surnames)[0] == "De La Rosa", \
        "longest matching surname wins, not the first"
    assert M.peel("Brooks-Powers Bright Future", surnames)[0] == "Brooks-Powers"
    assert M.peel("Eugenetics Institute", surnames) == (None, None), \
        "a surname must end at a space or comma, not mid-word"
    assert M.peel("Powers", surnames) == (None, None), "nothing left over is not a fix"

    # co-sponsor lists: consume the whole run...
    assert M.peel("Brannan, Lander, Maisel Brooklyn Alliance, Inc.", surnames) == (
        "Brannan, Lander, Maisel", "Brooklyn Alliance, Inc.")
    assert M.peel("Dromm, LGBT AIDS Center of Queens County, Inc.", surnames) == (
        "Dromm,", "LGBT AIDS Center of Queens County, Inc.")
    # ...but stop dead at the first element that is not a known surname
    assert M.peel("Ampry-Samuel, BLAC, Cornegy Bedford Stuyvesant Restoration", surnames) == (
        "Ampry-Samuel,", "BLAC, Cornegy Bedford Stuyvesant Restoration")

    for org, (removed, rest) in [(o, M.peel(o, surnames)) for o in (
            "Eugene 71st Precinct Community Council",
            "Brannan, Lander, Maisel Brooklyn Alliance, Inc.",
            "Dromm, LGBT AIDS Center of Queens County, Inc.")]:
        assert org.endswith(rest) and org[:-len(rest)].strip() == removed

    root = tempfile.mkdtemp()
    try:
        _awards(f"{root}/data/fy16/schedule_c/fy16_schedule_c_awards.csv", [
            ("De La Rosa", "A Corp", "1", 1), ("Brooks-", "B Corp", "2", 1),
            ("Brooks-Powers", "C Corp", "3", 1), ("Speaker", "D Corp", "4", 1),
            ("Center", "E Corp", "5", 1), ("The", "F Corp", "6", 1),
        ])
        s = M.build_surnames(M.surname_sources(f"{root}/data"))
        assert {"De La Rosa", "Rosa", "Brooks-Powers", "Powers"} <= s
        assert not ({"Speaker", "Center", "The"} & s), "parser residue is not a surname"
        assert M.BOROUGHS <= s, "borough sponsors bleed too, and are nominated the same way"
        assert "De" not in s and "La" not in s, "particles must not become peelable tokens"
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all passed")
