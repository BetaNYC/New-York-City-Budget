#!/usr/bin/env python3
"""
Tests for build_combined.py — the cross-year Schedule C roll-up builder.

The regression these guard against (DATA-ANOMALIES #8): the roll-up must carry the `purpose`
column through from the per-year award files. Dropping it collapsed source-distinct rows
(identical org/amount, different stated purpose) into apparent duplicates in the combined file —
manufacturing 7 duplicate instances that do not exist in any source. The fix added `purpose` to
AWARD_COLS. These tests assert the roll-up faithfully passes rows through and manufactures ZERO
duplicates of its own, both on a synthetic fixture and against the real committed data tree.

Run: pytest code/test_build_combined.py
"""
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_combined as B  # noqa: E402

AWARD_HDR = ("category,initiative,award_type,member,organization,program,"
             "ein,amount,agency,purpose")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def _full_row_dupes(rows):
    """Count extra copies (sum of count-1 over groups with count>1) of fully-identical rows."""
    c = Counter(tuple(r) for r in rows)
    return sum(v - 1 for v in c.values() if v > 1)


# --------------------------------------------------------------- synthetic regression fixture
def test_purpose_carried_through_no_false_dupes(tmp_path):
    """Two rows identical in the 9 non-purpose fields but with DIFFERENT purpose text must stay
    two distinct rows in the roll-up (not collapse to a duplicate). A genuinely identical pair
    (all 10 fields equal) must pass through as two rows."""
    data = tmp_path / "data"
    # fy24: rows A and B share org/amount but differ in purpose (source-distinct);
    #        rows C and C are fully identical (legitimate in-source repeat).
    _write(str(data / "fy24" / "schedule_c" / "fy24_schedule_c_awards.csv"),
           AWARD_HDR + "\n"
           "CJ,Init,initiative_provider,,Acme Inc.,,13-2612524,25000,DYCD,purpose one\n"
           "CJ,Init,initiative_provider,,Acme Inc.,,13-2612524,25000,DYCD,purpose two\n"
           "ED,Init,member_item,Rivera,Beta Org,,20-5620848,20000,DOE,\n"
           "ED,Init,member_item,Rivera,Beta Org,,20-5620848,20000,DOE,\n")

    rows = B.collect("awards", B.AWARD_COLS, data_dir=str(data))
    assert "purpose" in B.AWARD_COLS, "purpose must be in the roll-up schema"
    assert len(rows) == 4, rows

    purpose_idx = 1 + B.AWARD_COLS.index("purpose")  # +1 for the leading year column
    purposes = sorted(r[purpose_idx] for r in rows)
    assert purposes == ["", "", "purpose one", "purpose two"], purposes

    # The Acme pair differs only in purpose -> must NOT be a duplicate.
    # The Beta pair is fully identical -> that IS a faithful in-source repeat (1 extra copy).
    assert _full_row_dupes(rows) == 1, (
        "roll-up should preserve exactly the 1 genuine full-row repeat and manufacture no others")


def test_roll_up_faithful_to_per_year_sources_real_tree():
    """Against the committed data/ tree: the awards roll-up row count equals the sum of the
    per-year *_schedule_c_awards.csv row counts, it carries `purpose`, and it manufactures ZERO
    duplicates beyond those already present (identically) in the per-year sources."""
    import glob
    per_year_files = sorted(glob.glob(
        os.path.join(REPO, "data", "fy*", "schedule_c", "*_schedule_c_awards.csv")))
    assert per_year_files, "expected committed per-year award files"

    per_year_rows = 0
    per_year_full_dupes = 0
    for p in per_year_files:
        with open(p, newline="") as f:
            recs = list(csv.DictReader(f))
        per_year_rows += len(recs)
        cols = recs[0].keys()
        per_year_full_dupes += _full_row_dupes([tuple(r[c] for c in cols) for r in recs])

    combined = B.collect("awards", B.AWARD_COLS)
    assert len(combined) == per_year_rows, (len(combined), per_year_rows)
    assert "purpose" in B.AWARD_COLS

    # The number of full-row duplicate instances in the roll-up must equal the number already
    # present in the per-year sources — i.e. the roll-up invents none of its own. (Before the
    # purpose fix this was 149 vs 142, the 7-instance regression.)
    combined_full_dupes = _full_row_dupes([tuple(r) for r in combined])
    assert combined_full_dupes == per_year_full_dupes, (combined_full_dupes, per_year_full_dupes)


# --------------------------------------------------------------- initiative_canonical (DATA-ANOMALIES #17)
def test_house_style_and_canonical_for_units():
    """house_style() is the deterministic mechanical normalizer; canonical_for() prefers an
    explicit crosswalk mapping and falls back to house_style()."""
    assert B.house_style("*Cancer Initiatives") == "Cancer Initiatives"            # leading * marker
    assert B.house_style("Dropout Prevention & Intervention") == "Dropout Prevention and Intervention"
    assert B.house_style("City’s First Readers") == "City's First Readers"      # curly -> straight
    assert B.house_style("Legal  Services   for Veterans") == "Legal Services for Veterans"  # collapse ws
    # hyphen and source casing (acronyms) preserved — house_style does not touch them
    assert B.house_style("Cultural After-School Adventure (CASA)") == "Cultural After-School Adventure (CASA)"
    # crosswalk wins (handles dropped-word merges house_style can't); unmapped falls back to identity
    xw = {"Coalition of Theaters of Color": "Coalition Theaters of Color"}
    assert B.canonical_for("Coalition of Theaters of Color", xw) == "Coalition Theaters of Color"
    assert B.canonical_for("Brand New Initiative", xw) == "Brand New Initiative"


def test_initiative_canonical_column(tmp_path):
    """build() adds `initiative_canonical` immediately after `initiative`, and two source
    spellings of one program (& vs. and, split across years) collapse to a single canonical —
    the longitudinal-join fix. Raw `initiative` is preserved verbatim."""
    data = tmp_path / "data"
    _write(str(data / "fy17" / "schedule_c" / "fy17_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\n"
           "HEALTH,DOHMH,Reproductive & Sexual Health Services,1000\n")
    _write(str(data / "fy27" / "schedule_c" / "fy27_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\n"
           "HEALTH,DOHMH,Reproductive and Sexual Health Services,2000\n")
    xwalk = {
        "Reproductive & Sexual Health Services": "Reproductive and Sexual Health Services",
        "Reproductive and Sexual Health Services": "Reproductive and Sexual Health Services",
    }
    B.build("initiatives", B.INIT_COLS, data_dir=str(data), xwalk=xwalk)
    recs = list(csv.DictReader(open(os.path.join(str(data), "combined", "all_years_initiatives.csv"))))
    hdr = list(recs[0].keys())
    assert hdr.index("initiative_canonical") == hdr.index("initiative") + 1, hdr
    assert {r["initiative_canonical"] for r in recs} == {"Reproductive and Sexual Health Services"}
    assert {r["initiative"] for r in recs} == {
        "Reproductive & Sexual Health Services", "Reproductive and Sexual Health Services"}


def test_initiative_canonical_in_awards_rollup(tmp_path):
    """The awards roll-up gets the same derived column, positioned right after `initiative`."""
    data = tmp_path / "data"
    _write(str(data / "fy16" / "schedule_c" / "fy16_schedule_c_awards.csv"),
           AWARD_HDR + "\n"
           "CULTURE,City’s First Readers,member_item,,Org,,13-2612524,100,DCLA,\n")
    B.build("awards", B.AWARD_COLS, data_dir=str(data), xwalk={})
    recs = list(csv.DictReader(open(os.path.join(str(data), "combined", "all_years_awards.csv"))))
    hdr = list(recs[0].keys())
    assert hdr.index("initiative_canonical") == hdr.index("initiative") + 1, hdr
    assert recs[0]["initiative_canonical"] == "City's First Readers"  # curly -> straight via fallback


def test_canonical_house_style_fallback(tmp_path):
    """A raw label absent from the crosswalk is still normalized (leading *, curly apostrophe)."""
    data = tmp_path / "data"
    _write(str(data / "fy26" / "schedule_c" / "fy26_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\n"
           "HEALTH,DOHMH,*Asthma Control Program,500\n"
           "CULTURE,DCLA,City’s First Readers,600\n")
    B.build("initiatives", B.INIT_COLS, data_dir=str(data), xwalk={})
    recs = list(csv.DictReader(open(os.path.join(str(data), "combined", "all_years_initiatives.csv"))))
    m = {r["initiative"]: r["initiative_canonical"] for r in recs}
    assert m["*Asthma Control Program"] == "Asthma Control Program"
    assert m["City’s First Readers"] == "City's First Readers"


# --------------------------------------------------------------- category_canonical (DATA-ANOMALIES #18)
def test_category_canonical_for_units():
    """A split override on (category, initiative) beats a category-level rule; a category
    with no rule passes through verbatim (retired / left-as-is)."""
    cx = ({"HOUSING INITIATIVE": "Housing"},
          {("YOUTH AND COMMUNITY DEVELOPMENT", "Adult Literacy Services"): "Community Development"})
    assert B.category_canonical_for("HOUSING INITIATIVE", "anything", cx) == "Housing"          # rule
    assert B.category_canonical_for("YOUTH AND COMMUNITY DEVELOPMENT",
                                    "Adult Literacy Services", cx) == "Community Development"     # split wins
    assert B.category_canonical_for("YOUTH AND COMMUNITY DEVELOPMENT", "SYEP", cx) == \
        "YOUTH AND COMMUNITY DEVELOPMENT"                                                        # retired -> verbatim
    assert B.category_canonical_for("SANITATION", "x", cx) == "SANITATION"                       # no rule -> verbatim


def test_category_canonical_column(tmp_path):
    """build() adds `category_canonical` right after `category`; an ALL-CAPS/Title-Case pair
    collapses to one canonical while the raw `category` is preserved verbatim."""
    data = tmp_path / "data"
    _write(str(data / "fy09" / "schedule_c" / "fy09_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\nEDUCATION,DOE,Creative Arts,100\n")
    _write(str(data / "fy27" / "schedule_c" / "fy27_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\nEducation,DOE,Creative Arts,200\n")
    cat_xwalk = ({"EDUCATION": "Education"}, {})
    B.build("initiatives", B.INIT_COLS, data_dir=str(data), xwalk={}, cat_xwalk=cat_xwalk)
    recs = list(csv.DictReader(open(os.path.join(str(data), "combined", "all_years_initiatives.csv"))))
    hdr = list(recs[0].keys())
    assert hdr.index("category_canonical") == hdr.index("category") + 1, hdr
    assert {r["category_canonical"] for r in recs} == {"Education"}
    assert {r["category"] for r in recs} == {"EDUCATION", "Education"}  # raw preserved


def test_category_split_override(tmp_path):
    """Two initiatives in one compound category route to different canonicals; an unlisted
    line in the same category stays as-is (retired)."""
    data = tmp_path / "data"
    _write(str(data / "fy10" / "schedule_c" / "fy10_schedule_c_initiatives.csv"),
           "category,agencies,initiative,amount\n"
           "COMPOUND,X,Public Library Branches,500\n"
           "COMPOUND,X,Coalition of Theaters,300\n"
           "COMPOUND,X,Beacon Program,200\n")
    cat_xwalk = ({}, {("COMPOUND", "Public Library Branches"): "Libraries",
                      ("COMPOUND", "Coalition of Theaters"): "Cultural Organizations"})
    B.build("initiatives", B.INIT_COLS, data_dir=str(data), xwalk={}, cat_xwalk=cat_xwalk)
    recs = list(csv.DictReader(open(os.path.join(str(data), "combined", "all_years_initiatives.csv"))))
    m = {r["initiative"]: r["category_canonical"] for r in recs}
    assert m["Public Library Branches"] == "Libraries"
    assert m["Coalition of Theaters"] == "Cultural Organizations"
    assert m["Beacon Program"] == "COMPOUND"  # unlisted -> left as-is
