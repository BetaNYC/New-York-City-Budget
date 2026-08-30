#!/usr/bin/env python3
"""Decide whether the absorbed sidecar's suspicious rows are real duplicates.

Test: for a given (fiscal year, EIN, amount), how many designations does the Council's own
disclosure record? Compare that with how many rows the live corpus plus the sidecar together
now carry. corpus+sidecar > disclosure means the union over-counts.
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
import xlsxlib   # noqa: E402

SIDE = "data/recovered/schedule_c_absorbed_awards.csv"


def norm(v):
    return re.sub(r"\D", "", v or "")


def amt(r):
    try:
        return int(float(r.get("amount") or 0))
    except (TypeError, ValueError):
        return None


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def disclosure_counts(fy):
    """(ein, amount) -> number of published designation rows, with the member and name of each."""
    out = collections.defaultdict(list)
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return out
    for rn, d in xlsxlib.dicts(path):
        ein = nm = mem = src = None
        a = None
        for k, v in d.items():
            kl = k.strip().lower()
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
            if a is None and kl.startswith("amount"):
                try:
                    a = int(float(v))
                except (TypeError, ValueError):
                    a = None
        if ein and a is not None and nm:
            out[(ein, a)].append((mem or "", nm, src or ""))
    return out


def main():
    live = collections.defaultdict(list)
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                live[(fy_of(f), norm(r.get("ein")), amt(r))].append((f, ln))

    side = list(csv.DictReader(open(SIDE, newline="", encoding="utf-8")))
    sidecnt = collections.Counter((int(r["fiscal_year"]), norm(r["ein"]), amt(r)) for r in side)

    dc = {fy: disclosure_counts(fy) for fy in (2016, 2017, 2018, 2019)}

    over = []
    for (fy, ein, a), n_side in sorted(sidecnt.items()):
        n_live = len(live.get((fy, ein, a), []))
        n_pub = len(dc.get(fy, {}).get((ein, a), []))
        if n_live + n_side > n_pub:
            over.append((fy, ein, a, n_live, n_side, n_pub))

    print(f"(fy, ein, amount) keys in the absorbed sidecar: {len(sidecnt):,}")
    print(f"keys where live + sidecar EXCEEDS the number the Council published: {len(over)}")
    excess_rows = sum(nl + ns - np for _, _, _, nl, ns, np in over)
    excess_money = sum(a * (nl + ns - np) for _, _, a, nl, ns, np in over)
    print(f"excess rows: {excess_rows}   excess dollars: ${excess_money:,}")
    print()
    print(f"{'FY':<6}{'EIN':<12}{'amount':>12}  live side pub")
    for fy, ein, a, nl, ns, np in over:
        names = dc.get(fy, {}).get((ein, a), [])
        print(f"{fy:<6}{ein:<12}{a:>12,}  {nl:>4} {ns:>4} {np:>3}   "
              f"{[n[1][:34] for n in names[:2]]}")
        for f, ln in live.get((fy, ein, a), [])[:2]:
            print(f"        live row {f.split('/')[1]}:{ln}")
        for r in side:
            if (int(r["fiscal_year"]), norm(r["ein"]), amt(r)) == (fy, ein, a):
                print(f"        sidecar  {r['organization'][:44]!r} "
                      f"from {r['absorbed_from_file'].split('/')[1]}:{r['absorbed_from_line']} "
                      f"conf={r['confidence']} confirmed={r['disclosure_confirmed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
