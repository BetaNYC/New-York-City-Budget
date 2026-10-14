"""Tests for build_capital_council.py (#89 A6, A7, B8-B10). Synthetic workbooks and rows for the
rules; the committed sources for the pins. Each test names the outcome that would make it fail."""
import collections
import os
import sys
from decimal import Decimal

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_capital_council as C
from test_parse_expense_disclosure import _xlsx


@pytest.mark.parametrize("raw,pt,want", [
    ("P  D018", None, "P D018"), ("P-D018", None, "P D018"), ("P D018", None, "P D018"),
    ("PVDN132", "PV", "PV DN132"), ("P  1018", "P", "P 1018"), ("AG DN04L", None, "AG DN04L"),
    ("", None, ""), ("150000", None, ""), ("ERROR: #NAME?", None, ""),
])
def test_budget_line_normal_form(raw, pt, want):
    """FAILS if any spelling of a line ('P  D018', 'P-D018', OMB's spaceless 'PVDN132') does not
    reach one normal form, or a non-line value (an amount spilled into the column) gets one."""
    assert C.norm_line(raw, pt) == want


def test_council_series_is_the_d_lines():
    """FAILS if a non-Council line (OMB's 'P 1018', 'ED 0404') counts as Council series."""
    assert C.is_council_line("P D018") and C.is_council_line("PV DN132")
    assert not C.is_council_line("P 1018") and not C.is_council_line("ED 0404")
    assert not C.is_council_line("")


HDR17 = ["PROJECT", "POLBORO", "Budget Line", "DISTRICTS", "SPONSORS", "TITLE", "DESC",
         "FY17", "FY18"]


def _wb(tmp_path, rows, monkeypatch, header=HDR17, name="Capital-Database-FY17.xlsx"):
    p = _xlsx(tmp_path / name, [header] + rows, sheet="S")
    monkeypatch.setattr(C, "checked", lambda rel: rel)
    return str(p)


def test_totals_row_is_stripped_only_when_it_is_the_totals(tmp_path, monkeypatch):
    """B10. FAILS if a trailing row with no text whose amounts equal the column sums is counted,
    or if a text-less row that is NOT the totals is silently dropped instead of stopping."""
    rows = [["E  CN1", "M", "E  D001", "01", "Chin", "T1", "D1", 100, 0],
            ["E  CN2", "M", "E  D001", "01", "Chin", "T2", "D2", 50, 10]]
    p = _wb(tmp_path, rows + [[None] * 7 + [150, 10]], monkeypatch)
    recs, stripped, _ = C.read_workbook(2017, p)
    assert len(recs) == 2 and len(stripped) == 1
    (tmp_path / "x").mkdir()
    p2 = _wb(tmp_path / "x", rows + [[None] * 7 + [151, 10]], monkeypatch)
    with pytest.raises(ValueError, match="not the column totals"):
        C.read_workbook(2017, p2)


def test_unknown_header_is_a_stop(tmp_path, monkeypatch):
    """FAILS if a column the map does not know is ignored."""
    p = _wb(tmp_path, [["E CN1", "M", "E D001", "01", "Chin", "T", "D", 1, 0]], monkeypatch,
            header=HDR17[:6] + ["NOTES"] + HDR17[7:])
    with pytest.raises(ValueError, match="unmapped header"):
        C.read_workbook(2017, p)


def test_fy2015_project_column_must_hold_budget_lines(tmp_path, monkeypatch):
    """FAILS if FY2015's 'Project' column is read as a budget line when a value does not have
    a budget line's shape."""
    hdr = ["Project", "Borough", "District(s)", "Sponsors", "Fiscal Year Funded", "Title",
           "Description", "FY15"]
    ok = _wb(tmp_path, [["AG D001", "M", "08", "X", "2015", "T", "D", 5]], monkeypatch, header=hdr)
    recs, _, _ = C.read_workbook(2015, ok)
    assert recs[0]["budget_line"] == "AG D001" and "project_id" not in recs[0]
    (tmp_path / "b").mkdir()
    bad = _wb(tmp_path / "b", [["CN001", "M", "08", "X", "2015", "T", "D", 5]], monkeypatch,
              header=hdr)
    with pytest.raises(ValueError, match="not budget lines"):
        C.read_workbook(2015, bad)


def _t(**kw):
    r = {":id": "row-1", "reported": "2020", "fiscal_year": "FY20", "borough": "M",
         "award": "1000", "council_district": "3", "sponsor": "S", "title": "T",
         "description": "D", "id": "E  CN1", "budget_line": "E  D001"}
    r.update(kw)
    return r


def test_t474_split_records_are_flagged_never_reassembled():
    """B8. FAILS if a record's first row gets an amount, if a spilled fragment becomes a row,
    or if a row of some other broken shape is accepted silently."""
    rows = [_t(), _t(**{":id": "h", "award": "", "fiscal_year": ""}),
            _t(**{":id": "t", "reported": "PARK WEST", "borough": "FY20", "budget_line": "170000",
                  "award": "", "fiscal_year": "", "id": "ERROR: #NAME?"})]
    out, heads, tails = C.t474_rows(rows)
    assert [r["row_flag"] for r in out] == ["", "split_record_amount_unknown"]
    assert out[1]["amount"] == "" and out[1]["amount_fy"] == ""
    assert [h[":id"] for h in heads] == ["h"] and [t[":id"] for t in tails] == ["t"]
    with pytest.raises(ValueError, match="unrecognized row shape"):
        C.t474_split([_t(award="5", fiscal_year="")])


def test_reconcile_by_budget_line_uses_the_adopted_release():
    """A7. FAILS if the reconciliation uses a release other than the last one for the year, if
    a line equal in both years is not 'match', if the second year is ignored, or if lines
    present on one side only are dropped."""
    def omb(pub, line, y1, y2):
        return {"pub_date": pub, "release": "", "budget_line_norm": line, "yr1_fy": "2027",
                "year1_amt": str(y1), "year2_amt": str(y2)}
    rows = [omb("20260217", "P D018", 1, 0), omb("20260713", "P D018", 100, 5),
            omb("20260713", "P D019", 50, 0), omb("20260713", "S D129", 7, 0)]
    for r in rows:
        r["release"] = "adopted" if r["pub_date"] == "20260713" else ""

    def mine(line, fy, amt):
        return {"report_year": 2027, "amount_fy": fy, "budget_line_norm": line, "amount": amt}
    council = [mine("P D018", 2027, "60"), mine("P D018", 2027, "40"), mine("P D018", 2028, "5"),
               mine("P D019", 2027, "50"), mine("P D019", 2028, "1"), mine("PV DN1", 2027, "9")]
    got = {r["budget_line_norm"]: r["verdict"] for r in C.reconcile(council, rows)}
    assert got == {"P D018": "match", "P D019": "differ", "S D129": "omb_only",
                   "PV DN1": "council_only"}


def test_plan_totals_row_is_stripped():
    """FAILS if 2cmn-uidm's row with no release and no line (grand-total-sized amounts) is kept."""
    row = {":id": "x", "pub_date": "", "projtype": "", "budline": "", "budline_desc": "",
           "funding": "", "num_yrs_prsnt": "4", "yr1_fy": "",
           **{f"year{i}_amt": "1" for i in range(1, 6)}}
    good = dict(row, **{":id": "y", "pub_date": "20260928", "projtype": "P", "budline": "P D018",
                        "yr1_fy": "2027"})
    out, stripped = C.omb_plan_rows([row, good])
    assert [r["source_row"] for r in out] == ["y"] and [s[":id"] for s in stripped] == ["x"]


# ---------------------------------------------------------------- the committed build

@pytest.fixture(scope="module")
def built():
    return C.build()


def test_committed_outputs_are_current(built):
    """FAILS if a committed data/capital file is not what the committed sources produce."""
    import parse_expense_disclosure as P
    assert P.stale(C.outputs(built)) == []


def test_fy2027_reproduces_146_of_153(built):
    """The research finding (#87). FAILS if FY2027 stops showing 146 matching lines of 153, 7
    differing, 8 OMB-only, Council $853,688,000 vs OMB $879,477,000."""
    y = [r for r in built["recon"] if r["report_year"] == 2027]
    c = collections.Counter(r["verdict"] for r in y)
    assert (c["match"], c["differ"], c["omb_only"], c["council_only"]) == (146, 7, 8, 0)
    assert sum(Decimal(r["council_y1"] or 0) for r in y) == 853_688_000
    assert sum(Decimal(r["omb_y1"] or 0) for r in y) == 879_477_000


def test_corpus_pins(built):
    """FAILS if a year's first-year total moves, a totals row is counted, FY2018 appears, the
    split records change, or the FY2026 overlap stops being exactly P CN1606 $2,000,000."""
    tot = collections.Counter()
    for r in built["council"]:
        if r["amount"] and r["amount_fy"] == r["report_year"]:
            tot[r["report_year"]] += Decimal(r["amount"])
    assert tot[2015] == 465_143_000 and tot[2016] == 500_000_000 and tot[2017] == 514_807_000
    assert tot[2025] == 775_000_000 and tot[2026] == 779_320_000 and tot[2027] == 853_688_000
    assert 2018 not in tot
    assert [h["id"] for h in built["heads"]] == ["E  CN817", "E  CN832", "E  CN673", "E  CN136",
                                                 "P CN1606"]
    assert len(built["tails"]) == 7
    d = built["diff26"]
    assert d["only_wb"] == [(("P CN1606", 2026), [Decimal(2_000_000)])]
    assert d["only_od"] == [] and d["differ"] == []
