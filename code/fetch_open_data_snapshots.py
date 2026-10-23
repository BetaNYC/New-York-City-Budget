#!/usr/bin/env python3
"""fetch_open_data_snapshots.py -- pull the PLAN.md §3 datasets that have no fetcher of their own
(ujre-m2tj, djxg-kcfi, uvw5-9znb, and the mwzb-yiwb extract) into source/open-data-<id>/.

    python3 code/fetch_open_data_snapshots.py --cache DIR [--gap 2.5] [--only ID ...]

Etiquette (PLAN.md §4, epic #89), the same as code/fetch_open_data_capital.py:
  * metadata first (/api/views/<id>.json): rowsUpdatedAt, and the columns must equal the schema
    verified in code/open_data_registry.py, else stop;
  * count: GET /resource/<id>.json?$select=count(*)[&$where=...];
  * rows:  GET /resource/<id>.json?$select=:*,*&$order=:id&$limit=5000&$offset=N[&$where=...];
    one request at a time, >= --gap seconds apart (2 s floor); 403, or 429 twice, stops the host
    (code/polite_http.py); cached pages are never re-fetched;
  * the pulled row count must equal count(*), and :id must be unique across pages;
  * headers: the repo's User-Agent only, plus X-App-Token when SOCRATA_APP_TOKEN is set. The token
    is never printed or written; the MANIFEST says only whether one was used.

mwzb-yiwb (1.1 M rows) is pulled as a Council-relevant extract (PLAN Q2): the adopted release of
each fiscal year that has Terms & Conditions in the repo (the last publication_date before July 1
of the year before), and only the (agency, unit of appropriation) pairs those T&C files name.
Every pair a condition could mean is kept (a multi-agency condition contributes every agency x
every unit it lists), so the extract over-covers rather than misses. The $where is in the MANIFEST.

Snapshot policy (PLAN Q3, code/open_data_registry.py `policy`): the first snapshot is written at
source/open-data-<id>/<id>.csv.gz. Later ones: `every_change` writes source/open-data-<id>/<date>/,
`latest_only` replaces the top-level file. A snapshot is written only when rowsUpdatedAt moved.
"""
import argparse
import csv
import glob
import io
import json
import os
import re
import sys
import urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_open_data_capital as FC   # noqa: E402  (gz, the paging contract)
import open_data_registry as R         # noqa: E402
import open_data_watch as W            # noqa: E402
import polite_http as H                # noqa: E402
from retired_paths import family_glob  # noqa: E402

ROOT = os.path.dirname(HERE)
PAGE = 5000
SYSTEM = [":id", ":created_at", ":updated_at", ":version"]
OWN = [ds for ds, c in R.DATASETS.items() if c["fetcher"] == "code/fetch_open_data_snapshots.py"]


def source_dir(ds, root=ROOT):
    return os.path.join(root, "source", f"open-data-{ds}")


def _q(params):
    return urllib.parse.urlencode(params, safe=":*,$()'")


def rows_url(ds, offset, where=None, limit=PAGE):
    p = {"$select": ":*,*", "$order": ":id", "$limit": limit, "$offset": offset}
    if where:
        p["$where"] = where
    return f"{R.DOMAIN}/resource/{ds}.json?{_q(p)}"


def count_url(ds, where=None):
    p = {"$select": "count(*)"}
    if where:
        p["$where"] = where
    return f"{R.DOMAIN}/resource/{ds}.json?{_q(p)}"


def rows_csv(ds, rows):
    fields = SYSTEM + R.DATASETS[ds]["columns"]
    extra = sorted({k for r in rows for k in r} - set(fields))
    if extra:
        raise ValueError(f"{ds}: fields not in the verified schema: {extra}")
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    return out.getvalue()


# ---- the mwzb-yiwb extract ----------------------------------------------------------------

def terms_pairs(root=ROOT):
    """{fiscal_year: {(agency_code, unit)}} named by the repo's T&C files: the PDF-derived unit
    tables (data/fyNN/pdf/terms/*_terms_units.csv) where present, and the retired per-year CSVs
    (data/fyNN/terms/, or data/retired/fyNN/terms/ for the years redone from the PDF), where every
    agency of a condition is paired with every unit it lists."""
    out = {}
    for path in family_glob(os.path.join(root, "data"), "terms", "*.csv"):
        fy = 2000 + int(re.search(r"fy(\d\d)", os.path.basename(path)).group(1))
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                codes = re.findall(r"\d{3}", r.get("agency_code", ""))
                units = [u.strip() for u in r.get("units_of_appropriation", "").split(";")]
                for c in codes:
                    for u in units:
                        if re.fullmatch(r"\d{3}", u):
                            out.setdefault(fy, set()).add((c, u))
    for path in sorted(glob.glob(os.path.join(root, "data", "fy*", "pdf", "terms", "*_terms_units.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                u = r.get("unit_of_appropriation", "")
                if re.fullmatch(r"\d{3}", u):
                    out.setdefault(int(r["fiscal_year"]) if r.get("fiscal_year") else
                                   2000 + int(re.search(r"fy(\d\d)", path).group(1)),
                                   set()).add((r["agency_code"], u))
    return out


def adopted_release(pubs, fy):
    """The adopted release for fiscal year `fy`: the last publication_date (YYYYMMDD) before
    July 1 of fy-1, or None."""
    cut = f"{fy - 1}0701"
    before = sorted(p for p in pubs if p < cut)
    return before[-1] if before else None


def terms_where(pairs, pubs, years=range(2017, 2100)):
    """The $where for the extract, deterministic (sorted). Years without a release are skipped."""
    rel = {fy: adopted_release(pubs, fy) for fy in sorted(pairs) if fy in years}
    rel = {fy: p for fy, p in rel.items() if p}
    pub = " OR ".join(f"(publication_date='{p}' AND fiscal_year={fy})" for fy, p in rel.items())
    by_ag = {}
    for fy in rel:
        for a, u in pairs[fy]:
            by_ag.setdefault(a, set()).add(u)
    # Releases before 2023 write agency and unit numbers without leading zeros ('40', '1'), later
    # ones padded ('040', '001'): ask for both forms.
    def forms(x):
        return sorted({x, x.lstrip("0") or "0"})
    units = " OR ".join(
        f"(agency_number in ({','.join(repr(f) for f in forms(a))}) AND unit_appropriation_number in "
        f"({','.join(repr(f) for u in sorted(us) for f in forms(u))}))" for a, us in sorted(by_ag.items()))
    return f"({pub}) AND ({units})", rel


# ---- pull ----------------------------------------------------------------------------------

def get_json(fetcher, url, path, headers):
    body, fetched = fetcher.get_cached(url, path, headers=headers)
    return json.loads(body), body, fetched


def pull(fetcher, ds, cache, headers, where, expected, manifest_rows):
    rows, offset = [], 0
    while True:
        path = os.path.join(cache, "pages", f"offset-{offset:06d}.json")
        url = rows_url(ds, offset, where)
        page, body, fetched = get_json(fetcher, url, path, headers)
        manifest_rows.append({"file": os.path.relpath(path, cache), "url": url,
                              "retrieved_at": H.now_iso() if fetched else "(cached)",
                              "http_status": 200, "bytes": len(body),
                              "sha256": H.sha256_bytes(body), "rows": len(page)})
        print(f"{ds} offset={offset}: {len(page)} rows" + (" (fetched)" if fetched else " (cached)"))
        rows.extend(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    if len(rows) != expected:
        raise RuntimeError(f"{ds}: pulled {len(rows)} rows, count(*) says {expected}")
    ids = [r.get(":id") for r in rows]
    if len(set(ids)) != len(ids):
        raise RuntimeError(f"{ds}: duplicate :id across pages -- paging was not stable")
    return rows


def snapshot_dir(ds, rua, root=ROOT):
    """Where this snapshot goes, or None when the newest held snapshot already has `rua`."""
    held = W.held_rows_updated_at(ds, root)
    top = source_dir(ds, root)
    if held is None or not os.path.exists(os.path.join(top, f"{ds}.csv.gz")):
        return top
    if int(rua) <= held:
        return None
    if R.DATASETS[ds]["policy"] == "latest_only":
        return top
    return os.path.join(top, date.fromtimestamp(int(rua)).isoformat())


def write_manifest(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=H.MANIFEST_FIELDS, lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["file"]):
            w.writerow({k: r.get(k, "") for k in H.MANIFEST_FIELDS})


def fetch_one(f, ds, cache, headers, token_used, refresh=False):
    cfg = R.DATASETS[ds]
    meta, body, _ = get_json(f, W.view_url(ds), os.path.join(cache, "metadata.json"), headers)
    cols = [c["fieldName"] for c in meta["columns"] if not c["fieldName"].startswith(":")]
    if cols != cfg["columns"]:
        raise SystemExit(f"{ds}: metadata columns differ from the verified schema; update "
                         f"code/open_data_registry.py first.\n  got  {cols}\n  want {cfg['columns']}")
    rua = int(meta["rowsUpdatedAt"])
    out_dir = snapshot_dir(ds, rua)
    if out_dir is None and refresh and R.DATASETS[ds]["policy"] == "latest_only":
        out_dir = source_dir(ds)        # same rows upstream, a corrected extract filter
    if out_dir is None:
        print(f"{ds}: held snapshot is current (rowsUpdatedAt {rua}); nothing to pull")
        return
    mrows = [{"file": "metadata.json", "url": W.view_url(ds), "retrieved_at": H.now_iso(),
              "http_status": 200, "bytes": len(body), "sha256": H.sha256_bytes(body),
              "note": f"rowsUpdatedAt {rua}"}]
    where, note = None, ""
    if cfg.get("where") == "terms":
        g, gbody, _ = get_json(f, f"{R.DOMAIN}/resource/{ds}.json?" +
                               _q({"$select": "publication_date", "$group": "publication_date",
                                   "$order": "publication_date"}),
                               os.path.join(cache, "publications.json"), headers)
        pubs = [x["publication_date"] for x in g]
        where, rel = terms_where(terms_pairs(), pubs)
        # The cache is keyed by the filter: a changed $where never reuses another filter's pages.
        cache = os.path.join(cache, "where-" + H.sha256_bytes(where.encode())[:12])
        note = ("Council-relevant extract (PLAN Q2): adopted release per T&C fiscal year "
                + ", ".join(f"FY{fy}={p}" for fy, p in rel.items())
                + "; (agency, unit) pairs named by data/fy*/terms and data/fy*/pdf/terms. $where: " + where)
        mrows.append({"file": "publications.json", "url": f"{R.DOMAIN}/resource/{ds}.json?$select="
                      "publication_date&$group=publication_date", "retrieved_at": H.now_iso(),
                      "http_status": 200, "bytes": len(gbody), "sha256": H.sha256_bytes(gbody),
                      "rows": len(pubs)})
    cj, cbody, _ = get_json(f, count_url(ds, where), os.path.join(cache, "count.json"), headers)
    expected = int(cj[0]["count"])
    mrows.append({"file": "count.json", "url": count_url(ds, where), "retrieved_at": H.now_iso(),
                  "http_status": 200, "bytes": len(cbody), "sha256": H.sha256_bytes(cbody),
                  "rows": 1, "note": cbody.decode().strip()})
    print(f"{ds}: count(*) = {expected}")
    rows = pull(f, ds, cache, headers, where, expected, mrows)
    text = rows_csv(ds, rows)
    data = FC.gz(text)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{ds}.csv.gz"), "wb") as fh:
        fh.write(data)
    mrows.append({"file": f"{ds}.csv.gz",
                  "url": "(assembled from pages/*.json by code/fetch_open_data_snapshots.py; not a download)",
                  "retrieved_at": H.now_iso(), "bytes": len(data), "sha256": H.sha256_bytes(data),
                  "rows": len(rows),
                  "note": (f"rowsUpdatedAt {rua}; csv sha256 {H.sha256_bytes(text.encode())}; gzip "
                           f"mtime 0; app token {'used (not recorded)' if token_used else 'none'}"
                           + (f"; {note}" if note else ""))})
    if cfg.get("dictionary"):
        asset, fn = cfg["dictionary"]
        url = (f"{R.DOMAIN}/api/views/{ds}/files/{asset}?"
               + urllib.parse.urlencode({"download": "true", "filename": fn}))
        try:
            b, _ = f.get_cached(url, os.path.join(cache, fn), headers=headers)
            with open(os.path.join(out_dir, fn), "wb") as fh:
                fh.write(b)
            mrows.append({"file": fn, "url": url, "retrieved_at": H.now_iso(), "http_status": 200,
                          "bytes": len(b), "sha256": H.sha256_bytes(b)})
        except RuntimeError as e:
            print(f"{ds}: data dictionary not downloaded: {e}")
    write_manifest(os.path.join(out_dir, "MANIFEST.csv"), mrows)
    print(f"{ds}: wrote {os.path.relpath(out_dir, ROOT)}/{ds}.csv.gz ({len(rows)} rows, {len(data)} bytes)")
    return {"rows": len(rows), "rua": rua, "out_dir": out_dir, "bytes": len(data), "note": note}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--cache", required=True, help="cache root; one folder per dataset")
    ap.add_argument("--gap", type=float, default=2.5)
    ap.add_argument("--only", nargs="*", choices=OWN)
    ap.add_argument("--refresh", action="store_true",
                    help="re-pull a latest_only extract whose filter changed (rowsUpdatedAt unchanged)")
    a = ap.parse_args(argv)
    if a.gap < 2.0:
        raise SystemExit("--gap below 2 s breaks the shared Socrata budget")
    token = os.environ.get("SOCRATA_APP_TOKEN", "")
    headers = {"X-App-Token": token} if token else {}
    f = H.Fetcher(min_gap=a.gap)
    for ds in a.only or OWN:
        fetch_one(f, ds, os.path.join(a.cache, f"open-data-{ds}", date.today().isoformat()),
                  headers, bool(token), refresh=a.refresh)
    print("requests sent per host:", f.counts)
    print("statuses:", sorted({s for _, s in f.statuses}))


if __name__ == "__main__":
    sys.exit(main())
