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
