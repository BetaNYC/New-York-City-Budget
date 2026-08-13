#!/usr/bin/env python3
"""
fill_blank_initiatives.py — restore the initiative on award rows that lost it.

An `initiative_provider` is, by the README's own definition, "a provider named collectively under a
citywide initiative". A blank `initiative` on such a row is therefore missing data. The Council's
disclosure records the same award's funding stream in its `Source` column, so it can be restored on
the usual (EIN, amount) key.

TWO LIMITS, both deliberate, and together they are why this fills 1,314 rows and not 9,700.

1. `member_item` rows are NOT touched. A member item is an individual Council Member's local
   designation — it is not under a citywide initiative, so a blank there is CORRECT, not a defect.
   5,887 of the blanks are member items. An earlier sweep counted all 9,700 blanks as a defect
   worth $595M; most of that is the schema working as designed.

2. Only values ALREADY IN THAT YEAR'S initiative vocabulary are written. The disclosure names
   streams the Schedule C initiative axis does not use — "Speaker's Initiative" alone accounts for
   1,554 rows. Importing them would fragment the initiative axis exactly as DATA-ANOMALIES §17
   describes, where one program splits into several short-lived series because its label drifts.
   A gap is recoverable later; a polluted vocabulary is not.

    recoverable and vocabulary-consistent : 1,314   <- filled
    recoverable but new vocabulary        : 1,993   <- left blank, see §17
    ambiguous or absent from disclosure   :   506   <- left blank

Usage:  python3 code/fill_blank_initiatives.py [--dry-run]
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

# Funding streams, not initiatives. These are the appendix axes and the Speaker's pot; none is an
# initiative in the Schedule C sense, and writing them into `initiative` would be a category error.
STREAMS = {"Local", "Aging", "Youth", "Boro", "Speaker's Initiative"}


def pick(row, needles):
    for k, v in row.items():
        kl = (k or "").strip().lower()
        if "fc ein" in kl or "fiscal conduit" in kl:
            continue
        if any(n in kl for n in needles) and v not in (None, ""):
            return v
    return ""


def year_sources(fy):
    """(EIN, amount) -> set of disclosure Source values for that award."""
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
                    src = (pick(d, ("source",)) or "").strip()
                    try:
                        amt = int(float(pick(d, ("amount",)) or 0))
                    except (TypeError, ValueError):
                        el.clear(); continue
                    if ein and src:
                        idx.setdefault((ein, amt), set()).add(src)
                el.clear()
    return idx


def known_initiatives(key):
    """Initiative strings this fiscal year already uses — the vocabulary we must stay inside."""
    out = set()
    for f in glob.glob(f"data/{key}/schedule_c/*_schedule_c_*.csv"):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                v = (r.get("initiative") or "").strip()
                if v:
                    out.add(v)
    return out


def plan():
    out, skipped_vocab, skipped_amb = [], 0, 0
    for fy in range(2015, 2028):
        idx = year_sources(fy)
        if not idx:
            continue
        key = f"fy{str(fy)[2:]}"
        vocab = known_initiatives(key)
        for f in sorted(glob.glob(f"data/{key}/schedule_c/*_schedule_c_awards.csv")):
            with open(f, newline="", encoding="utf-8") as fh:
                for ln, r in enumerate(csv.DictReader(fh), start=2):
                    if (r.get("award_type") or "").strip() != "initiative_provider":
                        continue
                    if (r.get("initiative") or "").strip():
                        continue
                    ein = re.sub(r"\D", "", r.get("ein") or "")
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        continue
                    cand = {s for s in idx.get((ein, amt), set()) if s not in STREAMS}
                    if len(cand) != 1:
                        skipped_amb += 1
                        continue
                    src = next(iter(cand))
                    if src not in vocab:
                        skipped_vocab += 1
                        continue
                    out.append(dict(file=f, line=ln, column="initiative", ein=ein, amount=amt,
                                    defect="blank_initiative", source="council_disclosure",
                                    match_key="ein+amount",
                                    original_organization="", recovered_organization=src))
    return out, skipped_vocab, skipped_amb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows, sv, sa = plan()
    print(f"blank initiatives filled          : {len(rows):,}  ${sum(r['amount'] for r in rows):,}")
    print(f"  left blank — new vocabulary     : {sv:,}")
    print(f"  left blank — ambiguous/absent   : {sa:,}")
    for r in rows[:4]:
        print(f"    {r['file'].split('/')[1]}:{r['line']} -> {r['recovered_organization'][:50]!r}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    if not rows:
        return 0

    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], {})[r["line"]] = r["recovered_organization"]
    for f, edits in by_file.items():
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, val in edits.items():
            data[ln - 2]["initiative"] = val
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  filled {len(edits):>4} in {f}")

    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    cols = ["file", "line", "column", "ein", "amount", "defect", "source", "match_key",
            "original_organization", "recovered_organization"]
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in sorted(prior + rows, key=lambda x: (x["file"], int(x["line"]))):
            w.writerow({k: r.get(k, "") for k in cols})
    print(f"crosswalk {len(prior):,} -> {len(prior) + len(rows):,} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
