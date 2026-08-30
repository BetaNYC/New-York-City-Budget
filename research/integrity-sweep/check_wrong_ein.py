#!/usr/bin/env python3
"""Independently re-derive the 20 wrong_ein repairs from the disclosure workbooks.

Rebuilds the three structures fix_wrong_eins.py uses -- (canon name, amount) -> {ein},
ein -> {canon name}, and the set of fiscal-conduit EINs -- but with cells positioned by
reference and the conduit column identified by a substring that actually matches the header
used from FY2018 onward ('Fiscal Conduit EIN', which does NOT contain 'fc ein').
"""
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import xlsxlib                    # noqa: E402
import fix_wrong_eins as FWE      # noqa: E402

canon = FWE.canon
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def strict_year(fy):
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return None
    name_amt, ein_names, conduits = {}, {}, set()
    for rn, d in xlsxlib.dicts(path):
        ein = nm = fce = None
        amt = None
        for k, v in d.items():
            kl = k.strip().lower()
            is_conduit = ("fc ein" in kl) or ("fiscal conduit ein" in kl)
            if is_conduit:
                if fce is None:
                    fce = xlsxlib.norm_ein(v)
                continue
            if "fiscal conduit" in kl:
                continue
            if ein is None and ("tax id" in kl or "ein" in kl):
                ein = xlsxlib.norm_ein(v)
            if nm is None and "legal name" in kl:
                nm = (v or "").strip()
            if amt is None and kl.startswith("amount"):
                try:
                    amt = int(float(v))
                except (TypeError, ValueError):
                    amt = None
        if fce:
            conduits.add(fce)
        if ein and nm and amt is not None:
            name_amt.setdefault((canon(nm), amt), set()).add(ein)
            ein_names.setdefault(ein, set()).add(canon(nm))
    return name_amt, ein_names, conduits


def main():
    rows = [r for r in csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8"))
            if r["defect"] == "wrong_ein"]
    cache = {}
    print(f"{'row':<14}{'applied ein':<13}{'strict verdict'}")
    tally = {}
    for r in rows:
        fy = 2000 + int(re.search(r"/fy(\d\d)/", r["file"]).group(1))
        if fy not in cache:
            cache[fy] = strict_year(fy)
        name_amt, ein_names, conduits = cache[fy]
        org = re.sub(r"^\[ein \d+\]\s*", "", r["recovered_organization"])
        orig_ein = re.search(r"\[ein (\d+)\]", r["original_organization"]).group(1)
        amt = int(r["amount"])
        cand = name_amt.get((canon(org), amt), set())
        if len(cand) == 1 and next(iter(cand)) == r["ein"]:
            v = "CONFIRMED"
        elif len(cand) == 1:
            v = f"CONTRADICTED strict says {next(iter(cand))}"
        elif len(cand) > 1:
            v = f"AMBIGUOUS {sorted(cand)}"
        else:
            v = "NO_EVIDENCE"
        extra = []
        if r["ein"] in conduits:
            extra.append("APPLIED-EIN-IS-A-FISCAL-CONDUIT")
        if orig_ein in conduits:
            extra.append("original-ein-was-a-conduit(should have been skipped)")
        tally[v.split()[0]] = tally.get(v.split()[0], 0) + 1
        print(f"fy{fy % 100}:{r['line']:<9}{r['ein']:<13}{v}  {' '.join(extra)}")
        print(f"              {org[:70]!r}  ${amt:,}  (was {orig_ein})")
    print()
    print("tally:", tally)
    print()
    # Was the conduit guard alive at all?
    for fy in sorted(cache):
        _, _, strict_conduits = cache[fy]
        old = FWE.load_year(fy)
        print(f"FY{fy}: conduit EINs seen by fix_wrong_eins.py = {len(old[2]):5d}   "
              f"by a header-correct read = {len(strict_conduits):5d}")


if __name__ == "__main__":
    main()
