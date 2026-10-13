#!/usr/bin/env python3
"""Adversarial audit of the Council expense-disclosure dataset (data/fyNN/expense_disclosure/).

Why this exists: the Schedule C data shipped defects that its own checks could not see -- member
surnames bled into names, prose in the name column, truncated names, cents shifted into the
purpose column, rows merged across boundaries, wrong EINs, a positional cell shift because xlsx
omits empty cells, a header matched exactly that made a whole year invisible, and tests that could
not fail. This script asks every one of those questions again of the disclosure dataset, plus the
questions a spreadsheet source raises that a PDF source does not.

Independence. The dataset is produced by code/parse_expense_disclosure.py (zipfile + ElementTree
for .xlsx, xlrd for FY2013's .xls). Re-using that parser would audit nothing, so this script never
imports it. Workbooks are re-read a second way:
  * .xlsx: openpyxl (a separate OOXML implementation), twice -- cached values and formulas -- plus
    regex over the raw sheet XML for sheet-level facts (hidden rows, merged cells, autofilter);
  * FY2013 .xls: xlrd with formatting_info=True and its row-level API. The parser also uses xlrd,
    so FY2013 is only PARTLY independent (same library, different code path). Said in the report.
Headers are mapped here by this script's own keyword rules, not the parser's HEADER_MAP.

Each question in QUESTIONS names the earlier defect class it re-asks, whether it was harvested from
an earlier audit or is new, and whether its method is independent of the parser. A check whose
only evidence is the parser's own output is labeled `circular` in the report rather than counted
as verification.

Run:
  python3 code/audit_disclosure.py            print the findings table
  python3 code/audit_disclosure.py --write    write data/DISCLOSURE-AUDIT.md
  python3 code/audit_disclosure.py --check    exit 1 if data/DISCLOSURE-AUDIT.md is stale

Needs openpyxl and xlrd (code/requirements.txt). No network.
"""

import argparse
import collections
import csv
import datetime
import glob
import importlib.util
import inspect
import os
import re
import sys
import unicodedata
import warnings
import zipfile
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "source", "expense-funding-disclosure")
DATA_DIR = os.path.join(ROOT, "data")
REPORT = os.path.join(DATA_DIR, "DISCLOSURE-AUDIT.md")
MANIFEST = os.path.join(SRC_DIR, "MANIFEST.csv")

CITY_EIN = "136400434"
MAX_EXAMPLES = 6

FIELDS = ["fiscal_year", "mocs_id", "source", "council_member", "legal_name", "ein", "status",
          "status_norm", "amount", "agency", "program_name", "address1", "address2", "city",
          "state", "postal_code", "purpose", "fiscal_conduit", "fiscal_conduit_ein",
          "source_file", "source_row"]
# Fields that come from a workbook cell (the rest are derived by the parser).
CELL_FIELDS = ["mocs_id", "source", "council_member", "legal_name", "ein", "status", "amount",
               "agency", "program_name", "address1", "address2", "city", "state",
               "postal_code", "purpose", "fiscal_conduit", "fiscal_conduit_ein"]


# =============================================================== independent header mapping

def canon_header(text):
    """Map a printed column header to a field by keyword, independently of the parser's table.
    Returns None for a header this rule does not recognise (reported, never guessed)."""
    h = re.sub(r"[^a-z0-9 ]+", " ", str(text or "").lower())
    h = " ".join(h.split())
    if not h:
        return None
    words = set(h.split())
    if "mocs" in words:
        return "mocs_id"
    if h == "fiscal year":
        return "fiscal_year_col"
    if "conduit" in words or h.startswith("fc "):
        return "fiscal_conduit_ein" if ("ein" in words or "tax" in words) else "fiscal_conduit"
    if "legal" in words and "name" in words:
        return "legal_name"
    if h in ("ein", "tax id"):
        return "ein"
    if "council" in words and ("member" in words or "members" in words):
        return "council_member"
    if h == "status":
        return "status"
    if words & {"amount"}:
        return "amount"
    if h == "agency":
        return "agency"
    if "program" in words:
        return "program_name"
    if "address" in words:
        return "address2" if "2" in words else "address1"
    if h == "address 1":
        return "address1"
    if h == "city":
        return "city"
    if h == "state":
        return "state"
    if "zip" in words or "postal" in words:
        return "postal_code"
    if "purpose" in words:
        return "purpose"
    if h == "source":
        return "source"
    return None


# =============================================================== independent readers

class Cell:
    """One non-empty cell as the independent reader sees it."""
    __slots__ = ("formula", "is_date", "kind", "number_format", "value")

    def __init__(self, value, kind, number_format="", is_date=False, formula=None):
        self.value = value          # python value: str / int / float / datetime
        self.kind = kind            # "s" text, "n" number, "e" error, "b" bool, "d" date
        self.number_format = number_format
        self.is_date = is_date
        self.formula = formula      # formula text if the cell holds one, else None


class Sheet:
    """Everything the audit needs from one workbook, read without the parser."""

    def __init__(self, path):
        self.path = path
        self.file = os.path.basename(path)
        self.fy = int(re.search(r"FY(\d{4})", self.file).group(1))
        self.rows = {}              # row number -> {column index (1-based): Cell}
        self.header = {}            # column index -> header text
        self.sheets = []            # [(name, state, max_row)]
        self.hidden_rows = []
        self.hidden_cols = []
        self.merged = []
        self.autofilter = ""
        self.phonetic_runs = 0
        self.max_row = 0
        self.independent = True
        if path.endswith(".xls"):
            self._read_xls()
        else:
            self._read_xlsx()

    # ---- .xlsx via openpyxl + raw XML
    def _read_xlsx(self):

        import openpyxl  # noqa: PLC0415 -- lazy: --help and the pure detectors need no openpyxl
        warnings.simplefilter("ignore")  # openpyxl warns about unrelated styling extensions
        vals = openpyxl.load_workbook(self.path, read_only=True, data_only=True)
        forms = openpyxl.load_workbook(self.path, read_only=True, data_only=False)
        for ws in vals.worksheets:
            self.sheets.append((ws.title, ws.sheet_state, ws.max_row or 0))
        ws, wf = vals.worksheets[0], forms.worksheets[0]
        formula_at = {}
        for row in wf.iter_rows():
            for c in row:
                if getattr(c, "data_type", None) == "f" or (
                        isinstance(c.value, str) and c.value.startswith("=")):
                    formula_at[(c.row, c.column)] = str(c.value)
        for row in ws.iter_rows():
            for c in row:
                if c.value is None or not hasattr(c, "column"):
                    continue
                kind = {"s": "s", "n": "n", "e": "e", "b": "b", "d": "d", "inlineStr": "s",
                        "str": "s"}.get(c.data_type, c.data_type)
                if c.is_date:
                    kind = "d"
                self.rows.setdefault(c.row, {})[c.column] = Cell(
                    c.value, kind, c.number_format or "", bool(c.is_date),
                    formula_at.get((c.row, c.column)))
                self.max_row = max(self.max_row, c.row)
        vals.close()
        forms.close()
        z = zipfile.ZipFile(self.path)
        sheet_xml = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
        raw = z.read(sheet_xml[0]).decode("utf-8", "replace")
        self.hidden_rows = [int(m) for m in re.findall(r'<row [^>]*?r="(\d+)"[^>]*?hidden="(?:1|true)"', raw)]
        self.hidden_cols = re.findall(r'<col [^>]*?hidden="(?:1|true)"[^>]*?/>', raw)
        self.merged = re.findall(r'<mergeCell ref="([^"]+)"', raw)
        af = re.search(r'<autoFilter ref="([^"]+)"', raw)
        self.autofilter = af.group(1) if af else ""
        last = re.findall(r'<row [^>]*?r="(\d+)"', raw)
        self.max_row = max([self.max_row] + [int(x) for x in last])
        if "xl/sharedStrings.xml" in z.namelist():
            self.phonetic_runs = z.read("xl/sharedStrings.xml").count(b"<rPh")
        self._header()

    # ---- FY2013 .xls via xlrd's row API with formatting info
    def _read_xls(self):
        import xlrd  # noqa: PLC0415
        self.independent = False  # same library as the parser (different code path)
        book = xlrd.open_workbook(self.path, formatting_info=True)
        for s in book.sheets():
            self.sheets.append((s.name, {0: "visible", 1: "hidden", 2: "veryHidden"}.get(
                s.visibility, str(s.visibility)), s.nrows))
        sh = book.sheet_by_index(0)
        self.hidden_rows = [r + 1 for r, i in sh.rowinfo_map.items() if i.hidden]
        self.hidden_cols = [c for c, i in sh.colinfo_map.items() if i.hidden]
        self.merged = [str(m) for m in sh.merged_cells]
        for r in range(sh.nrows):
            types, values = sh.row_types(r), sh.row_values(r)
            for ci, (t, v) in enumerate(zip(types, values)):
                if t in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                    continue
                kind = {xlrd.XL_CELL_TEXT: "s", xlrd.XL_CELL_NUMBER: "n", xlrd.XL_CELL_DATE: "d",
                        xlrd.XL_CELL_BOOLEAN: "b", xlrd.XL_CELL_ERROR: "e"}[t]
                xf = book.xf_list[sh.cell_xf_index(r, ci)]
                fmt = book.format_map[xf.format_key].format_str
                if kind == "n" and v == int(v):
                    v = int(v)
                self.rows.setdefault(r + 1, {})[ci + 1] = Cell(v, kind, fmt, kind == "d")
                self.max_row = max(self.max_row, r + 1)
        self._header()

    def _header(self):
        first = min(self.rows) if self.rows else 1
        self.header_row = first
        self.header = {ci: str(c.value) for ci, c in self.rows.get(first, {}).items()}
        self.col_field = {ci: canon_header(h) for ci, h in self.header.items()}
        self.field_col = {f: ci for ci, f in self.col_field.items() if f}

    def get(self, rn, field):
        ci = self.field_col.get(field)
        return self.rows.get(rn, {}).get(ci) if ci else None


def text_of(cell):
    """The audit's own rendering of a cell to the dataset's text convention: a soft hyphen is a
    hyphen (dropped beside a '-' or '/'), other invisible format characters (category Cf)
    deleted, whitespace runs to one space, integral numbers without '.0'."""
    if cell is None:
        return ""
    v = cell.value
    if isinstance(v, bool):
        return str(v).upper()
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v)
    # The dataset's documented convention (DATA-DICTIONARY): a soft hyphen (U+00AD) is a hyphen,
    # unless a '-' or '/' already stands next to it (then it adds nothing); every other
    # invisible format character, Unicode category Cf (zero-width space, LRM, BOM), is deleted.
    # Written here from the documented rule, not imported from the parser (issue #68).
    s = re.sub("[-/]\u00ad+|\u00ad+(?=[-/])", lambda m: m.group(0).replace("\u00ad", ""), s)
    s = re.sub("\u00ad+", "-", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Cf")
    return " ".join(s.split())


def excel_serial(dt, epoch=None):
    """datetime -> Excel 1900-system serial day number (what the sheet XML stores)."""
    base = epoch or datetime.datetime(1899, 12, 30)
    d = dt - base
    return d.days if not d.seconds else d.days + d.seconds / 86400


def number_of(cell):
    """float value of a numeric-looking cell, or None."""
    if cell is None:
        return None
    if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
        return float(cell.value)
    try:
        return float(str(cell.value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def is_award_row(sheet, rn):
    """The audit's own row rule: a designation has a numeric amount and either a clearance
    status or an organization name. Everything else non-empty is a summary/footer row."""
    status = text_of(sheet.get(rn, "status")).lower()
    name = text_of(sheet.get(rn, "legal_name"))
    amt = number_of(sheet.get(rn, "amount"))
    return amt is not None and (status in ("cleared", "pending") or bool(name))


# =============================================================== loading

def load_csv_rows(data_dir=DATA_DIR):
    rows = []
    for f in sorted(glob.glob(os.path.join(data_dir, "fy*", "expense_disclosure", "*_expense_awards.csv"))):
        with open(f, newline="", encoding="utf-8") as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def load_sheets(src_dir=SRC_DIR):
    paths = sorted(glob.glob(os.path.join(src_dir, "funded_disclosure_FY*.xls*")))
    return {s.fy: s for s in (Sheet(p) for p in paths)}


def stripped_rows_listed(fy, data_dir=DATA_DIR):
    """Row numbers the parser's reconciliation report lists as stripped (parsed from its text)."""
    p = os.path.join(data_dir, f"fy{fy % 100:02d}", "expense_disclosure",
                     f"fy{fy % 100:02d}_expense_reconciliation.txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        txt = fh.read()
    m = re.search(r"Stripped rows \(\d+\):\n(.*?)\n\n", txt, re.S)
    return sorted(int(x) for x in re.findall(r"^\s+row\s+(\d+)\s", m.group(1), re.M)) if m else []


def read_manifest(path=MANIFEST):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# =============================================================== result helpers

def ref(r):
    return f"{r['source_file']}:{r['source_row']}"


def result(status, count=0, examples=(), note=""):
    return {"status": status, "count": count, "examples": list(examples)[:MAX_EXAMPLES],
            "note": note}


def flagged(rows, pred, show, note="", status_if_any="finding"):
    hits = [r for r in rows if pred(r)]
    return result(status_if_any if hits else "pass", len(hits), [show(r) for r in hits], note)


def short(s, n=70):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


# =============================================================== text detectors (pure)

LEGAL_SUFFIX = r"(?:Inc|Incorporated|Corp|Corporation|LLC|Ltd|L\.P|LP|Co)\.?"
PROSE = re.compile(r"\b(to provide|will be used|funds? will|funding (?:will|to|for the)|in order to|"
                   r"to support the|this funding|to fund)\b", re.I)
# ", The" is the Council's inverted-article convention ("Museum, The"), not a cut.
TRAILING_CUT = re.compile(r"(?:\s(?:and|of|for|&|to|in|at)|[,&/\-(])$", re.I)
# A cents tail at the very start (".00 Funds will..."), or a field that is ONLY a money amount.
# "$500 to every PTA" is prose that mentions money, not a shifted amount.
AMOUNTISH = re.compile(r"^(?:\.\d{2}|\d+\.\d{2})(?:\s|$)|^\$?\d[\d,]*(?:\.\d+)?$")
INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u00ad\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MOJIBAKE = re.compile("Ã.|â€|Â[^\\w]|\ufffd")


def unbalanced(s):
    return s.count("(") != s.count(")") or s.count("[") != s.count("]") or s.count('"') % 2 == 1


def looks_truncated(s):
    return bool(s) and (unbalanced(s) or bool(TRAILING_CUT.search(s)))


_SUFFIX_SPLIT = re.compile(r"\b(?:Inc|Incorporated|Corp|Corporation|LLC|Ltd)\b\.?", re.I)


def merged_name(s):
    """Two organizations glued into one cell: two legal-entity suffixes, each preceded by a
    segment of at least two real words (3+ letters). 'Education and Assistance Corporation
    (EAC), Inc.' and 'Oceanic Hook and Ladder Co. No. 1, Inc.' are one name, not two."""
    if re.search(r"\bd\.?/?b\.?/?a\b|\bf\.?/?k\.?/?a\b|\bc/o\b|\bon behalf of\b", s, re.I):
        return False
    parts = _SUFFIX_SPLIT.split(s)
    if len(parts) < 3:  # fewer than two suffixes
        return False
    # The text after the first suffix must open a NEW name: a capitalized word that is not a
    # connective ('Corporation of Crown Heights, Inc.' is one name).
    second = parts[1].lstrip(" ,;")
    if not re.match(r"[A-Z]", second) or re.match(r"(?:Of|For|And|The)\b", second):
        return False
    wordy = [p for p in parts[:-1] if len(re.findall(r"[A-Za-z]{3,}", p)) >= 2]
    return len(wordy) >= 2


def is_placeholder_ein(e):
    return e in ("000000000", "111111111", "123456789", "999999999", "987654321") or \
        (len(set(e)) == 1 and len(e) == 9)


def canon_name(s):
    s = re.sub("['\u2019\u2018]", "", s.lower())  # "Children's" == "Childrens"
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(the|inc|incorporated|corp|corporation|llc|ltd|co|of|and|for|a)\b", " ", s)
    return " ".join(s.split())


# =============================================================== the questions

QUESTIONS = []


def question(qid, text, defect_class, origin, independent):
    """Register a check. origin: 'harvested' (asked of Schedule C before) or 'new'.
    independent: 'yes' (reads the workbook without the parser), 'partial', or 'circular'
    (only the parser's own output is evidence)."""
    def deco(fn):
        QUESTIONS.append({"id": qid, "question": text, "defect_class": defect_class,
                          "origin": origin, "independent": independent, "fn": fn,
                          # cleandoc + split/join: Python 3.13+ dedents docstrings at
                          # compile time and 3.11 does not; the report must not depend on it.
                          "method": " ".join(inspect.cleandoc(fn.__doc__ or "").split("\n\n")[0].split())})
        return fn
    return deco


# ---------------------------------------------------------------- A. reading the right thing

@question("A1", "Does every workbook have exactly one sheet carrying data, and is it visible "
          "(are we reading the right sheet)?", "multiple sheets / hidden sheet", "new", "yes")
def q_sheets(ctx):
    """Lists every sheet, its visibility and row count with the independent reader; a second
    sheet holding rows, or a hidden data sheet, is a finding."""
    bad = []
    for fy, s in sorted(ctx["sheets"].items()):
        data = [x for x in s.sheets if x[2] > 0]
        if len(data) != 1 or data[0][1] != "visible" or s.sheets[0] != data[0]:
            bad.append(f"{s.file}: {s.sheets}")
    note = "FY2013 .xls has Sheet2/Sheet3 at 0x0; every .xlsx has one sheet."
    return result("finding" if bad else "pass", len(bad), bad, note)


@question("A2", "Are any rows or columns hidden, or any cells merged, in a data sheet?",
          "hidden rows / merged cells", "new", "yes")
def q_hidden_merged(ctx):
    """Raw sheet XML (xlsx) or xlrd formatting info (xls): rows/cols with hidden=1, mergeCell
    elements."""
    bad = []
    for fy, s in sorted(ctx["sheets"].items()):
        if s.hidden_rows or s.hidden_cols or s.merged:
            bad.append(f"{s.file}: hidden rows {s.hidden_rows[:5]} cols {len(s.hidden_cols)} "
                       f"merged {s.merged[:5]}")
    return result("finding" if bad else "pass", len(bad), bad)


@question("A3", "Does every printed header map to a field, and does every field the dataset "
          "claims have a column (no column silently dropped, no year invisible to an exact "
          "header match)?", "header exact-match missed a year (FY2016 invisible) / header drift",
          "harvested", "yes")
def q_headers(ctx):
    """Maps each year's header with this script's own keyword rules; an unmapped header, a
    duplicate mapping, or a missing required field is a finding."""
    bad = []
    required = {"source", "council_member", "legal_name", "ein", "status", "amount"}
    for fy, s in sorted(ctx["sheets"].items()):
        unmapped = [h for ci, h in s.header.items() if not s.col_field.get(ci)]
        dup = [f for f, n in collections.Counter(f for f in s.col_field.values() if f).items() if n > 1]
        missing = required - set(s.field_col)
        if unmapped or dup or missing:
            bad.append(f"{s.file}: unmapped {unmapped} dup {dup} missing {sorted(missing)}")
    return result("finding" if bad else "pass", len(bad), bad)


@question("A4", "Does any non-empty cell sit in a column with no header (data the parser "
          "cannot name and would drop)?", "silent column loss", "new", "yes")
def q_unheaded(ctx):
    """Every non-empty cell below the header whose column has no header text."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        for rn, cells in sorted(s.rows.items()):
            if rn == s.header_row:
                continue
            for ci, c in cells.items():
                if ci not in s.header and text_of(c):
                    hits.append(f"{s.file}:{rn} col {ci} = {short(text_of(c), 40)!r}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("A5", "Do the sheet's row counts reconcile: rows after the header = CSV award rows + "
          "stripped rows + blank rows, and do the audit's own award rows equal the CSV rows "
          "one-for-one by row number?", "silent row loss / row cap (#42)", "harvested", "yes")
def q_row_accounting(ctx):
    """Classifies every sheet row with the audit's own rule (numeric amount and a status or a
    name) and compares the set of award row numbers with the CSV's source_row set, and the
    non-award non-empty rows with the rows the reconciliation report lists as stripped."""
    bad = []
    by_fy = ctx["csv_by_fy"]
    for fy, s in sorted(ctx["sheets"].items()):
        mine = {rn for rn in s.rows if rn != s.header_row and is_award_row(s, rn)}
        other = {rn for rn in s.rows if rn != s.header_row and rn not in mine
                 and any(text_of(c) for c in s.rows[rn].values())}
        theirs = {int(r["source_row"]) for r in by_fy.get(fy, [])}
        listed = set(stripped_rows_listed(fy, ctx["data_dir"]) or [])
        if mine != theirs or other != listed:
            bad.append(f"{s.file}: audit awards {len(mine)} vs CSV {len(theirs)} "
                       f"(only audit {sorted(mine - theirs)[:5]}, only CSV {sorted(theirs - mine)[:5]}); "
                       f"non-award rows {sorted(other)[:6]} vs listed stripped {sorted(listed)[:6]}")
    n_rows = sum(len(v) for v in by_fy.values())
    return result("finding" if bad else "pass", len(bad), bad,
                  f"{n_rows:,} CSV rows across {len(by_fy)} years checked row-by-row.")


@question("A6", "Does every CSV cell equal the workbook cell it came from, read a second way "
          "(no positional shift, no field written into its neighbour)?",
          "positional cell shift: xlsx omits empty cells (reader_diff)", "harvested", "yes")
def q_cell_by_cell(ctx):
    """For every CSV row, re-reads its source row with the independent reader and compares all
    17 cell-sourced fields: text after whitespace folding, amounts as floats, EINs as digits
    (an 8-digit NUMERIC cell may be left-padded; a text one may not)."""
    mism = collections.Counter()
    ex = []
    n = 0
    for r in ctx["csv"]:
        s = ctx["sheets"][int(r["fiscal_year"])]
        rn = int(r["source_row"])
        for f in CELL_FIELDS:
            c = s.get(rn, f)
            if f not in s.field_col:
                ok = r[f] == ""
            elif f == "amount":
                ok = number_of(c) is not None and float(r[f]) == number_of(c)
            elif f in ("ein", "fiscal_conduit_ein"):
                t = text_of(c)
                digits = t.replace("-", "") if re.fullmatch(r"\d{2}-\d{7}", t) else t
                if c is not None and c.kind == "n" and digits.isdigit() and len(digits) == 8:
                    digits = digits.zfill(9)
                ok = r[f] == digits
            elif c is not None and c.kind == "d":
                # A date-typed cell (reported by A8): the dataset carries the Excel serial.
                ok = r[f] == str(excel_serial(c.value))
            else:
                ok = r[f] == text_of(c)
            n += 1
            if not ok:
                mism[f] += 1
                if len(ex) < MAX_EXAMPLES:
                    ex.append(f"{ref(r)} {f}: CSV {short(r[f], 30)!r} vs workbook "
                              f"{short(text_of(c), 30)!r}")
    note = f"{n:,} cells compared. Mismatches by field: {dict(mism) or 'none'}."
    return result("finding" if mism else "pass", sum(mism.values()), ex, note)


@question("A7", "Is any EIN or ZIP stored as a NUMBER in the workbook, and did any lose a "
          "leading zero (EIN < 9 digits, ZIP < 5)?", "leading-zero loss / Excel number coercion",
          "harvested", "yes")
def q_numeric_ids(ctx):
    """Counts numeric EIN/FC-EIN/ZIP cells per the independent reader, and lists those whose
    digits are too short to be a full EIN/ZIP as stored."""
    short_ids, numeric = [], collections.Counter()
    for fy, s in sorted(ctx["sheets"].items()):
        for rn in s.rows:
            if rn == s.header_row:
                continue
            for f, width in (("ein", 9), ("fiscal_conduit_ein", 9), ("postal_code", 5)):
                c = s.get(rn, f)
                if c is not None and c.kind == "n":
                    numeric[f] += 1
                    if len(text_of(c)) < width:
                        short_ids.append(f"{s.file}:{rn} {f} stored as number {text_of(c)}")
    note = (f"Numeric-stored cells: {dict(numeric)}. A 9-digit numeric EIN keeps its value; only "
            f"an EIN with a leading zero is at risk. The parser re-pads 8-digit numeric EINs and "
            f"lists them in the reconciliation report.")
    return result("finding" if short_ids else "pass", len(short_ids), short_ids, note)


@question("A8", "Is any cell typed as a DATE (an Excel serial) in a column that is not a date?",
          "Excel date coercion", "new", "yes")
def q_date_cells(ctx):
    """Every date-typed or date-formatted cell below the header, by the independent reader."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        for rn, cells in sorted(s.rows.items()):
            if rn == s.header_row:
                continue
            for ci, c in cells.items():
                if c.kind == "d":
                    hits.append(f"{s.file}:{rn} {s.col_field.get(ci) or ci} = {c.value!r} "
                                f"(format {c.number_format!r})")
    return result("finding" if hits else "pass", len(hits), hits,
                  "The CSV carries the serial number as text; the value was almost certainly "
                  "not meant as a date.")


@question("A9", "Does any cell hold a spreadsheet ERROR value (#N/A, #REF!, #VALUE!) that the "
          "dataset publishes as if it were data?", "spreadsheet error as data", "new", "yes")
def q_error_cells(ctx):
    """Error-typed cells (independent reader) and any CSV field equal to an Excel error literal."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        for rn, cells in sorted(s.rows.items()):
            for ci, c in cells.items():
                if c.kind == "e":
                    hits.append(f"{s.file}:{rn} {s.col_field.get(ci)} = {c.value}")
    err = re.compile(r"^#(N/A|REF!|VALUE!|DIV/0!|NAME\?|NUM!|NULL!)$")
    csv_hits = sum(1 for r in ctx["csv"] for f in CELL_FIELDS if err.match(r[f]))
    return result("finding" if hits else "pass", len(hits), hits,
                  f"{csv_hits} CSV cells carry an Excel error literal verbatim: kept as published "
                  f"text by decision (issue #71), counted by the validator, never read as a value.")


@question("A10", "Is any amount computed by an in-cell formula, and does the CSV carry the "
          "formula's cached result (never the formula text, never a stale value)?",
          "formula cells / derived amounts", "new", "yes")
def q_formulas(ctx):
    """Formula cells per column (openpyxl, data_only=False) and their cached values (data_only=
    True) against the CSV amount for the same row."""
    per_col, bad = collections.Counter(), []
    csv_amt = {(int(r["fiscal_year"]), int(r["source_row"])): float(r["amount"]) for r in ctx["csv"]}
    for fy, s in sorted(ctx["sheets"].items()):
        for rn, cells in s.rows.items():
            for ci, c in cells.items():
                if c.formula:
                    f = s.col_field.get(ci) or str(ci)
                    per_col[(fy, f)] += 1
                    if f == "amount" and (fy, rn) in csv_amt and csv_amt[(fy, rn)] != number_of(c):
                        bad.append(f"{s.file}:{rn} {c.formula} cached {c.value} CSV {csv_amt[(fy, rn)]}")
                    if f != "amount" and rn != s.header_row and (fy, rn) in csv_amt:
                        bad.append(f"{s.file}:{rn} formula in {f}: {c.formula} -> {short(text_of(c), 30)!r}")
    note = "Formula cells by (year, field): " + ", ".join(
        f"FY{fy} {f} {n}" for (fy, f), n in sorted(per_col.items()))
    return result("finding" if bad else "pass", len(bad), bad, note)


@question("A11", "Do shared strings carry phonetic runs (<rPh>) that a naive reader would glue "
          "into the text?", "reader concatenation artifact", "new", "yes")
def q_phonetic(ctx):
    """Counts <rPh> elements in each workbook's sharedStrings.xml."""
    hits = [f"{s.file}: {s.phonetic_runs}" for s in ctx["sheets"].values() if s.phonetic_runs]
    return result("finding" if hits else "pass", len(hits), hits)


@question("A12", "Are there rows below the end of the sheet's autofilter range (rows appended "
          "after the Council last set up the sheet)?", "post-adoption additions / appended rows",
          "new", "yes")
def q_autofilter(ctx):
    """Compares the autoFilter ref's last row with the last data row, per workbook. Informational:
    appended rows are not wrong, but they are where post-adoption designations live."""
    info = []
    for fy, s in sorted(ctx["sheets"].items()):
        m = re.search(r"(\d+)$", s.autofilter or "")
        if m and int(m.group(1)) < s.max_row:
            info.append(f"{s.file}: autofilter ends row {m.group(1)}, data to row {s.max_row} "
                        f"({s.max_row - int(m.group(1))} rows below)")
    return result("info" if info else "pass", len(info), info)


@question("A13", "Does the Fiscal Year column, where printed, agree with the year in the "
          "filename on every row?", "wrong-year rows", "new", "yes")
def q_fy_column(ctx):
    """Independent reader's Fiscal Year cell vs the filename year, every award row."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        if "fiscal_year_col" not in s.field_col:
            continue
        for rn in s.rows:
            if rn == s.header_row or not is_award_row(s, rn):
                continue
            v = text_of(s.get(rn, "fiscal_year_col"))
            if v and re.sub(r"\D", "", v)[-4:] not in (str(fy), ) and v not in (str(fy), f"FY{fy % 100:02d}"):
                hits.append(f"{s.file}:{rn} Fiscal Year {v!r}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("A14", "Is any amount stored as TEXT rather than a number (e.g. '$5,000')?",
          "Excel text-number coercion", "new", "yes")
def q_amount_text(ctx):
    """Award rows whose amount cell is a string cell per the independent reader."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        for rn in s.rows:
            if rn != s.header_row and is_award_row(s, rn):
                c = s.get(rn, "amount")
                if c is not None and c.kind == "s":
                    hits.append(f"{s.file}:{rn} amount text {c.value!r}")
    return result("finding" if hits else "pass", len(hits), hits)


# ---------------------------------------------------------------- B. totals

@question("B1", "Does the independent reader's sum, per fiscal year and status, equal the CSV "
          "sum to the cent (no row dropped, doubled or mis-statused)?",
          "silent loss / circular validation", "harvested", "yes")
def q_totals(ctx):
    """Decimal sums of the CSV vs float->Decimal sums of the workbook cells read independently,
    grouped by (fiscal_year, status folded to lower case)."""
    mine, theirs = collections.Counter(), collections.Counter()
    for r in ctx["csv"]:
        theirs[(int(r["fiscal_year"]), r["status_norm"])] += Decimal(r["amount"])
    for fy, s in ctx["sheets"].items():
        for rn in s.rows:
            if rn != s.header_row and is_award_row(s, rn):
                st = text_of(s.get(rn, "status")).lower()
                st = st if st in ("cleared", "pending") else "other"
                mine[(fy, st)] += Decimal(repr(number_of(s.get(rn, "amount"))))
    bad = [f"FY{k[0]} {k[1]}: audit {mine[k]} vs CSV {theirs[k]}"
           for k in sorted(set(mine) | set(theirs)) if round(mine[k], 2) != round(theirs[k], 2)]
    return result("finding" if bad else "pass", len(bad), bad,
                  f"{len(set(mine) | set(theirs))} (year, status) cells compared.")


@question("B2", "Does MANIFEST.csv's award_rows and total_amount agree with the CSV?",
          "provenance drift", "harvested", "circular")
def q_manifest(ctx):
    """CSV row count and Decimal sum per workbook vs MANIFEST.csv. CIRCULAR: the parser wrote
    both; this only proves they were written from the same run. B1 is the independent check."""
    bad = []
    by_file = collections.defaultdict(list)
    for r in ctx["csv"]:
        by_file[r["source_file"]].append(r)
    for m in ctx["manifest"]:
        if not m["file"].startswith("funded_disclosure"):
            continue
        rows = by_file.get(m["file"], [])
        tot = sum((Decimal(r["amount"]) for r in rows), Decimal(0))
        if len(rows) != int(m["award_rows"]) or tot != Decimal(m["total_amount"]):
            bad.append(f"{m['file']}: CSV {len(rows)} rows {tot} vs manifest {m['award_rows']} {m['total_amount']}")
    return result("finding" if bad else "pass", len(bad), bad)


@question("B3", "Does any award row equal a footer/subtotal of other rows: the year total, or "
          "the total of its own source, agency or council member?",
          "summary/footer rows leaking in as awards", "harvested", "yes")
def q_subtotal_rows(ctx):
    """For each year, sums the other rows by year, source, agency and member; an award equal to
    a group's total excluding itself (group of 2+ rows) is a candidate subtotal. Plus any name
    containing 'total'."""
    hits = []
    for fy, rows in sorted(ctx["csv_by_fy"].items()):
        amt = [Decimal(r["amount"]) for r in rows]
        year_total = sum(amt, Decimal(0))
        for key in ("source", "agency", "council_member"):
            groups = collections.defaultdict(list)
            for r, a in zip(rows, amt):
                groups[r[key]].append(a)
            sums = {k: (sum(v, Decimal(0)), len(v)) for k, v in groups.items()}
            for r, a in zip(rows, amt):
                g, n = sums[r[key]]
                if n >= 3 and a == g - a:
                    hits.append(f"{ref(r)} {a} = rest of {key} {short(r[key], 30)!r}")
        for r, a in zip(rows, amt):
            if a == year_total - a or re.search(r"\b(sub)?total\b", r["legal_name"], re.I):
                hits.append(f"{ref(r)} {short(r['legal_name'], 40)!r} {a}")
    return result("info" if hits else "pass", len(hits), hits,
                  "Candidates only. Every one listed names an organization and carries an EIN, so "
                  "each reads as a real designation that happens to equal the rest of its group "
                  "(e.g. a lead organization plus partners); a footer would have neither. "
                  "No legal_name contains 'total'." if hits and all(
                      "total" not in h.lower() for h in hits) else "")


@question("B4", "Where the workbook prints a total of its own, does the independent sum equal "
          "it; and is any figure the Council did NOT print described as the Council's?",
          "derived figure attributed to the Council", "harvested", "yes")
def q_printed_totals(ctx):
    """Every typed or formula number on a non-award row, read independently, with the label on
    its row; the 'New Total' / 'Master List Total' style labels are compared with the
    independent award sum. Reports which years print a total at all."""
    out, bad = [], []
    for fy, s in sorted(ctx["sheets"].items()):
        award_sum = sum((Decimal(repr(number_of(s.get(rn, "amount")))) for rn in s.rows
                         if rn != s.header_row and is_award_row(s, rn)), Decimal(0))
        for rn, cells in sorted(s.rows.items()):
            if rn == s.header_row or is_award_row(s, rn):
                continue
            label = " ".join(text_of(c) for c in cells.values() if isinstance(c.value, str))
            for ci, c in cells.items():
                v = number_of(c)
                if v is None or not isinstance(c.value, (int, float)):
                    continue
                if re.search(r"\btotal\b", label, re.I) and s.col_field.get(ci) == "amount":
                    tag = "equals" if Decimal(repr(v)) == award_sum else "DIFFERS from"
                    out.append(f"FY{fy} row {rn} {label!r} {v:,.0f} {tag} independent sum {award_sum:,.0f}")
                    if tag != "equals":
                        bad.append(out[-1])
    years = sorted({o.split()[0] for o in out})
    note = f"Years printing a total in the Amount column: {years or 'none'}. Every other year's sum is our arithmetic, not a Council figure."
    return result("finding" if bad else "pass", len(bad), bad or out, note)


# ---------------------------------------------------------------- C. identifiers

@question("C1", "Is any EIN shorter or longer than 9 digits, non-numeric, or blank?",
          "wrong_ein / leading-zero loss", "harvested", "yes")
def q_ein_shape(ctx):
    """Every CSV ein not matching ^\\d{9}$."""
    return flagged(ctx["csv"], lambda r: not re.fullmatch(r"\d{9}", r["ein"]),
                   lambda r: f"{ref(r)} ein={r['ein']!r} {short(r['legal_name'], 40)!r}")


@question("C2", "Is any fiscal-conduit EIN filled but not 9 digits (e.g. a name in the EIN "
          "column: a column shift in the source)?", "positional shift / wrong_ein", "new", "yes")
def q_fc_ein_shape(ctx):
    """Every non-blank CSV fiscal_conduit_ein not matching ^\\d{9}$."""
    return flagged(ctx["csv"], lambda r: r["fiscal_conduit_ein"] and not re.fullmatch(r"\d{9}", r["fiscal_conduit_ein"]),
                   lambda r: f"{ref(r)} fc_ein={r['fiscal_conduit_ein']!r} fc={short(r['fiscal_conduit'], 30)!r}")


@question("C3", "Is any EIN a placeholder (000000000, 123456789, all one digit)?",
          "wrong_ein", "new", "yes")
def q_placeholder_ein(ctx):
    """Placeholder patterns on ein and fiscal_conduit_ein."""
    return flagged(ctx["csv"], lambda r: is_placeholder_ein(r["ein"]) or is_placeholder_ein(r["fiscal_conduit_ein"]),
                   lambda r: f"{ref(r)} ein={r['ein']}")


@question("C4", "How are rows on the City's own EIN 136400434 used: is it a city body, or an "
          "outside grantee carrying the City's EIN (so an EIN lookup would read many bodies as "
          "one grantee)?", "wrong_ein / City EIN pooling", "harvested", "yes")
def q_city_ein(ctx):
    """Rows with ein == 136400434: count, pending share, distinct legal names, and those whose
    name does not read as a City body (agency, school, precinct, library, DA, borough
    president, community board, NYCHA development, CUNY college...). Listed for a human: a
    City-EIN row for an outside organization may be a pass-through, not a wrong EIN."""
    city = re.compile(r"department|dept\b|\bdoe\b|nycha|houses\b|housing authority|city university|"
                      r"cuny|college|library|borough president|\bbp\b|police|fire|precinct|"
                      r"community board|\bcb\s?\d|commission|office of|mayor|city of new york|"
                      r"new york city|school|\bp\.?s\.?\s?\d|\bi\.?s\.?\s?\d|\bj\.?h\.?s|"
                      r"\bh\.?s\.?\s?\d|academy|district attorney|\bda\b|parks|playground|"
                      r"sanitation|transportation|administration|corrections|health \+ hospitals|"
                      r"hhc|hospital|probation|aging|youth|education|services|council|court|"
                      r"museum|zoo|garden|park\b|center|centre|campus", re.I)
    rows = [r for r in ctx["csv"] if r["ein"] == CITY_EIN]
    odd = [r for r in rows if not city.search(r["legal_name"])]
    names = {canon_name(r["legal_name"]) for r in rows}
    note = (f"{len(rows):,} rows carry the City EIN ({sum(r['status_norm'] == 'pending' for r in rows)} "
            f"pending), under {len(names):,} distinct names. An EIN search for 136400434 is many "
            f"City bodies, not one grantee. Rows whose name does not read as a City body: {len(odd)}.")
    return result("info", len(odd),
                  [f"{ref(r)} {short(r['legal_name'], 45)!r} agency={r['agency']} ${r['amount']}" for r in odd], note)


@question("C5", "Does one EIN carry names that share no significant word, within one fiscal "
          "year (a wrong EIN typed onto an unrelated grantee)?", "wrong_ein", "harvested", "yes")
def q_ein_name_conflict(ctx):
    """Per (fiscal_year, ein), excluding the City EIN: groups of canonical names; flags EINs
    whose names have no word of 4+ letters in common with the year's most frequent name."""
    groups = collections.defaultdict(list)
    for r in ctx["csv"]:
        if r["ein"] and r["ein"] != CITY_EIN:
            groups[(r["fiscal_year"], r["ein"])].append(r)
    hits = []
    for (fy, ein), rows in sorted(groups.items()):
        names = collections.Counter(canon_name(r["legal_name"]) for r in rows)
        if len(names) < 2:
            continue
        top = names.most_common(1)[0][0]
        topw = {w for w in top.split() if len(w) >= 4}
        for n in names:
            if n != top and topw and not (topw & {w for w in n.split() if len(w) >= 4}):
                r = next(x for x in rows if canon_name(x["legal_name"]) == n)
                hits.append(f"FY{fy} EIN {ein}: {short(r['legal_name'], 35)!r} ({ref(r)}) vs {short(top, 35)!r}")
    return result("finding" if hits else "pass", len(hits), hits,
                  "Candidates only: a fiscal sponsor or a renamed body also trips this.")


@question("C6", "Is any MOCS ID duplicated within a year, blank from FY2024 on, or in an "
          "unexpected shape?", "duplicate rows / identifier drift", "new", "yes")
def q_mocs(ctx):
    """Counts (fiscal_year, mocs_id) duplicates, FY2024+ blanks, and shapes other than
    'FYyy NNNNN' (reports the 'FYyyGP NNNNN' variant separately)."""
    c = collections.Counter((r["fiscal_year"], r["mocs_id"]) for r in ctx["csv"] if r["mocs_id"])
    dups = [f"FY{k[0]} {k[1]} x{n}" for k, n in c.items() if n > 1]
    blanks = [ref(r) for r in ctx["csv"] if int(r["fiscal_year"]) >= 2024 and not r["mocs_id"]]
    shapes = collections.Counter(re.sub(r"\d", "9", r["mocs_id"]) for r in ctx["csv"] if r["mocs_id"])
    wrong_year = [ref(r) for r in ctx["csv"] if r["mocs_id"] and not r["mocs_id"].startswith(f"FY{int(r['fiscal_year']) % 100:02d}")]
    bad = dups + blanks + wrong_year
    return result("finding" if bad else "pass", len(bad), bad, f"Shapes: {dict(shapes)}.")


# ---------------------------------------------------------------- D. names and text columns

def _member_values(rows):
    by_fy = collections.defaultdict(set)
    for r in rows:
        if r["council_member"]:
            by_fy[r["fiscal_year"]].add(r["council_member"])
    return by_fy


@question("D1", "Does any legal_name begin with a council member's surname that belongs in "
          "council_member (member_bleed)?", "member_bleed", "harvested", "yes")
def q_member_bleed(ctx):
    """legal_name whose first word(s) equal a member value from the same year (delegations,
    'Speaker' and boroughs excluded) AND whose remainder is printed as the legal name for the
    same EIN elsewhere in the disclosure: the peel is corroborated, so the prefix is a bleed."""
    members = _member_values(ctx["csv"])
    names_by_ein = collections.defaultdict(set)
    for r in ctx["csv"]:
        names_by_ein[r["ein"]].add(canon_name(r["legal_name"]))
    skip = re.compile(r"delegation|speaker|citywide|manhattan|bronx|brooklyn|queens|staten|^cd\d", re.I)
    hits = []
    for r in ctx["csv"]:
        for m in sorted(members[r["fiscal_year"]]):
            if skip.search(m) or not r["legal_name"].startswith(m + " "):
                continue
            rest = canon_name(r["legal_name"][len(m) + 1:])
            if rest and rest in names_by_ein[r["ein"]]:
                hits.append(f"{ref(r)} {short(r['legal_name'], 45)!r} member={r['council_member']!r}")
                break
    return result("finding" if hits else "pass", len(hits), hits)


@question("D2", "Does any legal_name contain purpose prose that belongs in program_name or "
          "purpose (org_prose)?", "org_prose", "harvested", "yes")
def q_org_prose(ctx):
    """Prose markers ('to provide', 'will be used', 'funds will', 'in order to', ...) in
    legal_name."""
    return flagged(ctx["csv"], lambda r: bool(PROSE.search(r["legal_name"])),
                   lambda r: f"{ref(r)} {short(r['legal_name'], 60)!r}")


@question("D3", "Is any legal_name, program_name or source truncated: unbalanced parenthesis or "
          "quote, or ending on a connective ('and', 'of', '&', ',')?",
          "truncated_org_name", "harvested", "yes")
def q_truncated(ctx):
    """looks_truncated() on legal_name, program_name and source. Reported per field; the
    workbook is checked by A6 to hold the same text, so a hit here is as published."""
    per = collections.Counter()
    ex = []
    for r in ctx["csv"]:
        for f in ("legal_name", "program_name", "source"):
            if looks_truncated(r[f]):
                per[f] += 1
                if len(ex) < MAX_EXAMPLES:
                    ex.append(f"{ref(r)} {f}={short(r[f], 55)!r}")
    return result("finding" if per else "pass", sum(per.values()), ex, f"By field: {dict(per)}.")


@question("D4", "Has any text cell hit a fixed length limit (255/256 or 1024 characters), the "
          "signature of an export truncating it?", "truncated_org_name (export limit)", "new", "yes")
def q_length_limits(ctx):
    """Length histogram tail of every text field; cells of exactly 255, 256 or 1024 chars."""
    hits = [f"{ref(r)} {f} len {len(r[f])}" for r in ctx["csv"] for f in CELL_FIELDS
            if len(r[f]) in (255, 256, 1024)]
    longest = max((len(r[f]), f) for r in ctx["csv"] for f in CELL_FIELDS)
    return result("finding" if hits else "pass", len(hits), hits, f"Longest cell: {longest[0]} chars ({longest[1]}).")


@question("D5", "Has an amount or cents bled into purpose, program_name or legal_name "
          "(fy18_aging_shift)?", "fy18_aging_shift (cents in purpose)", "harvested", "yes")
def q_amount_bleed(ctx):
    """purpose / program_name / legal_name that begin with a money-shaped token ('.00',
    '12,500', '$5')."""
    per = collections.Counter()
    ex = []
    for r in ctx["csv"]:
        for f in ("purpose", "program_name", "legal_name"):
            if AMOUNTISH.search(r[f]):
                per[f] += 1
                if len(ex) < MAX_EXAMPLES:
                    ex.append(f"{ref(r)} {f}={short(r[f], 50)!r}")
    return result("finding" if per else "pass", sum(per.values()), ex, f"By field: {dict(per)}.")


@question("D6", "Does any legal_name hold two organizations glued together (two entity "
          "suffixes), or an EIN-shaped number (lost row boundary, org_merged, #52)?",
          "org_merged / lost row boundaries (#52)", "harvested", "yes")
def q_merged(ctx):
    """merged_name() (two Inc/Corp/LLC suffixes with text between, d/b/a and 'for' excluded) or
    a 9-digit / NN-NNNNNNN run inside legal_name."""
    return flagged(ctx["csv"], lambda r: merged_name(r["legal_name"]) or
                   bool(re.search(r"\b\d{9}\b|\b\d{2}-\d{7}\b", r["legal_name"])),
                   lambda r: f"{ref(r)} {short(r['legal_name'], 60)!r}")


@question("D7", "Is any legal_name a fragment: 2 characters or fewer, only a legal suffix, or "
          "starting with punctuation (split_org_name)?",
          "split_org_name", "harvested", "yes")
def q_fragments(ctx):
    """legal_name length <= 2, equal to a bare suffix, or first char punctuation (quotes,
    digits and '(' allowed)."""
    def frag(s):
        # Short acronyms (HHC, OST) and lower-case brand names (hackNY, viBe) are real names;
        # a fragment is 2 characters or fewer, a bare suffix, or a leading punctuation mark.
        return len(s) <= 2 or re.fullmatch(LEGAL_SUFFIX, s, re.I) is not None or \
            bool(re.match(r"[,;.:&\-/]", s))
    return flagged(ctx["csv"], lambda r: frag(r["legal_name"]),
                   lambda r: f"{ref(r)} {r['legal_name']!r}")


@question("D8", "Does any field contain zero-width, soft-hyphen or control characters, or "
          "mojibake (Ã©, â€™)?", "zero-width / invisible chars", "harvested", "yes")
def q_invisible(ctx):
    """INVISIBLE and MOJIBAKE regexes over every field of every CSV row."""
    hits = []
    for r in ctx["csv"]:
        for f in FIELDS:
            if INVISIBLE.search(r[f]) or MOJIBAKE.search(r[f]):
                hits.append(f"{ref(r)} {f}={short(repr(r[f]), 50)}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("D9", "Does any field carry leading/trailing whitespace or a doubled space?",
          "whitespace variants", "new", "yes")
def q_whitespace(ctx):
    """v != v.strip() or '  ' in v, every field."""
    return flagged(ctx["csv"], lambda r: any(v != v.strip() or "  " in v for v in r.values()),
                   lambda r: ref(r))


# ---------------------------------------------------------------- E. amounts

@question("E1", "Is any amount zero, negative, or non-numeric?", "amount sanity", "new", "yes")
def q_amount_sign(ctx):
    """Decimal(amount) <= 0, or unparseable."""
    def bad(r):
        try:
            return Decimal(r["amount"]) <= 0
        except Exception:  # noqa: BLE001 -- an unparseable amount IS the finding
            return True
    return flagged(ctx["csv"], bad, lambda r: f"{ref(r)} amount={r['amount']!r}")


@question("E2", "Does any amount carry fractional cents (more than 2 decimals) or float "
          "residue (65469.00000000001)?", "float rounding on cents", "harvested", "yes")
def q_subcent(ctx):
    """Amount text with more than two decimal places. Published as the workbook holds them;
    listed so a reader knows these are not whole cents."""
    hits = [r for r in ctx["csv"] if "." in r["amount"] and len(r["amount"].split(".")[1]) > 2]
    by_fy = collections.Counter(r["fiscal_year"] for r in hits)
    residue = [r for r in hits if re.search(r"\.\d*(?:0{5,}|9{5,})\d$", r["amount"])]
    live = [r for r in residue
            if (c := ctx["sheets"][int(r["fiscal_year"])].get(int(r["source_row"]), "amount")) is not None
            and c.formula]
    sample = ", ".join(ref(r) + " " + r["amount"] for r in residue[:3])
    return result("finding" if hits else "pass", len(hits),
                  [f"{ref(r)} {r['amount']}" for r in hits],
                  f"By year: {dict(sorted(by_fy.items()))}. {len(residue)} are binary float residue "
                  f"({sample}); {len(live)} of those is still a live formula in the workbook.")


@question("E3", "Is any single designation implausibly large for a discretionary award (over "
          "$5M), the signature of a total typed into a row?", "summary rows as awards", "new", "yes")
def q_outliers(ctx):
    """Amounts over $5,000,000, listed for a human. Informational."""
    big = sorted((r for r in ctx["csv"] if Decimal(r["amount"]) > 5_000_000),
                 key=lambda r: -Decimal(r["amount"]))
    return result("info" if big else "pass", len(big),
                  [f"{ref(r)} ${Decimal(r['amount']):,.0f} {short(r['legal_name'], 40)!r}" for r in big])


# ---------------------------------------------------------------- F. duplicates

@question("F1", "Are any two rows identical in every published field except their row number "
          "(and, from FY2024, are any identical except for the MOCS ID)?",
          "duplicate rows (internal_dups)", "harvested", "yes")
def q_exact_dups(ctx):
    """Groups CSV rows on every field except source_row. Separately, FY2024+ groups identical
    except for mocs_id, which the Council numbered as distinct designations."""
    key = [f for f in FIELDS if f != "source_row"]
    groups = collections.defaultdict(list)
    for r in ctx["csv"]:
        groups[tuple(r[f] for f in key)].append(r)
    dup = [g for g in groups.values() if len(g) > 1]
    extra = sum(len(g) - 1 for g in dup)
    money = sum(Decimal(g[0]["amount"]) * (len(g) - 1) for g in dup)
    years = sorted({g[0]["fiscal_year"] for g in dup})
    key2 = [f for f in key if f != "mocs_id"]
    g2 = collections.defaultdict(list)
    for r in ctx["csv"]:
        if int(r["fiscal_year"]) >= 2024:
            g2[tuple(r[f] for f in key2)].append(r)
    mocs_only = [g for g in g2.values() if len(g) > 1]
    return result("finding" if dup else "pass", len(dup),
                  [f"{' & '.join(ref(r) for r in g)} {short(g[0]['legal_name'], 30)!r} ${g[0]['amount']}" for g in dup],
                  f"{len(dup)} groups, {extra} surplus rows, ${money:,} if they were double entries, "
                  f"FY{years[0] if years else '-'}–FY{years[-1] if years else '-'}. From FY2024, "
                  f"{len(mocs_only)} more groups ({sum(len(g) - 1 for g in mocs_only)} surplus rows) are "
                  f"identical except for distinct MOCS IDs, i.e. numbered as separate designations. "
                  f"Whether the earlier repeats are real is a judgment for a human; every row is kept.")


@question("F2", "Do (EIN, amount, member, source, program) repeat within a year with only "
          "purpose/address/status differing?", "duplicate rows / double count", "harvested", "yes")
def q_soft_dups(ctx):
    """Groups on (fiscal_year, ein, amount, council_member, source, program_name); groups of
    2+ that are NOT exact duplicates (F1)."""
    full = [f for f in FIELDS if f not in ("source_row", "mocs_id")]
    groups = collections.defaultdict(list)
    for r in ctx["csv"]:
        groups[(r["fiscal_year"], r["ein"], r["amount"], r["council_member"], r["source"], r["program_name"])].append(r)
    soft = [g for g in groups.values() if len(g) > 1 and len({tuple(r[f] for f in full) for r in g}) > 1]
    return result("info" if soft else "pass", len(soft),
                  [f"{' & '.join(ref(r) for r in g[:3])} {short(g[0]['legal_name'], 30)!r} ${g[0]['amount']}" for g in soft])


# ---------------------------------------------------------------- G. controlled vocabularies

def _variants(values):
    groups = collections.defaultdict(set)
    for v in sorted(values):
        groups[re.sub(r"[^a-z0-9]", "", v.lower())].add(v)
    return sorted(sorted(g) for g in groups.values() if len(g) > 1)


@question("G1", "Do status values vary in case or spelling, and does status_norm agree with "
          "status on every row?", "status drift", "new", "yes")
def q_status(ctx):
    """Distinct raw statuses per year; any row whose status_norm is not the folded status."""
    raw = collections.Counter((r["fiscal_year"], r["status"]) for r in ctx["csv"])
    bad = [ref(r) for r in ctx["csv"]
           if r["status_norm"] != (r["status"].strip().lower() if r["status"].strip().lower() in ("cleared", "pending") else "other")]
    odd = sorted({f"FY{fy} {s!r}" for (fy, s) in raw if s not in ("Cleared", "Pending")})
    return result("finding" if bad else "pass", len(bad), bad, f"Non-title-case raw statuses: {odd or 'none'}.")


@question("G2", "Does the same funding stream (source) appear under spelling variants, within "
          "or across years (case, hyphen, a lost closing parenthesis)?",
          "source spelling drift", "new", "yes")
def q_source_variants(ctx):
    """Groups distinct source values that are equal after removing case and punctuation."""
    v = _variants({r["source"] for r in ctx["csv"]})
    return result("finding" if v else "pass", len(v), [" | ".join(g) for g in v],
                  "These split one stream's totals across two names in any group-by-source.")


@question("G3", "Does the same council member appear under spelling variants, or is a value not "
          "a member at all (a district label, a borough delegation spelled two ways, several "
          "names in one cell)?", "member identity ambiguity (#51)", "harvested", "partial")
def q_member_values(ctx):
    """Variant groups of council_member (case/punctuation), and values shaped like a district
    ('CD28'), with digits, '/', '&' or ' and '. No Council roster by year exists in this repo, so
    whether a surname was a sitting member that year cannot be checked here (partial)."""
    vals = {r["council_member"] for r in ctx["csv"] if r["council_member"]}
    v = [" | ".join(g) for g in _variants(vals)]
    odd = sorted(x for x in vals if re.search(r"\d|/|&|\band\b|,", x))
    deleg = sorted(x for x in vals if re.search(r"deleg", x, re.I))
    blank = collections.Counter(r["fiscal_year"] for r in ctx["csv"] if not r["council_member"])
    hits = v + [f"not a surname: {x!r}" for x in odd]
    return result("finding" if hits else "pass", len(hits), hits,
                  f"Delegation spellings: {deleg}. Blank council_member rows by year: "
                  f"{dict(sorted(blank.items()))}.")


@question("G4", "Does a surname filter catch more than one member (e.g. 'Levin' also matches "
          "'Levine', 'Won' matches 'Wong') -- the ambiguity a substring member search inherits?",
          "member identity ambiguity (#51)", "harvested", "yes")
def q_member_substring(ctx):
    """For every member value, the other member values in the SAME year that contain it as a
    case-insensitive substring."""
    members = _member_values(ctx["csv"])
    hits = []
    for fy, ms in sorted(members.items()):
        for m in sorted(ms):
            sup = sorted(x for x in ms if x != m and m.lower() in x.lower())
            if sup:
                hits.append(f"FY{fy} {m!r} also matches {sup}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("G5", "Do agency, state and postal_code hold the shapes they should (agency "
          "variants, a state other than two letters, a ZIP not 5 or 9 digits)?",
          "field shape drift", "new", "yes")
def q_shapes(ctx):
    """agency variant groups; state not ^[A-Z]{2}$ when filled; postal_code not 5/9 digits
    (ZIP+4 with hyphen allowed) when filled."""
    av = [" | ".join(g) for g in _variants({r["agency"] for r in ctx["csv"]})]
    st = collections.Counter(r["state"] for r in ctx["csv"] if r["state"] and not re.fullmatch(r"[A-Z]{2}", r["state"]))
    zips = [r for r in ctx["csv"] if r["postal_code"] and not re.fullmatch(r"\d{5}(-?\d{4})?", r["postal_code"])]
    hits = av + [f"state {k!r} x{n}" for k, n in st.most_common()] + \
        [f"{ref(r)} postal_code={r['postal_code']!r}" for r in zips]
    return result("finding" if hits else "pass", len(hits), hits,
                  f"{len(av)} agency variant groups, {sum(st.values())} odd states, {len(zips)} odd ZIPs.")


# ---------------------------------------------------------------- H. more harvested + provenance

@question("A15", "Is the header row repeated anywhere below the top (a page break or pasted "
          "block that a reader could take for data, or that hides a lost row)?",
          "repeated header row deleting real rows (DA13)", "harvested", "yes")
def q_repeated_header(ctx):
    """Every row after the first whose cells, folded to lower case, match the header text in
    three or more columns."""
    hits = []
    for fy, s in sorted(ctx["sheets"].items()):
        hdr = {ci: " ".join(h.lower().split()) for ci, h in s.header.items()}
        for rn, cells in s.rows.items():
            if rn == s.header_row:
                continue
            same = sum(1 for ci, c in cells.items() if hdr.get(ci) and text_of(c).lower() == hdr[ci])
            if same >= 3:
                hits.append(f"{s.file}:{rn} repeats the header in {same} columns")
    return result("finding" if hits else "pass", len(hits), hits)


@question("A16", "As of when is each workbook? (the Council's sheet-name date, the file's "
          "own last-saved date, and our download date, side by side)",
          "vintage / export lag (SA3, SA6)", "harvested", "yes")
def q_vintage(ctx):
    """Sheet name (the Council stamps a date into it from FY2019), docProps/core.xml
    dcterms:modified (xlsx), and MANIFEST.csv's retrieved date. Informational: lag between
    the fiscal year and the export decides who council_member is and how much is Pending."""
    retrieved = {m["file"]: m["retrieved"] for m in ctx["manifest"]}
    out = []
    for fy, s in sorted(ctx["sheets"].items()):
        modified = ""
        if s.path.endswith(".xlsx"):
            core = zipfile.ZipFile(s.path).read("docProps/core.xml").decode("utf-8", "replace") \
                if "docProps/core.xml" in zipfile.ZipFile(s.path).namelist() else ""
            m = re.search(r"<dcterms:modified[^>]*>([^<]+)<", core)
            modified = m.group(1)[:10] if m else "?"
        out.append(f"FY{fy}: sheet {s.sheets[0][0]!r}, saved {modified or 'n/a (.xls)'}, "
                   f"retrieved {retrieved.get(s.file, '?')}")
    return result("info", len(out), out[-MAX_EXAMPLES:], " ".join(out[:-MAX_EXAMPLES]))


@question("C7", "Is the grantee EIN ever the fiscal conduit's EIN (conduit confused with "
          "grantee)?", "fiscal-conduit EIN confused with grantee EIN", "harvested", "yes")
def q_conduit_same(ctx):
    """Rows where ein == fiscal_conduit_ein (both filled). Informational: the conduit fields are
    rarely filled; when they equal the grantee's, a search on either EIN finds the row."""
    hits = [r for r in ctx["csv"] if r["fiscal_conduit_ein"] and r["ein"] == r["fiscal_conduit_ein"]]
    filled = collections.Counter(r["fiscal_year"] for r in ctx["csv"] if r["fiscal_conduit_ein"])
    return result("info" if hits else "pass", len(hits),
                  [f"{ref(r)} {short(r['legal_name'], 35)!r} conduit {short(r['fiscal_conduit'], 30)!r}" for r in hits],
                  f"Rows with a conduit EIN, by year: {dict(sorted(filled.items()))}.")


@question("D10", "Has a grantee identity (an EIN, or a bare dollar amount) been parked in a "
          "column that is not legal_name/ein/amount (source, program_name, council_member, "
          "agency, city, address)?", "identity in the wrong column (sweep B3/B35)", "harvested", "yes")
def q_identity_elsewhere(ctx):
    """EIN-shaped runs (9 digits, NN-NNNNNNN) or a field that is only a money amount in source,
    program_name, council_member, agency, city, state, fiscal_conduit."""
    pat = re.compile(r"\b\d{2}-\d{7}\b|(?<![\d-])\d{9}(?![\d-])|^\$?\d[\d,]*(?:\.\d+)?$")
    per, ex = collections.Counter(), []
    for r in ctx["csv"]:
        for f in ("source", "program_name", "council_member", "agency", "city", "state", "fiscal_conduit"):
            if r[f] and pat.search(r[f]):
                per[f] += 1
                if len(ex) < MAX_EXAMPLES:
                    ex.append(f"{ref(r)} {f}={short(r[f], 40)!r}")
    return result("finding" if per else "pass", sum(per.values()), ex, f"By field: {dict(per)}.")


@question("D11", "Is a legal_name a cut-off prefix of a longer name the same EIN carries "
          "elsewhere (truncated_org_name, corroborated)?", "truncated_org_name", "harvested", "yes")
def q_prefix_truncation(ctx):
    """Per EIN (City EIN excluded), names that are a strict prefix of another name for that EIN
    and end without a closing word boundary the longer one has, e.g. '..., In' vs '..., Inc.'.
    A name that is a whole-word prefix ('Day One' vs 'Day One New York') is a variant, not a
    cut, and is not counted."""
    names = collections.defaultdict(set)
    for r in ctx["csv"]:
        if r["ein"] and r["ein"] != CITY_EIN:
            names[r["ein"]].add(r["legal_name"])
    cut = set()
    for ein, ns in names.items():
        for a in ns:
            for b in ns:
                if a != b and b.startswith(a) and len(b) - len(a) >= 2 and b[len(a)].isalnum() \
                        and a[-1:].isalnum():
                    cut.add((ein, a, b))
    rows = [r for r in ctx["csv"] if any(r["ein"] == e and r["legal_name"] == a for e, a, _ in cut)]
    longer = {}
    for e, a, b in sorted(cut):
        longer.setdefault((e, a), b)
    return result("finding" if rows else "pass", len(rows),
                  [f"{ref(r)} {short(r['legal_name'], 40)!r} vs {short(longer[(r['ein'], r['legal_name'])], 45)!r}" for r in rows],
                  f"{len(cut)} distinct cut names.")


@question("D12", "Do names for the same EIN differ only by a curly vs straight apostrophe or "
          "quote, '&' vs 'and', or a soft hyphen (so a name search finds one spelling and "
          "misses the other)?", "invisible/char variants fork keys (sweep B4, DA17)", "harvested", "yes")
def q_char_variants(ctx):
    """Per EIN, distinct legal_names that become equal after mapping curly quotes to straight,
    '&' to 'and', and deleting soft hyphens. Plus a count of rows whose legal_name holds a
    curly quote at all."""
    def fold(s):
        s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
        return " ".join(s.replace("\u00ad", "").replace("&", " and ").lower().split())
    groups = collections.defaultdict(set)
    for r in ctx["csv"]:
        groups[(r["ein"], fold(r["legal_name"]))].add(r["legal_name"])
    # Case-only differences are excluded: every search here is case-insensitive.
    v = [sorted(g) for g in groups.values() if len({x.lower() for x in g}) > 1]
    curly = sum(1 for r in ctx["csv"] if re.search("[\u2018\u2019\u201c\u201d]", r["legal_name"]))
    return result("finding" if v else "pass", len(v), [" | ".join(g) for g in v],
                  f"{curly:,} rows have a curly quote in legal_name; a search typed with a straight "
                  f"apostrophe does not find them.")


@question("D13", "Does any address lose a hyphen between the workbook and the CSV, or gain one "
          "(a Queens house number '12-11 40th Avenue' published as '1211', or a soft hyphen "
          "beside a printed '-' doubled into '12--11')?",
          "invisible character deleted with meaning (issue #68)", "new", "yes")
def q_address_hyphens(ctx):
    """For every CSV row, counts the hyphen joins in its workbook address1/address2 cell (two
    word characters separated by any run of '-' and soft hyphens U+00AD) and the joins in the
    CSV cell (two word characters separated by '-'); any row where they differ is a
    finding, as is any '--' in the CSV that the workbook cell does not print. Date-typed cells
    (A8) are skipped."""
    raw_join = re.compile("\\w[-\u00ad]+\\w")
    csv_join = re.compile("\\w-+\\w")
    hits, shy_cells, joins = [], 0, 0
    for r in ctx["csv"]:
        s = ctx["sheets"][int(r["fiscal_year"])]
        for f in ("address1", "address2"):
            c = s.get(int(r["source_row"]), f)
            if c is not None and c.kind == "d":
                continue  # a date-typed cell carries a serial, not text (A8 lists it)
            raw = "" if c is None else str(c.value)
            if "\u00ad" in raw:
                shy_cells += 1
            n_raw = len(raw_join.findall(raw))
            n_csv = len(csv_join.findall(r[f]))
            joins += n_raw
            if n_raw != n_csv or (r[f].count("--") > raw.count("--")):
                hits.append(f"{ref(r)} {f}: workbook {short(repr(raw), 40)} vs CSV {short(r[f], 40)!r}")
    return result("finding" if hits else "pass", len(hits), hits,
                  f"{shy_cells} workbook address cells hold a soft hyphen; {joins:,} hyphen joins "
                  f"in the workbook address cells, compared one for one with the CSV.")


@question("G6", "Which funding-stream labels does each year use (Local / Youth / Aging and "
          "their older names), so a stream filter is not searching for a word the year never "
          "printed?", "label vocabulary drifts by year (FR blocker, SA10)", "harvested", "yes")
def q_stream_census(ctx):
    """Rows per year for every source value matching local|youth|aging|speaker|boro that is a
    STREAM label (not a named initiative). Informational."""
    stream = re.compile(r"^(local|youth|aging|speaker'?s initiative|boro|local initiatives?|"
                        r"local discretionary|youth initiatives|youth discretionary|aging discretionary)$", re.I)
    c = collections.Counter((r["fiscal_year"], r["source"]) for r in ctx["csv"] if stream.match(r["source"]))
    by = collections.defaultdict(list)
    for (fy, src), n in sorted(c.items()):
        by[fy].append(f"{src} {n}")
    out = [f"FY{fy}: " + ", ".join(v) for fy, v in sorted(by.items())]
    return result("info", len(c), out[-MAX_EXAMPLES:], "; ".join(out[:-MAX_EXAMPLES]))


@question("H1", "Does every generated report state the retrieval date of the snapshot it was "
          "actually built from (no stale provenance after a re-pull)?",
          "derived figure / provenance misattributed", "harvested", "yes")
def q_report_provenance(ctx):
    """Every 'retrieved YYYY-MM-DD' in data/DISCLOSURE-COVERAGE.md and the coverage script's
    header must be a date MANIFEST.csv records for the disclosure workbooks."""
    current = {m["retrieved"] for m in ctx["manifest"] if m["file"].startswith("funded")}
    hits = []
    for rel in ("data/DISCLOSURE-COVERAGE.md",):
        p = os.path.join(os.path.dirname(ctx["data_dir"]), rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        for d in re.findall(r"retrieved (\d{4}-\d{2}-\d{2})", text):
            if d not in current:
                hits.append(f"{rel}: says retrieved {d}; MANIFEST.csv says {sorted(current)}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("H2", "Does any doc still call the MOCS ID a stable key, or an established join to "
          "registered contracts, when the snapshots show it re-prefixed and re-issued?",
          "unverified claim stated as fact", "new", "yes")
def q_mocs_claims(ctx):
    """Greps README.md, DATA-DICTIONARY.md, the source README and mcp/README.md for 'stable'
    near 'MOCS', and for the MOCS ID described as 'the join' / 'the key' to contracts without
    the word 'unverified' on the same line."""
    root = os.path.dirname(ctx["data_dir"])
    hits = []
    for rel in ("README.md", "DATA-DICTIONARY.md", "source/expense-funding-disclosure/README.md",
                "mcp/README.md"):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines, 1):
            if not re.search(r"mocs", line, re.I):
                continue
            stable = re.search(r"\bstable\b", line, re.I) and not re.search(r"not stable|unstable", line, re.I)
            join = re.search(r"(the join|the key|joins) to registered contracts", line, re.I) and \
                not re.search(r"unverified", line, re.I)
            if stable or join:
                hits.append(f"{rel}:{i}: {short(line.strip(), 90)}")
    return result("finding" if hits else "pass", len(hits), hits)


@question("H3", "Does the snapshot diff ever pair rows on council_member (the roster at export, "
          "which moves when a seat changes hands)?", "member used as a join key (DA21, #51)",
          "harvested", "yes")
def q_diff_key(ctx):
    """Reads COMPOSITE from code/diff_disclosure_snapshots.py. Keyed on the member, two FY2026
    rows whose member alone changed (FY26 00144, FY26 06277) showed as removed + added."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diff_disclosure_snapshots.py")
    spec = importlib.util.spec_from_file_location("_diffmod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bad = [f for f in ("council_member",) if f in mod.COMPOSITE]
    return result("finding" if bad else "pass", len(bad), [f"COMPOSITE = {mod.COMPOSITE}"] if bad else [],
                  f"COMPOSITE = {mod.COMPOSITE}.")


# =============================================================== run + report

def build_context(src_dir=SRC_DIR, data_dir=DATA_DIR, manifest=MANIFEST):
    rows = load_csv_rows(data_dir)
    by_fy = collections.defaultdict(list)
    for r in rows:
        by_fy[int(r["fiscal_year"])].append(r)
    return {"csv": rows, "csv_by_fy": dict(by_fy), "sheets": load_sheets(src_dir),
            "manifest": read_manifest(manifest), "data_dir": data_dir}


def run(ctx, only=None):
    out = []
    for q in QUESTIONS:
        if only and q["id"] not in only:
            continue
        out.append({**{k: v for k, v in q.items() if k != "fn"}, **q["fn"](ctx)})
    return out


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def report_text(results, ctx, mcp_results=None):
    retrieved = sorted({m["retrieved"] for m in ctx["manifest"] if m["file"].startswith("funded")})
    n = len(results)
    counts = collections.Counter(r["status"] for r in results)
    L = [
        "---",
        "title: Expense disclosure — adversarial audit",
        "type: audit",
        "status: generated",
        "tags: [nyc-budget, expense-disclosure, audit]",
        "---",
        "",
        "# Expense disclosure — adversarial audit",
        "",
        f"**Generated by:** `code/audit_disclosure.py` from committed files only "
        f"(`source/expense-funding-disclosure/*.xls*`, retrieved {', '.join(retrieved)} per "
        f"`MANIFEST.csv`; `data/fyNN/expense_disclosure/`). No network. Re-running it on the same "
        f"files reproduces this report byte for byte; `code/test_audit_disclosure.py` fails if it "
        f"is stale.",
        "",
        "**What it asks.** Every question the Schedule C audits asked (`research/integrity-sweep/`, "
        "`research/audit-2026-08-13/`, issues #41–#60), re-asked of the disclosure, plus the "
        "questions a spreadsheet source raises that a PDF does not. `origin` says which.",
        "",
        "**Independence.** The workbooks are re-read with openpyxl and raw XML, not with "
        "`parse_expense_disclosure.py`, and headers are mapped by this script's own rules. "
        "FY2013 (`.xls`) is read with xlrd's row API: the same library as the parser, so FY2013 "
        "is *partly* independent. A check whose only evidence is the parser's own output is "
        "labeled `circular` and is not counted as verification.",
        "",
        "**Result key.** `pass` = the question was asked and nothing was found. `finding` = the "
        "data shows it; the count and up to six examples (`file:row`) follow. A finding is not "
        "necessarily a parser bug: A6 shows the CSV equals the workbook cell for cell, so most "
        "findings are *as the Council published them*. `info` = listed for a human, not a defect.",
        "",
        f"**Totals:** {n} data questions — {counts['pass']} pass, {counts['finding']} finding, "
        f"{counts['info']} info. Harvested {sum(r['origin'] == 'harvested' for r in results)}, "
        f"new {sum(r['origin'] == 'new' for r in results)}.",
        "",
        "| id | question | defect class it re-asks | origin | independent | result | count | method / examples |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    for r in results:
        detail = r["method"]
        if r.get("note"):
            detail += " **Note:** " + r["note"]
        if r["examples"]:
            detail += " **Examples:** " + "; ".join(f"`{_md(e)}`" for e in r["examples"])
        L.append(f"| {r['id']} | {_md(r['question'])} | {_md(r['defect_class'])} | {r['origin']} | "
                 f"{r['independent']} | **{r['status']}** | {r['count']:,} | {_md(detail)} |")
    L += ["", "## The MCP tool (`search_disclosure_awards`)", "",
          "The same questions, asked of the served tool, live in `mcp/test/disclosure-audit.test.js` "
          "(run with `npm test` in `mcp/`). Each test computes its expected value from the committed "
          "CSVs with csv-parse, independently of the SQLite index the tool reads, and states what "
          "would make it fail.", ""]
    for q in MCP_QUESTIONS:
        L.append(f"- **{q[0]}** {q[1]} *(re-asks: {q[2]}; {q[3]})*")
    L += ["", "## Independent red-team review, 2026-10-12", "",
          "A separate reviewer re-read every workbook with its own readers: all 139,556 rows match "
          "the raw cells, coverage recomputes exactly, MCP totals match. Its ten items, and where "
          "each is now asked:", "",
          "| item | asked by | outcome |", "|---|---|---|"]
    for item, qs, outcome in RED_TEAM:
        L.append(f"| {_md(item)} | {qs} | {_md(outcome)} |")
    L.append("")
    return "\n".join(L)


# Questions asked of the MCP tool. Answered by mcp/test/disclosure-audit.test.js; listed here so
# the question bank is one table. (id, question, defect class, origin)
MCP_QUESTIONS = [
    ("M1", "Do the tool's totals equal the CSV sum, summed exactly and rounded to the cent, for every fiscal_year x status?", "circular validation / silent loss", "harvested"),
    ("M2", "Does `matched` equal the true CSV count when the page is truncated (limit 1, 50, 500), with totals unchanged?", "truncation hiding true totals (#49)", "harvested"),
    ("M3", "Are the rows shown the highest amounts of ALL matches across years, sorted before the limit?", "sort-before-limit (#41/#48)", "harvested"),
    ("M4", "limit edges: 0 and negative are an error (they silently returned 1 row; FIXED), 1 and 500 honored, 501 capped at 500 with totals unchanged, a fraction refused?", "silent row cap (#42)", "harvested"),
    ("M5", "Is an unknown parameter rejected rather than silently ignored?", "silent filter drop (#37/#40)", "harvested"),
    ("M6", "EIN with and without hyphen agree; a leading zero is kept; an EIN that is not 9 digits ('N/A' matched the 6 blank-EIN rows, an 8-digit one silently matched nothing) is an error naming the fix (FIXED); the filter never matches the fiscal conduit's EIN (now pinned); an EIN pooling many names (the City's 136400434) says how many (FIXED)?", "leading-zero loss / wrong_ein / conduit confusion / City EIN pooling", "harvested"),
    ("M7", "Are text filters case- and surrounding-whitespace-insensitive?", "whitespace/case variants", "new"),
    ("M8", "Are LIKE wildcards in a filter ('%', '_', backslash) taken literally? (legal_name '_' matched all 139,556 rows; FIXED)", "filter over-match", "new"),
    ("M9", "When a substring filter on council_member, source or agency matches more than one distinct value ('Levin' -> Levin + Levine, 'Youth' -> Youth + Summer Youth Employment Program ...), does the answer list each value with its rows and dollars? (it summed them silently; FIXED)", "member identity ambiguity (#51) / source over-match", "harvested"),
    ("M10", "An empty result is not an error, names the covered years and the snapshot?", "absence claims (#53)", "harvested"),
    ("M11", "Do fractional FY2013-FY2015 amounts sum without float residue in the displayed totals?", "float rounding on cents", "harvested"),
    ("M12", "Are the rows at the top of an unfiltered answer clean (9-digit EIN, no prose or amount as a name)?", "mangled row at position 1 (#48 CSSA)", "harvested"),
]


# The independent red-team review of 2026-10-12 (its own openpyxl/xlrd readers, read-only), each
# item mapped to the question that now asks it and what was done. (item, question ids, outcome)
RED_TEAM = [
    ("1. Snapshot diff keyed composite pairs on council_member: 2 FY2026 rows whose member alone changed showed as added + removed (true figures: 131 re-numbered, +62/-55, 161 Bottcher -> Wilson).",
     "H3", "FIXED: member dropped from the key; reports regenerated; DATA-ANOMALIES §22, mcp/README, snapshot README corrected."),
    ("2. DISCLOSURE-COVERAGE.md said 'retrieved 2026-07-15' (typed into the script) for tables built from the 2026-10-12 files.",
     "H1", "FIXED: the date is read from MANIFEST.csv."),
    ("3. MCP ein 'N/A' matched the 6 blank-EIN rows; an 8-digit EIN silently matched nothing.",
     "M6", "FIXED: a non-9-digit EIN is an error naming the zero-padded form; never padded."),
    ("4. 211 soft hyphens and 2 left-to-right marks survived, though the docs say invisible characters are removed.",
     "D8, A6", "FIXED: every Unicode Cf character is deleted, except that a soft hyphen is a hyphen (issue #68: deleting it turned the Queens address 12-11 40th Avenue into 1211; D13). Mojibake such as 'EspaÃ±ol' is in the source cell and kept, flagged by D8."),
    ("5. Docs called the MOCS ID a stable per-award key and the join to registered contracts.",
     "H2, C6", "FIXED: reworded as not stable across snapshots and an unverified contract join."),
    ("6. 64 amounts carry sub-cent precision; 7 are float residue of in-cell formulas. (Checked: 7 are float residue, but only FY2014 row 109 is still a live formula; the other 6 are stored values.)",
     "E2, A10", "DOCUMENTED, not rounded: rounding moves no year's total by more than 1.2 cents and would break cell-for-cell identity with the workbook (A6)."),
    ("7. 321 groups / 341 rows identical in every field but source_row, FY2013-FY2023.",
     "F1", "DOCUMENTED in DATA-ANOMALIES §22; whether they are real repeat designations is a QUESTION FOR NOEL."),
    ("8. MCP limit 0/negative returned 1 row; LIKE wildcards unescaped (legal_name '_' matched every row).",
     "M4, M8", "FIXED, with tests."),
    ("9. No test pinned 'ein matches the grantee EIN only'; no test checked the committed snapshot reports were current.",
     "M6", "FIXED: mcp/test/disclosure-audit.test.js pins the conduit rule (mutation OR-ing the conduit fails it); code/test_diff_disclosure_snapshots.py regenerates each report from the superseded workbook found in git history by its MANIFEST-HISTORY hash."),
    ("10. ~24 FY2027 add/remove pairs share EIN + amount + legal name under a new MOCS ID.",
     "C6", "FIXED: the diff lists them as 'Likely re-issued' (24 in FY2027, 2 in FY2026), a nomination that is never paired or netted."),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true", help="write data/DISCLOSURE-AUDIT.md")
    g.add_argument("--check", action="store_true", help="exit 1 if data/DISCLOSURE-AUDIT.md is stale")
    a = ap.parse_args(argv)
    for mod in ("openpyxl", "xlrd"):
        try:
            __import__(mod)
        except ImportError:
            sys.exit(f"audit_disclosure: {mod} is required (pip install -r code/requirements.txt)")
    ctx = build_context()
    results = run(ctx)
    text = report_text(results, ctx)
    if a.write:
        with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {os.path.relpath(REPORT, ROOT)}")
    elif a.check:
        cur = ""
        if os.path.exists(REPORT):
            with open(REPORT, encoding="utf-8") as fh:
                cur = fh.read()
        if cur != text:
            print("STALE: data/DISCLOSURE-AUDIT.md -- run code/audit_disclosure.py --write")
            return 1
        print("data/DISCLOSURE-AUDIT.md is current")
    for r in results:
        print(f"{r['id']:4} {r['status']:8} {r['count']:>7,}  {short(r['question'], 90)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
