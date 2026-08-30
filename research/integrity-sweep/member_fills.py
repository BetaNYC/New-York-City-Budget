#!/usr/bin/env python3
"""Audit the 166 rows where the peel wrote a value into an empty `member` column.

The org-name half of the peel is corroborated by the Council's own disclosure. The MEMBER half
is not: the disclosure's own Council Member column was deliberately excluded from the join key
(roster-vintage drift), so nothing checked that the removed token names the actual sponsor.
This asks the disclosure anyway, for the rows where it can answer.
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

CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
SRC = "source/expense-funding-disclosure"


def disclosure_members():
    """(ein, amount) -> {council member string} straight from the workbooks."""
    out = collections.defaultdict(set)
    for p in sorted(glob.glob(os.path.join(SRC, "funded_disclosure_FY*.xlsx"))):
        for rn, d in xlsxlib.dicts(p):
            ein = amt = mem = None
            for k, v in d.items():
                kl = k.strip().lower()
                if "fiscal conduit" in kl or "fc ein" in kl:
                    continue
                if ein is None and ("tax id" in kl or "ein" in kl):
                    ein = xlsxlib.norm_ein(v)
                if mem is None and "council member" in kl:
                    mem = (v or "").strip()
                if amt is None and kl.startswith("amount"):
                    try:
                        amt = int(float(v))
                    except (TypeError, ValueError):
                        amt = None
            if ein and amt is not None and mem:
                out[(ein, amt)].add(mem)
    return out


def main():
    dm = disclosure_members()
    rows = [r for r in csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8"))
            if r["defect"] == "member_bleed" and "|member<-" in r["match_key"]]
    print(f"rows that gained a `member` from the peel: {len(rows)}")
    tally = collections.Counter()
    verdict = collections.Counter()
    examples = collections.defaultdict(list)
    for r in rows:
        tok = r["match_key"].split("|member<-")[1]
        tally[tok] += 1
        cand = dm.get((r["ein"], int(r["amount"])), set())
        if not cand:
            v = "no disclosure member"
        elif any(tok.lower() in c.lower() or c.lower() in tok.lower() for c in cand):
            v = "agrees with disclosure"
        else:
            v = "DISAGREES with disclosure"
        verdict[v] += 1
        examples[v].append((r, tok, sorted(cand)))

    print("\ntoken written into `member`:")
    for t, n in tally.most_common():
        print(f"  {t:<22} {n}")
    print("\nchecked against the disclosure's own Council Member column:")
    for v, n in verdict.most_common():
        print(f"  {v:<28} {n}")
    for v in ("DISAGREES with disclosure",):
        print(f"\n--- {v} ---")
        for r, tok, cand in examples[v][:25]:
            print(f"  {r['file'].split('/')[1]}:{r['line']} wrote member={tok!r} "
                  f"disclosure says {cand[:3]}")
            print(f"      org: {r['recovered_organization'][:60]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
