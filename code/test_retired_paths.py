#!/usr/bin/env python3
"""
Tests for retired_paths.py — finding the old PDF-parser CSVs after the redone years moved to
data/retired/ (#218).

Run: pytest code/test_retired_paths.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import retired_paths as RP  # noqa: E402


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def test_family_dir_and_glob_on_a_fixture(tmp_path):
    data = tmp_path / "data"
    _touch(str(data / "fy17" / "schedule_c" / "fy17_schedule_c_awards.csv"))
    _touch(str(data / "retired" / "fy18" / "schedule_c" / "fy18_schedule_c_awards.csv"))
    _touch(str(data / "fy19" / "schedule_c" / "fy19_schedule_c_awards.csv"))
    _touch(str(data / "retired" / "fy26" / "schedule_c" / "fy26_schedule_c_awards.csv"))
    assert RP.family_dir(str(data), "fy18", "schedule_c") == str(data / "retired" / "fy18" / "schedule_c")
    assert RP.family_dir(str(data), "fy17", "schedule_c") == str(data / "fy17" / "schedule_c")
    # a year with no folder anywhere falls back to the old place (callers test existence)
    assert RP.family_dir(str(data), "fy10", "schedule_c") == str(data / "fy10" / "schedule_c")
    got = RP.family_glob(str(data), "schedule_c", "*_awards.csv")
    assert [RP.fy_of(p) for p in got] == ["fy17", "fy18", "fy19", "fy26"]


def test_current_path_maps_a_pre_move_path(tmp_path):
    _touch(str(tmp_path / "data" / "retired" / "fy18" / "terms" / "fy18_terms_and_conditions.csv"))
    _touch(str(tmp_path / "data" / "fy17" / "terms" / "fy17_terms_and_conditions.csv"))
    root = str(tmp_path)
    assert RP.current_path("data/fy18/terms/fy18_terms_and_conditions.csv", root) == \
        "data/retired/fy18/terms/fy18_terms_and_conditions.csv"
    assert RP.current_path("data/fy17/terms/fy17_terms_and_conditions.csv", root) == \
        "data/fy17/terms/fy17_terms_and_conditions.csv"
    assert RP.current_path("data/fy18/terms/missing.csv", root) == "data/fy18/terms/missing.csv"


def test_real_tree_redone_years_are_retired_and_the_rest_are_not():
    """FAILS if a family-year that data/pdf_years.csv lists as redone still has its old parse under
    data/fyNN/, or if an old parse sits under data/retired/ for a year not redone."""
    import csv
    folder = {"schedule_c": "schedule_c", "transparency": "transparency-resolutions",
              "capital_sd": "capital", "terms": "terms"}
    with open(os.path.join(REPO, "data", "pdf_years.csv"), newline="", encoding="utf-8") as f:
        redone = {(f"fy{int(r['fiscal_year']) % 100:02d}", folder[r["family"]]) for r in csv.DictReader(f)}
    data = os.path.join(REPO, "data")
    for yy, fam in redone:
        assert not os.path.isdir(os.path.join(data, yy, fam)), f"data/{yy}/{fam} is redone but not retired"
    retired = {(yy, fam) for yy in os.listdir(os.path.join(data, "retired")) if yy.startswith("fy")
               for fam in os.listdir(os.path.join(data, "retired", yy))}
    assert retired <= redone, sorted(retired - redone)
    assert len(retired) == 33, sorted(retired)
