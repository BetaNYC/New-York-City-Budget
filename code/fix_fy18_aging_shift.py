#!/usr/bin/env python3
"""
fix_fy18_aging_shift.py — repair the column shift in FY2018's aging appendix.

fy18_appendix_a_aging.csv parsed, but one column short. The amount's decimal tail landed at the
front of `purpose`, so every row reads:

    amount='20000'   purpose='.00 Funds will go to G.R.A.N.N.Y program, which provides...'

The amount itself is intact — 20000 is 20000.00 — so no money is at risk. What is wrong is that
every purpose string in the file begins with four characters of a different field. A caller
reading purposes gets '.00 ' prefixed to all 422 of them.

Row 1 carries the PDF's own heading in `organization`:
    organization='Appendix A: Aging Discretionary Council Memb...'  ein=132690309  amount=20000

That row is NOT junk and must not be dropped, which was this script's first draft. The heading
overwrote the name of a real designation: the Council's FY2018 disclosure holds EIN 13-2690309 at
$20,000 under source Aging as "1332 Fulton Avenue Day Care Center, Inc.". Deleting the row would
have destroyed a $20,000 award and moved money. The name is recovered instead, on the same
(EIN, amount) key everything else uses.

Both are mechanical and self-evidencing: the fix applies only where `purpose` literally starts with
'.00 ', and only to this one file. No external source is needed and no judgement is exercised, so
this does not go through the (EIN, amount) disclosure gate the name repairs use — but it is still
recorded in the crosswalk, because every automated edit to this corpus is.

Usage:  python3 code/fix_fy18_aging_shift.py [--dry-run]
"""
import argparse
import csv
import os
import sys

TARGET = "data/fy18/schedule_c/fy18_appendix_a_aging.csv"
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
PREFIX = ".00 "


def disclosure_name(ein, amount):
    """Legal name for one (EIN, amount) in FY2018's workbook, or '' if not unique."""
    import re
    import zipfile
    import xml.etree.ElementTree as ET
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    path = "source/expense-funding-disclosure/funded_disclosure_FY2018.xlsx"
    if not os.path.exists(path):
        return ""
    ein = re.sub(r"\D", "", ein or "")
    try:
        amt = int(float(amount or 0))
    except (TypeError, ValueError):
        return ""
    z = zipfile.ZipFile(path)
    shared = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == ns + "si":
                shared.append("".join(t.text or "" for t in el.iter(ns + "t")))
                el.clear()

    def cv(c):
        v = c.find(ns + "v")
        if v is None or v.text is None:
            return ""
        return shared[int(v.text)] if c.get("t") == "s" else v.text

    def field(d, needles):
        for k, v in d.items():
            kl = (k or "").lower()
            if "fc ein" in kl:
                continue
            if any(n in kl for n in needles) and v not in (None, ""):
                return v
        return ""

    hdr, found = None, set()
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == ns + "row":
                vals = [cv(c) for c in el.findall(ns + "c")]
                if hdr is None:
                    hdr = vals
                else:
                    d = dict(zip(hdr, vals))
                    if re.sub(r"\D", "", field(d, ("tax id", "ein")) or "") == ein:
                        try:
                            if int(float(field(d, ("amount",)) or 0)) == amt:
                                found.add((field(d, ("legal name",)) or "").strip())
                        except (TypeError, ValueError):
                            pass
                el.clear()
    found.discard("")
    return next(iter(found)) if len(found) == 1 else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(TARGET, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        fields, rows = rdr.fieldnames, list(rdr)

    heading = [i for i, r in enumerate(rows)
               if (r.get("organization") or "").startswith("Appendix A:")]
    shifted = [i for i, r in enumerate(rows) if (r.get("purpose") or "").startswith(PREFIX)]
    recovered_names = {}
    for i in heading:
        nm = disclosure_name(rows[i].get("ein", ""), rows[i].get("amount", ""))
        if nm:
            recovered_names[i] = nm

    print(f"{TARGET}: {len(rows)} rows")
    print(f"  purpose values beginning {PREFIX!r} : {len(shifted)}")
    print(f"  rows whose organization holds the PDF heading: {len(heading)}"
          f"  ({len(recovered_names)} recoverable from disclosure)")
    for i, nm in recovered_names.items():
        print(f"    line {i + 2}: heading -> {nm!r}  (${int(float(rows[i]['amount'])):,})")
    for i in shifted[:3]:
        print(f"    line {i + 2}: {rows[i]['purpose'][:62]!r}")
        print(f"          -> {rows[i]['purpose'][len(PREFIX):][:62]!r}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    if not shifted and not heading:
        print("nothing to do")
        return 0

    entries = []
    for i in shifted:
        before = rows[i]["purpose"]
        rows[i]["purpose"] = before[len(PREFIX):]
        entries.append(dict(file=TARGET, line=i + 2, ein=rows[i].get("ein", ""),
                            amount=rows[i].get("amount", ""), defect="fy18_aging_shift",
                            column="purpose", source="mechanical", match_key="purpose_prefix",
                            # NOT truncated: the audit gate compares this against the baseline
                            # cell verbatim, so a shortened record reads as fabricated provenance.
                            original_organization=before,
                            recovered_organization=rows[i]["purpose"]))
    # NO ROW IS DELETED. An earlier draft dropped the heading row; the audit gate caught it,
    # because removing a row renumbers every line after it and invalidates the crosswalk's
    # (file, line) keys — and because that row carries a real $20,000 designation.
    for i, nm in recovered_names.items():
        before = rows[i]["organization"]
        rows[i]["organization"] = nm
        entries.append(dict(file=TARGET, line=i + 2, ein=rows[i].get("ein", ""),
                            amount=rows[i].get("amount", ""), defect="org_prose",
                            column="organization", source="council_disclosure",
                            match_key="ein+amount",
                            original_organization=before, recovered_organization=nm))

    with open(TARGET, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"  stripped {len(shifted)} purpose prefixes, "
          f"recovered {len(recovered_names)} heading-overwritten name(s). No row deleted.")

    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    cols = ["file", "line", "column", "ein", "amount", "defect", "source", "match_key",
            "original_organization", "recovered_organization"]
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in sorted(prior + entries, key=lambda x: (x["file"], int(x["line"]))):
            w.writerow({k: r.get(k, "") for k in cols})
    print(f"  crosswalk {len(prior):,} -> {len(prior) + len(entries):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
