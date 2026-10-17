"""Tests for audit_capital.py: each question must fail on a constructed defect and pass on the
committed data. Each test names the outcome that would make it fail."""
import copy
import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
pytest.importorskip("openpyxl")
import audit_capital as A


@pytest.fixture(scope="module")
def ctx():
    return A.load()


def _row(**kw):
    r = {"report_year": "2027", "amount_fy": "2027", "project_id": "CC1", "borough": "M",
         "budget_line": "P D018", "budget_line_norm": "P D018", "council_district": "01",
         "sponsor": "S", "title": "T", "description": "D", "amount": "100",
         "source_kind": "council_workbook", "source_file": "wb.xlsx", "source_row": "2",
         "row_flag": ""}
    r.update(kw)
    return r


def _reader(recs, textless=()):
    return lambda path, fy: (recs, list(textless))


WB = {2: {"project_id": "CC1", "borough": "M", "budget_line": "P D018",
          "council_district": "01", "sponsor": "S", "title": "T", "description": "D",
          "amounts": {2027: Decimal(100), 2028: Decimal(0)}}}


def test_k1_catches_an_edited_cell_a_lost_record_and_a_wrong_amount():
    """FAILS if a table equal to the workbook is reported, or if an edited title, a workbook
    record missing from the table, or an amount moved to another year passes."""
    ok = {"table": [_row()], "reader": _reader(WB)}
    assert A.q_workbook_cells(ok)["status"] == "pass"
    for table, recs in (([_row(title="X")], WB), ([_row()], {**WB, 3: WB[2]}),
                        ([_row(amount_fy="2028")], WB)):
        assert A.q_workbook_cells({"table": table, "reader": _reader(recs)})["count"] >= 1


def test_k2_catches_a_totals_row_that_does_not_add_up():
    """FAILS if a totals row equal to the table's sums is reported, or one that differs (a row
    dropped or doubled) passes, or a text-less row in a year other than FY2015/16 passes."""
    t = [_row(report_year="2015", amount_fy="2015", amount="100")]
    assert A.q_totals_rows({"table": t, "reader": _reader(WB, [{2015: Decimal(100)}])})["status"] == "pass"
    assert A.q_totals_rows({"table": t, "reader": _reader(WB, [{2015: Decimal(101)}])})["count"] == 1
    assert A.q_totals_rows({"table": [_row()], "reader": _reader(WB, [{2027: Decimal(100)}])})["count"] >= 1


def test_k3_catches_a_dropped_t474_row_and_an_unflagged_blank(ctx):
    """FAILS if the committed table is reported, or a table missing one t474 row, or a raw
    split record whose blank-amount row is not the table's, passes."""
    assert A.q_t474(ctx)["status"] == "pass"
    t = [r for r in ctx["table"]]
    first = next(i for i, r in enumerate(t) if r["source_kind"] == "open_data_t474" and r["amount"])
    assert A.q_t474({"table": t[:first] + t[first + 1:]})["count"] >= 1
    blank = next(i for i, r in enumerate(t) if r["source_kind"] == "open_data_t474" and not r["amount"])
    t2 = copy.deepcopy(t)
    t2[blank]["amount"], t2[blank]["amount_fy"] = "0", t2[blank]["report_year"]
    assert A.q_t474({"table": t2})["count"] >= 1
    t3 = copy.deepcopy(t)
    t3[blank]["source_row"] = "row-not-the-split-record"
    assert A.q_t474({"table": t3})["count"] == 1


def test_k4_catches_a_wrong_verdict_and_a_wrong_release(ctx):
    """FAILS if the committed reconciliation is reported, or if one flipped verdict passes, or
    if the Council side changes on a line that matched."""
    assert A.q_recon(ctx)["status"] == "pass"
    rec = copy.deepcopy(ctx["recon"])
    i = next(i for i, r in enumerate(rec) if r["verdict"] == "match")
    rec[i]["verdict"] = "differ"
    assert A.q_recon({"table": ctx["table"], "recon": rec})["count"] >= 1
    t = copy.deepcopy(ctx["table"])
    j = next(i for i, r in enumerate(t) if r["report_year"] == "2027" and r["budget_line_norm"] == "HO D003")
    t[j]["amount"] = str(int(t[j]["amount"]) + 1)
    assert A.q_recon({"table": t, "recon": ctx["recon"]})["count"] >= 1


def test_k5_catches_a_mis_spelled_line_and_cents():
    """FAILS if 'P  D018' -> 'P D018' is reported, or a normal form that drops the space, or a
    fractional amount, passes."""
    assert A.q_lines({"table": [_row(budget_line="P  D018")]})["status"] == "pass"
    assert A.q_lines({"table": [_row(budget_line_norm="PD018")]})["count"] == 1
    assert A.q_lines({"table": [_row(amount="100.5")]})["count"] == 1


def test_committed_report_is_current(ctx):
    """FAILS if data/capital/CAPITAL-AUDIT.md is not what the audit produces today."""
    with open(A.REPORT, encoding="utf-8") as f:
        assert A.report_text(A.run(ctx)) == f.read()
