#!/usr/bin/env python3
"""
build_recovered_awards.py — emit the absorbed Schedule C awards as a SIDECAR dataset.

The Schedule C parser identifies an award by an EIN followed by an amount. Where the source PDF
prints something between them, the pattern misses and the award's text is absorbed into the next
row the parser does match (DATA-ANOMALIES.md §20). Those absorbed awards exist in the printed
budget and have no row anywhere in data/.

This writes them to data/recovered/schedule_c_absorbed_awards.csv. It deliberately does NOT add
them to the per-year CSVs:

  * Nothing already published moves. Anyone who cited a figure last month still reproduces it.
  * Recovered rows carry provenance columns naming where each field came from, which the
    per-year schema has no place for.
  * The per-year files stay "what the PDF deterministically yielded", which is the repo's contract.

Evidence that these are real awards rather than parsing noise, from the Phase 3 investigation:
across FY2016-FY2019 there are 87 initiatives that both join to a printed initiative amount and
contain at least one absorbed award. Adding the absorbed awards closes the gap to EXACTLY $0 in
32 of them. Shuffling the same absorbed totals across the same initiatives 20,000 times yields a
mean of 0.77 exact closures and never reaches 32 (P < 0.00005). They close reconciliation gaps;
they do not overshoot.

Usage:  python3 code/build_recovered_awards.py
"""
import csv
import os

SRC = "code/absorbed_award_candidates.csv"
OUT = "data/recovered/schedule_c_absorbed_awards.csv"

# Award schema, then provenance. Every recovered row states where it came from and how sure we are.
FIELDS = [
    "fiscal_year", "category", "initiative", "award_type", "member", "organization",
    "program", "ein", "amount", "agency", "purpose",
    "confidence", "name_source", "absorbed_from_file", "absorbed_from_line",
    "absorbed_from_ein", "disclosure_confirmed",
]

# verdict -> confidence. `absent` means the Council's disclosure has no counterpart: the award is
# still in the printed budget (that is where it was extracted from) but nothing independent
# corroborates it, so it is labelled and shipped rather than dropped or silently upgraded.
CONFIDENCE = {
    "unique": "high",           # unique same-year (EIN, amount) match in Council disclosure
    "unique_by_name": "medium", # matched on name where the amount pairing was not unique
    "ambiguous": "low",         # more than one disclosure candidate
    "absent": "low",            # no disclosure counterpart
}


def main():
    with open(SRC, newline="", encoding="utf-8") as fh:
        cands = list(csv.DictReader(fh))

    os.makedirs("data/recovered", exist_ok=True)
    rows, skipped = [], 0
    for c in cands:
        # Two candidates already exist in the corpus under another row; adding them would
        # double-count. Skip, do not "recover".
        if c.get("already_in_corpus") == "1":
            skipped += 1
            continue
        # Prefer the Council's own legal name; fall back to the name printed in the absorbed text.
        name = (c.get("d_organization") or "").strip() or (c.get("extracted_name") or "").strip()
        rows.append({
            "fiscal_year": "20" + c["fy"][2:],
            # category/initiative/award_type are inherited from the ABSORBING row: the absorbed
            # award was printed inside that row's table, so it belongs to the same initiative.
            # This is the one inherited-not-observed field group; `name_source` records that.
            "category": c.get("absorbing_category", ""),
            "initiative": c.get("absorbing_initiative", ""),
            "award_type": c.get("absorbing_award_type", ""),
            "member": (c.get("d_member") or "").strip(),
            "organization": name,
            "program": (c.get("d_program") or "").strip(),
            "ein": c["ein"],
            "amount": c["amount"],
            "agency": (c.get("d_agency") or "").strip(),
            "purpose": (c.get("d_purpose") or "").strip(),
            "confidence": CONFIDENCE.get(c.get("verdict", ""), "low"),
            "name_source": "council_disclosure" if c.get("d_organization") else "absorbed_text",
            "absorbed_from_file": c["absorbing_file"],
            "absorbed_from_line": c["absorbing_line"],
            "absorbed_from_ein": c["absorbing_ein"],
            "disclosure_confirmed": "yes" if c.get("d_organization") else "no",
        })

    rows.sort(key=lambda r: (r["fiscal_year"], r["organization"], int(r["amount"])))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    total = sum(int(float(r["amount"])) for r in rows)
    print(f"wrote {OUT}: {len(rows):,} awards, ${total:,}")
    print(f"  skipped (already in corpus): {skipped}")
    for lvl in ("high", "medium", "low"):
        n = [r for r in rows if r["confidence"] == lvl]
        if n:
            print(f"  {lvl:<7} {len(n):>4} awards  ${sum(int(float(r['amount'])) for r in n):,}")


if __name__ == "__main__":
    main()
