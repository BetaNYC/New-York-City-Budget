"""Tests for the Open Data tracking build (PLAN 2026-10-21): open_data_watch.py,
fetch_open_data_snapshots.py and build_open_data_crosswalk.py. No network: fake openers and the
committed snapshots. Each test names the outcome that would make it fail."""
import csv
import gzip
import io
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_open_data_crosswalk as X     # noqa: E402
import fetch_open_data_snapshots as S     # noqa: E402
import open_data_registry as R            # noqa: E402
import open_data_watch as W               # noqa: E402
import polite_http as H                   # noqa: E402

ROOT = os.path.dirname(HERE)


# ---- watch ---------------------------------------------------------------------------------

def meta(cols, rua=1700000000, n=10):
    return {"name": "x", "rowsUpdatedAt": rua,
            "columns": [{"fieldName": c, "cachedContents": {"non_null": n, "null": 0}} for c in cols]}


def test_watch_verdicts():
    """FAILS if a moved rowsUpdatedAt is not `changed`, a new column not `schema_changed`, or an
    unheld dataset not `not_held`."""
    cols = R.DATASETS["uvw5-9znb"]["columns"]
    assert W.summarize("uvw5-9znb", meta(cols, 200), 100)["verdict"] == "changed"
    assert W.summarize("uvw5-9znb", meta(cols, 100), 100)["verdict"] == "current"
    assert W.summarize("uvw5-9znb", meta(cols + ["new"], 100), 100)["verdict"] == "schema_changed"
    assert W.summarize("uvw5-9znb", meta(cols), None)["verdict"] == "not_held"


def test_watch_reads_held_snapshot_from_repo():
    """FAILS if the held rowsUpdatedAt of a committed snapshot is not found (README or MANIFEST)."""
    assert W.held_rows_updated_at("4d7f-74pe") == 1618932382
    assert W.held_rows_updated_at("t474-a92g") == 1766003942
    assert W.held_rows_updated_at("uvw5-9znb") == 1775844029


class _Resp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_watch_sends_only_the_standard_user_agent(tmp_path, monkeypatch):
    """FAILS if any header other than the repo's User-Agent goes out (no token, nothing personal),
    or if a request goes anywhere but /api/views/<id>.json."""
    sent = []

    def opener(req, timeout):
        sent.append(req)
        return _Resp(json.dumps(meta(R.DATASETS["uvw5-9znb"]["columns"])).encode())
    f = H.Fetcher(min_gap=0.0, opener=opener, sleep=lambda s: None)
    monkeypatch.setattr(W, "WATCH", str(tmp_path / "watch.csv"))
    W.main(["--only", "uvw5-9znb", "--dry-run"], fetcher=f)
    assert len(sent) == 1 and sent[0].full_url.endswith("/api/views/uvw5-9znb.json")
    assert {k.lower() for k in sent[0].headers} == {"user-agent"}
    assert sent[0].headers["User-agent"] == H.USER_AGENT


# ---- fetch ---------------------------------------------------------------------------------

def test_rows_url_pages_on_id_and_carries_the_filter():
    """FAILS if paging loses $order=:id, exceeds 5,000 rows, drops system fields or the $where."""
    u = S.rows_url("mwzb-yiwb", 10000, where="fiscal_year=2027")
    assert "$order=:id" in u and "$limit=5000" in u and "$offset=10000" in u and "$select=:*,*" in u
    assert "%24where=fiscal_year%3D2027" in u or "$where=fiscal_year%3D2027" in u


def test_unknown_field_is_a_stop():
    """FAILS if a row with a field outside the verified schema is written."""
    with pytest.raises(ValueError, match="not in the verified schema"):
        S.rows_csv("uvw5-9znb", [{":id": "r", "surprise": 1}])


def test_adopted_release_is_the_last_before_july():
    """FAILS if FY2027's adopted release is not the June 2026 one, or a later one leaks in."""
    pubs = ["20260217", "20260512", "20260630", "20270116"]
    assert S.adopted_release(pubs, 2027) == "20260630"
    assert S.adopted_release(pubs, 2026) is None


def test_terms_where_asks_for_padded_and_unpadded_numbers():
    """FAILS if the extract filter misses the pre-2023 unpadded forms ('40', '1')."""
    where, rel = S.terms_where({2021: {("040", "001")}}, ["20200630"])
    assert rel == {2021: "20200630"}
    assert "agency_number in ('040','40')" in where and "'001','1'" in where


def test_committed_snapshots_match_their_manifests():
    """FAILS if a committed snapshot's bytes differ from its MANIFEST sha256 or row count, or a
    MANIFEST records an app token."""
    for ds in S.OWN:
        d = S.source_dir(ds)
        rows = {r["file"]: r for r in csv.DictReader(open(os.path.join(d, "MANIFEST.csv")))}
        g = rows[f"{ds}.csv.gz"]
        data = open(os.path.join(d, f"{ds}.csv.gz"), "rb").read()
        assert H.sha256_bytes(data) == g["sha256"]
        n = sum(1 for _ in csv.DictReader(io.StringIO(gzip.decompress(data).decode())))
        assert n == int(g["rows"])
        text = open(os.path.join(d, "MANIFEST.csv")).read()
        assert "X-App-Token" not in text and "app token none" in text


# ---- crosswalk -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return X.build()


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_committed_crosswalk_equals_regeneration(built):
    """FAILS if data/open_data/ drifted from a fresh build (run --write)."""
    for rel, content in built.items():
        data = content if isinstance(content, bytes) else content.encode()
        assert open(os.path.join(ROOT, rel), "rb").read() == data, rel


def test_statuses_and_no_not_covered_rows(built):
    """FAILS if a status outside the plan appears, or not_covered rows are written."""
    for rel, content in built.items():
        if rel.endswith(".csv") and "crosswalk_" in rel:
            st = {r["match_status"] for r in rows(content)}
            assert st <= set(X.STATUSES) - {"not_covered"}, (rel, st)


def test_bucket_matching_never_guesses():
    """FAILS if two candidates are paired, or a lone pair is not left for same/differs."""
    ours = [{"fiscal_year": 2016, "k": "a"}, {"fiscal_year": 2016, "k": "b"}, {"fiscal_year": 2016, "k": "b"}]
    theirs = [{"fiscal_year": 2016, "k": "a"}, {"fiscal_year": 2016, "k": "b"},
              {"fiscal_year": 2016, "k": "c"}]
    res, only = X.match_buckets(ours, theirs, lambda r: (r["fiscal_year"], r["k"]),
                                lambda t: (t["fiscal_year"], t["k"]))
    assert res[id(ours[0])][0] is None
    assert res[id(ours[1])][0] == "ambiguous" and "equal counts" not in res[id(ours[1])][1]
    assert only[2016] == 1                       # the portal's "c"


def test_amount_tiers():
    """FAILS if the portal's documented rounding is not `same`, or a real gap is."""
    from decimal import Decimal as D
    assert X.amount_tier(D("5437.50"), D("5438")) == "rounded_dollars"
    assert X.amount_tier(D("1.005"), D("1.01")) == "rounded_cents"
    assert X.amount_tier(D("23296.5"), D("23296")) is None


def test_golden_rows(built):
    """FAILS if known records lose their known verdicts (checked by hand, 2026-10-21)."""
    cap = {r["record_key"]: r for r in rows(built["data/open_data/crosswalk_capital_award.csv"])}
    r = cap["2026|1005|2026"]                    # P CN1606: broken on the portal
    assert r["match_status"] == "differs" and "broken" in r["differing_fields"]
    damaged = [r for r in cap.values() if "Avil├⌐s" in r["differing_fields"]]
    assert damaged and all(r["match_status"] == "differs" for r in damaged)
    exp = rows(built["data/open_data/crosswalk_expense.csv"])
    u = [r for r in exp if r["dataset_id"] == "ujre-m2tj" and r["match_status"] == "same"]
    assert u and all(r["portal_as_of"] == "2021-06-09" for r in u)
    t = rows(built["data/open_data/crosswalk_terms_unit.csv"])
    assert any(r["fiscal_year"] == "2021" and r["match_status"] == "context" and "|040|" in r["record_key"] for r in t)


def test_coverage_adds_up(built):
    """FAILS if a covered year's statuses do not sum to its records."""
    for r in rows(built["data/open_data/coverage.csv"]):
        tot = sum(int(r[s]) for s in X.STATUSES)
        assert tot == int(r["records"]), r
