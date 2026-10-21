#!/usr/bin/env python3
"""open_data_watch.py -- read the metadata of every tracked NYC Open Data dataset and say whether
its rows changed since the snapshot the repo holds (PLAN.md §4, "watch metadata, pull on change").

    python3 code/open_data_watch.py [--gap 2.5] [--only ID ...] [--dry-run]

Metadata only: one GET of https://data.cityofnewyork.us/api/views/<id>.json per dataset, one at a
time, >= --gap seconds apart, with the repo's standard User-Agent (code/polite_http.py). No rows,
no app token, nothing personal in any header. Run by hand (PLAN Q4); no scheduler.

Appends one line per dataset per run to source/open-data-watch.csv:

  checked_at          when the metadata was read (local ISO time)
  dataset_id, name
  rows_updated_at     the portal's rowsUpdatedAt, as ISO date and epoch
  cached_rows         the largest per-column cached count in the metadata (not a SoQL count)
  columns_ok          the metadata's columns equal the verified schema (yes / no / unverified)
  held_rows_updated_at  rowsUpdatedAt of the newest snapshot under source/open-data-<id>/
  verdict             current | changed (pull a new snapshot) | not_held | schema_changed

A changed dataset is pulled with the script named in code/open_data_registry.py; a
schema_changed one is a stop until a person updates the verified schema.
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import open_data_registry as R  # noqa: E402
import polite_http as H         # noqa: E402

ROOT = os.path.dirname(HERE)
WATCH = os.path.join(ROOT, "source", "open-data-watch.csv")
FIELDS = ["checked_at", "dataset_id", "name", "rows_updated_at", "rows_updated_at_epoch",
          "cached_rows", "columns_ok", "held_rows_updated_at", "verdict"]
_RUA = re.compile(r"rowsUpdatedAt`?\s*`?(\d{9,11})")


def view_url(ds):
    return f"{R.DOMAIN}/api/views/{ds}.json"


def verified_columns(ds):
    """The schema the repo verified for `ds`, from the registry or the dataset's own fetcher."""
    cfg = R.DATASETS[ds]
    if cfg.get("columns"):
        return list(cfg["columns"])
    if ds == "4d7f-74pe":
        import fetch_open_data_4d7f74pe as F4
        return list(F4.COLUMNS)
    import fetch_open_data_capital as FC
    return list(FC.DATASETS[ds]["columns"])


def held_rows_updated_at(ds, root=ROOT):
    """The newest rowsUpdatedAt recorded for a snapshot of `ds` (MANIFEST.csv notes and README),
    or None when the repo holds no snapshot."""
    d = os.path.join(root, "source", f"open-data-{ds}")
    found = []
    for path in [os.path.join(d, "README.md")] + sorted(glob.glob(os.path.join(d, "**", "MANIFEST.csv"),
                                                                 recursive=True)):
        if os.path.exists(path):
            found += [int(x) for x in _RUA.findall(open(path, encoding="utf-8").read())]
    return max(found) if found else None


def summarize(ds, meta, held):
    """One watch row from a metadata dict (no network)."""
    cols = [c["fieldName"] for c in meta.get("columns", []) if not c["fieldName"].startswith(":")]
    try:
        want = verified_columns(ds)
        columns_ok = "yes" if cols == want else "no"
    except (ImportError, KeyError):
        columns_ok = "unverified"
    counts = []
    for c in meta.get("columns", []):
        cc = c.get("cachedContents") or {}
        if "non_null" in cc or "null" in cc:
            counts.append(int(cc.get("non_null", 0)) + int(cc.get("null", 0)))
    rua = meta.get("rowsUpdatedAt")
    if columns_ok == "no":
        verdict = "schema_changed"
    elif held is None:
        verdict = "not_held"
    elif rua and int(rua) > held:
        verdict = "changed"
    else:
        verdict = "current"
    return {"dataset_id": ds, "name": meta.get("name", R.DATASETS[ds]["name"]),
            "rows_updated_at": datetime.fromtimestamp(int(rua)).date().isoformat() if rua else "",
            "rows_updated_at_epoch": rua or "", "cached_rows": max(counts) if counts else "",
            "columns_ok": columns_ok,
            "held_rows_updated_at": datetime.fromtimestamp(held).date().isoformat() if held else "",
            "verdict": verdict}


def append(rows, path=WATCH):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerows(rows)


def main(argv=None, fetcher=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--gap", type=float, default=2.5)
    ap.add_argument("--only", nargs="*", choices=sorted(R.DATASETS))
    ap.add_argument("--dry-run", action="store_true", help="print, do not append")
    a = ap.parse_args(argv)
    if a.gap < 2.0:
        raise SystemExit("--gap below 2 s breaks the shared Socrata budget")
    f = fetcher or H.Fetcher(min_gap=a.gap)
    out = []
    for ds in a.only or list(R.DATASETS):
        status, body = f.get(view_url(ds))
        if status != 200:
            raise SystemExit(f"{ds}: metadata HTTP {status}")
        row = {"checked_at": H.now_iso(), **summarize(ds, json.loads(body), held_rows_updated_at(ds))}
        out.append(row)
        print(f"{ds:<10} {row['verdict']:<15} portal {row['rows_updated_at']}  held "
              f"{row['held_rows_updated_at'] or '-'}  columns {row['columns_ok']}")
    if not a.dry_run:
        append(out)
    return 1 if any(r["verdict"] == "schema_changed" for r in out) else 0


if __name__ == "__main__":
    sys.exit(main())
