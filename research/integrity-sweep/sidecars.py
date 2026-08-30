#!/usr/bin/env python3
"""Test both sidecars for duplication against the per-year award corpus.

A sidecar that re-publishes an award already present in data/fy*/schedule_c/ double counts it
for any consumer that unions the two. Matching is deliberately fuzzy in three independent ways,
because an exact-tuple test would miss precisely the duplicates that matter:

  strict   (fy, ein, amount)
  loose    (fy, canon(organization), amount)      -- catches a different EIN formatting/typo
  rounded  (fy, ein, amount rounded to $100)      -- catches a rounded republication
  nameonly (fy, canon(organization))              -- upper bound; same grantee, same year
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
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def amt_of(r):
    try:
        return int(float(r.get("amount") or 0))
    except (TypeError, ValueError):
        return None


def fy_of(path):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", path)
    return 2000 + int(m.group(1)) if m else None


def corpus(kinds=("all",)):
    """Return per-year award rows, tagged by which file family they came from."""
    rows = []
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        fam = "appendix" if "appendix" in f else "awards"
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                rows.append((fy_of(f), fam, f, ln, norm_ein(r.get("ein")),
                             (r.get("organization") or "").strip(), amt_of(r)))
    return rows


def index(rows):
    ix = {"strict": collections.Counter(), "loose": collections.Counter(),
          "rounded": collections.Counter(), "nameonly": collections.Counter()}
    for fy, fam, f, ln, ein, org, amt in rows:
        if amt is None:
            continue
        ix["strict"][(fy, ein, amt)] += 1
        ix["loose"][(fy, canon(org), amt)] += 1
        ix["rounded"][(fy, ein, round(amt / 100) * 100)] += 1
        ix["nameonly"][(fy, canon(org))] += 1
    return ix


def probe(name, path, ix, corpus_rows):
    print(f"\n===== {name} =====")
    hits = {k: 0 for k in ix}
    money = {k: 0 for k in ix}
    n = 0
    total = 0
    per_year = collections.Counter()
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            fy = int(r["fiscal_year"])
            ein = norm_ein(r.get("ein"))
            org = (r.get("organization") or "").strip()
            amt = amt_of(r)
            if amt is None:
                continue
            n += 1
            total += amt
            per_year[fy] += 1
            keys = {"strict": (fy, ein, amt), "loose": (fy, canon(org), amt),
                    "rounded": (fy, ein, round(amt / 100) * 100),
                    "nameonly": (fy, canon(org))}
            for k, key in keys.items():
                if ix[k].get(key):
                    hits[k] += 1
                    money[k] += amt
    print(f"rows: {n:,}   dollars: ${total:,}")
    print(f"rows per fiscal year: {dict(sorted(per_year.items()))}")
    for k in ("strict", "loose", "rounded", "nameonly"):
        print(f"  collides on {k:<9} {hits[k]:6,} rows  (${money[k]:,})")
    return n, total


def main():
    rows = corpus()
    ix_all = index(rows)
    ix_app = index([x for x in rows if x[1] == "appendix"])
    ix_awd = index([x for x in rows if x[1] == "awards"])

    print("per-year corpus:", f"{len(rows):,} rows",
          f"appendix={sum(1 for x in rows if x[1] == 'appendix'):,}",
          f"awards={sum(1 for x in rows if x[1] == 'awards'):,}")
    print("per-year corpus dollars:",
          f"${sum(x[6] or 0 for x in rows):,}")

    for label, ix in (("vs ENTIRE per-year corpus", ix_all),
                      ("vs per-year APPENDIX files only", ix_app),
                      ("vs per-year AWARDS files only", ix_awd)):
        print(f"\n############ {label} ############")
        probe("schedule_c_absorbed_awards.csv",
              "data/recovered/schedule_c_absorbed_awards.csv", ix, rows)
        probe("schedule_c_appendix_recovered.csv",
              "data/recovered/schedule_c_appendix_recovered.csv", ix, rows)

    # Which years actually have populated appendix files?
    print("\n===== populated per-year appendix files =====")
    for f in sorted(glob.glob("data/fy*/schedule_c/*appendix*.csv")):
        with open(f, newline="", encoding="utf-8") as fh:
            d = list(csv.DictReader(fh))
        tot = sum(amt_of(r) or 0 for r in d)
        print(f"  {f:<52} rows={len(d):5d}  ${tot:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
