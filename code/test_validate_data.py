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
    assert V.detect_type("data/combined/all_years_awards.csv") == "combined_awards"
    assert V.detect_type("data/combined/all_years_initiatives.csv") == "combined_initiatives"


# --------------------------------------------------- combined-schema drift guard (canonical cols)
# build_combined.py inserts `category_canonical` / `initiative_canonical` right after their raw
# source columns. These are the EXACT committed headers of data/combined/*.csv. The validator specs
# must include them, or the schema check flags them as "unexpected columns" -> HARD failure (the
# code/schema drift this test exists to catch). Mirrors build_combined.py's insertion order.
COMBINED_AWARDS_HDR = ("year,category,category_canonical,initiative,initiative_canonical,"
                       "award_type,member,organization,program,ein,amount,agency,purpose")
COMBINED_INITIATIVES_HDR = ("year,category,category_canonical,agencies,initiative,"
                            "initiative_canonical,amount")


def test_combined_files_validate_clean_with_canonical_columns(tmp_path):
    root = tmp_path / "data"
    _write(str(root / "combined" / "all_years_awards.csv"),
           COMBINED_AWARDS_HDR + "\n"
           "2020,EDUCATION,Education,Init A,Init A,initiative_provider,,Acme Org Inc.,,"
           "13-2612524,50000,DOE,\n")
    _write(str(root / "combined" / "all_years_initiatives.csv"),
           COMBINED_INITIATIVES_HDR + "\n"
           "2020,EDUCATION,Education,DOE,Init A,Init A,50000\n")
    results, _recon, _s = V.validate_tree(str(root))
    by_type = {V.detect_type(r.path): r for r in results}
    assert set(by_type) == {"combined_awards", "combined_initiatives"}
    for kind, r in by_type.items():
        schema_hard = [m for c, m in r.hard if c == "schema"]
        assert schema_hard == [], f"{kind} schema findings: {schema_hard}"
        assert r.hard == [], f"{kind} hard findings: {r.hard}"


def test_combined_specs_require_canonical_columns():
    """Negative control: dropping a canonical column MUST trip the schema check, proving the specs
    now depend on them (guards against the columns being silently removed from the spec again)."""
    for kind in ("combined_awards", "combined_initiatives"):
        cols = set(V.TYPES[kind]["cols"])
        assert "category_canonical" in cols, kind
        assert "initiative_canonical" in cols, kind


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))


# ------------------------------------------------- org_merged: lost row boundary (DATA-ANOMALIES §20)
def test_org_merged_flags_absorbed_award_row(tmp_path):
    """An EIN inside `organization` means a following award was absorbed into this row, so the
    row's `amount` may belong to a different org than the one named. Real FY2017 shape."""
    root = tmp_path / "data"
    _write(str(root / "fy17" / "schedule_c" / "fy17_schedule_c_awards.csv"), AWARD_HDR + "\n"
           "LEGAL SERVICES,Init A,initiative_provider,,"
           "Bronx Defenders 13-3931074 * $2076667 Brooklyn Defenders Services,,"
           "11-3305406,2076666,MOCJ,\n")
    results, _, _ = V.validate_tree(str(root))
    (r,) = results
    assert not r.hard, "must stay SOFT — the row is real data, not a build breaker"
    assert any(k == "org_merged" for k, _ in r.soft), [k for k, _ in r.soft]


def test_org_merged_flags_purpose_prose_in_org(tmp_path):
    """FY2024-FY2026 variant: purpose prose lands in `organization`, detected by the `$`."""
    root = tmp_path / "data"
    _write(str(root / "fy25" / "schedule_c" / "fy25_schedule_c_awards.csv"), AWARD_HDR + "\n"
           "FOOD,Init A,initiative_provider,,"
           "The funds requested will subsidize farm shares to $12 per share,,"
           "11-2880221,50000,DOHMH,\n")
    results, _, _ = V.validate_tree(str(root))
    (r,) = results
    assert any(k == "org_merged" for k, _ in r.soft), [k for k, _ in r.soft]


def test_org_merged_does_not_fire_on_clean_rows(tmp_path):
    """Zero false positives on well-formed organization names — the whole basis for shipping it."""
    root = tmp_path / "data"
    _clean_award_file(str(root / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"))
    results, _, _ = V.validate_tree(str(root))
    (r,) = results
    assert not any(k == "org_merged" for k, _ in r.soft), [k for k, _ in r.soft]


# ============================================================ check 8: initiative reconciliation
# The award stream's first pass/fail target. Award rows summed per initiative must equal that
# initiative's PRINTED amount in *_schedule_c_initiatives.csv. See validate_data.py's
# `initiative_reconciliation` and research/missing-absorbed-awards/RECONCILIATION.md.

INIT_HDR = "category,agencies,initiative,amount"
SIDECAR_HDR = ("fiscal_year,category,initiative,award_type,member,organization,program,ein,amount,"
               "agency,purpose,confidence,name_source,absorbed_from_file,absorbed_from_line,"
               "absorbed_from_ein,disclosure_confirmed")


def _year_tree(root, fy, initiatives, awards, sidecar=None):
    """Write one fiscal year's initiatives + awards (and optionally the recovered sidecar).
    `initiatives` / `awards` / `sidecar` are lists of CSV body lines."""
    d = str(root / f"fy{fy}" / "schedule_c")
    _write(os.path.join(d, f"fy{fy}_schedule_c_initiatives.csv"),
           INIT_HDR + "\n" + "".join(x + "\n" for x in initiatives))
    _write(os.path.join(d, f"fy{fy}_schedule_c_awards.csv"),
           AWARD_HDR + "\n" + "".join(x + "\n" for x in awards))
    if sidecar is not None:
        _write(str(root / "recovered" / "schedule_c_absorbed_awards.csv"),
               SIDECAR_HDR + "\n" + "".join(x + "\n" for x in sidecar))


def _by_initiative(year_rec):
    return {r["initiative"]: r for r in year_rec["rows"]}


def test_canon_initiative_folds_punctuation_and_case():
    """The summary table and the body headers punctuate the same initiative differently."""
    assert (V.canon_initiative("Alternatives to Incarceration (ATI’s)")
            == V.canon_initiative("Alternatives to Incarceration (ATI's)"))
    assert V.canon_initiative("City’s First Readers") == V.canon_initiative("Citys First Readers")
    assert V.canon_initiative("Crisis Management System – Bronx") == "crisismanagementsystembronx"
    assert V.canon_initiative("") == "" and V.canon_initiative(None) == ""
    # distinct initiatives must NOT collide
    assert V.canon_initiative("Cancer Services") != V.canon_initiative("Cancer Prevention")


def test_initiative_recon_balanced_short_and_over(tmp_path):
    root = tmp_path / "data"
    _year_tree(root, "20",
               ["HEALTH,,Exact Init,100000",
                "HEALTH,,Short Init,100000",
                "HEALTH,,Over Init,100000"],
               ["HEALTH,Exact Init,initiative_provider,,Org A,,13-2612524,60000,DOE,",
                "HEALTH,Exact Init,initiative_provider,,Org B,,20-5620848,40000,DOE,",
                "HEALTH,Short Init,initiative_provider,,Org C,,13-2612524,75000,DOE,",
                "HEALTH,Over Init,initiative_provider,,Org D,,13-2612524,130000,DOE,"])
    years, present = V.initiative_reconciliation(str(root))
    assert present is False, "no sidecar was written"
    (y,) = years
    assert y["year"] == 2020
    assert (y["balanced"], y["short"], y["over"]) == (1, 1, 1)
    rows = _by_initiative(y)
    assert rows["Exact Init"]["status"] == "balanced"
    assert rows["Exact Init"]["residual"] == 0
    assert rows["Exact Init"]["n_awards"] == 2
    assert rows["Short Init"]["status"] == "short"
    assert rows["Short Init"]["residual"] == 25_000 * 100      # cents
    assert rows["Over Init"]["status"] == "over"
    assert rows["Over Init"]["residual"] == -30_000 * 100


def test_initiative_recon_joins_across_punctuation_drift(tmp_path):
    """Real corpus shape: the summary prints a curly apostrophe, the body header a straight one.
    Without folding, the initiative would show as unjoined and its printed target would be lost."""
    root = tmp_path / "data"
    _year_tree(root, "18",
               ["EDU,,City’s First Readers,50000"],
               ["EDU,City's First Readers,initiative_provider,,Org A,,13-2612524,50000,DOE,"])
    (y,), _ = V.initiative_reconciliation(str(root))
    assert len(y["rows"]) == 1 and y["balanced"] == 1
    assert y["unjoined_labels"] == 0


def test_initiative_recon_refuses_prefix_join(tmp_path):
    """FY2018 has six `Crisis Management System - <sub-program>` award labels whose parent is one
    initiative line. A prefix/fuzzy join would pool them and manufacture a fake balance, so the
    join is EXACT: the sub-programs stay unjoined and the parent stays untested."""
    root = tmp_path / "data"
    _year_tree(root, "18",
               ["PUBLIC SAFETY,,Crisis Management System,300000"],
               ["PUBLIC SAFETY,Crisis Management System - Bronx,initiative_provider,,"
                "Org A,,13-2612524,100000,MOCJ,",
                "PUBLIC SAFETY,Crisis Management System - Queens,initiative_provider,,"
                "Org B,,20-5620848,200000,MOCJ,"])
    (y,), _ = V.initiative_reconciliation(str(root))
    assert y["rows"] == [], "no award label matches the parent initiative exactly"
    assert y["balanced"] == 0
    assert y["unjoined_labels"] == 2
    assert y["unjoined_amount"] == 300_000 * 100


def test_initiative_recon_counts_unlabeled_and_unjoined_dollars(tmp_path):
    """Award rows with no initiative label, and labels with no printed counterpart, are carried
    out as explicit tallies. Dropping them silently would make coverage look far better than it is
    ($172M of FY2026 award dollars sit on rows with no initiative label)."""
    root = tmp_path / "data"
    _year_tree(root, "26",
               ["HEALTH,,Known Init,100000"],
               ["HEALTH,Known Init,initiative_provider,,Org A,,13-2612524,100000,DOE,",
                "HEALTH,Ghost Init,initiative_provider,,Org B,,20-5620848,70000,DOE,",
                "HEALTH,,member_item,Rivera,Org C,,13-5562301,5000,DOE,"])
    (y,), _ = V.initiative_reconciliation(str(root))
    assert y["balanced"] == 1
    assert (y["unjoined_labels"], y["unjoined_amount"]) == (1, 70_000 * 100)
    assert (y["unlabeled_rows"], y["unlabeled_amount"]) == (1, 5_000 * 100)


def test_initiative_recon_sidecar_is_optional_and_closes_the_gap(tmp_path):
    """The recovered sidecar is an optional inclusion: absent, the `after` figures equal the base
    ones; present, they show the same gap with the recovered awards added. This is the FY2017
    Discretionary Child Care shape — visible rows short by exactly the absorbed total."""
    root = tmp_path / "data"
    inits = ["CHILDREN,,Discretionary Child Care,100000"]
    awards = ["CHILDREN,Discretionary Child Care,initiative_provider,,Org A,,13-2612524,60000,ACS,"]
    _year_tree(root, "17", inits, awards)                      # no sidecar yet
    (y,), present = V.initiative_reconciliation(str(root))
    assert present is False
    assert y["recovered"] == 0
    assert _by_initiative(y)["Discretionary Child Care"]["residual_after"] == 40_000 * 100
    assert y["balanced_after"] == 0

    _year_tree(root, "17", inits, awards, sidecar=[
        "2017,CHILDREN,Discretionary Child Care,initiative_provider,,Org B,,20-5620848,40000,ACS,"
        ",high,council_disclosure,data/fy17/schedule_c/fy17_schedule_c_awards.csv,2,132612524,yes"])
    (y,), present = V.initiative_reconciliation(str(root))
    assert present is True
    r = _by_initiative(y)["Discretionary Child Care"]
    assert r["status"] == "short" and r["residual"] == 40_000 * 100, "base figures must not move"
    assert r["recovered"] == 40_000 * 100
    assert r["residual_after"] == 0
    assert y["balanced"] == 0 and y["balanced_after"] == 1


def test_initiative_recon_sidecar_unjoinable_rows_are_not_attributed(tmp_path):
    """A recovered award whose initiative is blank or unmatched must be reported as unjoinable,
    never folded into some plausible initiative. 80 of the 443 sidecar rows carry a blank label."""
    root = tmp_path / "data"
    _year_tree(root, "17",
               ["CHILDREN,,Known Init,100000"],
               ["CHILDREN,Known Init,initiative_provider,,Org A,,13-2612524,60000,ACS,"],
               sidecar=["2017,CHILDREN,,initiative_provider,,Org B,,20-5620848,40000,ACS,"
                        ",low,absorbed_text,data/fy17/schedule_c/fy17_schedule_c_awards.csv,2,"
                        "132612524,no"])
    (y,), _ = V.initiative_reconciliation(str(root))
    assert _by_initiative(y)["Known Init"]["recovered"] == 0
    assert _by_initiative(y)["Known Init"]["residual_after"] == 40_000 * 100
    assert y["recovered_unjoined"] == 40_000 * 100


def test_initiative_recon_sums_duplicate_printed_labels(tmp_path):
    """One initiative printed on two summary lines (different agencies) is one join target: its
    printed amounts sum. Occurs in FY2019-FY2025."""
    root = tmp_path / "data"
    _year_tree(root, "23",
               ["YOUTH,DYCD,Beacon Programs,60000",
                "YOUTH,DOE,Beacon Programs,40000"],
               ["YOUTH,Beacon Programs,initiative_provider,,Org A,,13-2612524,100000,DYCD,"])
    (y,), _ = V.initiative_reconciliation(str(root))
    assert _by_initiative(y)["Beacon Programs"]["printed"] == 100_000 * 100
    assert y["balanced"] == 1


def test_initiative_recon_skips_years_with_no_award_file(tmp_path):
    """FY2009-FY2014 are initiatives-only by nature — no award rows exist to reconcile."""
    root = tmp_path / "data"
    _write(str(root / "fy12" / "schedule_c" / "fy12_schedule_c_initiatives.csv"),
           INIT_HDR + "\nHEALTH,,Init A,100000\n")
    years, _ = V.initiative_reconciliation(str(root))
    assert years == []


def test_initiative_recon_is_soft_never_a_hard_failure(tmp_path):
    """A wildly unbalanced year must not gate the build: this data has known structural gaps and
    the check exists to surface them, not to break on them."""
    root = tmp_path / "data"
    _year_tree(root, "20",
               ["HEALTH,,Init A,9000000"],
               ["HEALTH,Init A,initiative_provider,,Org A,,13-2612524,1000,DOE,"])
    results, _recon, _s = V.validate_tree(str(root))
    assert sum(len(r.hard) for r in results) == 0, [f for r in results for f in r.hard]
    (y,), _ = V.initiative_reconciliation(str(root))
    assert y["short"] == 1 and y["rows"][0]["residual"] == 8_999_000 * 100


def test_initiative_recon_section_renders_without_a_sidecar(tmp_path):
    """The markdown section must say the sidecar is absent rather than implying the `after`
    columns mean something they do not."""
    root = tmp_path / "data"
    _year_tree(root, "20", ["HEALTH,,Init A,100000"],
               ["HEALTH,Init A,initiative_provider,,Org A,,13-2612524,75000,DOE,"])
    md = "\n".join(V._initiative_recon_section(*V.initiative_reconciliation(str(root))))
    assert "**It is absent" in md
    assert "| FY2020 |" in md
    assert "Initiatives that do not balance (1)" in md
    assert "25,000" in md


# --------------------------------------------------------------- --dry-run must write NOTHING
def test_dry_run_writes_no_file(tmp_path):
    """Hard rule: a dry run touches nothing. Guarded here because the report path defaults to
    inside the data tree, so a regression would silently overwrite a committed artifact."""
    import subprocess
    import sys as _sys
    root = tmp_path / "data"
    _year_tree(root, "20", ["HEALTH,,Init A,100000"],
               ["HEALTH,Init A,initiative_provider,,Org A,,13-2612524,75000,DOE,"])
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    proc = subprocess.run(
        [_sys.executable, os.path.join(HERE, "validate_data.py"),
         "--data-dir", str(root), "--dry-run"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "Initiative-level award reconciliation" in proc.stdout
    assert "WROTE" not in proc.stdout
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before
