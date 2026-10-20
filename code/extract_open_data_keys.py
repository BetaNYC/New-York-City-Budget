#!/usr/bin/env python3
"""extract_open_data_keys.py -- commit the five Open Data 4d7f-74pe columns the disclosure
dataset needs to attach Open Data's MOCS IDs (GitHub #89 A4), so the build never reads the cache.

    python3 code/extract_open_data_keys.py --open-data CACHE/4d7f-74pe.csv [--check]

Input: the assembled Open Data CSV in the local cache. Its sha256 must equal the `4d7f-74pe.csv`
row of source/open-data-4d7f-74pe/MANIFEST.csv (the file the #85 diff used), or this stops.

Output: source/open-data-4d7f-74pe/4d7f-74pe-keys.csv.gz -- every row, five columns exactly as
served (`:id`, `fiscal_year`, `mocs_id`, `ein`, `amount`), in the CSV's row order (SODA `:id`
order). gzip with mtime 0 and no file name, so the same input gives the same bytes with the
same zlib (--check compares the decompressed text, since another zlib may compress differently). Its own
manifest row (sha256 of the .gz, rows) is upserted into MANIFEST.csv.

Why a subset and not the whole 47 MB CSV: these five columns are all the MOCS-ID match reads
(EIN + amount, per fiscal year). The rest of Open Data (names, addresses, geocodes) is not used
by the dataset (#89 A4, B7) and stays in the cache, pinned by the manifest's sha256.

Stdlib only. No network.
"""
import argparse
import csv
import gzip
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polite_http as H

ROOT = os.path.dirname(HERE)
DIR = os.path.join(ROOT, "source", "open-data-4d7f-74pe")
MANIFEST = os.path.join(DIR, "MANIFEST.csv")
OUT = os.path.join(DIR, "4d7f-74pe-keys.csv.gz")
COLUMNS = [":id", "fiscal_year", "mocs_id", "ein", "amount"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_row(name, manifest=MANIFEST):
    for r in H.read_manifest(manifest):
        if r["file"] == name:
            return r
    raise SystemExit(f"{manifest}: no row for {name}")


def manifest_sha(name, manifest=MANIFEST):
    return manifest_row(name, manifest)["sha256"]


def keys_bytes(open_data_path):
    """The .csv.gz bytes for the five columns of every row. Deterministic."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    n = 0
    with open(open_data_path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        missing = set(COLUMNS) - set(rd.fieldnames or [])
        if missing:
            raise SystemExit(f"{open_data_path}: missing columns {sorted(missing)}")
        for r in rd:
            w.writerow([r[c] for c in COLUMNS])
            n += 1
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as gz:
        gz.write(buf.getvalue().encode("utf-8"))
    return out.getvalue(), n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--open-data", required=True)
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed file differs")
    a = ap.parse_args(argv)
    if sha256_file(a.open_data) != manifest_sha("4d7f-74pe.csv"):
        raise SystemExit(f"{a.open_data}: sha256 differs from MANIFEST.csv's 4d7f-74pe.csv row")
    data, n = keys_bytes(a.open_data)
    if a.check:
        cur = b""
        if os.path.exists(OUT):
            with open(OUT, "rb") as f:
                cur = f.read()
        # Content, not bytes: another zlib may compress the same text differently. The committed
        # bytes are pinned by the manifest's sha256 (checked here and by the parser).
        ok = (bool(cur) and gzip.decompress(cur) == gzip.decompress(data)
              and manifest_sha(os.path.basename(OUT)) == H.sha256_bytes(cur))
        print(f"{os.path.relpath(OUT, ROOT)}: {'current' if ok else 'STALE'}")
        return 0 if ok else 1
    with open(OUT, "wb") as f:
        f.write(data)
    H.upsert_manifest(MANIFEST, {
        "file": os.path.basename(OUT),
        "url": "(derived from 4d7f-74pe.csv by code/extract_open_data_keys.py; not a download)",
        # The rows' own retrieval time: the pull that produced 4d7f-74pe.csv.
        "retrieved_at": manifest_row("4d7f-74pe.csv")["retrieved_at"], "bytes": len(data),
        "sha256": H.sha256_bytes(data), "rows": n,
        "note": "columns :id fiscal_year mocs_id ein amount, values as served; gzip mtime 0"})
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {n} rows, {len(data)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
