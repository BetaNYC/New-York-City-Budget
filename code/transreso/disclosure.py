"""
Stage 9 for transparency charts -- what each resolution adds, removes and moves, checked
against outside lists. Report-only: nothing here changes a PDF value (PLAN §1 rule 3).

Two questions, both with the one join rule (DATA-ANOMALIES §23): (EIN, amount) as a multiset,
never EIN alone, never the member; the City's EIN 13-6400434 also needs a name match.

1. **Did each designation land?** Every positive row on a designation chart for fiscal year Y
   (not an agency's side of a transfer) is looked for in the Council's expense disclosure for
   Y (data/fyNN/expense_disclosure/). The FY2026 disclosure was taken 2026-07-15, after the
   last FY2026 resolution (2026-06-30), so every surviving FY2026 designation should be in it.
   (Each year's README says when its disclosure snapshot was taken.)
   Rows are taken newest resolution first, so a key that was designated twice is matched by
   the latest designation. A row that does not match gets one reason:
     later_rescinded   a later resolution rescinds the same (EIN, amount)
     amount_differs    the EIN is in the disclosure, at other amounts
     ein_not_in_disclosure
     city_ein_name_mismatch / key_already_claimed
2. **Where did each rescission come from?** Every negative row on a designation chart (not an
   agency's side) is looked for, as (EIN, |amount|), among earlier designations: the same
   resolution's own earlier rows, earlier resolutions' positive rows, and, for the document
   year itself, that year's committed Schedule C award files (data/retired/fyNN/schedule_c/,
   or data/fyNN/schedule_c/ for a year not yet redone; PDF-derived by the old parser and not
   trusted as values; used here as a cross-check only). Reasons: earlier_resolution,
   schedule_c, partial (the EIN has a larger earlier amount), not_found.
"""
import csv
import os
import re
from collections import defaultdict
from decimal import Decimal

from retired_paths import family_dir
from schedc.config import ROOT

CITY_EIN = "136400434"


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_disclosure(fy):
    yy = f"fy{fy % 100:02d}"
    path = os.path.join(ROOT, "data", yy, "expense_disclosure", f"{yy}_expense_awards.csv")
    if not os.path.exists(path):
        return None
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ein = re.sub(r"\D", "", r["ein"] or "")
            try:
                amt = int(Decimal(r["amount"]))
            except Exception:
                continue
            out.append(dict(ein=ein, amount=amt, name=r["legal_name"], status=r["status_norm"],
                            row=int(r["source_row"]), source=r["source"]))
    return out


def load_schedule_c(fy):
    """(EIN, amount) multiset from the committed Schedule C award files of fiscal year `fy`."""
    yy = f"fy{fy % 100:02d}"
    d = family_dir(os.path.join(ROOT, "data"), yy, "schedule_c")
    keys = defaultdict(int)
    for fn in (f"{yy}_schedule_c_awards.csv", f"{yy}_appendix_a_aging.csv",
               f"{yy}_appendix_b_local.csv", f"{yy}_appendix_c_youth.csv"):
        with open(os.path.join(d, fn), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ein = re.sub(r"\D", "", r["ein"] or "")
                try:
                    keys[(ein, int(Decimal(r["amount"])))] += 1
                except Exception:
                    pass
    return keys


def _is_award(r):
    return r["chart_kind"] == "designation" and r["amount"] is not None and not r["agency_side"]


def align(rows, fy=2026):
    """`fy` is the document year (its Schedule C is the rescission cross-check). Returns dict(per_row{row_id: (status, reason, disclosure_row)}, disc_years, summary)."""
    per_row, summary = {}, {}
    years = sorted({r["budget_fiscal_year"] for r in rows if r["budget_fiscal_year"]})
    for fy in years:
        disc = load_disclosure(fy)
        mine = [r for r in rows if r["budget_fiscal_year"] == fy and _is_award(r)]
        if disc is None:
            for r in mine:
                per_row[r["row_id"]] = ("no_disclosure", f"no fy{fy % 100:02d} disclosure in data/", "")
            summary[fy] = dict(disclosure_rows=0)
            continue
        by_key = defaultdict(list)
        for i, d in enumerate(disc):
            by_key[(d["ein"], d["amount"])].append(i)
        taken = set()
        pos = sorted((r for r in mine if r["amount"] > 0),
                     key=lambda r: (-r["resolution_seq"], r["pdf_page"], r["row_index"]))
        neg = [r for r in mine if r["amount"] < 0]
        for r in pos:
            cands = [i for i in by_key.get((r["ein"], r["amount"]), ())
                     if i not in taken and (r["ein"] != CITY_EIN or
                                            (norm_name(disc[i]["name"]) and
                                             norm_name(r["org"]).startswith(norm_name(disc[i]["name"]))))]
            if cands:
                i = min(cands, key=lambda i: ({"cleared": 0, "pending": 1}.get(disc[i]["status"], 2), disc[i]["row"]))
                taken.add(i)
                per_row[r["row_id"]] = ("matched", disc[i]["status"], disc[i]["row"])
                continue
            later = any(n["ein"] == r["ein"] and -n["amount"] == r["amount"] and
                        n["resolution_seq"] > r["resolution_seq"] for n in neg)
            if later:
                reason = "later_rescinded"
            elif (r["ein"], r["amount"]) in by_key:
                reason = "city_ein_name_mismatch" if r["ein"] == CITY_EIN else "key_already_claimed"
            elif any(d["ein"] == r["ein"] for d in disc):
                reason = "amount_differs"
            else:
                reason = "ein_not_in_disclosure"
            per_row[r["row_id"]] = ("unmatched", reason, "")
        summary[fy] = dict(disclosure_rows=len(disc), positive_rows=len(pos),
                           matched=sum(1 for r in pos if per_row[r["row_id"]][0] == "matched"))

    # Rescission origins.
    sc = load_schedule_c(fy)
    for r in rows:
        if not (_is_award(r) and r["amount"] < 0):
            continue
        key = (r["ein"], -r["amount"])
        earlier = [x for x in rows if _is_award(x) and x["amount"] > 0 and
                   x["budget_fiscal_year"] == r["budget_fiscal_year"] and x["ein"] == r["ein"] and
                   (x["resolution_seq"], x["pdf_page"], x["row_index"]) <
                   (r["resolution_seq"], r["pdf_page"], r["row_index"])]
        if any(x["amount"] == -r["amount"] for x in earlier):
            reason = "earlier_resolution"
        elif r["budget_fiscal_year"] == fy and sc.get(key):
            reason = "schedule_c"
        elif any(x["amount"] > -r["amount"] for x in earlier) or (
                r["budget_fiscal_year"] == fy and
                any(k[0] == r["ein"] and k[1] > -r["amount"] for k in sc)):
            reason = "partial"
        else:
            reason = "not_found"
        per_row[r["row_id"]] = ("rescission", reason, "")
    return dict(per_row=per_row, summary=summary)


def retired_path(fy):
    yy = f"fy{fy % 100:02d}"
    d = family_dir(os.path.join(ROOT, "data"), yy, "transparency-resolutions")
    return os.path.relpath(os.path.join(d, f"{yy}_transparency_all.csv"), ROOT)


def compare_retired(rows, fy=2026):
    """The retired data/retired/fyNN/transparency-resolutions/fyNN_transparency_all.csv (old parser)
    against these rows, as a (resolution, EIN, amount) multiset. None when the year has no
    retired file (FY2025 was never parsed by the old parser)."""
    path = os.path.join(ROOT, retired_path(fy))
    if not os.path.exists(path):
        return None
    old = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                old[(int(r["resolution"]), re.sub(r"\D", "", r["ein"]), int(r["amount"]))].append(r)
            except ValueError:
                old[(int(r["resolution"]), "", None)].append(r)
    new = defaultdict(list)
    for r in rows:
        new[(r["resolution_seq"], r["ein"], r["amount"])].append(r)
    only_new, only_old, matched = [], [], 0
    for k in sorted(set(old) | set(new), key=str):
        a, b = new.get(k, []), old.get(k, [])
        matched += min(len(a), len(b))
        only_new += a[len(b):]
        only_old += b[len(a):]
    only_new.sort(key=lambda r: (r["resolution_seq"], r["pdf_page"], r["row_index"]))
    return dict(old_rows=sum(len(v) for v in old.values()), new_rows=len(rows), matched=matched,
                only_new=only_new, only_old=only_old)
