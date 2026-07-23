"""
Stage 7 -- the reconciliation and OCR-quality report.

Two things are being reported, and they must not be confused with each other.

1. RECONCILIATION. Every other Transparency-Resolution year is flatly NOT RECONCILABLE --
   the documents print no totals. FY09 is the exception: several charts print a total line
   ($500,000.00 on the Veterans Resource Center chart; $0.00 on a net-zero transfer chart).
   Where a total is printed we check it EXACTLY, and that check is the strongest available
   evidence that the OCR read the dollar figures correctly. Charts with no printed total
   remain NOT RECONCILABLE, exactly as in FY10-FY24.

2. OCR QUALITY. FY09 figures are model-read, not text-layer-extracted, so the report
   states plainly how confident the reading was and how many values a human still needs to
   confirm. Same spirit as the HIGH/MODERATE/LOW org-text confidence band the other years
   carry -- the caveat travels with the data.
"""
from collections import Counter

from .assemble import (FLAG_AGENCY, FLAG_AMOUNT, FLAG_CODE, FLAG_EIN, FLAG_LOWCONF,
                       FLAG_MEMBER)

FLAG_LABELS = [
    (FLAG_EIN, "EIN failed its ##-####### shape check"),
    (FLAG_AMOUNT, "amount failed its $#,###.## shape check"),
    (FLAG_CODE, "Agy #/U/A not a 3-digit code"),
    (FLAG_AGENCY, "agency code not in the FY10-FY27 agency vocabulary"),
    (FLAG_MEMBER, "member cell is not name-shaped"),
    (FLAG_LOWCONF, "a cell fell below the confidence threshold"),
]


def quality_band(flag_rate, mean_conf):
    """Same three-band vocabulary the other years use, so the label means one thing across
    the repo."""
    if flag_rate <= 0.02 and mean_conf >= 0.90:
        return "HIGH"
    if flag_rate <= 0.08 and mean_conf >= 0.80:
        return "MODERATE"
    return "LOW"


def _fmt_money(v):
    return f"${v:,}" if v >= 0 else f"(${abs(v):,})"


def build_report(prefix, per_reso, all_rows, reviews, page_kinds, conf_samples,
                 min_conf, member_hits=0, member_misses=0):
    """Render the full reconciliation text. `per_reso` is [(resolution, date, rows, totals)]."""
    L = []
    A = L.append

    A(f"{prefix.upper()} TRANSPARENCY RESOLUTIONS -- OCR EXTRACTION REPORT")
    A("=" * 72)
    A("")
    A("SOURCE: 300-dpi bitonal scans with no text layer (source/FY09/transparency-resolutions/).")
    A("METHOD: docTR OCR over ruled-grid cells -- see code/PARSING.md, 'OCR pipeline'.")
    A("")
    A("*** These figures are MODEL-READ, not extracted from a PDF text layer. Every other")
    A("*** fiscal year in this repo is read deterministically from the document's own text")
    A("*** layer; FY2009 has no text layer to read. Values are validated by shape checks,")
    A("*** an agency-code dictionary, and -- where the document prints one -- an exact")
    A("*** total. Anything that failed is flagged in the `flags` column and listed in")
    A(f"*** {prefix}_transparency_needs_review.csv with a crop of the original pixels.")
    A("")

    # -- pages ------------------------------------------------------------------
    A("PAGE ACCOUNTING")
    A("-" * 72)
    kinds = Counter(page_kinds.values())
    for kind, n in sorted(kinds.items()):
        A(f"  {kind:<12} {n:>5}")
    A(f"  {'TOTAL':<12} {sum(kinds.values()):>5}")
    A("")

    # -- rows -------------------------------------------------------------------
    A("ROWS BY RESOLUTION")
    A("-" * 72)
    for resolution, date, rows, _totals in per_reso:
        designate = sum(1 for r in rows if r["action"] == "designate")
        rescind = len(rows) - designate
        A(f"  reso {resolution:02d}  {date}  {len(rows):>5} rows "
          f"({designate} designate / {rescind} rescind)")
    A(f"  {'TOTAL':<20} {len(all_rows):>5} rows")
    A("")

    # -- reconciliation ---------------------------------------------------------
    A("RECONCILIATION -- PRINTED CHART TOTALS")
    A("-" * 72)
    checked = passed = 0
    for resolution, _date, rows, totals in per_reso:
        for t in totals:
            if t["printed"] is None:
                A(f"  reso {resolution:02d}  {t['chart'][:40]:<40}  UNREADABLE printed total "
                  f"(raw {t['raw']!r}) -> queued for review")
                checked += 1
                continue
            parsed = sum(r["amount"] for r in rows
                         if r["chart"] == t["chart"] and isinstance(r["amount"], int))
            checked += 1
            if parsed == t["printed"]:
                passed += 1
                A(f"  reso {resolution:02d}  {t['chart'][:40]:<40}  EXACT  "
                  f"{_fmt_money(t['printed'])}")
            else:
                A(f"  reso {resolution:02d}  {t['chart'][:40]:<40}  MISMATCH  "
                  f"printed {_fmt_money(t['printed'])} vs parsed {_fmt_money(parsed)} "
                  f"(diff {_fmt_money(parsed - t['printed'])})")
    if checked:
        A("")
        A(f"  {passed}/{checked} printed chart totals reconcile exactly.")
    else:
        A("  No printed totals found.")
    A("")
    A("  Charts that print no total remain NOT RECONCILABLE, as in every other")
    A("  Transparency-Resolution year. The only internal check available for them is that")
    A("  a transfer's rescind and re-designate net out:")
    net = sum(r["amount"] for r in all_rows if isinstance(r["amount"], int))
    A(f"    net of all designations across FY09 = {_fmt_money(net)} (informational)")
    A("")

    # -- OCR quality ------------------------------------------------------------
    A("OCR QUALITY")
    A("-" * 72)
    flagged = [r for r in all_rows if r["flags"] and any(f.startswith("ocr:")
                                                         for f in r["flags"].split(";"))]
    rate = len(flagged) / len(all_rows) if all_rows else 0.0
    mean_conf = sum(conf_samples) / len(conf_samples) if conf_samples else 0.0
    ordered = sorted(conf_samples)

    def pct(p):
        return ordered[int(p * (len(ordered) - 1))] if ordered else 0.0

    A(f"  cells recognized      {len(conf_samples):>7}")
    A(f"  mean cell confidence  {mean_conf:>7.3f}")
    A(f"  p05 / p25 / median    {pct(0.05):.3f} / {pct(0.25):.3f} / {pct(0.50):.3f}")
    A(f"  confidence threshold  {min_conf:>7.2f}")
    A("")
    counts = Counter()
    for r in all_rows:
        for f in r["flags"].split(";"):
            if f.startswith("ocr:"):
                counts[f] += 1
    for flag, label in FLAG_LABELS:
        n = counts.get(flag, 0)
        A(f"  {flag:<14} {n:>6}  ({n / len(all_rows) * 100 if all_rows else 0:5.2f}% of rows)  {label}")
    A("")
    A(f"  rows with at least one flag   {len(flagged)} / {len(all_rows)} ({rate * 100:.2f}%)")
    A(f"  cells queued for human review {len(reviews)}")
    if member_hits or member_misses:
        total = member_hits + member_misses
        A(f"  member cells matching a Schedule C roster name: {member_hits}/{total} "
          f"({member_hits / total * 100:.1f}%) -- informational; the FY2015+ rosters do not")
        A("    cover every member of the 2008-09 Council, so a miss is not an error.")
    A("")
    A(f"  OCR CONFIDENCE BAND: {quality_band(rate, mean_conf)}")
    A("")
    A("STATUS: NOT RECONCILABLE overall (no document-wide printed total), with the")
    A("        per-chart printed totals above checked exactly where they exist.")
    return "\n".join(L) + "\n"
