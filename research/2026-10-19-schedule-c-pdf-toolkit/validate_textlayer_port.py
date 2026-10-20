#!/usr/bin/env python3
"""
Dev-only validation harness: does code/pdf_condition.py's pypdfium2 port of Christian
Moscardi's text-layer probe classify every PDF in source/ the same way as his original
(nyc_executive_orders/textlayer.py, PyMuPDF)?

PyMuPDF is AGPL, so it is NOT a dependency of the shipped code; it is pulled in only for this
one-off comparison:

  uv run --with 'pymupdf>=1.24,<2' python research/2026-10-19-schedule-c-pdf-toolkit/validate_textlayer_port.py \
      ~/Code/nyc-executive-orders/src/nyc_executive_orders/textlayer.py

Compares, per PDF, the classification and the low-text page list (Christian's
image_only_pages) against data/pdf_condition.csv. Prints every difference; exits 1 if any.
"""
import csv
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def compact(pages):
    out, s, p = [], None, None
    for x in sorted(pages):
        if s is None:
            s = p = x
        elif x == p + 1:
            p = x
        else:
            out.append(f"{s}-{p}" if p != s else str(s)); s = p = x
    if s is not None:
        out.append(f"{s}-{p}" if p != s else str(s))
    return ",".join(out)


def main():
    spec = importlib.util.spec_from_file_location("textlayer", sys.argv[1])
    tl = importlib.util.module_from_spec(spec)
    sys.modules["textlayer"] = tl
    spec.loader.exec_module(tl)
    with open(REPO / "data/pdf_condition.csv", newline="") as fh:
        ours = {r["path"]: r for r in csv.DictReader(fh)}
    diffs = 0
    counts = {}
    max_share_gap = 0.0
    for rel, row in sorted(ours.items()):
        r = tl.classify_pdf(REPO / rel)
        counts[r.classification] = counts.get(r.classification, 0) + 1
        theirs_low = compact(r.image_only_pages)
        gap = abs(r.invisible_share - float(row["invisible_char_share"]))
        max_share_gap = max(max_share_gap, gap)
        if r.classification != row["textlayer_class"] or theirs_low != row["low_text_pages"]:
            diffs += 1
            print(f"DIFF {rel}: original={r.classification} low={theirs_low!r} "
                  f"cpp={r.chars_per_page:.1f} share={r.invisible_share:.4f} | "
                  f"port={row['textlayer_class']} low={row['low_text_pages']!r} "
                  f"cpp={row['chars_per_page_mean']} share={row['invisible_char_share']}")
    print(f"compared={len(ours)} original_counts={counts} differences={diffs} "
          f"max_invisible_share_gap={max_share_gap:.4f}")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
