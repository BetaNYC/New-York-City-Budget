#!/usr/bin/env python3
"""
inventory_absorbed.py — Q1: exactly which awards did the Schedule C parser absorb, and which
of those have no row anywhere in data/?

READ-ONLY on data/. Writes one CSV next to this file. Not wired into the build.

THE DEFECT
  The parser finds an award as "EIN followed by amount". Where the PDF prints an asterisk, a
  program name, or a footnote marker between the two, the pattern misses and that award's
  entire printed text is absorbed into the next row that DOES match:

      row:  ein 11-3305406  amount 2,076,666
      org:  "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"

  Read left to right: a NAME, then THAT NAME'S ein and amount, then the next name. So the
  TRAILING name is the surviving row (its ein/amount are the row's own columns) and every
  ein/amount printed INSIDE the text is a separate award that may have been lost.

WHY THE PAIRING IS A WALK, NOT A REGEX
  Three printed variants must be read by one pass:
      "<name> <ein> * $<amt>"               common
      "<name> <ein> $<amt>"                 no asterisk
      "<name> <ein> <program name> $<amt>"  a program sits between ein and amount
  One regex spanning ein..amount either misses the third, or -- made permissive -- lets an ein
  claim an amount belonging to a LATER award. So this walks eins in order and bounds each
  amount search at the NEXT ein. An ein can only claim an amount printed before the next ein
  appears. That bound is the whole safety of the pairing; an ein with no amount inside its
  window is reported as an orphan, never guessed at.

THE KEY, AND THE CORRECTION THIS SCRIPT MAKES TO IT
  code/recover_org_names.py established (EIN, amount) as the award key, because EIN alone is
  not safe: fiscal sponsors pass funds through for many grantees, and 13-2612524 carries 229
  distinct names in this corpus. That reasoning is sound and is kept.

  But (EIN, amount) is not sufficient for a PRESENCE test, and this is the central measured
  finding of this inventory. Council initiatives fund the same organization at the same
  standard amount year after year -- $29,730 per provider in Community Housing Preservation
  Strategies, for instance, recurs across FY2017-FY2020. So a FY2016 absorbed award tests as
  "already present" against a FY2019 row that is a DIFFERENT award. Measured below: the
  year-agnostic test calls 406 of 647 triples present; adding fiscal year drops that to 5.
  Both numbers are printed, because the difference IS the finding.
"""
import csv, glob, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "absorbed_triples_inventory.csv")

# validate_data.py:353's org_merged trigger, reproduced exactly so this operates on the same
# 303 rows the advisory reports and no others.
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")
# An EIN as printed: hyphenated in the Schedule C body, bare 9 digits in the FY18 Appendix A
# stream. Guarded both sides so a 9-digit run inside a longer number is not mistaken for one.
EIN = re.compile(r"(?<![\d-])(\d{2}-\d{7}|\d{9})(?![\d-])")
AMT = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def to_amt(v):
    try:
        return int(round(float(str(v).replace(",", "").replace("$", "").strip())))
    except (TypeError, ValueError):
        return None


def award_files():
    """Per-year awards + the three appendices. Initiatives carry no EIN; reconciliation is prose."""
    return [f for f in sorted(glob.glob("data/fy*/schedule_c/*.csv"))
            if "initiatives" not in f and "reconcil" not in f]


def fy_of(path):
    return "FY20" + re.search(r"/fy(\d\d)/", path).group(1)


def extract(text):
    """Every (ein, amount, name) absorbed into one free-text field, in printed order.

    Returns (triples, orphan_eins). See module docstring for why the window is bounded at the
    next EIN.
    """
    text = text or ""
    eins = list(EIN.finditer(text))
    triples, orphans, cut = [], [], 0
    for i, m in enumerate(eins):
        stop = eins[i + 1].start() if i + 1 < len(eins) else len(text)
        a = AMT.search(text, m.end(), stop)
        # ponytail: trailing '.' is NOT stripped -- "Inc." ends in one and it is part of the name.
        name = text[cut:m.start()].lstrip(" *,;.-\t").rstrip(" *,;-\t")
        amt = to_amt(a.group(1)) if a else None
        if amt is None:
            orphans.append(dict(ein_printed=m.group(1), name=name))
            continue
        triples.append(dict(ein=norm_ein(m.group(1)), ein_printed=m.group(1), amount=amt,
                            name=name))
        cut = a.end()
    return triples, orphans


def present_index():
    """Two indexes over every award row in data/: keyed with and without fiscal year.

    Counts, not sets, so multiplicity stays visible. The combined roll-up is included for the
    year-agnostic index; it is derived from the per-year files and carries its own `year`
    column, which feeds the year-scoped index.
    """
    with_fy, any_fy = Counter(), Counter()
    for f in award_files():
        fy = fy_of(f)
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                e, a = norm_ein(r.get("ein")), to_amt(r.get("amount"))
                if len(e) == 9 and a is not None:
                    with_fy[(fy, e, a)] += 1
                    any_fy[(e, a)] += 1
    combined = "data/combined/all_years_awards.csv"
    if os.path.exists(combined):
        with open(combined, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                e, a = norm_ein(r.get("ein")), to_amt(r.get("amount"))
                if len(e) == 9 and a is not None:
                    with_fy[(r.get("year") or "?", e, a)] += 1
                    any_fy[(e, a)] += 1
    return with_fy, any_fy


def populations():
    """Three populations, kept apart because they have different standing.

    flagged   -- the 303 rows validate_data.py reports as org_merged.
    unflagged -- rows with a CLEAN `organization` but absorbed text in `program`/`purpose`.
                 Same defect, different column; the advisory never fires on them.
    """
    flagged, unflagged = [], []
    for f in award_files():
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = r.get("organization") or ""
                if EIN_IN_TEXT.search(org) or "$" in org:
                    flagged.append((f, ln, r))
                elif any(EIN.search(r.get(c) or "") and "$" in (r.get(c) or "")
                         for c in ("program", "purpose")):
                    unflagged.append((f, ln, r))
    return flagged, unflagged


def harvest(rows, cols, scope):
    triples, orphans, empty = [], [], []
    for f, ln, r in rows:
        got = False
        for c in cols:
            t, o = extract(r.get(c) or "")
            for x in t + o:
                x.update(file=f, line=ln, column=c, year=fy_of(f), scope=scope,
                         host_ein=norm_ein(r.get("ein")), host_amount=to_amt(r.get("amount")))
            triples += t
            orphans += o
            got = got or bool(t)
        if not got and cols == ("organization",):
            empty.append((f, ln, r.get("organization") or ""))
    return triples, orphans, empty


def band(label, triples, with_fy, any_fy):
    a_any = [t for t in triples if any_fy[(t["ein"], t["amount"])] == 0]
    a_fy = [t for t in triples if with_fy[(t["year"], t["ein"], t["amount"])] == 0]
    print(f"\n=== {label}")
    print(f"  triples extracted                         : {len(triples):>6,}")
    print(f"  present somewhere in data/ (ein, amount)   : {len(triples) - len(a_any):>6,}"
          f"   -> ABSENT {len(a_any):,}")
    print(f"  present in their OWN FY (fy, ein, amount)  : {len(triples) - len(a_fy):>6,}"
          f"   -> ABSENT {len(a_fy):,}")
    for tag, absent in (("year-agnostic", a_any), ("year-scoped", a_fy)):
        uniq = {}
        for t in absent:
            uniq.setdefault((t["year"], t["ein"], t["amount"]), t)
        by = defaultdict(lambda: [0, 0])
        for (y, _, amt) in uniq:
            by[y][0] += 1
            by[y][1] += amt
        tot = sum(v[1] for v in by.values())
        print(f"    [{tag}] distinct absent awards: {len(uniq):,}   dollars ${tot:,}")
        for y in sorted(by):
            print(f"        {y}  {by[y][0]:>4,} awards   ${by[y][1]:>14,}")
    return a_any, a_fy


def main():
    with_fy, any_fy = present_index()
    print(f"award rows indexed: (fy, ein, amount) keys {len(with_fy):,} / "
          f"(ein, amount) keys {len(any_fy):,}")

    flagged, unflagged = populations()
    print(f"org_merged rows (advisory)                 : {len(flagged):,}")
    print(f"rows with absorbed text the advisory MISSES : {len(unflagged):,}")

    org_t, org_o, org_empty = harvest(flagged, ("organization",), "q1_organization")
    spill_t, _, _ = harvest(flagged, ("program", "purpose"), "spill_same_rows")
    unf_t, _, _ = harvest(unflagged, ("program", "purpose"), "unflagged_rows")

    band("Q1 SCOPE - organization column of the 303 org_merged rows", org_t, with_fy, any_fy)
    band("same 303 rows, absorbed text that spilled into program/purpose", spill_t, with_fy, any_fy)
    band(f"the {len(unflagged)} rows the org_merged advisory never flags", unf_t, with_fy, any_fy)
    all_t = org_t + spill_t + unf_t
    band("CORPUS TOTAL", all_t, with_fy, any_fy)

    print(f"\norg_merged rows yielding NO triple: {len(org_empty)}")
    for f, ln, o in org_empty:
        why = "malformed EIN" if EIN_IN_TEXT.search(o) or re.search(r"\d{2}-\d{8,}", o) \
            else "prose with '$', no EIN - advisory false positive"
        print(f"  {f}:{ln}  [{why}]  {o[:95]!r}")

    print(f"\norphan EINs (no amount before the next EIN): {len(org_o)}")
    for x in org_o:
        print(f"  {x['file']}:{x['line']} {x['ein_printed']} after {x['name'][:55]!r}")

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["scope", "year", "file", "line", "column",
                                           "ein", "ein_printed", "amount", "name",
                                           "host_ein", "host_amount",
                                           "present_any_year", "present_same_year"])
        w.writeheader()
        for t in all_t:
            w.writerow({**t,
                        "present_any_year": any_fy[(t["ein"], t["amount"])],
                        "present_same_year": with_fy[(t["year"], t["ein"], t["amount"])]})
    print(f"\nwrote {len(all_t):,} triples -> {OUT}")


def self_check():
    """One runnable check on the parser: the three printed variants, the window bound, and the
    claim that a grantee's name is printed immediately BEFORE its own EIN."""
    t, o = extract("Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services")
    assert not o and t == [dict(ein="133931074", ein_printed="13-3931074", amount=2076667,
                                name="Bronx Defenders")], t

    t, _ = extract("Make the Road New York 113344389 * $52,692 New York Immigration Coalition")
    assert (t[0]["ein"], t[0]["amount"]) == ("113344389", 52692), t

    # program name between EIN and amount; and a name read after a consumed amount
    t, _ = extract("East Flatbush Village, Inc. 80-0612019 Meyer Levin High School $18,000 "
                   "Afro-Latin Jazz Alliance of New York, Inc. 45-3665976 Brownsville Academy $18,000 X")
    assert [x["ein"] for x in t] == ["800612019", "453665976"], t
    assert t[1]["name"] == "Afro-Latin Jazz Alliance of New York, Inc.", t[1]["name"]

    t, _ = extract("Vocal Ease, Inc. 371469320 * $3,500.00 Funding will be used")
    assert t[0]["amount"] == 3500, t

    # THE WINDOW BOUND: without it, 11-1111111 would steal the next award's $500.
    t, o = extract("Alpha 11-1111111 Beta 22-2222222 * $500 Gamma")
    assert [x["ein"] for x in t] == ["222222222"] and t[0]["amount"] == 500, t
    assert [x["ein_printed"] for x in o] == ["11-1111111"], o

    # prose with a '$' and no EIN yields nothing (the FY24-FY26 advisory false positives)
    assert extract("subsidize farm shares to $12 per share for low income")[0] == []
    # a 9-digit run inside a longer number is not an EIN
    assert extract("code 1234567890123 $5")[0] == []
    print("self-check OK")


if __name__ == "__main__":
    sys.exit(self_check() if "--self-check" in sys.argv else main())
