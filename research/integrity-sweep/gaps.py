#!/usr/bin/env python3
"""Two gaps the branch leaves behind, quantified.

1. FY2018 is the one year in the sidecar's range whose Local and Youth appendices are still
   empty. build_appendix_from_disclosure.py hardcodes (2015, 2016, 2017, 2019, 2020) and its own
   emptiness guard is per-YEAR, not per-FILE: FY2018 has a populated Aging file, so the whole
   year is skipped.

2. What is still flagged after the repairs, so the residue can be stated exactly.
"""
import collections
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import xlsxlib                   # noqa: E402
import recover_org_names as ROG  # noqa: E402

STREAMS = {"Local": "appendix_b_local", "Aging": "appendix_a_aging", "Youth": "appendix_c_youth"}
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")


def pick(d, needles, exclude=("fc ein", "fiscal conduit")):
    for k, v in d.items():
        kl = (k or "").strip().lower()
        if any(x in kl for x in exclude):
            continue
        if any(n in kl for n in needles) and v not in (None, ""):
            return v
    return ""


def corpus_keys(fy):
    keys = set()
    for f in glob.glob(f"data/fy{str(fy)[2:]}/schedule_c/*.csv"):
        if "initiatives" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                e = re.sub(r"\D", "", r.get("ein") or "")
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                if e:
                    keys.add((e, a))
    return keys


def main():
    print("=== 1. FY2018 appendix designations the branch leaves unrecovered ===")
    present = corpus_keys(2018)
    tot = collections.Counter()
    money = collections.Counter()
    for rn, d in xlsxlib.dicts("source/expense-funding-disclosure/funded_disclosure_FY2018.xlsx"):
        src = (pick(d, ("source",)) or "").strip()
        if src not in STREAMS:
            continue
        ein = re.sub(r"\D", "", pick(d, ("tax id", "ein")) or "")
        name = (pick(d, ("legal name",)) or "").strip()
        try:
            amt = int(float(pick(d, ("amount",)) or 0))
        except (TypeError, ValueError):
            continue
        if not ein or not name or amt <= 0 or (ein, amt) in present:
            continue
        tot[STREAMS[src]] += 1
        money[STREAMS[src]] += amt
    for s in sorted(tot):
        print(f"  {s:<20} {tot[s]:>5} rows  ${money[s]:>12,}")
    print(f"  {'TOTAL':<20} {sum(tot.values()):>5} rows  ${sum(money.values()):>12,}")

    print("\n=== 2. residue still flagged in the live data ===")
    res = collections.Counter()
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                org = (r.get("organization") or "").strip()
                if not org:
                    res["empty organization"] += 1
                elif EIN_IN_TEXT.search(org) or "$" in org:
                    res["org_merged (EIN or $ in the name)"] += 1
                elif ROG.is_prose(org):
                    res["org_prose (purpose text in the name)"] += 1
    for k, v in res.most_common():
        print(f"  {k:<40} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
