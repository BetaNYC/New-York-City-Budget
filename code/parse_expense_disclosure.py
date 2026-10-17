#!/usr/bin/env python3
"""Parse the NYC Council's expense funding disclosure workbooks into one record shape, and
publish them as a parallel award-level dataset.

Source: source/expense-funding-disclosure/funded_disclosure_FY{YYYY}.xlsx  (FY2014-FY2027)
        source/expense-funding-disclosure/funded_disclosure_FY2013.xls   (legacy BIFF)

FY2014-FY2027 are read with the Python standard library only. An .xlsx is a zip of XML, so
zipfile + xml.etree is all that is needed. Shared strings are streamed with iterparse -- these
files carry ~1.2MB of sharedStrings.xml and a DOM parse of the whole worksheet is what makes
naive readers hang.

FY2013 is legacy OLE2/BIFF and needs `xlrd` (code/requirements.txt). xlrd is imported lazily,
only when an .xls is actually parsed, so this module stays importable -- and FY2014-FY2027 stay
parseable -- without it. Without xlrd, FY2013 is reported as skipped with the reason; the
`--write` and `--check` modes refuse to run on a skipped year rather than publish a partial
dataset.

Run it:
  python3 code/parse_expense_disclosure.py            demo() self-check + per-year summary
  python3 code/parse_expense_disclosure.py --write    write data/fyNN/expense_disclosure/*
  python3 code/parse_expense_disclosure.py --check    exit 1 if anything committed is stale
  python3 code/parse_expense_disclosure.py --manifest [--retrieved YYYY-MM-DD]
                                                [--verified YYYY-MM-DD]
                                                       write source/.../MANIFEST.csv, and append
                                                       every superseded row to
                                                       source/.../MANIFEST-HISTORY.csv

Outputs (one folder per fiscal year, matching data/fyNN/<doctype>/fyNN_<name>.csv):
  data/fyNN/expense_disclosure/fyNN_expense_awards.csv          one row per published row
                                                                 (exact copies kept, flagged
                                                                 in duplicate_group)
  data/fyNN/expense_disclosure/fyNN_expense_reconciliation.txt  totals, printed totals,
                                                                 every stripped row
"""

import argparse
import csv
import hashlib
import io
import os
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import NamedTuple

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "source", "expense-funding-disclosure")
DATA_DIR = os.path.join(ROOT, "data")
MANIFEST = os.path.join(SRC_DIR, "MANIFEST.csv")
MANIFEST_HISTORY = os.path.join(SRC_DIR, "MANIFEST-HISTORY.csv")
# Files in the source folder that are about the workbooks, not workbooks.
NOT_SOURCE = ("README.md", "MANIFEST.csv", "MANIFEST-HISTORY.csv")

# The Council rewords headers most years. Eight distinct header layouts exist across
# FY2013-FY2027, not two. Mapping by normalized header TEXT (not column position, not a
# per-era branch) collapses all of them into one table. Verified against every file:
#   FY2013  16 cols (.xls), no Fiscal Year, "Council Member" / "Legal Name of Organization" /
#           "EIN" / "Amount ($" / "Address 2" / "Fiscal Conduit Name" / "FC EIN"
#   FY2014  16 cols, no Fiscal Year, "Council Member" / "Legal Name of Organization" / "EIN"
#   FY2015  17 cols, "Council Members"
#   FY2016  16 cols, no Fiscal Year, "Legal Name of Organization Requesting Funding"
#   FY2017  17 cols, "Council Members"
#   FY2018-FY2020  17 cols, "Legal Name" / "EIN" / "CM Purpose of Funds"
#   FY2021-FY2023  17 cols, "Tax ID"
#   FY2024-FY2027  18 cols, adds "MOCS ID#"
# Synonyms with no file currently using them ("mocs id", "amount ($)", "address 2 (optional)")
# are carried over from the 2026-07-15 normalizer so a cosmetic re-punctuation by the Council
# does not stop the build; an unknown header still does.
HEADER_MAP = {
    "mocs id#": "mocs_id",
    "mocs id": "mocs_id",
    "fiscal year": "fiscal_year_col",
    "source": "source",
    "council member": "council_member",
    "council members": "council_member",
    "legal name": "legal_name",
    "legal name of organization": "legal_name",
    "legal name of organization requesting funding": "legal_name",
    "ein": "ein",
    "tax id": "ein",
    "status": "status",
    "amount": "amount",
    "amount ($": "amount",  # FY2013/FY2014 header is literally truncated mid-parenthesis
    "amount ($)": "amount",
    "agency": "agency",
    "program name": "program_name",
    "address": "address1",
    "street address 1": "address1",
    "grantee street address 1": "address1",
    "address 2": "address2",  # FY2013
    "address 2 (optional": "address2",  # FY2014, also truncated
    "address 2 (optional)": "address2",
    "street address 2": "address2",
    "grantee street address 2": "address2",
    "city": "city",
    "state": "state",
    "zip code": "postal_code",
    "postal code": "postal_code",
    "purpose of funds": "purpose",
    "cm purpose of funds": "purpose",
    "purpose to be listed in schedule c": "purpose",
    "fiscal conduit": "fiscal_conduit",
    "fiscal conduit name": "fiscal_conduit",
    "fc ein": "fiscal_conduit_ein",
    "fiscal conduit ein": "fiscal_conduit_ein",
}

# Invisible FORMAT characters (Unicode category Cf) are deleted -- a zero-width space inside one
# FY2015 EIN, two left-to-right marks (U+200E), BOMs -- with ONE exception, the soft hyphen
# (U+00AD). In these workbooks a soft hyphen is a HYPHEN that lost its glyph (text pasted from a
# PDF), never a line-break hint: all 211 cells that hold one (185 address1, 1 address2, 25
# purpose; no other field) read as hyphenated words or ranges -- the Queens house number
# "12<SHY>11 40th Avenue" (FY2018 rows 2796-2811), "after<SHY>school", "ages 12<SHY>19",
# "multi<SHY>media". Deleting it, as an earlier version did, turned "12-11 40th Avenue" into
# "1211 40th Avenue", a different address. So a soft hyphen becomes "-", EXCEPT where the cell
# already prints a "-" or "/" right beside it ("12-<SHY>11", 169 address cells; "E<SHY>-waste";
# "disposal/<SHY>destruction"): there the visible character is already the separator, and a
# second "-" would invent "12--11". See SHY_ADJACENT and _soft_hyphens().
# A no-break space is a real word separator ("Youth Design Center,<NBSP>Inc." in FY2026/FY2027),
# so it becomes a space; deleting it, as an earlier version did, glued two words together.
SHY = "\u00ad"
SHY_ADJACENT = "-/"
_WS = re.compile(r"\s+")

# Descriptive only: used to NAME the kind of a stripped row in the report. It never decides
# whether a row is stripped -- the Status column does that (see _classify).
_SUMMARY_WORDS = re.compile(r"total|difference|new add|master list", re.I)

# The two clearance states the Council publishes. Case varies (FY2018 is UPPERCASE); the raw
# value is kept verbatim in `status` and this is the folded form in `status_norm`.
KNOWN_STATUS = ("cleared", "pending")

# Printed totals each workbook carries about itself, and which of them the kept rows must
# equal. In the snapshot committed here only FY2024 prints any total; every other year prints
# none, and the reconciliation report says so rather than attributing our own sum to the Council.
#   FY2024  "New Total" = SUM(H2:H10818) in the Amount column, and = Adoption Total + Admin
#           New Add in column J. Both cells print 527,971,414.
RECONCILE_TO = {
    2024: ("New Total",),
}

# Totals an EARLIER snapshot printed and the current one no longer does. Reported beside our
# sum, labeled with the snapshot date, never as the current workbook's own figure and never as
# the verdict. Values are copied from that snapshot's committed reconciliation report.
#   FY2026  The 2026-07-15 workbook (sheet "FY26 (06-08-26)") printed "Master List Total" =
#           SUM(H2:H11762) and a typed "Updated Total", both 716,213,155, in four footer rows.
#           The 2026-10-12 workbook (sheet "FY26 (09-14-26)") has no footer rows at all.
PRIOR_PRINTED = {
    2026: [("2026-07-15", "Master List Total", Decimal(716213155)),
           ("2026-07-15", "Updated Total", Decimal(716213155))],
}

OUT_FIELDS = [
    "fiscal_year", "mocs_id", "source", "council_member", "council_member_id",
    "council_member_type", "legal_name", "ein", "status",
    "status_norm", "amount", "agency", "program_name", "address1", "address2", "city", "state",
    "postal_code", "zip", "zip_status", "zip_candidates", "purpose", "fiscal_conduit", "fiscal_conduit_ein",
    "source_file", "source_row", "duplicate_group",
]

# Fields that identify a designation for the exact-copy flag (GitHub #69): every published field
# except where the row sits (source_row) and what the parser derives from the others.
DUPLICATE_KEY = ["mocs_id", "source", "council_member", "legal_name", "ein", "status",
                 "amount", "agency", "program_name", "address1", "address2", "city", "state",
                 "postal_code", "purpose", "fiscal_conduit", "fiscal_conduit_ein"]

MANIFEST_FIELDS = ["file", "sha256", "bytes", "retrieved", "format", "sheet", "sheet_rows",
                   "award_rows", "stripped_rows", "total_amount"]


class Award(NamedTuple):
    """One designation. Same shape for every fiscal year."""
    fiscal_year: int          # from the FILENAME, which is authoritative: FY2013, FY2014 and
                              # FY2016 have no Fiscal Year column at all.
    mocs_id: str              # "" before FY2024
    source: str               # Local / Youth / Aging / Speaker's Initiative / named initiative
    council_member: str
    legal_name: str
    ein: str                  # 9 digits, leading zeros preserved
    status: str               # RAW, as published: "Cleared" / "CLEARED" / "Pending" / "PENDING"
    status_norm: str          # "cleared" / "pending" / "other". Never replaces status.
    amount: float
    agency: str
    program_name: str
    address1: str
    address2: str
    city: str
    state: str
    postal_code: str
    purpose: str
    fiscal_conduit: str
    fiscal_conduit_ein: str
    source_file: str          # provenance: which workbook
    source_row: int           # provenance: 1-based sheet row, so any record can be eyeballed
    amount_text: str = ""     # the amount exactly as the cell holds it, for exact (Decimal) sums


class YearReport(NamedTuple):
    fiscal_year: int
    source_file: str
    sheet_name: str
    skipped: str              # "" if parsed; reason string if the file was skipped
    n_rows_present: int       # rows after the header, up to the last row the sheet holds
                              # (an .xlsx omits empty rows from its XML; they count as blank)
    n_awards: int
    n_blank: int
    n_stripped: int
    stripped: list            # [{"row": int, "kind": str, "cells": {header-or-letter: value}}]
    total_amount: float
    by_status: dict           # {"cleared": n, "pending": n, ...} rows, on status_norm
    header_note: str          # anything the file did that the others did not
    amount_by_status: dict = {}   # {"cleared": Decimal, "pending": Decimal, "other": Decimal}
    printed: tuple = ()       # ({"row", "label", "column", "value", "formula"}, ...)
    ein_padded: tuple = ()    # source rows whose numeric EIN cell lost a leading zero
    format: str = ""          # "xlsx" / "xls"
    sheet_rows: int = 0       # rows in the sheet, header included


# ---------------------------------------------------------------- readers

def _shared_strings(z):
    """Stream sharedStrings.xml. Streaming is not an optimization here -- these files are
    ~1.2MB of XML and building the whole tree is what makes a naive reader appear to hang."""
    out = []
    if "xl/sharedStrings.xml" not in z.namelist():
        return out
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                out.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
    return out


def _rows(z, sheet_path, shared, numeric=None, formulas=None):
    """Yield (row_number, {column_letter: value}) streaming, one row at a time.

    If `numeric` is a dict it is filled with {row_number: set(column_letter)} for cells stored
    as numbers (not strings) -- the only cells that can have lost a leading zero. If `formulas`
    is a dict it is filled with {(row_number, column_letter): formula_text}."""
    with z.open(sheet_path) as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != NS + "row":
                continue
            rn = int(el.get("r"))
            cells = {}
            for c in el.findall(NS + "c"):
                ref = c.get("r") or ""
                m = re.match(r"[A-Z]+", ref)
                if not m:
                    continue
                col = m.group(0)
                t = c.get("t")
                v = c.find(NS + "v")
                inline = c.find(NS + "is")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr" and inline is not None:
                    val = "".join(x.text or "" for x in inline.iter(NS + "t"))
                elif v is not None:
                    val = v.text
                    if numeric is not None and t in (None, "n"):
                        numeric.setdefault(rn, set()).add(col)
                else:
                    val = None
                if formulas is not None:
                    fe = c.find(NS + "f")
                    if fe is not None and fe.text:
                        formulas[(rn, col)] = fe.text
                cells[col] = val
            yield rn, cells
            el.clear()


def _col_letter(i):
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _xls_number(v):
    """Render an xlrd float the way the .xlsx files render the same cell: integral values with
    no '.0' (so EIN 136400434.0 -> '136400434', ZIP 11375.0 -> '11375'), anything else as the
    shortest repr that round-trips."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def _xls_rows(path, numeric=None):
    """Yield (row_number, {column_letter: value}) from the FIRST sheet of a legacy .xls.

    Needs xlrd; raises ImportError if it is absent (parse_year turns that into a reported
    skip). FY2013's workbook holds three sheets -- MASTER plus Sheet2/Sheet3, both 0x0 -- and
    only the first carries data. Cell types per xlrd.biffh: XL_CELL_EMPTY/BLANK (no value),
    XL_CELL_TEXT, XL_CELL_NUMBER (float), and DATE/BOOLEAN/ERROR, which no FY2013 cell uses;
    meeting one is a stop, not a guess at how to render it."""
    import xlrd  # noqa: PLC0415 -- deliberate lazy import, see module docstring

    book = xlrd.open_workbook(path)
    sh = book.sheet_by_index(0)
    for r in range(sh.nrows):
        rn = r + 1
        cells = {}
        for ci in range(sh.ncols):
            c = sh.cell(r, ci)
            col = _col_letter(ci)
            if c.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                val = None
            elif c.ctype == xlrd.XL_CELL_TEXT:
                val = c.value
            elif c.ctype == xlrd.XL_CELL_NUMBER:
                val = _xls_number(c.value)
                if numeric is not None:
                    numeric.setdefault(rn, set()).add(col)
            else:
                raise ValueError(f"{os.path.basename(path)} row {rn} col {col}: cell type "
                                 f"{c.ctype} (date/boolean/error) has no defined rendering")
            cells[col] = val
        yield rn, cells


def _xls_sheet_name(path):
    import xlrd  # noqa: PLC0415
    return xlrd.open_workbook(path, on_demand=True).sheet_names()[0]


def _soft_hyphens(v):
    """U+00AD -> '-', or deleted where a '-' or '/' already sits beside it (see SHY above)."""
    if SHY not in v:
        return v
    out = []
    for i, ch in enumerate(v):
        if ch != SHY:
            out.append(ch)
            continue
        prev = v[i - 1] if i else ""
        nxt = v[i + 1] if i + 1 < len(v) else ""
        # A run of soft hyphens is one hyphen; a visible '-' or '/' beside it is the separator.
        if (prev and prev in SHY_ADJACENT + SHY) or (nxt and nxt in SHY_ADJACENT):
            continue
        out.append("-")
    return "".join(out)


def _clean(v):
    """Text cell -> one line. A soft hyphen becomes a hyphen (deleted only where a '-' or '/'
    already sits beside it); every other invisible format character (category Cf: zero-width
    space, left-to-right mark, BOM) is deleted; every run of whitespace (line breaks, tabs,
    no-break spaces, doubled spaces -- 368 cells across the corpus hold a line break) collapsed
    to one space; ends trimmed. No character that carries meaning is removed, and amounts/EINs
    contain no whitespace to begin with."""
    if v is None:
        return ""
    v = "".join(ch for ch in _soft_hyphens(v) if unicodedata.category(ch) != "Cf")
    return _WS.sub(" ", v).strip()


def _sheet_and_name(z):
    """Locate the single worksheet. Every one of these workbooks has exactly one."""
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    names = [s.get("name") for s in wb.iter(NS + "sheet")]
    paths = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
    if len(paths) != 1:
        raise ValueError(f"expected exactly one worksheet, found {paths}")
    return paths[0], (names[0] if names else "")


# ---------------------------------------------------------------- row classification

def norm_status(raw):
    """'Cleared' / 'CLEARED ' -> 'cleared'; 'Pending' -> 'pending'; anything else -> 'other'."""
    s = _clean(raw).lower()
    return s if s in KNOWN_STATUS else "other"


def parse_amount_text(s):
    """Decimal of a cell's amount, or None if it is not a number.

    Workbooks store amounts as IEEE doubles. The .xlsx XML writes them with 17 significant
    digits ("22320.420999999998") while xlrd hands back the double itself; both are rendered
    here as the SHORTEST decimal that round-trips to that same double ("22320.421"). Same
    value, one spelling, whichever reader produced it -- and integral amounts, which are all
    but 281 of 139,186 rows, are exact either way."""
    try:
        f = float(_clean(s).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return Decimal(repr(f))


def format_amount(d):
    """Decimal -> CSV text. Integral amounts print with no decimal point, matching every other
    amount column in data/. Fractional ones (FY2014/15/17/19 carry some, e.g. 13881.76 and the
    Council's own float residue 65469.00000000001) are kept exactly as published."""
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


def classify(status, legal_name, amount_text):
    """Decide what one non-blank row is. Returns 'award' or 'stripped'.

    The decision is made on the STATUS column first, never on a label's wording:
      - Status is a clearance state (Cleared/Pending, any case)  -> award. Such a row must also
        carry a legal name and a numeric amount; if it does not, the published schema moved
        and that is a stop (ValueError), not a silent drop.
      - Status is anything else, blank included -> a summary/footer row, UNLESS the row still
        names an organization and carries a numeric amount. Then it is kept as an award with
        status_norm 'other', so a status value the Council introduces later is surfaced in
        every report rather than lost.
    FY2024's footer totals have a blank Status and their labels in a different column from
    FY2026's; both fall to the second rule because neither names an organization."""
    sn = norm_status(status)
    has_amount = parse_amount_text(amount_text) is not None
    if sn in KNOWN_STATUS:
        if not legal_name or not has_amount:
            raise ValueError(f"row has clearance status {status!r} but legal_name="
                             f"{legal_name!r} amount={amount_text!r}")
        return "award"
    if legal_name and has_amount:
        return "award"
    return "stripped"


_HYPHENATED_EIN = re.compile(r"\d{2}-\d{7}")


def clean_ein(raw, was_numeric):
    """Return (ein, padded). An EIN is 9 digits, no hyphen (the repo-wide convention).

    - The IRS print form NN-NNNNNNN (FY2013 has 175) loses its hyphen. Formatting only.
    - A cell STORED AS A NUMBER drops a leading zero (FY2013 holds three such rows), so an
      8-digit numeric cell is left-padded and the row reported. Text cells are never padded:
      an 8-character text EIN would be a typo, and padding it would invent a digit.
    Anything else is returned as published, for the validator to flag."""
    e = _clean(raw)
    if _HYPHENATED_EIN.fullmatch(e):
        return e.replace("-", ""), False
    if was_numeric and e.isdigit() and len(e) == 8:
        return e.zfill(9), True
    return e, False


# ---------------------------------------------------------------- parse

def parse_year(path):
    """Parse one workbook. Returns (list[Award], YearReport)."""
    fname = os.path.basename(path)
    m = re.search(r"FY(\d{4})", fname)
    if not m:
        raise ValueError(f"cannot read a fiscal year out of {fname}")
    fy = int(m.group(1))

    numeric, formulas = {}, {}
    if zipfile.is_zipfile(path):
        fmt = "xlsx"
        z = zipfile.ZipFile(path)
        sheet_path, sheet_name = _sheet_and_name(z)
        shared = _shared_strings(z)
        it = _rows(z, sheet_path, shared, numeric=numeric, formulas=formulas)
    else:
        # Legacy OLE2/BIFF (magic d0cf11e0a1b11ae1): FY2013 only.
        fmt = "xls"
        try:
            sheet_name = _xls_sheet_name(path)
        except ImportError:
            return [], YearReport(
                fy, fname, "", "legacy .xls (OLE2/BIFF) needs xlrd, which is not installed "
                "(pip install -r code/requirements.txt)", 0, 0, 0, 0, [], 0.0, {}, "",
                format=fmt)
        it = _xls_rows(path, numeric=numeric)

    header_rn, header_cells = next(it)
    col_field = {}
    for col, raw in header_cells.items():
        h = re.sub(r"\s+", " ", _clean(raw)).lower()
        if not h:
            continue
        if h not in HEADER_MAP:
            # A column we do not recognize means the published schema moved. Silently
            # ignoring it is how a field goes missing for a year without anyone noticing,
            # so this is a stop.
            raise ValueError(f"{fname}: unmapped header {raw!r} in column {col}. "
                             f"Add it to HEADER_MAP.")
        col_field[col] = HEADER_MAP[h]
    field_col = {f: c for c, f in col_field.items()}
    for required in ("legal_name", "amount", "status", "ein", "source", "council_member"):
        if required not in field_col:
            raise ValueError(f"{fname}: no column maps to {required}")

    notes = []
    if "mocs_id" not in field_col:
        notes.append("no MOCS ID#")
    if "fiscal_year_col" not in field_col:
        notes.append("no Fiscal Year column (year taken from filename)")

    awards, stripped, padded = [], [], []
    fy_col_mismatch = 0
    last_rn = header_rn

    for rn, cells in it:
        last_rn = rn
        get = lambda f: _clean(cells.get(field_col[f])) if f in field_col else ""  # noqa: E731

        if not any(_clean(v) for v in cells.values()):
            continue

        status, legal_name, amount_s = get("status"), get("legal_name"), get("amount")
        if classify(status, legal_name, amount_s) == "stripped":
            joined = " ".join(str(v) for v in cells.values() if v)
            stripped.append({
                "row": rn,
                "kind": "labeled_summary" if _SUMMARY_WORDS.search(joined) else "orphan_value",
                "cells": {col_field.get(c, c): v for c, v in cells.items() if _clean(v)},
                "letters": {c: v for c, v in cells.items() if _clean(v)},
            })
            continue

        amount_d = parse_amount_text(amount_s)

        if "fiscal_year_col" in field_col:
            fyc = get("fiscal_year_col")
            if fyc and fyc.split(".")[0] != str(fy):
                fy_col_mismatch += 1

        ein, was_padded = clean_ein(cells.get(field_col["ein"]),
                                    field_col["ein"] in numeric.get(rn, ()))
        if was_padded:
            padded.append(rn)

        awards.append(Award(
            fiscal_year=fy,
            mocs_id=get("mocs_id"),
            source=get("source"),
            council_member=get("council_member"),
            legal_name=legal_name,
            ein=ein,
            status=status,
            status_norm=norm_status(status),
            amount=float(amount_d),
            agency=get("agency"),
            program_name=get("program_name"),
            address1=get("address1"),
            address2=get("address2"),
            city=get("city"),
            state=get("state"),
            postal_code=get("postal_code"),
            purpose=get("purpose"),
            fiscal_conduit=get("fiscal_conduit"),
            fiscal_conduit_ein=clean_ein(cells.get(field_col.get("fiscal_conduit_ein")),
                                         field_col.get("fiscal_conduit_ein")
                                         in numeric.get(rn, ()))[0],
            source_file=fname,
            source_row=rn,
            amount_text=format_amount(amount_d),
        ))

    # Blank = every row after the header that is neither an award nor stripped: rows present
    # with only empty cells, and rows an .xlsx simply omits (FY2024 has 12 such, ten of them
    # interleaved with its footer). Counting by row NUMBER, not by <row> element, is what makes
    # awards + stripped + blank account for every row of the sheet.
    n_present = last_rn - header_rn
    n_blank = n_present - len(awards) - len(stripped)

    if fy_col_mismatch:
        notes.append(f"{fy_col_mismatch} rows whose Fiscal Year cell != {fy}")
    if any(a.status != a.status.title() for a in awards):
        notes.append("Status published in UPPERCASE")

    by_status, amount_by_status = {}, {s: Decimal(0) for s in KNOWN_STATUS + ("other",)}
    for a in awards:
        by_status[a.status_norm] = by_status.get(a.status_norm, 0) + 1
        amount_by_status[a.status_norm] += Decimal(a.amount_text)

    return awards, YearReport(
        fiscal_year=fy, source_file=fname, sheet_name=sheet_name, skipped="",
        n_rows_present=n_present, n_awards=len(awards), n_blank=n_blank,
        n_stripped=len(stripped), stripped=stripped,
        total_amount=sum(a.amount for a in awards), by_status=by_status,
        header_note="; ".join(notes),
        amount_by_status=amount_by_status,
        printed=tuple(_printed_values(stripped, formulas)),
        ein_padded=tuple(padded),
        format=fmt,
        sheet_rows=last_rn,
    )


def _printed_values(stripped, formulas):
    """Every number the workbook prints on a stripped row, with the label printed on the same
    row and the cell's formula if it has one. Their numbers, not ours: this is what the
    reconciliation compares against."""
    out = []
    for s in stripped:
        letters = s["letters"]
        labels = [(c, _clean(v)) for c, v in letters.items()
                  if parse_amount_text(v) is None and _clean(v)]
        label = " / ".join(v.rstrip(":").strip() for _, v in labels)
        for col, v in letters.items():
            d = parse_amount_text(v)
            if d is None:
                continue
            out.append({"row": s["row"], "label": label, "column": col, "value": d,
                        "formula": formulas.get((s["row"], col), "")})
    return out


def parse_all(src_dir=SRC_DIR):
    """Parse every funded_disclosure_FY*. Returns [(awards, YearReport)] ordered by year."""
    paths = sorted(
        p for p in (os.path.join(src_dir, f) for f in os.listdir(src_dir))
        if re.search(r"funded_disclosure_FY\d{4}\.(xlsx|xls)$", p)
    )
    return [parse_year(p) for p in paths]


def _labeled_total(rep, *words):
    """Pull the value out of one of a year's own embedded summary rows, by its label.
    Used to check our sum against the Council's printed sum -- their number, not ours."""
    for s in rep.stripped:
        vals = list(s["cells"].values())
        for i, v in enumerate(vals):
            if any(w.lower() in str(v).lower() for w in words):
                for other in vals[:i] + vals[i + 1:]:
                    try:
                        return float(other)
                    except (TypeError, ValueError):
                        continue
    return None


# ---------------------------------------------------------------- reconciliation

def total_decimal(awards):
    return sum((Decimal(a.amount_text) for a in awards), Decimal(0))


def reconcile(awards, rep):
    """Compare the kept rows to the workbook's own printed totals.

    Returns (verdict, checks) where verdict is 'RECONCILED', 'MISMATCH' or 'NO PRINTED TOTAL',
    and checks is [(label, column, printed_value, formula, ok)] for every target label."""
    targets = RECONCILE_TO.get(rep.fiscal_year, ())
    if not targets:
        if any("total" in p["label"].lower() for p in rep.printed):
            # A year started printing a total and nobody told RECONCILE_TO. Stop.
            raise ValueError(f"FY{rep.fiscal_year} prints a total "
                             f"{[p['label'] for p in rep.printed]} not listed in RECONCILE_TO")
        return "NO PRINTED TOTAL", []
    ours = total_decimal(awards)
    checks = []
    for t in targets:
        hits = [p for p in rep.printed if p["label"].lower() == t.lower()]
        if not hits:
            raise ValueError(f"FY{rep.fiscal_year}: printed total {t!r} not found in workbook")
        for p in hits:
            checks.append((t, p["column"], p["value"], p["formula"], p["value"] == ours))
    return ("RECONCILED" if all(c[-1] for c in checks) else "MISMATCH"), checks


def _usd(d):
    d = Decimal(d)
    return f"{d:,.0f}" if d == d.to_integral_value() else f"{d:,.2f}"


def reconciliation_text(awards, rep):
    """The per-year report. Deterministic: same inputs, byte-identical output."""
    verdict, checks = reconcile(awards, rep)
    yy = f"fy{rep.fiscal_year % 100:02d}"
    L = [f"EXPENSE DISCLOSURE RECONCILIATION  ({yy})  [parser: parse_expense_disclosure.py]",
         f"source: {rep.source_file}  (sheet {rep.sheet_name!r}, {rep.format}, "
         f"{rep.sheet_rows} rows incl. header)",
         f"printed total: {verdict}",
         "",
         "Every non-blank row after the header is either an award or a stripped row. A row is",
         "decided by its Status cell: Cleared/Pending (any case) is an award; anything else is",
         "stripped unless it still names an organization and an amount (then it is kept with",
         "status_norm 'other'). Every stripped row is listed below with its cells.",
         "",
         f"rows after header: {rep.n_rows_present}   blank: {rep.n_blank}   "
         f"awards: {rep.n_awards}   stripped: {rep.n_stripped}",
         "",
         f"{'status_norm':<14}{'rows':>8}{'amount':>20}"]
    for s in KNOWN_STATUS + ("other",):
        L.append(f"{s:<14}{rep.by_status.get(s, 0):>8}{_usd(rep.amount_by_status.get(s, 0)):>20}")
    L.append(f"{'ALL':<14}{rep.n_awards:>8}{_usd(total_decimal(awards)):>20}")
    L.append("")
    L.append("Headline figure = cleared only. 'ALL' adds pending (and other) and is labeled so.")
    L.append("")
    if verdict == "NO PRINTED TOTAL":
        L.append("This workbook prints no total of its own. The sums above are computed by this")
        L.append("parser from the rows; they are not a figure published by the Council.")
        prior = PRIOR_PRINTED.get(rep.fiscal_year, [])
        if prior:
            L.append("")
            L.append("An earlier snapshot of this workbook did print totals. They are NOT this")
            L.append("workbook's figures; they are shown so a change in the year's total is seen:")
            ours = total_decimal(awards)
            for when, label, val in prior:
                L.append(f"  snapshot {when} {label!r}: {_usd(val)} vs kept rows {_usd(ours)}  "
                         f"{'SAME' if val == ours else 'DIFFERENT'}")
    else:
        L.append("Printed totals (the workbook's own numbers):")
        for p in rep.printed:
            f = f"  formula ={p['formula']}" if p["formula"] else "  (typed value)"
            L.append(f"  row {p['row']:>6} col {p['column']:<3} {p['label']!r:<26}"
                     f"{_usd(p['value']):>16}{f}")
        L.append("")
        L.append("Reconciled against:")
        for label, col, val, formula, ok in checks:
            L.append(f"  {label!r} col {col}: {_usd(val)} vs kept rows "
                     f"{_usd(total_decimal(awards))}  {'OK' if ok else 'DIFF'}")
    L.append("")
    L.append(f"Stripped rows ({rep.n_stripped}):")
    if not rep.stripped:
        L.append("  none")
    for s in rep.stripped:
        L.append(f"  row {s['row']:>6}  {s['kind']:<16} {s['letters']}")
    L.append("")
    L.append(f"EIN cells stored as numbers that lost a leading zero, left-padded to 9 digits "
             f"({len(rep.ein_padded)}): {list(rep.ein_padded) or 'none'}")
    dup = duplicate_groups(awards)
    by_rn = {a.source_row: a for a in awards}
    extra = [rn for rn, g in dup.items() if rn != g]
    L.append(f"Rows identical to another row in every field but source_row, kept and flagged in "
             f"duplicate_group: {len(set(dup.values()))} group(s), {len(dup)} row(s); "
             f"{len(extra)} beyond the first of each group, "
             f"${_usd(sum((Decimal(by_rn[rn].amount_text) for rn in extra), Decimal(0)))}")
    if rep.header_note:
        L.append(f"notes: {rep.header_note}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- outputs

def out_dir(fy, data_dir=DATA_DIR):
    return os.path.join(data_dir, f"fy{fy % 100:02d}", "expense_disclosure")


def duplicate_groups(awards):
    """{source_row: group} for rows identical to another row of the SAME workbook in every
    DUPLICATE_KEY field (GitHub #69). The group is the source_row of the group's first row, so
    it reads as "same as row N" and is stable for a given workbook. Unique rows are absent.

    Every row is kept: the workbooks print these repeats verbatim, and whether each is a real
    second designation or a filing error cannot be told from the file. The flag lets a reader
    see them and choose."""
    groups = {}
    for a in awards:
        d = a._asdict()
        d["amount"] = a.amount_text
        groups.setdefault(tuple(d[f] for f in DUPLICATE_KEY), []).append(a.source_row)
    out = {}
    for rows in groups.values():
        if len(rows) > 1:
            for rn in rows:
                out[rn] = min(rows)
    return out


_ZCTAS = None


def _zctas():
    """The committed ZCTA -> state(s) table (code/zcta_states.py, GitHub #70), loaded once."""
    global _ZCTAS
    if _ZCTAS is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import zcta_states  # sibling module, needed only when writing CSVs
        _ZCTAS = zcta_states
        _ZCTAS.TABLE_DATA = zcta_states.load_table()
    return _ZCTAS


CROSSWALK = os.path.join(DATA_DIR, "disclosure_council_member_crosswalk.csv")
_MEMBERS = None


def _members():
    """{(fiscal_year, council_member): (type, id)} from the committed member crosswalk
    (code/build_member_crosswalk.py, GitHub #72), loaded once."""
    global _MEMBERS
    if _MEMBERS is None:
        with open(CROSSWALK, newline="", encoding="utf-8") as f:
            _MEMBERS = {(int(r["fiscal_year"]), r["council_member"]):
                        (r["council_member_type"], r["council_member_id"])
                        for r in csv.DictReader(f)}
    return _MEMBERS


def member_of(a):
    """(council_member_id, council_member_type) for one award. A (year, printed value) the
    crosswalk does not hold is a stop: a re-pull that brings a new name must re-run the
    crosswalk, never publish a row with no type."""
    hit = _members().get((a.fiscal_year, a.council_member))
    if hit is None:
        raise ValueError(f"FY{a.fiscal_year} council_member {a.council_member!r} is not in "
                         f"{os.path.relpath(CROSSWALK, ROOT)}; run "
                         f"code/build_member_crosswalk.py --write")
    return hit[1], hit[0]


def csv_text(awards):
    """The per-year CSV. `postal_code` is the cell as published; `zip`, `zip_status` and
    `zip_candidates` are derived from it and the row's `state` against the Census 2020 ZCTA list
    (GitHub #70; rules in zcta_states.derive_zip). Nothing published is rewritten."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(OUT_FIELDS)
    dup = duplicate_groups(awards)
    z = _zctas()
    for a in awards:
        d = a._asdict()
        d["amount"] = a.amount_text
        d["duplicate_group"] = dup.get(a.source_row, "")
        d["zip"], d["zip_status"], d["zip_candidates"] = z.derive_zip(a.postal_code, a.state,
                                                                      z.TABLE_DATA)
        d["council_member_id"], d["council_member_type"] = member_of(a)
        w.writerow([d[f] for f in OUT_FIELDS])
    return buf.getvalue()


def outputs(results, data_dir=DATA_DIR):
    """{path: text} for every file --write produces. Pure: nothing touches disk."""
    skipped = [r for _, r in results if r.skipped]
    if skipped:
        raise SystemExit("refusing to write a partial dataset; skipped: "
                         + "; ".join(f"FY{r.fiscal_year}: {r.skipped}" for r in skipped))
    out = {}
    for awards, rep in results:
        d = out_dir(rep.fiscal_year, data_dir)
        yy = f"fy{rep.fiscal_year % 100:02d}"
        out[os.path.join(d, f"{yy}_expense_awards.csv")] = csv_text(awards)
        out[os.path.join(d, f"{yy}_expense_reconciliation.txt")] = reconciliation_text(awards,
                                                                                      rep)
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path=MANIFEST):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def manifest_rows(results, src_dir=SRC_DIR, retrieved=None, previous=None, verified=None):
    """One row per file in the source folder (NOT_SOURCE excluded).

    `retrieved` is the date of the most recent download that produced this exact file. A new or
    changed file needs `retrieved` passed explicitly -- the date a file was pulled is a fact
    about the pull, and is never inferred from the file. An unchanged file keeps its previous
    date, unless `verified` is passed: the date it was downloaded again and came back
    byte-identical (same sha256), which then becomes its `retrieved` date."""
    prev = {r["file"]: r for r in (previous or [])}
    by_file = {r.source_file: (aw, r) for aw, r in results}
    rows = []
    for fname in sorted(os.listdir(src_dir)):
        if fname in NOT_SOURCE or fname.startswith("."):
            continue
        p = os.path.join(src_dir, fname)
        digest = sha256(p)
        old = prev.get(fname)
        if old and old["sha256"] == digest:
            when = verified or old["retrieved"]
        elif retrieved:
            when = retrieved
        else:
            raise SystemExit(f"{fname} is new or changed (sha256 {digest[:12]}); pass "
                             f"--retrieved YYYY-MM-DD with the date it was downloaded")
        row = {"file": fname, "sha256": digest, "bytes": os.path.getsize(p),
               "retrieved": when, "format": "xlsx" if zipfile.is_zipfile(p) else "xls",
               "sheet": "", "sheet_rows": "", "award_rows": "", "stripped_rows": "",
               "total_amount": ""}
        if fname in by_file:
            aw, rep = by_file[fname]
            row.update(sheet=rep.sheet_name, sheet_rows=rep.sheet_rows, award_rows=rep.n_awards,
                       stripped_rows=rep.n_stripped, total_amount=format_amount(
                           total_decimal(aw)))
        elif row["format"] == "xlsx":
            z = zipfile.ZipFile(p)
            sp, name = _sheet_and_name(z)
            n = 0
            for n, _ in _rows(z, sp, _shared_strings(z)):
                pass
            row.update(sheet=name, sheet_rows=n)
        rows.append(row)
    return rows


def manifest_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


HISTORY_FIELDS = MANIFEST_FIELDS + ["superseded_on"]


def superseded_rows(previous, rows):
    """Previous manifest rows that the new manifest no longer carries verbatim, each stamped
    with `superseded_on` = the retrieved date of the row that replaced it ('removed' if the
    file is gone). Appended to MANIFEST-HISTORY.csv, so an old hash stays traceable after the
    workbook it describes has been overwritten."""
    new = {r["file"]: {k: str(v) for k, v in r.items()} for r in rows}
    out = []
    for old in previous or []:
        cur = new.get(old["file"])
        if cur is not None and all(cur[k] == old.get(k, "") for k in MANIFEST_FIELDS):
            continue
        out.append(dict(old, superseded_on=cur["retrieved"] if cur else "removed"))
    return out


def history_text(existing_text, superseded):
    """MANIFEST-HISTORY.csv is append-only: existing lines are kept byte for byte."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HISTORY_FIELDS, lineterminator="\n")
    if not existing_text:
        w.writeheader()
    w.writerows(superseded)
    return (existing_text or "") + buf.getvalue()


def write_files(files):
    for path, text in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)


def stale(files):
    """Paths whose on-disk content differs from what would be written."""
    bad = []
    for path, text in files.items():
        if not os.path.exists(path):
            bad.append((path, "missing"))
            continue
        with open(path, encoding="utf-8", newline="") as f:
            if f.read() != text:
                bad.append((path, "differs"))
    return bad


# ---------------------------------------------------------------- self-check

def demo():
    """One runnable self-check against the real corpus. Fails loudly if the parser drifts."""
    results = parse_all()
    by_fy = {rep.fiscal_year: (aw, rep) for aw, rep in results}

    assert set(by_fy) == set(range(2013, 2028)), sorted(by_fy)
    for fy in range(2014, 2028):
        assert by_fy[fy][1].skipped == "", by_fy[fy][1]

    # FY2013 is legacy .xls: parsed when xlrd is present, skipped WITH a reason when it is not.
    aw13, rep13 = by_fy[2013]
    if rep13.skipped:
        assert aw13 == [] and "xlrd" in rep13.skipped, rep13
    else:
        assert rep13.n_awards == 4987 and rep13.n_stripped == 0, rep13
        assert len(rep13.ein_padded) == 3, rep13.ein_padded

    # The strongest check available: each year that publishes its own total must agree with
    # the total we compute from the rows we kept. Their arithmetic, not a number we hardcoded.
    # FY2026 printed its own total until the 2026-10-12 re-pull dropped the footer rows; its
    # rows must still equal what the earlier snapshot printed (PRIOR_PRINTED).
    aw26, rep26 = by_fy[2026]
    assert rep26.n_stripped == 0, rep26.stripped
    assert reconcile(aw26, rep26)[0] == "NO PRINTED TOTAL"
    assert all(total_decimal(aw26) == v for _, _, v in PRIOR_PRINTED[2026])

    # FY2024's summary rows carry DIFFERENT words in DIFFERENT columns than FY2026's.
    # Matching on the Status column for "Schedule C Total:" misses every one of them; their
    # Status is blank, which is what strips them.
    aw24, rep24 = by_fy[2024]
    assert rep24.n_stripped == 5, rep24.stripped
    printed24 = _labeled_total(rep24, "New Total")
    assert printed24 is not None and abs(rep24.total_amount - printed24) < 0.01, \
        (rep24.total_amount, printed24)
    assert any(s["kind"] == "orphan_value" for s in rep24.stripped), rep24.stripped
    assert reconcile(aw24, rep24)[0] == "RECONCILED"

    # Nothing else strips anything. A regression that widened the predicate shows up here.
    assert sum(r.n_stripped for _, r in results) == 5, [
        (r.fiscal_year, r.n_stripped) for _, r in results]

    # Status is kept verbatim AND normalized. FY2018 publishes it uppercase.
    aw18 = by_fy[2018][0]
    assert any(a.status == "CLEARED" for a in aw18)
    assert all(a.status_norm in ("cleared", "pending") for a in aw18)
    assert by_fy[2018][1].by_status["cleared"] == 8843, by_fy[2018][1].by_status

    # All eight header layouts land in one shape.
    assert all(a.mocs_id == "" for a in aw13 + by_fy[2014][0][:50])
    assert by_fy[2024][0][0].mocs_id.startswith("FY24 "), by_fy[2024][0][0]
    assert by_fy[2016][0][0].fiscal_year == 2016  # FY2016 has no Fiscal Year column
    assert by_fy[2014][0][0].council_member  # header said "Council Member"
    assert by_fy[2015][0][0].council_member  # header said "Council Members"

    # Dirty keys: EINs keep leading zeros, and the one FY2015 EIN with an embedded
    # zero-width space comes out clean.
    eins = [a.ein for _, (aw, _) in sorted(by_fy.items()) for a in aw]
    assert all(len(e) == 9 for e in eins if e), \
        sorted({e for e in eins if e and len(e) != 9})[:5]
    assert any(e.startswith("0") for e in eins)

    # Org names arrive with leading spaces in the source; they must not.
    assert not any(a.legal_name != a.legal_name.strip()
                   for _, (aw, _) in by_fy.items() for a in aw)

    print("demo: OK")
    return results


def print_summary(results):
    hdr = (f"{'FY':<6}{'awards':>8}{'total $':>18}{'cleared $':>18}{'pending $':>16}"
           f"{'other':>6}{'strip':>6}  printed total")
    print(hdr)
    print("-" * len(hdr))
    for aw, r in results:
        if r.skipped:
            print(f"{r.fiscal_year:<6}{'-':>8}  SKIPPED: {r.skipped}")
            continue
        verdict = reconcile(aw, r)[0]
        print(f"{r.fiscal_year:<6}{r.n_awards:>8}{_usd(total_decimal(aw)):>18}"
              f"{_usd(r.amount_by_status['cleared']):>18}"
              f"{_usd(r.amount_by_status['pending']):>16}{r.by_status.get('other', 0):>6}"
              f"{r.n_stripped:>6}  {verdict}")

    strippers = [r for _, r in results if r.n_stripped]
    print("\nYears containing embedded summary / orphan rows: "
          + (", ".join(f"FY{r.fiscal_year} ({r.n_stripped})" for r in strippers) or "none"))
    for r in strippers:
        print(f"\n  FY{r.fiscal_year} -- stripped rows:")
        for s in r.stripped:
            print(f"    row {s['row']:>6}  {s['kind']:<16} {s['cells']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="write data/fyNN/expense_disclosure/ for every year")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any committed output or the manifest is stale")
    ap.add_argument("--manifest", action="store_true", help="write source/.../MANIFEST.csv")
    ap.add_argument("--retrieved", help="YYYY-MM-DD download date for new/changed files")
    ap.add_argument("--verified", help="YYYY-MM-DD date unchanged files were downloaded again "
                    "and found byte-identical; becomes their retrieved date")
    a = ap.parse_args(argv)

    if not (a.write or a.check or a.manifest):
        results = demo()
        print()
        print_summary(results)
        return 0

    results = parse_all()
    files = outputs(results)
    for d in (a.retrieved, a.verified):
        if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            raise SystemExit(f"not a YYYY-MM-DD date: {d!r}")
    if a.manifest or a.check:
        previous = read_manifest()
        rows = manifest_rows(results, retrieved=a.retrieved, previous=previous,
                             verified=a.verified)
        files[MANIFEST] = manifest_text(rows)
    if a.check:
        bad = stale(files)
        for path, why in bad:
            print(f"STALE ({why}): {os.path.relpath(path, ROOT)}")
        print(f"check: {len(files)} files, {len(bad)} stale")
        return 1 if bad else 0
    if not a.write:
        files = {MANIFEST: files[MANIFEST]}
    gone = superseded_rows(previous, rows) if a.manifest else []
    if gone:
        existing = ""
        if os.path.exists(MANIFEST_HISTORY):
            with open(MANIFEST_HISTORY, encoding="utf-8", newline="") as f:
                existing = f.read()
        files[MANIFEST_HISTORY] = history_text(existing, gone)
    write_files(files)
    for path in sorted(files):
        print(f"wrote {os.path.relpath(path, ROOT)}")
    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
