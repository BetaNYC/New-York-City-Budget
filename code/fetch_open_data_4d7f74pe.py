#!/usr/bin/env python3
"""fetch_open_data_4d7f74pe.py -- pull NYC Open Data "City Council Discretionary Funding"
(4d7f-74pe) whole, slowly, into the local cache, and record a manifest (GitHub #85).

    python3 code/fetch_open_data_4d7f74pe.py --cache DIR [--gap 2.5]

Interface, from the Socrata SODA documentation (dev.socrata.com):
  * rows:   GET https://data.cityofnewyork.us/resource/4d7f-74pe.json
            ?$select=:*,*  (system fields :id, :created_at, :updated_at plus every column;
                            docs/system-fields.html)
            &$order=:id    (stable paging; docs/paging.html requires an $order for paging)
            &$limit=5000&$offset=N   (docs/queries/limit.html, offset.html)
  * count:  GET .../resource/4d7f-74pe.json?$select=count(*)   (docs/queries/select.html)
  * token:  header X-App-Token (docs/app-tokens.html). Read from the environment variable
            SOCRATA_APP_TOKEN; never printed or written anywhere.
  * the data dictionary: the attachment listed in the dataset metadata
            (metadata.attachments[].assetId/filename), at the portal's attachment link
            /api/views/4d7f-74pe/files/<assetId>?download=true&filename=<filename>. That link
            form is the portal UI's, not a documented SODA endpoint; a non-200 is reported and
            the dictionary is skipped, never guessed at.
JSON rows omit a field whose value is null; the combined CSV writes it as empty.

Access rules (epic #89, and the 2026-10-14 dispatch): one request at a time, at least `--gap`
seconds apart (default 2.5 s; the cap is 1 request per 2 s because another agent shares the
budget). Pages already in the cache are never re-fetched.

Writes:
  <cache>/pages/offset-NNNNNN.json      one file per page, as served
  <cache>/4d7f-74pe.csv                 every row, columns in schema order (+ :id, :created_at,
                                         :updated_at), values exactly as served
  <cache>/<data dictionary>.xlsx
  source/open-data-4d7f-74pe/MANIFEST.csv   one row per downloaded file (committed)
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polite_http as H

ROOT = os.path.dirname(HERE)
DOMAIN = "https://data.cityofnewyork.us"
DATASET = "4d7f-74pe"
PAGE = 5000
MANIFEST = os.path.join(ROOT, "source", "open-data-4d7f-74pe", "MANIFEST.csv")
SYSTEM = [":id", ":created_at", ":updated_at", ":version"]  # ":*" also returns :version (seen 2026-10-14)
# Schema order, verified against the live metadata on 2026-10-14 (27 columns).
COLUMNS = ["mocs_id", "fiscal_year", "source", "council_member", "legal_name_of_organization",
           "ein", "status", "amount", "agency", "program_name", "address", "address_2_optional",
           "city", "state", "postcode", "purpose_of_funds", "fiscal_conduit_name", "fc_ein",
           "borough", "latitude", "longitude", "community_board", "council_district",
           "census_tract", "bin", "bbl", "nta"]


def rows_url(offset, limit=PAGE):
    q = urllib.parse.urlencode({"$select": ":*,*", "$order": ":id", "$limit": limit,
                                "$offset": offset}, safe=":*,$")
    return f"{DOMAIN}/resource/{DATASET}.json?{q}"


def count_url():
    return f"{DOMAIN}/resource/{DATASET}.json?" + urllib.parse.urlencode(
        {"$select": "count(*)"}, safe="()*$")


def rows_csv(rows):
    """Rows (list of dicts as served) -> CSV text. Unknown keys are a stop: the schema moved."""
    fields = SYSTEM + COLUMNS
    extra = sorted({k for r in rows for k in r} - set(fields))
    if extra:
        raise ValueError(f"fields not in the verified schema: {extra}")
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    return out.getvalue()


def pull(fetcher, cache, headers, expected=None, log=print):
    """Fetch every page (cached pages skipped). Returns the list of rows."""
    rows, offset = [], 0
    while True:
        path = os.path.join(cache, "pages", f"offset-{offset:06d}.json")
        url = rows_url(offset)
        body, fetched = fetcher.get_cached(url, path, headers=headers)
        page = json.loads(body)
        if fetched:
            H.upsert_manifest(MANIFEST, {
                "file": os.path.relpath(path, cache), "url": url, "retrieved_at": H.now_iso(),
                "http_status": 200, "bytes": len(body), "sha256": H.sha256_bytes(body),
                "rows": len(page)})
            log(f"page offset={offset}: {len(page)} rows (fetched)")
        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    if expected is not None and len(rows) != expected:
        raise RuntimeError(f"pulled {len(rows)} rows, count(*) says {expected}")
    ids = [r.get(":id") for r in rows]
    if len(set(ids)) != len(ids):
        raise RuntimeError("duplicate :id across pages -- paging was not stable")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", required=True)
    ap.add_argument("--gap", type=float, default=2.5)
    ap.add_argument("--metadata", help="dataset metadata JSON already on disk (for the "
                    "data dictionary attachment); if absent the dictionary is skipped")
    a = ap.parse_args(argv)
    if a.gap < 2.0:
        raise SystemExit("--gap below 2 s breaks the shared Socrata budget")
    token = os.environ.get("SOCRATA_APP_TOKEN", "")
    if not token:
        raise SystemExit("SOCRATA_APP_TOKEN is not set; refusing to pull without an app token")
    headers = {"X-App-Token": token}
    f = H.Fetcher(min_gap=a.gap)

    count_path = os.path.join(a.cache, "count.json")
    body, fetched = f.get_cached(count_url(), count_path, headers=headers)
    expected = int(json.loads(body)[0]["count"])
    print(f"count(*) = {expected}" + (" (fetched)" if fetched else " (cached)"))

    rows = pull(f, a.cache, headers, expected=expected)
    text = rows_csv(rows)
    out = os.path.join(a.cache, f"{DATASET}.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print(f"wrote {out}: {len(rows)} rows, sha256 {H.sha256_bytes(text.encode())}")

    if a.metadata:
        with open(a.metadata, encoding="utf-8") as fh:
            meta = json.load(fh)
        for att in meta.get("metadata", {}).get("attachments", []):
            fn = att["filename"]
            url = (f"{DOMAIN}/api/views/{DATASET}/files/{att['assetId']}?"
                   + urllib.parse.urlencode({"download": "true", "filename": fn}))
            path = os.path.join(a.cache, fn)
            try:
                b, fetched = f.get_cached(url, path, headers=headers)
            except RuntimeError as e:
                print(f"data dictionary not downloaded: {e}")
                continue
            if fetched:
                H.upsert_manifest(MANIFEST, {
                    "file": fn, "url": url, "retrieved_at": H.now_iso(), "http_status": 200,
                    "bytes": len(b), "sha256": H.sha256_bytes(b), "rows": ""})
            print(f"data dictionary {fn}: {len(b)} bytes" + (" (fetched)" if fetched else ""))
    print("requests sent per host:", f.counts)


if __name__ == "__main__":
    main()
