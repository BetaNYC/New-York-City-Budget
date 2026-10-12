#!/usr/bin/env python3
"""reconcile_disclosure_schedule_c.py -- join the Council's expense disclosure to this repo's
Schedule C award files, per fiscal year, and report what each covers of the other.

Inputs (all committed, all read-only here):
  data/fyNN/expense_disclosure/fyNN_expense_awards.csv        the disclosure (parse_expense_disclosure.py)
  data/fyNN/schedule_c/fyNN_schedule_c_awards.csv             Schedule C body       } the PUBLISHED
  data/fyNN/schedule_c/fyNN_appendix_{a_aging,b_local,c_youth}.csv  appendices    } award set (what
                                                                                    } the MCP indexes)
  data/recovered/schedule_c_absorbed_awards.csv               sidecar: awards the parser absorbed
  data/recovered/schedule_c_appendix_recovered.csv            sidecar: BUILT FROM THE DISCLOSURE --
                                                              matching it to the disclosure is
                                                              circular, so it is reported apart and
                                                              never counted as coverage evidence.

The key is (EIN, amount) within one fiscal year, matched as a MULTISET: a key printed three times
in the disclosure and twice in Schedule C is two matches and one unmatched row. Never EIN alone
(a fiscal sponsor's EIN covers hundreds of grantees; FCNY's covers 229 names) and never the
council member (the disclosure's roster is the one at export time, not at adoption).

When a key's disclosure rows differ in stream or status and Schedule C has fewer rows than the
disclosure, WHICH disclosure rows are the matched ones is not knowable from (EIN, amount). The
allocation is deterministic -- a Schedule C stream claims a disclosure row of its own stream
first (body -> non-appendix streams, appendix A -> Aging, B -> Local, C -> Youth), then cleared
before pending, then sheet order -- and every row allocated that way is COUNTED as ambiguous in
the report rather than presented as a fact.

Second question, GitHub #57 blocker 2: are the appendix CSVs a SUBSET of the body (adding them
double-counts) or ADDITIVE (separate awards)? Settled per year from the disclosure's own
`source` column, which names each designation's stream:
  * body rows whose key the disclosure carries ONLY under Local/Aging/Youth -- what a body that
    re-printed the appendices would contain;
  * double-listed rows -- keys in both body and appendix where the disclosure has fewer rows
    than body + appendix together, i.e. the same designation printed twice.
Both zero (or a listed handful) and the appendices are additive.

Usage:
  python3 code/reconcile_disclosure_schedule_c.py            print, and write the two outputs
  python3 code/reconcile_disclosure_schedule_c.py --check    exit 1 if a committed output is stale
  python3 code/reconcile_disclosure_schedule_c.py --dry-run  print only
Outputs: data/DISCLOSURE-COVERAGE.md, data/disclosure_schedule_c_coverage.csv
Stdlib only. No network.
"""
import argparse
import csv
import io
import os
import sys
from collections import Counter, defaultdict
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_MD = os.path.join(DATA, "DISCLOSURE-COVERAGE.md")
OUT_CSV = os.path.join(DATA, "disclosure_schedule_c_coverage.csv")
YEARS = range(2013, 2028)
SC_YEARS = range(2015, 2028)      # Schedule C award files exist FY2015 onward
CITY_EIN = "136400434"            # the City of New York's own EIN (undesignated pool money)

APPENDIX_FILES = (("appendix_a", "appendix_a_aging", "aging"),
                  ("appendix_b", "appendix_b_local", "local"),
                  ("appendix_c", "appendix_c_youth", "youth"))
APPENDIX_STREAMS = {"aging", "local", "youth"}
# Which disclosure stream each Schedule C file claims first when a key is shared.
PREFERS = {"body": ("speaker", "initiative"), "appendix_a": ("aging",),
           "appendix_b": ("local",), "appendix_c": ("youth",),
           "absorbed": ("speaker", "initiative"), "appendix_recovered": ()}
PUBLISHED = ("body", "appendix_a", "appendix_b", "appendix_c")
SIDECARS = ("absorbed", "appendix_recovered")
STREAMS = ("local", "aging", "youth", "speaker", "initiative")
STATUSES = ("cleared", "pending", "other")


def stream_of(source):
    """Disclosure `source` -> stream. The three appendix streams are named exactly 'Local',
    'Aging', 'Youth' in every year; 'Speaker's Initiative' (either apostrophe) is the Speaker's
    pool; everything else is a named citywide initiative."""
    s = (source or "").strip().lower()
    if s in APPENDIX_STREAMS:
        return s
    if s.startswith("speaker"):
        return "speaker"
    return "initiative"


def norm_ein(e):
    return (e or "").strip().replace("-", "")


def money(s):
    s = (s or "").strip()
    return Decimal(s) if s else Decimal(0)


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_disclosure(fy, data_dir=DATA):
    yy = f"fy{fy % 100:02d}"
    rows = _read(os.path.join(data_dir, yy, "expense_disclosure", f"{yy}_expense_awards.csv"))
    return [dict(key=(norm_ein(r["ein"]), money(r["amount"])), amount=money(r["amount"]),
                 stream=stream_of(r["source"]), status=r["status_norm"],
                 row=int(r["source_row"]), ein=norm_ein(r["ein"]), name=r["legal_name"],
                 source=r["source"]) for r in rows]


def load_schedule_c(fy, data_dir=DATA):
    """{stream_name: [row dicts]} for one year. Missing files are an empty list."""
    yy = f"fy{fy % 100:02d}"
    out = {k: [] for k in PUBLISHED + SIDECARS}
    sc = os.path.join(data_dir, yy, "schedule_c")
    p = os.path.join(sc, f"{yy}_schedule_c_awards.csv")
    if os.path.exists(p):
        out["body"] = _read(p)
    for name, suffix, _ in APPENDIX_FILES:
        p = os.path.join(sc, f"{yy}_{suffix}.csv")
        if os.path.exists(p):
            out[name] = _read(p)
    for name, fname in (("absorbed", "schedule_c_absorbed_awards.csv"),
                        ("appendix_recovered", "schedule_c_appendix_recovered.csv")):
        p = os.path.join(data_dir, "recovered", fname)
        if os.path.exists(p):
            out[name] = [r for r in _read(p) if r.get("fiscal_year") == str(fy)]
    for rows in out.values():
        for r in rows:
            r["_key"] = (norm_ein(r.get("ein")), money(r.get("amount")))
    return out


def match_year(disc, sc, order=PUBLISHED + SIDECARS):
    """Multiset match. Returns (matched, unmatched_sc, ambiguous) where
         matched[i]     = Schedule C stream that claimed disclosure row i (or absent)
         unmatched_sc   = {stream: [rows with no disclosure counterpart]}
         ambiguous      = set of disclosure indices whose claim was a choice, not a fact."""
    by_key = defaultdict(list)
    for i, d in enumerate(disc):
        by_key[d["key"]].append(i)
    status_rank = {"cleared": 0, "pending": 1, "other": 2}
    matched, unmatched_sc = {}, {k: [] for k in order}
    for name in order:
        prefer = PREFERS[name]
        for r in sc.get(name, []):
            free = [i for i in by_key.get(r["_key"], ()) if i not in matched]
            if not free:
                unmatched_sc[name].append(r)
                continue
            free.sort(key=lambda i: (disc[i]["stream"] not in prefer,
                                     status_rank.get(disc[i]["status"], 3), disc[i]["row"]))
            matched[free[0]] = name
    ambiguous = set()
    for idxs in by_key.values():
        claimed = [i for i in idxs if i in matched]
        if not claimed or len(claimed) == len(idxs):
            continue  # nothing claimed, or everything claimed: no choice was made
        kinds = {(disc[i]["stream"], disc[i]["status"]) for i in idxs}
        if len(kinds) > 1:
            ambiguous.update(idxs)
    return matched, unmatched_sc, ambiguous


def blocker2(disc, sc):
    """Additive-vs-subset evidence for one year. All counts are rows."""
    disc_streams = defaultdict(Counter)
    for d in disc:
        disc_streams[d["key"]][d["stream"] in APPENDIX_STREAMS] += 1
    body_keys = Counter(r["_key"] for r in sc["body"])
    app_rows = [r for n, _, _ in APPENDIX_FILES for r in sc[n]]
    app_keys = Counter(r["_key"] for r in app_rows)
    only_app_keys = sorted(k for k in body_keys
                           if disc_streams[k][True] and not disc_streams[k][False])
    body_only_app = sum(body_keys[k] for k in only_app_keys)
    app_only_init = sum(n for k, n in app_keys.items()
                        if disc_streams[k][False] and not disc_streams[k][True])
    # On a key printed b times in the body and a times in the appendices, an additive reading
    # needs the disclosure to hold b + a rows. Whatever it lacks -- up to min(b, a) -- is the
    # same designation printed in both places.
    # A key the disclosure does not carry at all says nothing either way: it is counted as
    # unconfirmed, not as double-listed.
    double, double_keys, unconfirmed = 0, [], 0
    for k in sorted(set(body_keys) & set(app_keys)):
        b, a = body_keys[k], app_keys[k]
        have = disc_streams[k][True] + disc_streams[k][False]
        if not have:
            unconfirmed += 1
            continue
        n = min(b, a, max(0, b + a - have))
        if n:
            double += n
            double_keys.append((k, b, a, have, n))
    disc_app_cleared = sum((d["amount"] for d in disc
                            if d["stream"] in APPENDIX_STREAMS and d["status"] == "cleared"),
                           Decimal(0))
    disc_app_all = sum((d["amount"] for d in disc if d["stream"] in APPENDIX_STREAMS),
                       Decimal(0))
    return dict(body_rows=len(sc["body"]), app_rows=len(app_rows),
                app_amount=sum((r["_key"][1] for r in app_rows), Decimal(0)),
                disc_app_rows=sum(1 for d in disc if d["stream"] in APPENDIX_STREAMS),
                disc_app_all=disc_app_all, disc_app_cleared=disc_app_cleared,
                body_only_app=body_only_app, app_only_init=app_only_init, double=double,
                body_only_app_amount=sum((k[1] * body_keys[k] for k in only_app_keys),
                                         Decimal(0)),
                only_app_keys=[(k, body_keys[k], disc_streams[k][True]) for k in only_app_keys],
                double_keys=double_keys, unconfirmed_shared_keys=unconfirmed)


def verdict(b):
    if b["app_rows"] == 0:
        return "NO APPENDIX ROWS"
    if b["body_only_app"] == 0 and b["double"] == 0:
        return "ADDITIVE"
    if b["double"] * 2 > b["app_rows"]:
        return "SUBSET"
    return "ADDITIVE (with exceptions)"


def analyse(data_dir=DATA):
    """Everything the report prints, as plain data. Deterministic."""
    years = []
    for fy in YEARS:
        disc = load_disclosure(fy, data_dir)
        sc = load_schedule_c(fy, data_dir)
        pub = {k: sc[k] for k in PUBLISHED}
        m_pub, un_pub, amb_pub = match_year(disc, pub, PUBLISHED)
        m_all, un_all, amb_all = match_year(disc, sc)
        cells = []
        for st in STREAMS:
            for s in STATUSES:
                idx = [i for i, d in enumerate(disc) if d["stream"] == st and d["status"] == s]
                if not idx:
                    continue
                amt = lambda ii: sum((disc[i]["amount"] for i in ii), Decimal(0))  # noqa: E731
                mp = [i for i in idx if i in m_pub]
                ma = [i for i in idx if i in m_all and m_all[i] != "appendix_recovered"]
                mr = [i for i in idx if m_all.get(i) == "appendix_recovered"]
                cells.append(dict(fiscal_year=fy, stream=st, status=s, disc_rows=len(idx),
                                  disc_amount=amt(idx), matched_rows=len(mp),
                                  matched_amount=amt(mp),
                                  ambiguous_rows=sum(1 for i in mp if i in amb_pub),
                                  matched_rows_with_absorbed=len(ma),
                                  matched_amount_with_absorbed=amt(ma),
                                  circular_rows=len(mr), circular_amount=amt(mr)))
        unmatched_disc = [disc[i] for i in range(len(disc)) if i not in m_pub]
        years.append(dict(
            fy=fy, disc=disc, cells=cells,
            sc_rows={k: len(v) for k, v in sc.items()},
            sc_amount={k: sum((r["_key"][1] for r in v), Decimal(0)) for k, v in sc.items()},
            unmatched_sc={k: len(v) for k, v in un_pub.items()},
            unmatched_sc_amount={k: sum((r["_key"][1] for r in v), Decimal(0))
                                 for k, v in un_pub.items()},
            unmatched_disc=unmatched_disc,
            unmatched_sc_rows={k: v for k, v in un_pub.items()},
            ambiguous=len(amb_pub & set(m_pub)),
            blocker2=blocker2(disc, sc) if fy in SC_YEARS else None,
            # The direct test: the body is matched FIRST, so an appendix row only matches if the
            # disclosure holds a designation the body did not already claim.
            app_matched_after_body=sum(1 for v in m_pub.values() if v.startswith("appendix")),
        ))
    return years


# ---------------------------------------------------------------- rendering

def usd(d):
    d = Decimal(d)
    return f"{d:,.0f}" if d == d.to_integral_value() else f"{d:,.2f}"


def pct(a, b):
    return f"{100 * Decimal(a) / Decimal(b):.1f}%" if b else "—"


CSV_FIELDS = ["fiscal_year", "stream", "status", "disc_rows", "disc_amount", "matched_rows",
              "matched_amount", "ambiguous_rows", "matched_rows_with_absorbed",
              "matched_amount_with_absorbed", "circular_rows", "circular_amount"]


def coverage_csv(years):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    w.writeheader()
    for y in years:
        for c in y["cells"]:
            w.writerow({k: (format(v, "f") if isinstance(v, Decimal) else v)
                        for k, v in c.items()})
    return buf.getvalue()


def _sum(cells, field, **where):
    return sum((c[field] for c in cells if all(c[k] == v for k, v in where.items())),
               Decimal(0) if "amount" in field else 0)


def report_md(years):
    L = ["# Expense disclosure vs Schedule C — coverage and the appendix question", "",
         "**Generated by:** `code/reconcile_disclosure_schedule_c.py` (stdlib, no network) from "
         "committed files only: `data/fyNN/expense_disclosure/` (the Council's disclosure "
         "workbooks, retrieved 2026-07-15) and `data/fyNN/schedule_c/` + `data/recovered/`. "
         "Re-running it on the same files reproduces this report byte for byte; "
         "`code/test_reconcile_disclosure_schedule_c.py` fails if it is stale.", "",
         "**Key:** `(EIN, amount)` within one fiscal year, matched as a multiset. Never EIN "
         "alone, never the council member. **Published set** = the Schedule C body + the three "
         "appendix CSVs (what the MCP indexes). `data/recovered/schedule_c_appendix_recovered.csv`"
         " was built *from* the disclosure, so it is reported separately as **circular** and is "
         "never counted as coverage.", "",
         "**Every figure here is this script's arithmetic on those files. None is a figure the "
         "Council publishes.**", ""]

    # ---- 1. headline per year
    L += ["## 1. Coverage per year (published set)", "",
          "Cleared is the headline; all statuses is shown beside it, labeled. Ambiguous = "
          "matched disclosure rows whose key has rows of different stream/status and fewer "
          "Schedule C rows than disclosure rows, so *which* of them matched is a deterministic "
          "choice, not a fact.", "",
          "| FY | disclosure rows | matched | cleared $ | cleared $ matched | % | all $ | "
          "all $ matched | % | ambiguous | Schedule C rows with no disclosure row |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for y in years:
        c = y["cells"]
        n, nm = _sum(c, "disc_rows"), _sum(c, "matched_rows")
        ca, cm = _sum(c, "disc_amount", status="cleared"), _sum(c, "matched_amount",
                                                               status="cleared")
        aa, am = _sum(c, "disc_amount"), _sum(c, "matched_amount")
        un = sum(y["unmatched_sc"][k] for k in PUBLISHED)
        sc_n = sum(y["sc_rows"][k] for k in PUBLISHED)
        L.append(f"| FY{y['fy']} | {n:,} | {nm:,} | {usd(ca)} | {usd(cm)} | {pct(cm, ca)} | "
                 f"{usd(aa)} | {usd(am)} | {pct(am, aa)} | {y['ambiguous']:,} | "
                 + (f"{un:,} of {sc_n:,}" if sc_n else "no award files") + " |")
    L += ["", "FY2013 and FY2014 have no Schedule C award files (initiatives only), so their "
          "coverage is zero by construction, not by measurement.", ""]

    # ---- 2. stream x status
    L += ["## 2. Coverage by year × stream × status (published set)", "",
          "Streams from the disclosure's `source` column: `local`, `aging`, `youth` (the three "
          "appendix streams, named exactly that in every workbook), `speaker` (Speaker's "
          "Initiative), `initiative` (every named citywide initiative). Rows: matched / "
          "disclosure. Full table with dollars, the absorbed-awards sidecar and the circular "
          "sidecar: `data/disclosure_schedule_c_coverage.csv`.", "",
          "| FY | " + " | ".join(f"{st} cleared | {st} pending" for st in STREAMS) + " |",
          "|---|" + "---:|" * (2 * len(STREAMS))]
    for y in years:
        if y["fy"] not in SC_YEARS:
            continue
        cells = []
        for st in STREAMS:
            for s in ("cleared", "pending"):
                d = _sum(y["cells"], "disc_rows", stream=st, status=s)
                m = _sum(y["cells"], "matched_rows", stream=st, status=s)
                cells.append(f"{m:,}/{d:,}" if d else "—")
        L.append(f"| FY{y['fy']} | " + " | ".join(cells) + " |")
    L += ["", "No disclosure row in any year has a status other than Cleared/Pending, so the "
          "`other` column is omitted here; it is in the CSV schema and would appear there.", ""]

    # ---- 3. sidecars
    L += ["## 3. What the sidecars add", "",
          "| FY | absorbed sidecar rows | of which match a disclosure row left unmatched by the "
          "published set | circular appendix sidecar rows | of which match |",
          "|---|---:|---:|---:|---:|"]
    for y in years:
        if y["fy"] not in SC_YEARS:
            continue
        c = y["cells"]
        add = _sum(c, "matched_rows_with_absorbed") - _sum(c, "matched_rows")
        L.append(f"| FY{y['fy']} | {y['sc_rows']['absorbed']:,} | {add:,} | "
                 f"{y['sc_rows']['appendix_recovered']:,} | {_sum(c, 'circular_rows'):,} |")
    L += ["", "The circular sidecar matching the disclosure says nothing about either source: it "
          "*is* disclosure rows. It is listed only so the reader can see it was not counted.", ""]

    # ---- 4. blocker 2
    L += ["## 4. GitHub #57 blocker 2 — are the appendix CSVs additive to the body, or a subset?",
          "", "Settled per year from the disclosure's own `source` column. **body rows that can "
          "only be appendix designations** = body rows whose `(EIN, amount)` the disclosure "
          "carries *only* under Local/Aging/Youth. **double-listed** = rows on keys present in "
          "both body and appendix beyond what the disclosure itself holds — the same "
          "designation printed twice. If the appendices were re-sorted subsets of the body, both "
          "would be close to the appendix row count.", "",
          "The direct test is the column **appendix rows matched after the body**: body rows "
          "are matched to the disclosure first, so an appendix row can only match a designation "
          "the body did not already claim. A subset would leave that column near zero.", "",
          "| FY | body rows | appendix rows | appendix rows matched after the body | appendix $ | disclosure L/A/Y rows | disclosure "
          "L/A/Y $ (all) | (cleared) | body rows that can only be appendix | $ | double-listed "
          "| appendix rows the disclosure files only under an initiative | verdict |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for y in years:
        b = y["blocker2"]
        if b is None:
            continue
        L.append(f"| FY{y['fy']} | {b['body_rows']:,} | {b['app_rows']:,} | "
                 f"{y['app_matched_after_body']:,} | {usd(b['app_amount'])} | {b['disc_app_rows']:,} | {usd(b['disc_app_all'])} | "
                 f"{usd(b['disc_app_cleared'])} | {b['body_only_app']:,} | "
                 f"{usd(b['body_only_app_amount'])} | {b['double']:,} | "
                 f"{b['app_only_init']:,} | {verdict(b)} |")
    L += ["", "**Reading the verdict.** `NO APPENDIX ROWS`: the year's appendix CSVs are empty "
          "(header only; the PDF parse missed them, GitHub #59), so there is nothing to add or "
          "to double-count; the disclosure-built sidecar holds that year's appendix awards and "
          "was built skipping any `(EIN, amount)` already in the body. `ADDITIVE`: no body row "
          "is an appendix-only designation and nothing is double-listed. `ADDITIVE (with "
          "exceptions)`: the same, except for the rows listed below — a handful per year "
          "against thousands of appendix rows, each a candidate extraction or filing error, "
          "not evidence that the appendices repeat the body.", "",
          "### 4b. The exceptions, key by key", "",
          "| FY | EIN | amount | kind | body rows | appendix rows | disclosure rows | rows |",
          "|---|---|---:|---|---:|---:|---:|---:|"]
    for y in years:
        b = y["blocker2"]
        if b is None:
            continue
        for (ein, amt), nb, nd in b["only_app_keys"]:
            L.append(f"| FY{y['fy']} | {ein} | {usd(amt)} | body row the disclosure files only "
                     f"under Local/Aging/Youth | {nb} | — | {nd} | {nb} |")
        for (ein, amt), nb, na, have, n in b["double_keys"]:
            L.append(f"| FY{y['fy']} | {ein} | {usd(amt)} | double-listed | {nb} | {na} | "
                     f"{have} | {n} |")
    L.append("")

    # ---- 5. what the unmatched disclosure rows are, per year
    L += ["## 5. Disclosure rows with no counterpart in the published set", "",
          f"Split by whether the grantee EIN is `{CITY_EIN}`, the City of New York's own.", "",
          "| FY | unmatched rows | $ | with City EIN | $ | other EINs | $ |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for y in years:
        u = y["unmatched_disc"]
        city = [d for d in u if d["ein"] == CITY_EIN]
        other = [d for d in u if d["ein"] != CITY_EIN]
        s = lambda xs: usd(sum((d["amount"] for d in xs), Decimal(0)))  # noqa: E731
        L.append(f"| FY{y['fy']} | {len(u):,} | {s(u)} | {len(city):,} | {s(city)} | "
                 f"{len(other):,} | {s(other)} |")
    fy27 = [y for y in years if y["fy"] == 2027][0]
    L += ["", "FY2027 in full (every unmatched disclosure row):", "",
          "| row | EIN | legal name | source | status | amount |", "|---:|---|---|---|---|---:|"]
    for d in sorted(fy27["unmatched_disc"], key=lambda d: d["row"]):
        L.append(f"| {d['row']} | {d['ein']} | {d['name']} | {d['source']} | {d['status']} | "
                 f"{usd(d['amount'])} |")
    L += ["", "And the other direction, FY2027 Schedule C rows with no disclosure row:", "",
          "| file | EIN | organization | amount |", "|---|---|---|---:|"]
    for name in PUBLISHED:
        for r in fy27["unmatched_sc_rows"][name]:
            L.append(f"| {name} | {r['_key'][0]} | {r.get('organization', '')} | "
                     f"{usd(r['_key'][1])} |")
    L.append("")
    return "\n".join(L) + "\n"


def outputs(data_dir=DATA):
    years = analyse(data_dir)
    return {OUT_MD: report_md(years), OUT_CSV: coverage_csv(years)}, years


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if a committed output is stale")
    ap.add_argument("--dry-run", action="store_true", help="print only, write nothing")
    a = ap.parse_args(argv)
    files, years = outputs()
    for y in years:
        b = y["blocker2"]
        print(f"FY{y['fy']}: {len(y['disc']):,} disclosure rows, "
              f"{sum(1 for c in y['cells'] for _ in range(c['matched_rows'])):,} matched"
              + (f"; blocker 2: {verdict(b)}" if b else ""))
    if a.check:
        bad = [p for p, t in files.items()
               if not os.path.exists(p) or open(p, encoding="utf-8").read() != t]
        for p in bad:
            print(f"STALE: {os.path.relpath(p, ROOT)}")
        return 1 if bad else 0
    if not a.dry_run:
        for p, t in files.items():
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(t)
            print(f"wrote {os.path.relpath(p, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
