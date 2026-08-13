#!/usr/bin/env python3
"""
build_appendix_from_disclosure.py — recover the appendix designations for the years whose
appendix CSVs are empty.

data/fy{15,16,17,19,20}/schedule_c/*_appendix_*.csv contain a header row and nothing else. Their
FY2021+ equivalents hold ~3,900-4,300 rows each. The awards are not absent from the budget: the
Council's own disclosure workbooks record them, at volumes directly comparable to the years that
DID parse.

    FY2016  Local 3,008  Aging 540  Youth 919      FY2021  Local 2,936  Aging 514  Youth 901
    FY2017  Local 3,127  Aging 558  Youth 925      FY2027  Local 2,558  Aging 467  Youth 835

So the empty files are an extraction failure, not a correct representation of those years.

This writes them to data/recovered/ as a SIDECAR, never into the per-year appendix files, for the
same reasons as build_recovered_awards.py: nothing already published moves, and recovered rows
carry provenance columns the per-year schema has no place for.

Rows already present in the corpus for that fiscal year — matched on (EIN, amount) — are SKIPPED,
because the main awards file for these years does carry some designations and re-emitting them
would double-count.

Usage:  python3 code/build_appendix_from_disclosure.py [--dry-run]
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
OUT = "data/recovered/schedule_c_appendix_recovered.csv"

# The three appendix streams, and the `Source` values in the disclosure that correspond to them.
STREAMS = {"Local": "appendix_b_local", "Aging": "appendix_a_aging", "Youth": "appendix_c_youth"}

FIELDS = ["fiscal_year", "stream", "member", "organization", "program", "ein", "amount",
          "agency", "purpose", "status", "confidence", "source_file"]


def pick(row, needles, exclude=("fc ein", "fiscal conduit")):
    for k, v in row.items():
        kl = (k or "").strip().lower()
        if any(x in kl for x in exclude):
            continue
        if any(n in kl for n in needles) and v not in (None, ""):
            return v
    return ""


def read_disclosure(fy):
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return []
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

    hdr, out = None, []
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "row":
                vals = [cv(c) for c in el.findall(NS + "c")]
                if hdr is None:
                    hdr = vals
                else:
                    out.append(dict(zip(hdr, vals)))
                el.clear()
    return out


def corpus_keys(fy):
    """(EIN, amount) already present anywhere in that fiscal year, so nothing is double-emitted."""
    keys = set()
    for f in glob.glob(f"data/fy{str(fy)[2:]}/schedule_c/*.csv"):
        if "initiatives" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                ein = re.sub(r"\D", "", r.get("ein") or "")
                try:
                    amt = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                if ein:
                    keys.add((ein, amt))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows, skipped = [], 0
    for fy in (2015, 2016, 2017, 2019, 2020):
        # Only act where the appendix files really are empty; if a year ever gets parsed properly
        # this script must not start shadowing it.
        files = glob.glob(f"data/fy{str(fy)[2:]}/schedule_c/*appendix*.csv")
        if not files or any(sum(1 for _ in open(f, encoding="utf-8")) > 1 for f in files):
            print(f"  FY{fy}: appendix files are populated — skipping")
            continue
        present = corpus_keys(fy)
        for d in read_disclosure(fy):
            src = (pick(d, ("source",)) or "").strip()
            if src not in STREAMS:
                continue
            ein = re.sub(r"\D", "", pick(d, ("tax id", "ein")) or "")
            name = (pick(d, ("legal name",)) or "").strip()
            try:
                amt = int(float(pick(d, ("amount",)) or 0))
            except (TypeError, ValueError):
                continue
            if not ein or not name or amt <= 0:
                continue
            if (ein, amt) in present:
                skipped += 1
                continue
            status = (pick(d, ("status",)) or "").strip()
            rows.append({
                "fiscal_year": fy, "stream": STREAMS[src],
                "member": (pick(d, ("council member",)) or "").strip(),
                "organization": name, "program": (pick(d, ("program name",)) or "").strip(),
                "ein": ein, "amount": amt, "agency": (pick(d, ("agency",)) or "").strip(),
                "purpose": (pick(d, ("purpose",)) or "").strip(), "status": status,
                # Pending designations had not cleared vetting when the Council published; they are
                # kept, labelled, so a caller can include or exclude them deliberately.
                "confidence": "high" if status.lower() == "cleared" else "medium",
                "source_file": f"funded_disclosure_FY{fy}.xlsx",
            })

    rows.sort(key=lambda r: (r["fiscal_year"], r["stream"], r["organization"], r["amount"]))
    total = sum(r["amount"] for r in rows)
    print(f"\nrecoverable appendix awards: {len(rows):,}  ${total:,}")
    print(f"  skipped, already in corpus: {skipped:,}")
    by_fy = {}
    for r in rows:
        by_fy.setdefault(r["fiscal_year"], []).append(r)
    for fy in sorted(by_fy):
        n = by_fy[fy]
        print(f"  FY{fy}: {len(n):>5} awards  ${sum(x['amount'] for x in n):>13,}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    os.makedirs("data/recovered", exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
