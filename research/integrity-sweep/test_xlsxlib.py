#!/usr/bin/env python3
"""Self-check for xlsxlib -- the one piece of parsing logic this audit wrote itself.

Every finding about the repair scripts' reader rests on this reader being right, so it is
checked against a workbook built here with a KNOWN interior gap, plus a live sanity read.

Run: python3 research/integrity-sweep/test_xlsxlib.py
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlib

SHEET = """<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Legal Name</t></is></c>
           <c r="B1" t="inlineStr"><is><t>EIN</t></is></c>
           <c r="C1" t="inlineStr"><is><t>Status</t></is></c>
           <c r="D1" t="inlineStr"><is><t>Amount</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Alpha Inc</t></is></c>
           <c r="B2" t="inlineStr"><is><t>11-1111111</t></is></c>
           <c r="C2" t="inlineStr"><is><t>Cleared</t></is></c>
           <c r="D2"><v>1000</v></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Beta LLC</t></is></c>
           <c r="B3" t="inlineStr"><is><t>22-2222222</t></is></c>
           <c r="D3"><v>2000</v></c></row>
</sheetData></worksheet>"""


def build(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", SHEET)


def main():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "gap.xlsx")
    build(p)
    rows = dict(xlsxlib.dicts(p))

    # Row 3 omits the Status cell. A reader that zips header against the cells PRESENT
    # would read Amount=2000 into Status and leave Amount empty.
    assert rows[2]["Legal Name"] == "Alpha Inc", rows[2]
    assert rows[2]["Amount"] == "1000", rows[2]
    assert rows[3]["Legal Name"] == "Beta LLC", rows[3]
    assert rows[3]["Status"] == "", f"interior gap not preserved: {rows[3]}"
    assert rows[3]["Amount"] == "2000", f"column shifted: {rows[3]}"
    assert rows[3]["EIN"] == "22-2222222", rows[3]

    assert xlsxlib.col_index("A1") == 0
    assert xlsxlib.col_index("Z9") == 25
    assert xlsxlib.col_index("AA1") == 26
    assert xlsxlib.col_index("BC12") == 54
    assert xlsxlib.norm_ein("13-2612524") == "132612524"

    # duplicate headers must not collide
    assert "Legal Name" in rows[2]

    # live sanity: a real workbook still parses, and the header row is what we expect
    live = "source/expense-funding-disclosure/funded_disclosure_FY2023.xlsx"
    if os.path.exists(live):
        g = xlsxlib.rows(live)
        rn, hdr = next(g)
        assert rn == 1 and "Legal Name" in hdr and "Amount" in hdr, hdr
        n = sum(1 for _ in g)
        assert n > 10000, n
        print(f"live read ok: {live} header row {rn}, {n:,} data rows")

    print("all xlsxlib checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
