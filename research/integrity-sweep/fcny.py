#!/usr/bin/env python3
"""The single contradicted repair: fy16:141, EIN 13-2612524, $258,800.

13-2612524 is the Fund for the City of New York -- a fiscal conduit that passes money through
for many grantees. Whether the Council's published name for this award is the conduit or the
program it hosts decides whether the applied name is right.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsxlib  # noqa: E402

EIN = "132612524"
AMT = 258800


def main():
    print("=== fy16 award rows 139-143 ===")
    rows = list(csv.DictReader(open("data/fy16/schedule_c/fy16_schedule_c_awards.csv",
                                    newline="", encoding="utf-8")))
    for ln in range(139, 144):
        r = rows[ln - 2]
        print(f"  {ln}: init={r.get('initiative','')[:34]!r} org={r.get('organization','')[:56]!r} "
              f"ein={r.get('ein')} amt={r.get('amount')}")

    print(f"\n=== every FY2016 disclosure row with EIN {EIN} and amount {AMT} ===")
    for rn, d in xlsxlib.dicts("source/expense-funding-disclosure/funded_disclosure_FY2016.xlsx"):
        ein = nm = fc = None
        amt = None
        for k, v in d.items():
            kl = k.strip().lower()
            if "fc ein" in kl:
                fc = v
                continue
            if "fiscal conduit" in kl:
                continue
            if ein is None and ("tax id" in kl or kl == "ein"):
                ein = xlsxlib.norm_ein(v)
            if nm is None and "legal name" in kl:
                nm = v
            if amt is None and kl.startswith("amount"):
                try:
                    amt = int(float(v))
                except (TypeError, ValueError):
                    amt = None
        if ein == EIN and amt == AMT:
            print(f"  xlsx row {rn}: name={nm!r} amount={amt} fc_ein={fc!r}")

    print(f"\n=== every FY2016 disclosure row whose FISCAL CONDUIT EIN is {EIN}, amount {AMT} ===")
    for rn, d in xlsxlib.dicts("source/expense-funding-disclosure/funded_disclosure_FY2016.xlsx"):
        fc = nm = None
        amt = None
        for k, v in d.items():
            kl = k.strip().lower()
            if "fc ein" in kl or "fiscal conduit ein" in kl:
                fc = xlsxlib.norm_ein(v)
            if nm is None and "legal name" in kl:
                nm = v
            if amt is None and kl.startswith("amount"):
                try:
                    amt = int(float(v))
                except (TypeError, ValueError):
                    amt = None
        if fc == EIN and amt == AMT:
            print(f"  xlsx row {rn}: name={nm!r} amount={amt}")

    print(f"\n=== transparency-resolution rows, EIN {EIN} amount {AMT} ===")
    import glob
    for f in sorted(glob.glob("data/fy*/transparency-resolutions/fy*_transparency_all.csv")):
        for r in csv.DictReader(open(f, newline="", encoding="utf-8")):
            try:
                a = abs(int(float(r.get("amount") or 0)))
            except (TypeError, ValueError):
                continue
            if xlsxlib.norm_ein(r.get("ein")) == EIN and a == AMT:
                print(f"  {f.split('/')[1]} reso={r.get('resolution')} fy={r.get('fiscal_year')} "
                      f"org={r.get('organization','')[:70]!r} amt={r.get('amount')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
