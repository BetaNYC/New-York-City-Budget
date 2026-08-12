#!/usr/bin/env python3
"""Parse the NYC Council's expense funding disclosure workbooks into one record shape.

Source: source/expense-funding-disclosure/funded_disclosure_FY{YYYY}.xlsx  (FY2014-FY2027)
        funded_disclosure_FY2013.xls is legacy BIFF and is skipped, not parsed.

Python standard library only. An .xlsx is a zip of XML, so zipfile + xml.etree is all that
is needed. Shared strings are streamed with iterparse -- these files carry ~1.2MB of
sharedStrings.xml and a DOM parse of the whole worksheet is what makes naive readers hang.

Run it:  python3 code/parse_expense_disclosure.py
That runs demo() (asserts against the real corpus) and then prints the per-year summary.
"""

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import NamedTuple

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "source", "expense-funding-disclosure")

# The Council rewords headers most years. Seven distinct header layouts exist across
# FY2014-FY2027, not two. Mapping by normalized header TEXT (not column position, not a
# per-era branch) collapses all seven into one table. Verified against every file:
#   FY2014  16 cols, no Fiscal Year, "Council Member" / "Legal Name of Organization" / "EIN"
#   FY2015  17 cols, "Council Members"
#   FY2016  16 cols, no Fiscal Year, "Legal Name of Organization Requesting Funding"
#   FY2017  17 cols, "Council Members"
#   FY2018-FY2020  17 cols, "Legal Name" / "EIN" / "CM Purpose of Funds"
#   FY2021-FY2023  17 cols, "Tax ID"
#   FY2024-FY2027  18 cols, adds "MOCS ID#"
HEADER_MAP = {
    "mocs id#": "mocs_id",
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
    "amount ($": "amount",  # FY2014 header is literally truncated mid-parenthesis
    "agency": "agency",
    "program name": "program_name",
    "address": "address1",
    "street address 1": "address1",
    "grantee street address 1": "address1",
    "address 2 (optional": "address2",  # FY2014, also truncated
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

# Zero-width space turned up inside one FY2015 EIN. Strip the invisibles before the key is
# used as a key.
_INVISIBLE = "​‌‍﻿\xa0"

_SUMMARY_WORDS = re.compile(r"total|difference|new add|master list", re.I)


class Award(NamedTuple):
    """One designation. Same shape for every fiscal year."""
    fiscal_year: int          # from the FILENAME, which is authoritative: FY2014 and FY2016
                              # have no Fiscal Year column at all.
    mocs_id: str              # "" before FY2024
    source: str               # Local / Youth / Aging / Speaker's Initiative / named initiative
    council_member: str
    legal_name: str
    ein: str                  # 9 digits, leading zeros preserved
    status: str               # RAW, as published: "Cleared" / "CLEARED" / "Pending" / "PENDING"
    status_norm: str          # "cleared" / "pending" / other, lowercased. Never replaces status.
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
    source_row: int           # provenance: 1-based xlsx row, so any record can be eyeballed


class YearReport(NamedTuple):
    fiscal_year: int
    source_file: str
    sheet_name: str
    skipped: str              # "" if parsed; reason string if the file was skipped
    n_rows_present: int       # <row> elements after the header
    n_awards: int
    n_blank: int
    n_stripped: int
    stripped: list            # [{"row": int, "kind": str, "cells": {header-or-letter: value}}]
    total_amount: float
    by_status: dict           # {"cleared": n, "pending": n, ...} on status_norm
    header_note: str          # anything the file did that the others did not


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


def _rows(z, sheet_path, shared):
    """Yield (row_number, {column_letter: value}) streaming, one row at a time."""
    with z.open(sheet_path) as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != NS + "row":
                continue
            cells = {}
            for c in el.findall(NS + "c"):
                ref = c.get("r") or ""
                m = re.match(r"[A-Z]+", ref)
                if not m:
                    continue
                t = c.get("t")
                v = c.find(NS + "v")
                inline = c.find(NS + "is")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr" and inline is not None:
                    val = "".join(x.text or "" for x in inline.iter(NS + "t"))
                elif v is not None:
                    val = v.text
                else:
                    val = None
                cells[m.group(0)] = val
            yield int(el.get("r")), cells
            el.clear()


def _clean(v):
    if v is None:
        return ""
    for ch in _INVISIBLE:
        v = v.replace(ch, "")
    return v.strip()


def _sheet_and_name(z):
    """Locate the single worksheet. Every one of these workbooks has exactly one."""
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    names = [s.get("name") for s in wb.iter(NS + "sheet")]
    paths = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
    if len(paths) != 1:
        raise ValueError(f"expected exactly one worksheet, found {paths}")
    return paths[0], (names[0] if names else "")


def parse_year(path):
    """Parse one workbook. Returns (list[Award], YearReport)."""
    fname = os.path.basename(path)
    m = re.search(r"FY(\d{4})", fname)
    if not m:
        raise ValueError(f"cannot read a fiscal year out of {fname}")
    fy = int(m.group(1))

    if not zipfile.is_zipfile(path):
        # FY2013 is legacy OLE2/BIFF (magic d0cf11e0a1b11ae1). Reading it needs a real
        # BIFF decoder; the stdlib has none. Skipped deliberately, and said out loud, rather
        # than dropped silently.
        return [], YearReport(fy, fname, "", "legacy .xls (OLE2/BIFF), not a zip - needs "
                              "a BIFF reader, stdlib has none", 0, 0, 0, 0, [], 0.0, {}, "")

    z = zipfile.ZipFile(path)
    sheet_path, sheet_name = _sheet_and_name(z)
    shared = _shared_strings(z)
    it = _rows(z, sheet_path, shared)

    _, header_cells = next(it)
    col_field = {}
    for col, raw in header_cells.items():
        h = _clean(raw).lower()
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

    awards, stripped = [], []
    n_present = n_blank = 0
    fy_col_mismatch = 0

    for rn, cells in it:
        n_present += 1
        get = lambda f: _clean(cells.get(field_col[f])) if f in field_col else ""

        if not any(_clean(v) for v in cells.values()):
            n_blank += 1
            continue

        legal_name, amount_s = get("legal_name"), get("amount")

        # THE data-row test. A real designation always names an organization and an amount.
        # Requiring both strips FY2026's labeled summary rows AND FY2024's unlabeled ones
        # -- which sit in different columns under different words -- with one predicate,
        # and drops nothing legitimate (verified: 9 rows stripped across 14 files, all of
        # them checked by hand, and 3 FY2014 rows that have no EIN but ARE real designations
        # are correctly kept).
        if not legal_name or not amount_s:
            joined = " ".join(str(v) for v in cells.values() if v)
            stripped.append({
                "row": rn,
                "kind": "labeled_summary" if _SUMMARY_WORDS.search(joined) else "orphan_value",
                "cells": {col_field.get(c, c): v for c, v in cells.items() if _clean(v)},
            })
            continue

        try:
            amount = float(amount_s)
        except ValueError:
            stripped.append({"row": rn, "kind": "unparseable_amount",
                             "cells": {col_field.get(c, c): v for c, v in cells.items()
                                       if _clean(v)}})
            continue

        if "fiscal_year_col" in field_col:
            fyc = get("fiscal_year_col")
            if fyc and fyc.split(".")[0] != str(fy):
                fy_col_mismatch += 1

        status = get("status")
        awards.append(Award(
            fiscal_year=fy,
            mocs_id=get("mocs_id"),
            source=get("source"),
            council_member=get("council_member"),
            legal_name=legal_name,
            ein=get("ein"),
            status=status,
            status_norm=status.lower(),
            amount=amount,
            agency=get("agency"),
            program_name=get("program_name"),
            address1=get("address1"),
            address2=get("address2"),
            city=get("city"),
            state=get("state"),
            postal_code=get("postal_code"),
            purpose=get("purpose"),
            fiscal_conduit=get("fiscal_conduit"),
            fiscal_conduit_ein=get("fiscal_conduit_ein"),
            source_file=fname,
            source_row=rn,
        ))

    if fy_col_mismatch:
        notes.append(f"{fy_col_mismatch} rows whose Fiscal Year cell != {fy}")
    if any(a.status != a.status.title() for a in awards):
        notes.append("Status published in UPPERCASE")

    by_status = {}
    for a in awards:
        by_status[a.status_norm] = by_status.get(a.status_norm, 0) + 1

    return awards, YearReport(
        fiscal_year=fy, source_file=fname, sheet_name=sheet_name, skipped="",
        n_rows_present=n_present, n_awards=len(awards), n_blank=n_blank,
        n_stripped=len(stripped), stripped=stripped,
        total_amount=sum(a.amount for a in awards), by_status=by_status,
        header_note="; ".join(notes),
    )


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


def demo():
    """One runnable self-check against the real corpus. Fails loudly if the parser drifts."""
    results = parse_all()
    by_fy = {rep.fiscal_year: (aw, rep) for aw, rep in results}

    assert set(by_fy) == set(range(2013, 2028)), sorted(by_fy)

    # FY2013 is legacy .xls: skipped, with a reason, never silently.
    aw13, rep13 = by_fy[2013]
    assert aw13 == [] and "legacy .xls" in rep13.skipped, rep13
    for fy in range(2014, 2028):
        assert by_fy[fy][1].skipped == "", by_fy[fy][1]

    # The strongest check available: each year that publishes its own total must agree with
    # the total we compute from the rows we kept. Their arithmetic, not a number we hardcoded.
    aw26, rep26 = by_fy[2026]
    assert rep26.n_stripped == 4, rep26.stripped
    assert all(s["kind"] == "labeled_summary" for s in rep26.stripped)
    printed26 = _labeled_total(rep26, "Master List Total")
    assert printed26 is not None and abs(rep26.total_amount - printed26) < 0.01, \
        (rep26.total_amount, printed26)

    # FY2024's summary rows carry DIFFERENT words in DIFFERENT columns than FY2026's.
    # Matching on the Status column for "Schedule C Total:" misses every one of them, which
    # is why the data-row predicate does the stripping instead.
    aw24, rep24 = by_fy[2024]
    assert rep24.n_stripped == 5, rep24.stripped
    printed24 = _labeled_total(rep24, "New Total")
    assert printed24 is not None and abs(rep24.total_amount - printed24) < 0.01, \
        (rep24.total_amount, printed24)
    assert any(s["kind"] == "orphan_value" for s in rep24.stripped), rep24.stripped

    # Nothing else strips anything. A regression that widened the predicate shows up here.
    assert sum(r.n_stripped for _, r in results) == 9, [
        (r.fiscal_year, r.n_stripped) for _, r in results]

    # Status is kept verbatim AND normalized. FY2018 publishes it uppercase.
    aw18 = by_fy[2018][0]
    assert any(a.status == "CLEARED" for a in aw18)
    assert all(a.status_norm in ("cleared", "pending") for a in aw18)
    assert by_fy[2018][1].by_status["cleared"] == 8843, by_fy[2018][1].by_status

    # All seven header layouts land in one shape.
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
    hdr = f"{'FY':<6}{'awards':>8}{'total $':>18}{'cleared':>9}{'pending':>9}{'stripped':>9}  notes"
    print(hdr)
    print("-" * len(hdr))
    tot = n = 0
    for _, r in results:
        if r.skipped:
            print(f"{r.fiscal_year:<6}{'-':>8}{'-':>18}{'-':>9}{'-':>9}{'-':>9}  SKIPPED: {r.skipped}")
            continue
        other = sum(v for k, v in r.by_status.items() if k not in ("cleared", "pending"))
        note = r.header_note + (f"; {other} other-status" if other else "")
        print(f"{r.fiscal_year:<6}{r.n_awards:>8}{r.total_amount:>18,.0f}"
              f"{r.by_status.get('cleared', 0):>9}{r.by_status.get('pending', 0):>9}"
              f"{r.n_stripped:>9}  {note}")
        tot += r.total_amount
        n += r.n_awards
    print("-" * len(hdr))
    print(f"{'ALL':<6}{n:>8}{tot:>18,.0f}")

    strippers = [r for _, r in results if r.n_stripped]
    print("\nYears containing embedded summary / orphan rows: "
          + (", ".join(f"FY{r.fiscal_year} ({r.n_stripped})" for r in strippers) or "none"))
    for r in strippers:
        print(f"\n  FY{r.fiscal_year} -- stripped rows:")
        for s in r.stripped:
            print(f"    row {s['row']:>6}  {s['kind']:<16} {s['cells']}")


if __name__ == "__main__":
    results = demo()
    print()
    print_summary(results)
    sys.exit(0)
