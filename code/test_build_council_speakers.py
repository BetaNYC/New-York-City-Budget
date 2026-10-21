"""Tests for code/build_council_speakers.py (DESIGN-NOTES item 3 groundwork). Each test names the
outcome that would make it fail."""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_council_speakers as S  # noqa: E402


def test_committed_table_equals_regeneration():
    """FAILS if data/reference/council_speakers.csv drifted from its records (run --write)."""
    assert open(os.path.join(S.ROOT, S.OUT), encoding="utf-8").read() == S.build()


def test_only_recorded_speakers_with_one_member_id_each():
    """FAILS if a Speaker appears with no printed record, or a person maps to two member ids."""
    rows = list(csv.DictReader(io.StringIO(S.build())))
    assert [r["person"] for r in rows] == ["Christine C. Quinn", "Melissa Mark-Viverito",
                                           "Corey D. Johnson", "Adrienne E. Adams"]
    assert all(r["council_member_id"].isdigit() and ".pdf p." in r["source"] for r in rows)
    named = {int(y) for r in rows for y in r["fiscal_years_named"].split(";")}
    assert not named & set(S.NOT_RECORDED)
