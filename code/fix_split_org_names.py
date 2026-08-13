#!/usr/bin/env python3
"""
fix_split_org_names.py — rejoin organization names the parser split across `member` and
`organization`, and clear the sponsor it fabricated doing so.

Where a grantee's legal name BEGINS with a token that also looks like a sponsor — a borough, or a
council surname — the extractor peels that token into `member` and leaves the remainder in
`organization`:

    member='Queens'         organization='Borough Public Library'
    member='Brooklyn'       organization='Defender Services'
    member='Staten Island'  organization='Heart Society, Inc.'

Both fields are then wrong. The organization is decapitated, and the row credits a sponsor who
made no such designation. That second half is the worse one: it is a positive false statement
about a named party, and it fires no advisory, because after the peel there is no leftover token
for a bleed detector to notice.

This is the inverse of fix_member_bleed.py. That script removes a sponsor token that does not
belong to the name; this one restores a token that does.

EVIDENCE REQUIRED, per row:
  * the Council's disclosure holds a legal name for this row's (EIN, amount), and
  * that name equals `member + " " + organization` canonically, and
  * it does NOT equal `organization` alone — so the join is what matches, not the fragment.

`member` is CLEARED rather than replaced. Measured across all 673 rows: the Council's member
disagrees with ours 267 times and is blank 406 times, and agrees ZERO times — the value is
manufactured in every case. Substituting the disclosure's member instead would import the
roster-vintage problem, since those workbooks are republished with the sitting member rather than
the one who adopted the budget. An empty sponsor is honest; a wrong one is an assertion.

Usage:  python3 code/fix_split_org_names.py [--dry-run]
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
    """Pure. Returns the list of rows to change; writes nothing."""
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
                    mem = (r.get("member") or "").strip()
                    org = (r.get("organization") or "").strip()
                    if not mem or not org:
                        continue
                    ein = re.sub(r"\D", "", r.get("ein") or "")
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        continue
                    cand = idx.get((ein, amt), {})
                    joined = canon(f"{mem} {org}")
                    # The join must match AND the fragment must not — otherwise the existing
                    # organization is already a real name and nothing is broken.
                    if joined in cand and canon(org) not in cand:
                        out.append(dict(file=f, line=ln, ein=ein, amount=amt,
                                        defect="split_org_name", source="council_disclosure",
                                        match_key="ein+amount",
                                        original_organization=org,
                                        recovered_organization=cand[joined],
                                        removed_member=mem))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = plan()
    total = sum(r["amount"] for r in rows)
    print(f"split names the Council's data can rejoin: {len(rows)}  ${total:,}")
    for r in rows[:5]:
        print(f"  {r['file'].split('/')[1]}:{r['line']}  member={r['removed_member']!r} + "
              f"{r['original_organization'][:32]!r}")
        print(f"      -> {r['recovered_organization'][:56]!r}   (member cleared)")

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
            data[ln - 2]["member"] = ""
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  rejoined {len(edits):>3} in {f}")

    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    fields = ["file", "line", "ein", "amount", "defect", "source", "match_key",
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
