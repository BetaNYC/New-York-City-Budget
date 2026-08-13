#!/usr/bin/env python3
"""
rederive_crosswalk.py — re-decide every applied repair against the CURRENT evidence, and revert
any that no longer holds.

The crosswalk accumulated across a changing evidence base. 1,291 of its entries were written while
code/recover_org_names.py matched disclosure headers by exact string, which made the whole FY2016
workbook invisible (its name column is headed "Legal Name of Organization Requesting Funding").
Commit 0627897 fixed the reader — but nothing re-derived what had already been applied.

That is not a hypothetical. fy16:141 (EIN 13-2612524, $258,800) was rewritten from
"Fund for the City of New York" to "Center for Court Innovation (Brownsville Community Justice
Center)". With FY2016 readable, the Council's own answer for that (EIN, amount) is
"Fund for the City of New York, Inc." — the original was right and the repair was wrong. The
script's own canon() guard exists to prevent exactly this and could not fire, because with the
workbook invisible there was only one candidate.

This walks every entry, re-runs the uniqueness test with the fixed reader, and REVERTS the data
where the evidence no longer supports what was applied. Reverting is always safe: the crosswalk
records the original value, which is the whole reason it exists.

Usage:  python3 code/rederive_crosswalk.py [--dry-run]
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
    """(EIN, amount) -> set of canonical names, for ONE fiscal year. Per year deliberately: a
    (EIN, amount) pair is unique within a year but not across the series, and pooling is what let
    a FY2015 spelling be applied to a FY2016 row."""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(CROSSWALK, newline="", encoding="utf-8") as fh:
        entries = list(csv.DictReader(fh))

    indices, reverts, kept, unchecked = {}, [], 0, 0
    for e in entries:
        # Only name repairs sourced from the disclosure are re-derivable this way. member_bleed and
        # residual entries used additional evidence (corpus, transparency resolutions) and are left
        # to their own scripts; wrong_ein repairs a different column.
        if e["defect"] not in ("org_prose", "org_merged") or e.get("source") != "council_disclosure":
            unchecked += 1
            continue
        fy = 2000 + int(e["file"].split("/")[1][2:])
        if fy not in indices:
            indices[fy] = year_index(fy)
        try:
            amt = int(float(e["amount"] or 0))
        except (TypeError, ValueError):
            unchecked += 1
            continue
        cand = indices[fy].get((e["ein"], amt), {})
        applied = e["recovered_organization"]
        # REVERT ONLY ON CONTRADICTION, never on absence.
        # An org_merged row's own absorbed text names the organization, and that is real evidence
        # independent of the workbook. Where the year's disclosure simply has no row for the key,
        # the repair rests on the absorbed text and stands. Only where the disclosure HAS that
        # (EIN, amount) and names something else has the evidence actually turned against us —
        # which is the fy16:141 case, and the only class worth undoing.
        if not cand:
            kept += 1                                  # unconfirmed, not contradicted
        elif canon(applied) in cand:
            kept += 1                                  # disclosure agrees
        else:
            reverts.append((e, sorted(cand.values())))  # disclosure names someone else

    print(f"crosswalk entries          : {len(entries):,}")
    print(f"  re-derivable (disclosure): {kept + len(reverts):,}")
    print(f"  still supported          : {kept:,}")
    print(f"  NO LONGER SUPPORTED      : {len(reverts):,}  <- reverting")
    print(f"  not re-derivable here    : {unchecked:,}")
    for e, cand in reverts[:6]:
        print(f"\n  {e['file'].split('/')[1]}:{e['line']}  ein {e['ein']} ${int(float(e['amount'])):,}")
        print(f"     applied  : {e['recovered_organization'][:58]}")
        print(f"     original : {e['original_organization'][:58]}")
        print(f"     evidence now says: {[c[:44] for c in cand] or '(no row for this key)'}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    if not reverts:
        print("\nnothing to revert")
        return 0

    by_file = {}
    for e, _ in reverts:
        by_file.setdefault(e["file"], {})[int(e["line"])] = e["original_organization"]
    for f, edits in by_file.items():
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, original in edits.items():
            data[ln - 2]["organization"] = original
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  reverted {len(edits):>3} in {f}")

    drop = {(e["file"], e["line"], e["defect"]) for e, _ in reverts}
    remaining = [e for e in entries if (e["file"], e["line"], e["defect"]) not in drop]
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(entries[0].keys()))
        w.writeheader()
        w.writerows(remaining)
    print(f"crosswalk {len(entries):,} -> {len(remaining):,} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
