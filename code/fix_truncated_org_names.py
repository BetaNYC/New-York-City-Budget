#!/usr/bin/env python3
"""
fix_truncated_org_names.py — restore organization names the parser cut short.

A grantee's legal name is dropped at the first " - ", leaving a prefix that is sometimes a
plausible name and sometimes meaningless:

    'Door'                              ->  'Door - A Center of Alternatives, Inc., The'
    'Boy Scouts of America'             ->  'Boy Scouts of America - Greater New York Council'
    'Spanish Speaking Elderly Council'  ->  'Spanish Speaking Elderly Council - RAICES'
    'Museum of Jewish Heritage'         ->  'Museum of Jewish Heritage - A Living Memorial...'

This class cannot be found by pattern. A first attempt looked for short one- or two-word names and
returned 1,382 rows, almost all legitimate — IlluminArt Productions, FAN4Kids, Hudson Guild,
Mekimi, BOOM!Health are real organizations, not fragments. Only the Council's own data can tell a
short name from a truncated one.

EVIDENCE REQUIRED, per row:
  * the Council's disclosure holds exactly ONE legal name for this row's (EIN, amount), and
  * our value is a strict canonical PREFIX of it, and
  * it is materially shorter — at least 3 canonical characters — so a punctuation or corporate
    suffix variant is never mistaken for a truncation.

Restoring the fuller name is a judgement worth stating plainly: 'Boy Scouts of America' is not
wrong, it is less specific than 'Boy Scouts of America - Greater New York Council', which is what
the Council published for that EIN and amount. The dataset's job is to say who received the money,
and the local council is who received it.

Usage:  python3 code/fix_truncated_org_names.py [--dry-run]
"""
import argparse
import csv
import glob
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def pick(row, needles):
    for k, v in row.items():
        kl = (k or "").strip().lower()
        if "fc ein" in kl or "fiscal conduit" in kl:
            continue
        if any(n in kl for n in needles) and v not in (None, ""):
            return v
    return ""


def canon(n):
    n = (n or "").lower().strip()
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def year_index(fy):
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return {}
    z = zipfile.ZipFile(path)
    shared = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()

    def cv(c):
        v = c.find(NS + "v")
        if v is None or v.text is None:
            return ""
        return shared[int(v.text)] if c.get("t") == "s" else v.text

    hdr, idx = None, {}
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "row":
                vals = [cv(c) for c in el.findall(NS + "c")]
                if hdr is None:
                    hdr = vals
                else:
                    d = dict(zip(hdr, vals))
                    ein = re.sub(r"\D", "", pick(d, ("tax id", "ein")) or "")
                    nm = (pick(d, ("legal name",)) or "").strip()
                    try:
                        amt = int(float(pick(d, ("amount",)) or 0))
                    except (TypeError, ValueError):
                        el.clear(); continue
                    if ein and nm:
                        idx.setdefault((ein, amt), {})[canon(nm)] = nm
                el.clear()
    return idx


def plan():
    """Pure. Returns the rows to change; writes nothing."""
    out = []
    for fy in range(2015, 2028):
        idx = year_index(fy)
        if not idx:
            continue
        for f in sorted(glob.glob(f"data/fy{str(fy)[2:]}/schedule_c/*.csv")):
            if "initiatives" in f or "reconcil" in f:
                continue
            with open(f, newline="", encoding="utf-8") as fh:
                for ln, r in enumerate(csv.DictReader(fh), start=2):
                    org = (r.get("organization") or "").strip()
                    if not org:
                        continue
                    ein = re.sub(r"\D", "", r.get("ein") or "")
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        continue
                    cand = idx.get((ein, amt), {})
                    if len(cand) != 1:
                        continue
                    ck, full = next(iter(cand.items()))
                    co = canon(org)
                    if co != ck and ck.startswith(co) and len(ck) - len(co) >= 3:
                        out.append(dict(file=f, line=ln, column="organization", ein=ein,
                                        amount=amt, defect="truncated_org_name",
                                        source="council_disclosure", match_key="ein+amount",
                                        original_organization=org,
                                        recovered_organization=full))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = plan()
    total = sum(r["amount"] for r in rows)
    print(f"truncated names the Council's data can complete: {len(rows)}  ${total:,}")
    for r in rows[:5]:
        print(f"  {r['file'].split('/')[1]}:{r['line']}  {r['original_organization'][:34]!r}")
        print(f"      -> {r['recovered_organization'][:60]!r}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    if not rows:
        return 0

    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], {})[r["line"]] = r
    for f, edits in by_file.items():
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, r in edits.items():
            data[ln - 2]["organization"] = r["recovered_organization"]
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  completed {len(edits):>3} in {f}")

    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    fields = ["file", "line", "column", "ein", "amount", "defect", "source", "match_key",
              "original_organization", "recovered_organization"]
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in sorted(prior + rows, key=lambda r: (r["file"], int(r["line"]))):
            w.writerow({k: row.get(k, "") for k in fields})
    print(f"crosswalk {len(prior):,} -> {len(prior) + len(rows):,} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
