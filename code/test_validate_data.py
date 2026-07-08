#!/usr/bin/env python3
"""
Tests for validate_data.py — the reusable row-level data-QA validator.

Runs the validator against tiny synthetic fixtures (no PDFs needed): one clean tree that must
produce zero HARD findings, and one deliberately broken tree that must produce a HARD finding for
each gated failure class (schema, malformed row, non-numeric amount, malformed EIN). Also unit-tests
the amount parser, the transparency sign rule, duplicate detection, the prior-year embedding
allowance, and the reconciliation roll-up parser.

Run: pytest code/test_validate_data.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import validate_data as V  # noqa: E402


AWARD_HDR = "category,initiative,award_type,member,organization,program,ein,amount,agency,purpose"


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _clean_award_file(path):
    _write(path, AWARD_HDR + "\n"
           "EDUCATION,Init A,initiative_provider,,Acme Org Inc.,,13-2612524,50000,DOE,\n"
           "EDUCATION,Init A,member_item,Rivera,Beta Org,,20-5620848,25000,DOE,to support\n")


# ---------------------------------------------------------------- clean tree -> no hard findings
def test_clean_tree_exits_zero(tmp_path):
    root = tmp_path / "data"
    _clean_award_file(str(root / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"))
    results, recon, surnames = V.validate_tree(str(root))
    hard = sum(len(r.hard) for r in results)
    assert hard == 0, [f for r in results for f in r.hard]
    # EIN coverage computed
    (r,) = results
    assert r.ein_valid == 2 and r.nrows == 2 and r.coverage() == 100.0


# ---------------------------------------------------------------- broken tree -> a hard per class
def test_broken_tree_flags_each_hard_class(tmp_path):
    root = tmp_path / "data"
    # missing 'purpose' column (schema), a non-numeric amount, and a short EIN
    _write(str(root / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"),
           "category,initiative,award_type,member,organization,program,ein,amount,agency\n"
           "EDUCATION,Init,initiative_provider,,Org,,12-34,NOTANUMBER,DOE\n")
    results, _recon, _s = V.validate_tree(str(root))
    (r,) = results
    kinds = {c for c, _m in r.hard}
    assert "schema" in kinds      # missing 'purpose'
    assert "ein" in kinds         # 12-34 is not 9 digits
    assert "amount" in kinds      # NOTANUMBER
    assert len(r.hard) >= 3


def test_malformed_row_field_count(tmp_path):
    root = tmp_path / "data"
    # second data row has too few fields
    _write(str(root / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"),
           AWARD_HDR + "\n"
           "EDUCATION,Init,initiative_provider,,Org,,13-2612524,50000,DOE,\n"
           "EDUCATION,Init,initiative_provider,,Org\n")
    (r,) = V.validate_tree(str(root))[0]
    assert any(c == "schema" and "field count" in m for c, m in r.hard)


# ---------------------------------------------------------------- targeted checks
def test_duplicate_detection(tmp_path):
    root = tmp_path / "data"
    row = "EDUCATION,Init,initiative_provider,,Org,,13-2612524,50000,DOE,\n"
    _write(str(root / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"),
           AWARD_HDR + "\n" + row + row)  # identical row twice
    (r,) = V.validate_tree(str(root))[0]
    assert r.dupes == 1
    assert any(c == "duplicate" for c, _m in r.soft)


def test_transparency_sign_rule():
    surnames = set()
    hdr = ("resolution,date,chart,fiscal_year,action,source,council_member,organization,program,"
           "ein,amount,agency,agy_num,ua,purpose,flags")
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "fy26", "transparency-resolutions", "fy26_transparency_all.csv")
    os.makedirs(os.path.dirname(p))
    _write(p, hdr + "\n"
           # designate with a negative amount is wrong; rescind positive is wrong; purpose_change ok
           "1,2025-06-01,A,2026,designate,src,Rivera,Org A,,13-2612524,-100,DOE,1,UA,,\n"
           "2,2025-06-01,A,2026,rescind,src,Rivera,Org B,,20-5620848,500,DOE,1,UA,,\n"
           "3,2025-06-01,A,2026,purpose_change,src,Rivera,Org C,,13-5562301,-300,DOE,1,UA,,\n")
    r = V.check_file(p, surnames)
    sign_msgs = [m for c, m in r.soft if c == "amount"]
    assert any("designate" in m for m in sign_msgs)
    assert any("rescind" in m for m in sign_msgs)
    # purpose_change negative must NOT be flagged
    assert not any("purpose_change" in m for m in sign_msgs)


def test_transparency_prior_year_not_flagged():
    """A fiscal_year below the folder year is expected (a resolution amends prior designations)."""
    surnames = set()
    hdr = ("resolution,date,chart,fiscal_year,action,source,council_member,organization,program,"
           "ein,amount,agency,agy_num,ua,purpose,flags")
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "fy26", "transparency-resolutions", "fy26_transparency_all.csv")
    os.makedirs(os.path.dirname(p))
    _write(p, hdr + "\n"
           "1,2025-06-01,A,2024,designate,src,Rivera,Org,,13-2612524,100,DOE,1,UA,,\n")   # FY2024 in FY26
    r = V.check_file(p, surnames)
    assert not any(c == "fiscal_year" and "implausible" in m for c, m in r.soft)
    assert any(c == "fiscal_year" and "EXPECTED" in m for c, m in r.soft)


def test_column_bleed_heuristic():
    surnames = {"brewer"}
    hdr = ("resolution,date,chart,fiscal_year,action,source,council_member,organization,program,"
           "ein,amount,agency,agy_num,ua,purpose,flags")
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "fy10", "transparency-resolutions", "fy10_transparency_all.csv")
    os.makedirs(os.path.dirname(p))
    _write(p, hdr + "\n"
           "1,2009,A,2010,designate,src,,Brewer ParentsofPublicSchool9 Inc.,,13-2612524,100,DOE,1,UA,,\n"
           "2,2009,A,2010,designate,src,,Legit Org Inc.,,20-5620848,100,DOE,1,UA,,\n")
    r = V.check_file(p, surnames)
    assert r.bleed == 1


def test_parse_amount():
    assert V.parse_amount("$1,499,254")[0] == 1499254
    assert V.parse_amount("$ 100,000")[0] == 100000
    assert V.parse_amount("")[0] is None and V.parse_amount("")[1] is True
    assert V.parse_amount("NaNaN")[1] is False


def test_reconciliation_rollup(tmp_path):
    root = tmp_path / "data"
    _write(str(root / "fy15" / "schedule_c" / "fy15_schedule_c_reconciliation.txt"),
           "SCHEDULE C RECONCILIATION (fy15)\n"
           "GRAND TOTAL ... 24/24 reconcilable categories exact\n")
    _write(str(root / "fy24" / "capital" / "fy24_capital_reconciliation.txt"),
           "CAPITAL RECON\n30/30 agency subtotals reconcile (amount + project count)\n")
    _write(str(root / "fy26" / "transparency-resolutions" / "fy26_transparency_reconciliation.txt"),
           "RECONCILIATION STATUS: NOT RECONCILABLE (against printed totals).\n")
    recon = V.parse_reconciliations(str(root))
    d = {(y, dt): (ratio, status) for y, dt, ratio, status in recon}
    assert d[(2015, "schedule_c")] == ("24/24", "PASS")
    assert d[(2024, "capital")] == ("30/30", "PASS")
    assert d[(2026, "transparency")][0] == "—"


def test_detect_type_and_skips():
    assert V.detect_type("data/fy20/schedule_c/fy20_schedule_c_awards.csv") == "schedule_c_awards"
    assert V.detect_type("data/fy20/capital/fy20_capital_projects.csv") == "capital"
    assert V.detect_type("data/combined/legistar_crosswalk.csv") is None  # skipped


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
