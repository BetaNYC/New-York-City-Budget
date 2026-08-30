#!/usr/bin/env python3
"""The single hard duplicate: FY2017, Central Astoria Local Development Coalition, $29,729.

Prints the neighbourhood of the award rows, the sidecar entry, and every FY2017 disclosure row
naming that organization, so the duplicate can be judged rather than asserted.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsxlib  # noqa: E402

AW = "data/fy17/schedule_c/fy17_schedule_c_awards.csv"


def main():
    rows = list(csv.DictReader(open(AW, newline="", encoding="utf-8")))
    print("=== fy17_schedule_c_awards.csv lines 157-164 (csv line numbers) ===")
    for ln in range(157, 165):
        r = rows[ln - 2]
        print(f"  {ln}: init={r.get('initiative','')[:26]!r} member={r.get('member','')!r} "
              f"org={r.get('organization','')[:52]!r} ein={r.get('ein')} amt={r.get('amount')}")

    print("\n=== sidecar rows absorbed from fy17 lines 159-163 ===")
    for r in csv.DictReader(open("data/recovered/schedule_c_absorbed_awards.csv",
                                 newline="", encoding="utf-8")):
        if "fy17" in r["absorbed_from_file"] and 159 <= int(r["absorbed_from_line"]) <= 163:
            print(f"  from line {r['absorbed_from_line']}: {r['organization'][:50]!r} "
                  f"ein={r['ein']} ${int(r['amount']):,} conf={r['confidence']} "
                  f"confirmed={r['disclosure_confirmed']} initiative={r['initiative'][:30]!r}")

    print("\n=== every FY2017 disclosure row naming Central Astoria ===")
    p = "source/expense-funding-disclosure/funded_disclosure_FY2017.xlsx"
    for rn, d in xlsxlib.dicts(p):
        nm = ""
        for k, v in d.items():
            if "legal name" in k.strip().lower():
                nm = v
                break
        if "central astoria" in (nm or "").lower():
            print(f"  xlsx row {rn}: " + " | ".join(
                f"{k}={v}" for k, v in d.items()
                if k.strip().lower() in ("source", "council members", "council member",
                                         "legal name of organization", "ein", "amount",
                                         "status", "program name")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
