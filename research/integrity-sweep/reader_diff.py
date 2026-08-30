#!/usr/bin/env python3
"""Compare the repair scripts' xlsx reader against an independent, cell-reference-based one.

Original reader (code/recover_org_names.py:read_workbook) positions cells by ordinal
position among the <c> elements that are PRESENT in the XML. xlsx omits empty cells, so any
row with an interior gap shifts every value after the gap one or more columns left.

This script quantifies the consequence for the (EIN, amount) -> legal-name lookup that every
repair on this branch was keyed on.
"""
import glob
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
import xlsxlib
import recover_org_names as R


# ---- independent lookup -------------------------------------------------------------------
GRANTEE_EIN = ("ein", "tax id")
CONDUIT = ("fiscal conduit", "fc ein")


def strict_lookup(path):
    """(ein, amount) -> {legal name}, with the grantee EIN column pinned and the fiscal-conduit
    EIN column explicitly excluded."""
    out = {}
    for rn, d in xlsxlib.dicts(path):
        ein = name = amt = None
        for k, v in d.items():
            kl = k.strip().lower()
            if any(c in kl for c in CONDUIT):
                continue                       # never let a conduit column answer
            if ein is None and any(n in kl for n in GRANTEE_EIN):
                ein = xlsxlib.norm_ein(v)
            if name is None and "legal name" in kl:
                name = (v or "").strip()
            if amt is None and kl.startswith("amount"):
                try:
                    amt = int(float(v))
                except (TypeError, ValueError):
                    amt = None
        if ein and name and amt is not None:
            out.setdefault((ein, amt), set()).add(name)
    return out


def main():
    files = sorted(glob.glob("source/expense-funding-disclosure/funded_disclosure_FY*.xlsx"))
    orig, strict = {}, {}
    for p in files:
        o = R.read_workbook(p)
        s = strict_lookup(p)
        for k, v in o.items():
            orig.setdefault(k, set()).update(v)
        for k, v in s.items():
            strict.setdefault(k, set()).update(v)
        only_o = len(set(o) - set(s))
        only_s = len(set(s) - set(o))
        diff = sum(1 for k in set(o) & set(s) if o[k] != s[k])
        print(f"{os.path.basename(p):34s} orig_keys={len(o):6d} strict_keys={len(s):6d} "
              f"orig_only={only_o:5d} strict_only={only_s:5d} name_set_differs={diff:5d}")

    print()
    print(f"TOTAL orig keys   : {len(orig):,}")
    print(f"TOTAL strict keys : {len(strict):,}")
    print(f"keys only in orig : {len(set(orig) - set(strict)):,}")
    print(f"keys only in strict: {len(set(strict) - set(orig)):,}")
    return orig, strict


if __name__ == "__main__":
    main()
