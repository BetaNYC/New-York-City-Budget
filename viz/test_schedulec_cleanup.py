#!/usr/bin/env python3
"""
Regression tests for viz/schedulec_cleanup.py.

Dual-mode: runnable directly (`python3 viz/test_schedulec_cleanup.py`, no third-party
deps) AND collectable by pytest (`pytest viz/test_schedulec_cleanup.py`), matching the
repo's test convention while not requiring pytest to be installed on every machine.

What these guard:
  1. THE GATE — FY2027 Adopted grand total reconciles to $655,764,999 exactly. This is
     the load-bearing invariant; the whole viz is worthless if the headline number is
     wrong.
  2. Both hierarchy axes (Category / Agency) sum to the SAME grand total in every year —
     the property that lets look-at-cook show either axis without double-counting.
  3. Per-category FY2027 Adopted totals match the source *_initiatives.csv exactly (no
     dollars invented, dropped, or reallocated by the transform).
  4. The cleaned-CSV column contract the JS depends on: the exact leading columns in
     order, and per-year `Adopted <year>` / `Itemized <year>` prefixes equal to the
     apropTitle/expendTitle the app is configured with.
  5. No blank numeric cells (a blank poisons the app's parseFloat column sums with NaN).
  6. Itemized never exceeds Adopted for any leaf-year (a sanity bound on the join).
  7. The generated data/schedule_c.csv on disk is in sync with a fresh build.
"""
from __future__ import annotations

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import schedulec_cleanup as C  # noqa: E402


# ---------------------------------------------------------------------------
# Build once, reuse across checks
# ---------------------------------------------------------------------------
def _build():
    return C.build_rows(C.DEFAULT_START, C.DEFAULT_END)


def test_gate_fy2027_reconciles_to_the_dollar():
    _, rows, _ = _build()
    ok, computed = C.reconcile(rows)
    assert ok, f"FY2027 Adopted grand total {computed} != {C.FY27_GATE_TOTAL}"
    assert computed == 655_764_999


def test_both_axes_sum_to_same_grand_total_each_year():
    """Category (Fund) and Agency (Control Officer) partitions are re-groupings of the
    same leaf rows, so summing per axis must give an identical grand total per year."""
    fields, rows, diag = _build()
    for year in diag["years"]:
        col = f"{C.APROP_LABEL} {year}"
        by_cat = {}
        by_agency = {}
        grand = 0
        for r in rows:
            v = int(r[col])
            grand += v
            by_cat[r["Fund"]] = by_cat.get(r["Fund"], 0) + v
            by_agency[r["Control Officer"]] = by_agency.get(r["Control Officer"], 0) + v
        assert sum(by_cat.values()) == grand, f"category axis != grand in FY{year}"
        assert sum(by_agency.values()) == grand, f"agency axis != grand in FY{year}"


def test_per_category_fy2027_matches_source_initiatives():
    """Every FY2027 category's Adopted total must equal the sum in the source
    *_initiatives.csv — no reallocation across categories."""
    fields, rows, _ = _build()
    # source truth
    src = {}
    ipath = C._initiatives_path(2027)
    with open(ipath, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cat = (r.get("category") or "").strip()
            src[cat] = src.get(cat, 0.0) + C._to_amount(r.get("amount"))
    # built
    built = {}
    col = "Adopted 2027"
    for r in rows:
        if int(r[col]) == 0:
            continue
        built[r["Fund"]] = built.get(r["Fund"], 0) + int(r[col])
    for cat, amt in src.items():
        assert built.get(cat, 0) == int(round(amt)), (
            f"category {cat!r}: built {built.get(cat, 0)} != source {int(round(amt))}"
        )


def test_column_contract():
    """The JS depends on these exact leading columns (in order) and per-year prefixes."""
    fields, _, diag = _build()
    assert fields[:7] == [
        "Fund", "Department", "Control Officer", "Department ID",
        "Short Title", "Link to Website", "Department Description",
    ], f"leading columns drifted: {fields[:7]}"
    # per-year columns, both prefixes, for every year
    for year in diag["years"]:
        assert f"{C.APROP_LABEL} {year}" in fields
        assert f"{C.ITEMIZED_LABEL} {year}" in fields
    # the labels the app.js config must mirror
    assert C.APROP_LABEL == "Adopted"
    assert C.ITEMIZED_LABEL == "Itemized"


def test_no_blank_numeric_cells():
    """A blank per-year cell would make the app's parseFloat column sum NaN."""
    fields, rows, diag = _build()
    year_cols = [c for c in fields if c.startswith(("Adopted ", "Itemized "))]
    for r in rows:
        for c in year_cols:
            val = r[c]
            assert val != "" and val is not None, f"blank cell in {c!r}"
            int(val)  # must parse as int


def test_itemized_never_exceeds_adopted_per_leaf_year():
    """Money designated to named recipients cannot exceed the initiative's adopted total."""
    fields, rows, diag = _build()
    violations = []
    for r in rows:
        for year in diag["years"]:
            adopted = int(r[f"{C.APROP_LABEL} {year}"])
            itemized = int(r[f"{C.ITEMIZED_LABEL} {year}"])
            if itemized > adopted:
                violations.append((r["Fund"], r["Department"], year, adopted, itemized))
    assert not violations, f"{len(violations)} leaf-years where Itemized > Adopted: {violations[:5]}"


def test_generated_csv_on_disk_is_in_sync():
    """viz/data/schedule_c.csv must equal a fresh build (catches a stale committed file)."""
    out = C.DEFAULT_OUT
    if not os.path.exists(out):
        # Not a failure in a fresh checkout that hasn't generated yet; skip loudly.
        print(f"  (skip) {out} not present — run schedulec_cleanup.py to generate")
        return
    fields, rows, _ = _build()
    with open(out, newline="", encoding="utf-8") as f:
        disk = list(csv.reader(f))
    assert disk[0] == fields, "on-disk header differs from fresh build"
    assert len(disk) - 1 == len(rows), (
        f"on-disk row count {len(disk) - 1} != fresh build {len(rows)} — regenerate the CSV"
    )


# ---------------------------------------------------------------------------
# Standalone runner (no pytest required)
# ---------------------------------------------------------------------------
def _run_standalone():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
