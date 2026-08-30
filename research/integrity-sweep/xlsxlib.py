#!/usr/bin/env python3
"""Independent stdlib xlsx reader for the audit.

Deliberately NOT reusing code/recover_org_names.py's reader: the point of this audit is to
check that reader's output, so inheriting its bugs would defeat the exercise.

Difference that matters: this one positions every cell by its `r` reference (A1 notation)
instead of by its ordinal position among the <c> elements present. xlsx omits empty cells,
so zip(header, cells_present) shifts columns on any row with a gap.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_index(ref):
    """'BC12' -> 54 (0-based column)."""
    n = 0
    for ch in ref:
        if ch.isdigit():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def shared_strings(z):
    out = []
    if "xl/sharedStrings.xml" not in z.namelist():
        return out
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                out.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
    return out


def rows(path, sheet="xl/worksheets/sheet1.xml"):
    """Yield (excel_row_number, list_of_cell_values) with empty cells preserved as ''."""
    z = zipfile.ZipFile(path)
    shared = shared_strings(z)

    def val(c):
        if c.get("t") == "inlineStr":
            return "".join(t.text or "" for t in c.iter(NS + "t"))
        v = c.find(NS + "v")
        if v is None or v.text is None:
            return ""
        if c.get("t") == "s":
            try:
                return shared[int(v.text)]
            except (ValueError, IndexError):
                return ""
        return v.text

    with z.open(sheet) as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != NS + "row":
                continue
            cells = {}
            for c in el.findall(NS + "c"):
                r = c.get("r")
                idx = col_index(r) if r else None
                if idx is None:
                    continue
                cells[idx] = val(c)
            width = (max(cells) + 1) if cells else 0
            out = [cells.get(i, "") for i in range(width)]
            yield int(el.get("r") or 0), out
            el.clear()


def dicts(path, sheet="xl/worksheets/sheet1.xml"):
    """Yield (excel_row_number, {header: value}) using the first non-empty row as header.

    Duplicate headers are disambiguated as 'header#2', 'header#3', ... so a second
    column never silently overwrites the first.
    """
    hdr = None
    for rn, vals in rows(path, sheet):
        if hdr is None:
            if not any(v.strip() for v in vals):
                continue
            seen = {}
            hdr = []
            for v in vals:
                key = (v or "").strip()
                seen[key] = seen.get(key, 0) + 1
                hdr.append(key if seen[key] == 1 else f"{key}#{seen[key]}")
            continue
        if len(vals) < len(hdr):
            vals = vals + [""] * (len(hdr) - len(vals))
        yield rn, dict(zip(hdr, vals))


def norm_ein(v):
    return re.sub(r"\D", "", v or "")
