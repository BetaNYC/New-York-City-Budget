#!/usr/bin/env python3
"""build_open_data_review_sheet.py -- a short, fixed sample of the Open Data / Council
near-matches for a person to check by eye (GitHub #89 B12).

    python3 code/build_open_data_review_sheet.py --open-data CACHE/4d7f-74pe.csv \
        [--out research/2026-10-14-open-data-diff/review-sheet.csv]

code/diff_open_data_disclosure.py pairs NYC Open Data 4d7f-74pe with the Council's disclosure
workbooks and, for what is left unmatched, NOMINATES pairs that look like the same designation
with one thing changed. Nominations are never counted as matches. This script takes those
nominations, in three classes, and draws a fixed sample for review:

  grantee_differs   same amount, source, agency and council member, a different organization
                    (likely re-designated)                                   160 in all years
  ein_differs       same organization and amount, a different EIN            66
  amount_differs    same organization and EIN, a different amount            199

Sample: SAMPLE_SIZES per class (20 rows), drawn with random.Random(SEED) from the class's
nominations sorted by (fiscal year, Open Data :id, Council file:row). Same inputs, same seed:
the same 20 rows, byte for byte. The population counts are checked against the numbers above
and the build stops if they moved (the diff changed; re-read it before re-sampling).

Inputs: the cached Open Data CSV (its sha256 must equal the `4d7f-74pe.csv` row of
source/open-data-4d7f-74pe/MANIFEST.csv), the four archived FY2009-FY2012 Council workbooks in
source/wayback-council/files/, and data/fyNN/expense_disclosure/ for FY2013-FY2021: exactly
the inputs of the committed diff (research/2026-10-14-open-data-vs-disclosure-diff.md).

Stdlib only (plus xlrd for the .xls workbooks). No network.
"""
import argparse
import csv
import hashlib
import io
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diff_open_data_disclosure as D
import parse_expense_disclosure as P

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "research", "2026-10-14-open-data-diff", "review-sheet.csv")
OD_MANIFEST = os.path.join(ROOT, "source", "open-data-4d7f-74pe", "MANIFEST.csv")
WAYBACK = os.path.join(ROOT, "source", "wayback-council", "files")
WORKBOOKS = {
    2009: os.path.join(WAYBACK, "20250212200136", "funded_disclosure_FY2009.xls"),
    2010: os.path.join(WAYBACK, "20250212200137", "funded_disclosure_FY2010.xls"),
    2011: os.path.join(WAYBACK, "20250212200134", "funded_disclosure_FY2011.xls"),
    2012: os.path.join(WAYBACK, "20250212200132", "funded_disclosure_FY2012.xls"),
}
SEED = 20261014
CLASSES = ("grantee_differs", "ein_differs", "amount_differs")
SAMPLE_SIZES = {"grantee_differs": 7, "ein_differs": 6, "amount_differs": 7}
POPULATION = {"grantee_differs": 160, "ein_differs": 66, "amount_differs": 199}
SHOWN = ("legal_name", "ein", "amount", "status", "source", "agency", "council_member",
         "program_name", "address1", "city", "postal_code")
FIELDS = (["review_id", "class", "fiscal_year", "council_side"]
          + [f"open_data_{f}" for f in SHOWN] + ["open_data_mocs_id", "open_data_row_id"]
          + [f"council_{f}" for f in SHOWN] + ["council_source_row"]
          + ["reviewer_verdict", "notes"])


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_sha(manifest=OD_MANIFEST):
    with open(manifest, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["file"] == "4d7f-74pe.csv":
                return r["sha256"]
    raise SystemExit(f"{manifest}: no 4d7f-74pe.csv row")


def nominations(od_rows, sides):
    """od_rows: normalized Open Data rows; sides: {fy: (label, [normalized Council rows])}.
    -> {class: [(fy, label, od_row, council_row)]}, each list sorted deterministically."""
    by_fy = {}
    for r in od_rows:
        by_fy.setdefault(r["fiscal_year"], []).append(r)
    out = {c: [] for c in CLASSES}
    for fy in sorted(sides):
        label, council = sides[fy]
        for kind, a, b in D.compare(by_fy.get(fy, []), council)["nominations"]:
            out[kind].append((fy, label, a, b))
    for c in CLASSES:
        out[c].sort(key=lambda t: (t[0], t[2]["ref"], t[3]["ref"]))
    return out


def sample(noms, sizes=None, seed=SEED):
    """Deterministic draw: one Random(seed) shared across the classes, in CLASSES order."""
    sizes = SAMPLE_SIZES if sizes is None else sizes
    rng = random.Random(seed)
    picked = []
    for c in CLASSES:
        pool = noms.get(c, [])
        k = min(sizes[c], len(pool))
        idx = sorted(rng.sample(range(len(pool)), k))
        picked += [(c, *pool[i]) for i in idx]
    return picked


def sheet_csv(picked):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for n, (c, fy, label, a, b) in enumerate(picked, start=1):
        row = {"review_id": f"R{n:02d}", "class": c, "fiscal_year": fy, "council_side": label,
               "open_data_mocs_id": a.get("mocs_id", ""), "open_data_row_id": a["ref"],
               "council_source_row": b["ref"], "reviewer_verdict": "", "notes": ""}
        for f in SHOWN:
            row[f"open_data_{f}"] = P.format_amount(a[f]) if f == "amount" else a.get(f, "")
            row[f"council_{f}"] = P.format_amount(b[f]) if f == "amount" else b.get(f, "")
        w.writerow(row)
    return buf.getvalue()


def build(open_data_path):
    if sha256_file(open_data_path) != expected_sha():
        raise SystemExit(f"{open_data_path}: sha256 differs from the 4d7f-74pe.csv row of "
                         f"{os.path.relpath(OD_MANIFEST, ROOT)}; not the file the diff used")
    od = D.load_open_data(open_data_path)
    sides = {fy: ("disclosure_2026_10_12", D.load_ours(fy)) for fy in D.OVERLAP}
    for fy, path in WORKBOOKS.items():
        sides[fy] = ("wayback_workbook", D.load_workbook(path)[0])
    noms = nominations(od, sides)
    got = {c: len(noms[c]) for c in CLASSES}
    if got != POPULATION:
        raise SystemExit(f"nomination counts moved: {got}, expected {POPULATION}")
    return sheet_csv(sample(noms))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--open-data", required=True)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true", help="exit 1 if --out is stale")
    a = ap.parse_args(argv)
    text = build(a.open_data)
    if a.check:
        cur = ""
        if os.path.exists(a.out):
            with open(a.out, encoding="utf-8") as f:
                cur = f.read()
        print(f"{os.path.relpath(a.out, ROOT)}: {'current' if cur == text else 'STALE'}")
        return 0 if cur == text else 1
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(a.out, ROOT)} ({text.count(chr(10)) - 1} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
