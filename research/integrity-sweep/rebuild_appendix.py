#!/usr/bin/env python3
"""Rebuild data/recovered/schedule_c_appendix_recovered.csv with a reference-positioned xlsx
read and diff it against the published sidecar.

build_appendix_from_disclosure.py positions cells by ordinal position among the <c> elements
present in the XML. FY2016's sheet omits empty cells on 274 rows, which shifts every value after
the gap. This measures what that cost.
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

OUT = "data/recovered/schedule_c_appendix_recovered.csv"
STREAMS = {"Local": "appendix_b_local", "Aging": "appendix_a_aging", "Youth": "appendix_c_youth"}


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
                ein = re.sub(r"\D", "", r.get("ein") or "")
                try:
                    amt = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                if ein:
                    keys.add((ein, amt))
    return keys


def build():
    rows = []
    for fy in (2015, 2016, 2017, 2019, 2020):
        present = corpus_keys(fy)
        path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
        for rn, d in xlsxlib.dicts(path):
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
                continue
            rows.append({"fiscal_year": str(fy), "stream": STREAMS[src], "organization": name,
                         "ein": ein, "amount": amt,
                         "member": (pick(d, ("council member",)) or "").strip(),
                         "status": (pick(d, ("status",)) or "").strip(),
                         "xlsx_row": rn})
    return rows


def sig(r):
    return (r["fiscal_year"], r["stream"], r["ein"], int(r["amount"]), r["organization"].strip())


def main():
    strict = build()
    pub = list(csv.DictReader(open(OUT, newline="", encoding="utf-8")))
    print(f"published sidecar : {len(pub):,} rows  ${sum(int(r['amount']) for r in pub):,}")
    print(f"strict rebuild    : {len(strict):,} rows  ${sum(r['amount'] for r in strict):,}")

    ps, ss = collections.Counter(sig(r) for r in pub), collections.Counter(sig(r) for r in strict)
    only_pub = +ps - ss
    only_str = +ss - ps
    print(f"\nrows in the PUBLISHED sidecar that a correct read does not produce: "
          f"{sum(only_pub.values()):,}  ${sum(k[3] * v for k, v in only_pub.items()):,}")
    print(f"rows a correct read produces that the sidecar is MISSING          : "
          f"{sum(only_str.values()):,}  ${sum(k[3] * v for k, v in only_str.items()):,}")

    by_fy = collections.Counter()
    for k, v in only_pub.items():
        by_fy[k[0]] += v
    print("  published-only by FY:", dict(sorted(by_fy.items())))
    by_fy = collections.Counter()
    for k, v in only_str.items():
        by_fy[k[0]] += v
    print("  strict-only by FY   :", dict(sorted(by_fy.items())))

    print("\nfirst 12 published-only rows (these are the ones a shifted read invented or mangled):")
    for k, v in list(only_pub.items())[:12]:
        print(f"  FY{k[0]} {k[1]:<18} ein={k[2]} ${k[3]:>10,}  {k[4][:50]!r}")
    print("\nfirst 12 strict-only rows:")
    for k, v in list(only_str.items())[:12]:
        print(f"  FY{k[0]} {k[1]:<18} ein={k[2]} ${k[3]:>10,}  {k[4][:50]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
