#!/usr/bin/env python3
"""fetch_open_data_capital.py -- pull three NYC Open Data capital datasets whole, slowly, into
the local cache, write a committed gzip CSV of each and a manifest (GitHub #89 A6-A8).

    python3 code/fetch_open_data_capital.py --cache DIR [--gap 2.5] [--only ID ...]

  t474-a92g  City Council Capital Budget (City Council), reports FY2019-FY2026
  46m8-77gv  Capital Budget (OMB): adopted/preliminary/executive appropriations, whole dollars
  2cmn-uidm  Capital Commitment Plan (OMB): planned commitments, THOUSANDS of dollars

Interface, from the Socrata SODA documentation (dev.socrata.com), as in
code/fetch_open_data_4d7f74pe.py:
  * rows:  GET https://data.cityofnewyork.us/resource/<id>.json?$select=:*,*&$order=:id
           &$limit=5000&$offset=N   (docs/paging.html: paging needs an $order; :id is stable)
  * count: GET .../resource/<id>.json?$select=count(*)
  * token: header X-App-Token (docs/app-tokens.html), from the environment variable
           SOCRATA_APP_TOKEN; never printed or written anywhere.
  * data dictionary: the dataset's metadata attachment, at the portal's attachment link
           /api/views/<id>/files/<assetId>?download=true&filename=<filename> (the portal UI's
           link form, not a documented SODA endpoint; a non-200 is reported and skipped).
Schemas (COLUMNS, attachment ids, rowsUpdatedAt) were read from each dataset's live metadata on
2026-10-14 through the socrata MCP, one call each; a row with any field outside the schema is a
stop. JSON rows omit null fields; the CSV writes them empty.

Access rules (epic #89; dispatch 2026-10-14): one request at a time, >= --gap seconds apart
(2 s floor), <= 5,000 rows a page, $order=:id; a 403, or a 429 twice, stops the host
(code/polite_http.py). Cached pages are never re-fetched.

Writes:
  <cache>/open-data-<id>/pages/offset-NNNNNN.json, count.json, <dictionary>.xlsx
  source/open-data-<id>/<id>.csv.gz        every row, schema order, values as served; gzip
                                           mtime 0 (committed)
  source/open-data-<id>/MANIFEST.csv       one row per downloaded file + the assembled CSV
"""
import argparse
import csv
import gzip
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
PAGE = 5000
SYSTEM = [":id", ":created_at", ":updated_at", ":version"]
# Verified against each dataset's live metadata, 2026-10-14 (socrata MCP get_data metadata).
DATASETS = {
    "t474-a92g": {
        "title": "City Council Capital Budget", "publisher": "City Council (NYCC)",
        "rows_updated_at": 1766003942,
        "columns": ["reported", "fiscal_year", "borough", "award", "council_district",
                    "sponsor", "title", "description", "id", "budget_line"],
        "dictionary": ("2448c272-f7d8-4e81-8fe8-889bee1425fc",
                       "City_Council_Capital_Budget_Data_Dictionary.xlsx")},
    "46m8-77gv": {
        "title": "Capital Budget", "publisher": "Mayor's Office of Management & Budget (OMB)",
        "rows_updated_at": 1783965522,
        "columns": ["pub_date", "proj_type", "proj_type_name", "budline", "budline_title",
                    "funding", "yr1_fy", "year1_amt", "year2_amt", "year3_amt", "year4_amt"],
        "dictionary": ("5864545c-db73-4a37-9a90-796087f4b4bd", "Capital_Budget_Data_Dictionary.xlsx")},
    "2cmn-uidm": {
        "title": "Capital Commitment Plan",
        "publisher": "Mayor's Office of Management & Budget (OMB)",
        "rows_updated_at": 1790628315,
        "columns": ["pub_date", "projtype", "projtype_desc", "budline", "budline_desc", "funding",
                    "num_yrs_prsnt", "yr1_fy", "year1_amt", "year2_amt", "year3_amt",
                    "year4_amt", "year5_amt"],
        "dictionary": ("15d5cd8a-0d21-430b-ba32-810bad15ce84", "Capital_Commitment_Plan.xlsx")},
}


def source_dir(ds):
    return os.path.join(ROOT, "source", f"open-data-{ds}")


def rows_url(ds, offset, limit=PAGE):
    q = urllib.parse.urlencode({"$select": ":*,*", "$order": ":id", "$limit": limit,
                                "$offset": offset}, safe=":*,$")
    return f"{DOMAIN}/resource/{ds}.json?{q}"


def count_url(ds):
    return f"{DOMAIN}/resource/{ds}.json?" + urllib.parse.urlencode({"$select": "count(*)"},
                                                                    safe="()*$")


def rows_csv(ds, rows):
    """Rows as served -> CSV text in schema order. A field outside the schema is a stop."""
    fields = SYSTEM + DATASETS[ds]["columns"]
    extra = sorted({k for r in rows for k in r} - set(fields))
    if extra:
        raise ValueError(f"{ds}: fields not in the verified schema: {extra}")
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    return out.getvalue()


def gz(text):
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as g:
        g.write(text.encode("utf-8"))
    return out.getvalue()


def pull(fetcher, ds, cache, headers, expected=None, log=print):
    """Every page of one dataset (cached pages skipped). Returns the rows."""
    manifest = os.path.join(source_dir(ds), "MANIFEST.csv")
    rows, offset = [], 0
    while True:
        path = os.path.join(cache, "pages", f"offset-{offset:06d}.json")
        url = rows_url(ds, offset)
        body, fetched = fetcher.get_cached(url, path, headers=headers)
        page = json.loads(body)
        if fetched:
            H.upsert_manifest(manifest, {
                "file": os.path.relpath(path, cache), "url": url, "retrieved_at": H.now_iso(),
                "http_status": 200, "bytes": len(body), "sha256": H.sha256_bytes(body),
                "rows": len(page)})
            log(f"{ds} page offset={offset}: {len(page)} rows (fetched)")
        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    if expected is not None and len(rows) != expected:
        raise RuntimeError(f"{ds}: pulled {len(rows)} rows, count(*) says {expected}")
    ids = [r.get(":id") for r in rows]
    if len(set(ids)) != len(ids):
        raise RuntimeError(f"{ds}: duplicate :id across pages -- paging was not stable")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", required=True, help="cache root; one folder per dataset")
    ap.add_argument("--gap", type=float, default=2.5)
    ap.add_argument("--only", nargs="*", choices=sorted(DATASETS))
    a = ap.parse_args(argv)
    if a.gap < 2.0:
        raise SystemExit("--gap below 2 s breaks the shared Socrata budget")
    token = os.environ.get("SOCRATA_APP_TOKEN", "")
    if not token:
        raise SystemExit("SOCRATA_APP_TOKEN is not set; refusing to pull without an app token")
    headers = {"X-App-Token": token}
    f = H.Fetcher(min_gap=a.gap)
    for ds in a.only or list(DATASETS):
        cache = os.path.join(a.cache, f"open-data-{ds}")
        manifest = os.path.join(source_dir(ds), "MANIFEST.csv")
        body, fetched = f.get_cached(count_url(ds), os.path.join(cache, "count.json"),
                                     headers=headers)
        expected = int(json.loads(body)[0]["count"])
        if fetched:
            H.upsert_manifest(manifest, {
                "file": "count.json", "url": count_url(ds), "retrieved_at": H.now_iso(),
                "http_status": 200, "bytes": len(body), "sha256": H.sha256_bytes(body),
                "rows": 1, "note": body.decode()})
        print(f"{ds}: count(*) = {expected}" + (" (fetched)" if fetched else " (cached)"))
        rows = pull(f, ds, cache, headers, expected=expected)
        text = rows_csv(ds, rows)
        data = gz(text)
        out = os.path.join(source_dir(ds), f"{ds}.csv.gz")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(data)
        H.upsert_manifest(manifest, {
            "file": f"{ds}.csv.gz",
            "url": "(assembled from pages/*.json by code/fetch_open_data_capital.py; not a download)",
            "retrieved_at": H.now_iso(), "bytes": len(data), "sha256": H.sha256_bytes(data),
            "rows": len(rows),
            "note": (f"rowsUpdatedAt {DATASETS[ds]['rows_updated_at']} (metadata read 2026-10-14); "
                     f"csv sha256 {H.sha256_bytes(text.encode())}; gzip mtime 0")})
        print(f"{ds}: wrote {os.path.relpath(out, ROOT)} ({len(rows)} rows, {len(data)} bytes)")
        asset, fn = DATASETS[ds]["dictionary"]
        url = (f"{DOMAIN}/api/views/{ds}/files/{asset}?"
               + urllib.parse.urlencode({"download": "true", "filename": fn}))
        try:
            b, fetched = f.get_cached(url, os.path.join(cache, fn), headers=headers)
        except RuntimeError as e:
            print(f"{ds}: data dictionary not downloaded: {e}")
            continue
        with open(os.path.join(source_dir(ds), fn), "wb") as fh:
            fh.write(b)
        if fetched:
            H.upsert_manifest(manifest, {
                "file": fn, "url": url, "retrieved_at": H.now_iso(), "http_status": 200,
                "bytes": len(b), "sha256": H.sha256_bytes(b), "rows": ""})
        print(f"{ds}: data dictionary {fn} ({len(b)} bytes)")
    print("requests sent per host:", f.counts)
    print("statuses:", sorted({s for _, s in f.statuses}))


if __name__ == "__main__":
    sys.exit(main())
