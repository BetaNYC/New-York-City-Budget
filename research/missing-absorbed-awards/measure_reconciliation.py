#!/usr/bin/env python3
"""
measure_reconciliation.py -- does adding the absorbed Schedule C awards move the award-row
sums toward the documents' printed totals, or past them?

Read-only. Touches nothing outside stdout. Two levels of comparison:

  CATEGORY level -- sum(award rows in a category) vs the printed category TOTAL in
    *_schedule_c_reconciliation.txt. This is the comparison DATA-ANOMALIES.md sec.20 names, and it
    is the WRONG instrument: most initiatives are lump sums to an agency with no per-grantee
    table in the PDF at all, so award rows cover only 27%-64% of printed dollars by design.
    Reported anyway, because "measured and rejected" beats "assumed away".

  INITIATIVE level -- sum(award rows under an initiative) vs that initiative's own printed
    amount in *_schedule_c_initiatives.csv. THIS is the real reconciliation target: where the
    PDF itemises an initiative at all, the itemisation is exhaustive, and 24%-77% of joined
    initiatives already balance to the dollar with no repair.

Absorbed awards are the (EIN, $amount) pairs sitting INSIDE an `organization` string -- the
org_merged defect. They are credited to the initiative of the row that swallowed them, which is
the initiative the PDF printed them under.

Join is exact on a normalised initiative name. Fuzzy/prefix joining was rejected: FY18 alone has
six "Crisis Management System - <sub-programme>" award labels whose parent is a single initiative
line, and a prefix join would silently pool them.

Usage: python3 research/missing-absorbed-awards/measure_reconciliation.py [--detail FY]
"""
import argparse, collections, csv, glob, os, re, sys

ABSORBED = re.compile(r'(\d{2}-?\d{7})\s*\*?\s*\$([\d,]+(?:\.\d{2})?)')
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")
# "NAME  <n,nnn,nnn>  <n,nnn,nnn>  OK|DIFF..." rows of the reconciliation report
RECON_ROW = re.compile(r"^(.*?)\s{2,}([\d,]+)\s+([\d,]+)\s+(OK|DIFF.*)$")
YEARS = [f"fy{n:02d}" for n in range(15, 28)]


def money(s):
    return int(float(str(s).replace(",", "").replace("$", "") or 0))


def canon(s):
    """Normalise an initiative name for JOINING only. Curly punctuation in the PDFs is
    inconsistent between the summary table and the body headers ('Alternatives to Incarceration
    (ATI's)' vs '(ATI’s)'), so fold it out before comparing."""
    s = (s or "").lower().replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", "", s)


def absorbed_pairs(org):
    """(ein, amount) awards swallowed into an organization string. Empty for a clean row."""
    if not (EIN_IN_TEXT.search(org) or "$" in org):
        return []
    return [(m.group(1), money(m.group(2))) for m in ABSORBED.finditer(org)]


def load_year(y):
    aw = f"data/{y}/schedule_c/{y}_schedule_c_awards.csv"
    iv = f"data/{y}/schedule_c/{y}_schedule_c_initiatives.csv"
    if not (os.path.exists(aw) and os.path.exists(iv)):
        return None
    awards = list(csv.DictReader(open(aw, encoding="utf-8")))
    inits = list(csv.DictReader(open(iv, encoding="utf-8")))
    return awards, inits


def printed_category_totals(y):
    """category -> printed TOTAL, from the year's reconciliation report."""
    p = f"data/{y}/schedule_c/{y}_schedule_c_reconciliation.txt"
    out = {}
    for ln in open(p, encoding="utf-8"):
        m = RECON_ROW.match(ln.rstrip())
        if not m:
            continue
        name = m.group(1).strip()
        if name.upper() in ("CATEGORY", "GRAND TOTAL"):
            continue
        out[name] = int(m.group(3).replace(",", ""))
    return out


def category_view(y, awards):
    printed = printed_category_totals(y)
    cur = collections.Counter()
    absd = collections.Counter()
    for r in awards:
        cur[r["category"]] += money(r["amount"])
        for _, amt in absorbed_pairs(r.get("organization", "")):
            absd[r["category"]] += amt
    return printed, cur, absd


def initiative_view(y, awards, inits):
    printed = collections.Counter()
    label = {}
    for r in inits:
        k = canon(r["initiative"])
        printed[k] += money(r["amount"])
        label.setdefault(k, r["initiative"])
    cur, n, absd, an = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    for r in awards:
        k = canon(r["initiative"])
        cur[k] += money(r["amount"])
        n[k] += 1
        for _, amt in absorbed_pairs(r.get("organization", "")):
            absd[k] += amt
            an[k] += 1
    joined = [k for k in cur if k and k in printed]
    return printed, label, cur, n, absd, an, joined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", help="fiscal year (e.g. fy17) to print per-initiative rows for")
    args = ap.parse_args()

    print("=" * 108)
    print("CATEGORY LEVEL -- award rows vs printed category TOTALs (all categories summed)")
    print("=" * 108)
    print(f"{'FY':<6}{'printed':>16}{'award rows':>16}{'gap':>16}{'absorbed':>14}{'gap after':>16}"
          f"{'cover now':>11}{'cover after':>12}")
    for y in YEARS:
        got = load_year(y)
        if not got:
            continue
        awards, _ = got
        printed, cur, absd = category_view(y, awards)
        P, C, A = sum(printed.values()), sum(cur.values()), sum(absd.values())
        print(f"{y:<6}{P:>16,}{C:>16,}{P - C:>16,}{A:>14,}{P - C - A:>16,}"
              f"{C / P:>10.1%}{(C + A) / P:>12.1%}")

    print()
    print("=" * 108)
    print("INITIATIVE LEVEL -- award rows vs the initiative's own printed amount (exact-name join)")
    print("=" * 108)
    print(f"{'FY':<6}{'joined':>8}{'bal now':>9}{'short':>7}{'over':>6}"
          f"{'printed':>15}{'awards':>15}{'gap':>14}{'absorbed':>13}{'gap after':>14}"
          f"{'newly bal':>11}{'newly over':>11}")
    tot = collections.Counter()
    for y in YEARS:
        got = load_year(y)
        if not got:
            continue
        awards, inits = got
        printed, label, cur, n, absd, an, joined = initiative_view(y, awards, inits)
        bal = short = over = newbal = newover = 0
        P = C = A = 0
        for k in joined:
            gap = printed[k] - cur[k]
            P += printed[k]; C += cur[k]; A += absd[k]
            if gap == 0:
                bal += 1
            elif gap > 0:
                short += 1
            else:
                over += 1
            if absd[k]:
                after = gap - absd[k]
                if after == 0:
                    newbal += 1
                elif after < 0 <= gap:
                    newover += 1
        tot["newbal"] += newbal; tot["newover"] += newover; tot["absorbed"] += A
        print(f"{y:<6}{len(joined):>8}{bal:>9}{short:>7}{over:>6}"
              f"{P:>15,}{C:>15,}{P - C:>14,}{A:>13,}{P - C - A:>14,}{newbal:>11}{newover:>11}")
    print(f"\ncorpus-wide: initiatives brought to an EXACT balance by the absorbed awards: "
          f"{tot['newbal']}   pushed past balance: {tot['newover']}   absorbed dollars: ${tot['absorbed']:,}")

    if args.detail:
        y = args.detail
        awards, inits = load_year(y)
        printed, label, cur, n, absd, an, joined = initiative_view(y, awards, inits)
        print()
        print("=" * 108)
        print(f"{y} per-initiative detail (rows where a gap or an absorbed award exists)")
        print("=" * 108)
        print(f"{'initiative':<50}{'printed':>12}{'awards':>12}{'gap':>12}"
              f"{'absorbed':>11}{'after':>12}  rows/abs")
        for k in sorted(joined, key=lambda k: -(printed[k] - cur[k])):
            gap = printed[k] - cur[k]
            if not gap and not absd[k]:
                continue
            print(f"{label[k][:48]:<50}{printed[k]:>12,}{cur[k]:>12,}{gap:>12,}"
                  f"{absd[k]:>11,}{gap - absd[k]:>12,}  {n[k]}/{an[k]}")
    return 0


def _selfcheck():
    """One runnable check: the absorbed-pair extractor on the canonical example and on the shapes
    that must NOT yield a pair. Run: python3 measure_reconciliation.py --selfcheck"""
    ex = "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"
    assert absorbed_pairs(ex) == [("13-3931074", 2076667)], absorbed_pairs(ex)
    chain = ("Harm Reduction Coalition 94-3204958 * $13,500 Housing Works, Inc. "
             "13-3584089 * $13,500 Kings County Hospital")
    assert absorbed_pairs(chain) == [("94-3204958", 13500), ("13-3584089", 13500)]
    # appendix shape: no hyphen in the EIN, cents on the amount
    assert absorbed_pairs("Asian Community United Society Inc. 264164117 * $10,000.00 To cover") \
        == [("264164117", 10000)]
    # prose that merely contains a dollar sign is NOT an absorbed award
    assert absorbed_pairs("subsidize the delivery of farm shares to $12 per share") == []
    # clean row
    assert absorbed_pairs("SCO Family of Services") == []
    # a 10-digit run is a mangled EIN, not a recoverable award -- must not match
    assert absorbed_pairs("Urban Health Plan, Inc. 15-24042810 $88,855 NYC MWBE Alliance") == []
    assert canon("Alternatives to Incarceration (ATI’s)") == canon("Alternatives to Incarceration (ATI's)")
    print("selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        _selfcheck()
    else:
        sys.exit(main())
