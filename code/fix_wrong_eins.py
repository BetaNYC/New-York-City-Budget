#!/usr/bin/env python3
"""
fix_wrong_eins.py — repair award rows carrying a neighbouring row's EIN.

A column shift can leave a row with the correct organization name and amount but the EIN of an
adjacent award. The row looks clean and fires no advisory, which makes it more dangerous than an
obviously broken one: README describes `ein` as "the reliable join key to IRS 990 / nonprofit
data", so a wrong EIN misattributes real money to a real, named, innocent organization.

Detection is conservative and requires all three to hold:
  1. our (canonical name, amount) matches EXACTLY ONE EIN in the Council's same-year disclosure,
  2. that EIN differs from the one on our row,
  3. our row's own EIN belongs to a DIFFERENT organization in that same disclosure.

Condition 3 is what separates this from a fiscal-conduit relationship, where the EIN legitimately
belongs to a sponsor rather than the grantee. Rows whose EIN appears as a `FC EIN` anywhere in the
year are skipped outright.

Every change is appended to the same crosswalk used for name recovery, so one file remains the
audit trail for every edit made to this corpus.

Usage:  python3 code/fix_wrong_eins.py [--dry-run]
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
        if any(n in (k or "").strip().lower() for n in needles) and v not in (None, ""):
            return v
    return ""


def canon(n):
    n = (n or "").lower().strip()
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def load_year(fy):
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return None
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

    hdr, name_amt, ein_names, conduits = None, {}, {}, set()
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "row":
                vals = [cv(c) for c in el.findall(NS + "c")]
                if hdr is None:
                    hdr = vals
                else:
                    d = dict(zip(hdr, vals))
                    ein = re.sub(r"\D", "", pick(d, ("tax id", "ein")) or "")
                    nm = pick(d, ("legal name",))
                    fce = re.sub(r"\D", "", pick(d, ("fc ein",)) or "")
                    if fce:
                        conduits.add(fce)
                    try:
                        amt = int(float(pick(d, ("amount",)) or 0))
                    except (TypeError, ValueError):
                        el.clear(); continue
                    if ein and nm:
                        name_amt.setdefault((canon(nm), amt), set()).add(ein)
                        ein_names.setdefault(ein, set()).add(canon(nm))
                el.clear()
    return name_amt, ein_names, conduits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fixes = []
    for fy in range(2015, 2028):
        loaded = load_year(fy)
        if not loaded:
            continue
        name_amt, ein_names, conduits = loaded
        for f in sorted(glob.glob(f"data/fy{str(fy)[2:]}/schedule_c/*.csv")):
            if "initiatives" in f or "reconcil" in f:
                continue
            with open(f, newline="", encoding="utf-8") as fh:
                for ln, r in enumerate(csv.DictReader(fh), start=2):
                    org = (r.get("organization") or "").strip()
                    ein = re.sub(r"\D", "", r.get("ein") or "")
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        continue
                    if not org or not ein or ein in conduits:
                        continue
                    if canon(org) in ein_names.get(ein, set()):
                        continue                       # name and EIN agree — nothing to do
                    cand = name_amt.get((canon(org), amt), set())
                    if len(cand) != 1:
                        continue                       # not uniquely resolvable — leave alone
                    right = next(iter(cand))
                    if right == ein or not ein_names.get(ein):
                        continue                       # our EIN is unknown to disclosure: skip
                    fixes.append(dict(file=f, line=ln, ein=right, amount=amt,
                                      defect="wrong_ein", source="council_disclosure",
                                      match_key="name+amount",
                                      original_organization=f"[ein {ein}] {org}",
                                      recovered_organization=f"[ein {right}] {org}"))

    print(f"rows with a wrong EIN, uniquely resolvable: {len(fixes)}")
    for x in fixes[:6]:
        print(f"  {x['file'].split('/')[1]}:{x['line']}  {x['original_organization'][:56]}")
        print(f"      -> {x['recovered_organization'][:56]}")
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    by_file = {}
    for x in fixes:
        by_file.setdefault(x["file"], {})[x["line"]] = x["ein"]
    for f, edits in by_file.items():
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, ein in edits.items():
            data[ln - 2]["ein"] = ein
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  fixed {len(edits):>3} EIN(s) in {f}")

    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    fields = ["file", "line", "ein", "amount", "defect", "source", "match_key",
              "original_organization", "recovered_organization"]
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in sorted(prior + fixes, key=lambda r: (r["file"], int(r["line"]))):
            w.writerow({k: row.get(k, "") for k in fields})
    print(f"crosswalk -> {CROSSWALK} ({len(prior) + len(fixes):,} total entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
