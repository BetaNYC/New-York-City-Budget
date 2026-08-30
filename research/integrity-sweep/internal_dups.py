#!/usr/bin/env python3
"""The five (fy, ein, amount, name) tuples that appear more than once inside the absorbed sidecar.

Two designations of the same amount to the same grantee in one year are ordinary -- different
council members do it constantly -- so this asks the Council's own disclosure how many it
published, and where each sidecar row was absorbed from.
"""
import collections
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import xlsxlib                   # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon
SIDE = "data/recovered/schedule_c_absorbed_awards.csv"


def main():
    rows = list(csv.DictReader(open(SIDE, newline="", encoding="utf-8")))
    key = lambda r: (r["fiscal_year"], re.sub(r"\D", "", r["ein"]),
                     int(float(r["amount"])), canon(r["organization"]))
    cnt = collections.Counter(key(r) for r in rows)
    dups = {k for k, v in cnt.items() if v > 1}

    pub = {}
    for fy in sorted({k[0] for k in dups}):
        p = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
        tbl = collections.defaultdict(list)
        for rn, d in xlsxlib.dicts(p):
            ein = nm = mem = src = None
            amt = None
            for kk, v in d.items():
                kl = kk.strip().lower()
                if "fiscal conduit" in kl or "fc ein" in kl:
                    continue
                if ein is None and ("tax id" in kl or "ein" in kl):
                    ein = xlsxlib.norm_ein(v)
                if nm is None and "legal name" in kl:
                    nm = (v or "").strip()
                if mem is None and "council member" in kl:
                    mem = (v or "").strip()
                if src is None and kl == "source":
                    src = (v or "").strip()
                if amt is None and kl.startswith("amount"):
                    try:
                        amt = int(float(v))
                    except (TypeError, ValueError):
                        amt = None
            if ein and amt is not None and nm:
                tbl[(ein, amt, canon(nm))].append((mem or "?", src or "?"))
        pub[fy] = tbl

    for k in sorted(dups):
        fy, ein, amt, cn = k
        published = pub[fy].get((ein, amt, cn), [])
        print(f"FY{fy} ein={ein} ${amt:,} {cn[:40]}")
        print(f"   sidecar copies : {cnt[k]}   published designations: {len(published)} "
              f"{published[:4]}")
        for r in rows:
            if key(r) == k:
                print(f"   absorbed from {r['absorbed_from_file'].split('/')[1]}:"
                      f"{r['absorbed_from_line']} (host ein {r['absorbed_from_ein']}) "
                      f"conf={r['confidence']}")
        verdict = "OK" if len(published) >= cnt[k] else "OVER-EMITTED"
        print(f"   -> {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
