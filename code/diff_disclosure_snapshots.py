#!/usr/bin/env python3
"""diff_disclosure_snapshots.py -- compare two snapshots of one fiscal year's Council expense
disclosure and report what moved.

    python3 code/diff_disclosure_snapshots.py OLD NEW [--out report.md]

OLD and NEW are each either a disclosure workbook (funded_disclosure_FY{YYYY}.xlsx / .xls, read
through code/parse_expense_disclosure.py) or a normalized CSV written by it
(data/fyNN/expense_disclosure/fyNN_expense_awards.csv). They may be mixed. Both must be the same
fiscal year; anything else is refused.

Reported:
  * status transitions  (pending -> cleared, cleared -> pending, and any move to/from 'other')
  * amount changes      (mocs_id-keyed years only; see below)
  * added and removed rows
  * totals by status_norm, old vs new, and the delta -- cleared, pending, other separately
  * ambiguity, counted: every place where the pairing of an old row to a new row was a choice

How rows are paired:
  * FY2024+ (mocs_id present): rows whose MOCS ID appears once in each snapshot pair by it. A
    MOCS ID that is blank or repeated inside either snapshot cannot key a row; those rows, and
    rows whose ID is on one side only, go to the composite key below. A row the Council merely
    re-numbered is therefore paired, not reported as one removal plus one addition. It is
    listed in its own RE-NUMBERED section (with a count per old-prefix -> new-prefix; the
    2026-10-12 re-pull moved 129 FY2026 rows from "FY26 NNNNN" to "FY26GP NNNNN"), never as a
    field change "on a MOCS-ID pair" -- a pair keyed on the MOCS ID cannot have a changed one.
  * Earlier years: composite key (ein, amount, agency, program_name, council_member, source),
    matched as a MULTISET -- a key printed twice is two rows. Because amount is part of the key,
    an amount change in these years is not detectable as such: it shows as one removed row and
    one added row. Where exactly one removed and one added row agree on every key field except
    amount, the pair is listed as a CANDIDATE amount change -- a nomination for a person to check
    in the workbooks, never counted as an amount change.
  * Inside one composite key, rows whose status did not change are paired first. If what is
    left on both sides still has more than one distinct status, which old row became which new
    row is not knowable; the group is counted as ambiguous and its transitions are reported as
    counts, not as row-to-row facts.

Stdlib only (plus xlrd if an .xls is given). No network: this compares files already on disk.
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import parse_expense_disclosure as P  # noqa: E402

COMPOSITE = ("ein", "amount", "agency", "program_name", "council_member", "source")
STATUSES = ("cleared", "pending", "other")
# Fields compared on a MOCS-ID pair besides status and amount; a change there is reported as a
# count per field, since a re-filed grantee name or EIN is worth knowing about.
OTHER_FIELDS = ("ein", "legal_name", "source", "council_member", "agency", "program_name",
                "purpose")


def load(path):
    """Snapshot -> (fiscal_year, [row dict], label). Row values are strings; amount is a
    Decimal. A workbook is parsed exactly as --write would parse it, so a workbook and the CSV
    written from it load identically."""
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        missing = set(P.OUT_FIELDS) - set(rows[0] if rows else P.OUT_FIELDS)
        if missing:
            raise SystemExit(f"{path}: not a disclosure CSV (missing {sorted(missing)})")
        years = {r["fiscal_year"] for r in rows}
        if len(years) != 1:
            raise SystemExit(f"{path}: expected one fiscal year, found {sorted(years)}")
        fy = int(years.pop())
    else:
        awards, rep = P.parse_year(path)
        if rep.skipped:
            raise SystemExit(f"{path}: {rep.skipped}")
        fy = rep.fiscal_year
        rows = []
        for a in awards:
            d = {k: str(v) for k, v in a._asdict().items()}
            d["amount"] = a.amount_text
            rows.append(d)
    for r in rows:
        r["amount"] = Decimal(r["amount"])
    # The file name alone cannot tell two snapshots of one year apart; the hash can, and it is
    # the key into source/.../MANIFEST.csv and MANIFEST-HISTORY.csv.
    return fy, rows, f"{os.path.basename(path)} (sha256 {P.sha256(path)[:12]})"


def _key(r, fields=COMPOSITE):
    return tuple(r[f] for f in fields)


def _pair_group(old, new):
    """Pair rows sharing one composite key. Returns (pairs, removed, added, ambiguous) where
    pairs are (old_row, new_row).

    Rule: rows whose status is unchanged pair first (no transition is reported where an
    unchanged pairing exists); leftovers then pair in sheet order; any surplus is removed/added.
    ambiguous is True when either side mixes statuses AND the two sides' status counts differ --
    then some other pairing is equally valid. Conservative: it can flag a group whose
    transitions are in fact forced, never the reverse."""
    old = sorted(old, key=lambda r: int(r["source_row"]))
    new = sorted(new, key=lambda r: int(r["source_row"]))
    pairs, lo, ln = [], [], list(new)
    for o in old:
        hit = next((n for n in ln if n["status_norm"] == o["status_norm"]), None)
        if hit is None:
            lo.append(o)
        else:
            ln.remove(hit)
            pairs.append((o, hit))
    k = min(len(lo), len(ln))
    pairs += list(zip(lo[:k], ln[:k]))
    removed, added = lo[k:], ln[k:]
    so = Counter(r["status_norm"] for r in old)
    sn = Counter(r["status_norm"] for r in new)
    ambiguous = bool(old and new) and so != sn and (len(so) > 1 or len(sn) > 1)
    return pairs, removed, added, ambiguous


def diff(old_rows, new_rows):
    """The comparison, as plain data."""
    # A MOCS ID keys a row only if it is non-blank and appears at most once in EACH snapshot.
    # Anything else falls back to the composite key on both sides, and is counted.
    co = Counter(r["mocs_id"] for r in old_rows)
    cn = Counter(r["mocs_id"] for r in new_rows)
    usable = {m for m in set(co) | set(cn) if m and co[m] <= 1 and cn[m] <= 1}
    pairs, removed, added = [], [], []
    ambiguous_groups = ambiguous_rows = 0
    fallback_old = [r for r in old_rows if r["mocs_id"] not in usable]
    fallback_new = [r for r in new_rows if r["mocs_id"] not in usable]

    # 1. MOCS ID, for IDs present in both snapshots.
    old_by_mocs = {r["mocs_id"]: r for r in old_rows if r["mocs_id"] in usable}
    new_by_mocs = {r["mocs_id"]: r for r in new_rows if r["mocs_id"] in usable}
    both = sorted(set(old_by_mocs) & set(new_by_mocs))
    pairs += [(old_by_mocs[m], new_by_mocs[m], "mocs_id") for m in both]
    paired = set(both)

    # 2. Composite multiset for everything else: the fallback rows AND any row whose MOCS ID is
    # on one side only -- a row the Council re-numbered is then paired, not reported as one
    # removal plus one addition.
    go, gn = defaultdict(list), defaultdict(list)
    for r in old_rows:
        if r["mocs_id"] not in paired:
            go[_key(r)].append(r)
    for r in new_rows:
        if r["mocs_id"] not in paired:
            gn[_key(r)].append(r)
    for k in sorted(set(go) | set(gn)):
        p, rem, add, amb = _pair_group(go.get(k, []), gn.get(k, []))
        pairs += [(o, n, "composite") for o, n in p]
        removed += rem
        added += add
        if amb:
            ambiguous_groups += 1
            ambiguous_rows += len(go.get(k, [])) + len(gn.get(k, []))

    transitions = Counter()
    amount_changes, field_changes, renumbered = [], Counter(), []
    composite_field_changes = Counter()
    for o, n, how in pairs:
        if o["status_norm"] != n["status_norm"]:
            transitions[(o["status_norm"], n["status_norm"])] += 1
        if how == "mocs_id":
            if o["amount"] != n["amount"]:
                amount_changes.append((o, n))
            for f in OTHER_FIELDS:
                if o[f] != n[f]:
                    field_changes[f] += 1
        else:
            # Composite pairs agree on every COMPOSITE field by construction; only the fields
            # outside the key can differ.
            for f in OTHER_FIELDS:
                if f not in COMPOSITE and o[f] != n[f]:
                    composite_field_changes[f] += 1
            if o["mocs_id"] != n["mocs_id"] and o["mocs_id"] and n["mocs_id"]:
                renumbered.append((o, n))

    # Candidate amount changes among composite-keyed leftovers: unique on both sides once the
    # amount is dropped from the key. A nomination, never counted.
    no_amt = tuple(f for f in COMPOSITE if f != "amount")
    rem_c, add_c = removed, added
    ro, an = defaultdict(list), defaultdict(list)
    for r in rem_c:
        ro[_key(r, no_amt)].append(r)
    for r in add_c:
        an[_key(r, no_amt)].append(r)
    candidates = [(ro[k][0], an[k][0]) for k in sorted(set(ro) & set(an))
                  if len(ro[k]) == 1 and len(an[k]) == 1]

    def totals(rows):
        t = {s: [0, Decimal(0)] for s in STATUSES}
        for r in rows:
            t[r["status_norm"]][0] += 1
            t[r["status_norm"]][1] += r["amount"]
        return t

    return dict(pairs=len(pairs), paired_by_mocs=sum(1 for p in pairs if p[2] == "mocs_id"),
                transitions=transitions, amount_changes=amount_changes,
                field_changes=field_changes, renumbered=renumbered,
                composite_field_changes=composite_field_changes, added=added, removed=removed,
                candidates=candidates, ambiguous_groups=ambiguous_groups,
                ambiguous_rows=ambiguous_rows, old_totals=totals(old_rows),
                new_totals=totals(new_rows),
                mocs_fallback=(len(fallback_old), len(fallback_new)))


def _usd(d):
    return P._usd(d)


def _prefix(mocs_id):
    """'FY26GP 00038' -> 'FY26GP'. Descriptive only: groups re-numberings in the report."""
    return mocs_id.split(" ", 1)[0] if " " in mocs_id else mocs_id


def _row(r):
    return (f"row {r['source_row']} | {r['mocs_id'] or '—'} | {r['ein']} | {r['legal_name']} | "
            f"{r['source']} | {r['status']} | {_usd(r['amount'])}")


def report(fy, old_label, new_label, d, limit=200):
    L = [f"# Disclosure snapshot diff — FY{fy}", "",
         f"- old: `{old_label}`", f"- new: `{new_label}`",
         f"- paired rows: {d['pairs']:,} ({d['paired_by_mocs']:,} by MOCS ID, the rest by the "
         f"composite key); added {len(d['added']):,}; removed {len(d['removed']):,}",
         f"- rows that could not use a MOCS ID (blank or repeated within a snapshot): "
         f"old {d['mocs_fallback'][0]:,}, new {d['mocs_fallback'][1]:,}",
         f"- ambiguous composite groups: {d['ambiguous_groups']:,} ({d['ambiguous_rows']:,} "
         f"rows) — the pairing inside these is a choice; their transitions are counts, not "
         f"row-to-row facts", "",
         "This compares two files. It is not a statement by the Council about what changed.", "",
         "## Totals by status", "",
         "| status | old rows | old $ | new rows | new $ | Δ rows | Δ $ |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for s in STATUSES:
        (on, oa), (nn, na) = d["old_totals"][s], d["new_totals"][s]
        L.append(f"| {s} | {on:,} | {_usd(oa)} | {nn:,} | {_usd(na)} | {nn - on:+,} | "
                 f"{'+' if na - oa >= 0 else '-'}{_usd(abs(na - oa))} |")
    on = sum(v[0] for v in d["old_totals"].values())
    nn = sum(v[0] for v in d["new_totals"].values())
    oa = sum(v[1] for v in d["old_totals"].values())
    na = sum(v[1] for v in d["new_totals"].values())
    L.append(f"| **all** | {on:,} | {_usd(oa)} | {nn:,} | {_usd(na)} | {nn - on:+,} | "
             f"{'+' if na - oa >= 0 else '-'}{_usd(abs(na - oa))} |")
    L += ["", "## Status transitions", ""]
    if d["transitions"]:
        L += ["| from | to | rows |", "|---|---|---:|"]
        for (a, b), n in sorted(d["transitions"].items()):
            L.append(f"| {a} | {b} | {n:,} |")
    else:
        L.append("None.")
    L += ["", f"## Amount changes (MOCS-ID pairs) — {len(d['amount_changes']):,}", ""]
    if d["amount_changes"]:
        L += ["| MOCS ID | EIN | legal name | old $ | new $ | Δ $ |", "|---|---|---|---:|---:|---:|"]
        for o, n in d["amount_changes"][:limit]:
            L.append(f"| {o['mocs_id']} | {n['ein']} | {n['legal_name']} | {_usd(o['amount'])} "
                     f"| {_usd(n['amount'])} | {_usd(n['amount'] - o['amount'])} |")
    if d["field_changes"]:
        L += ["", "Other fields changed on MOCS-ID pairs: "
              + ", ".join(f"`{f}` {n:,}" for f, n in sorted(d["field_changes"].items()))]
    L += ["", (f"## Re-numbered (paired by the composite key; MOCS ID differs) — "
               f"{len(d['renumbered']):,}"), "",
          ("The same designation under a different MOCS ID: every composite-key field "
           "(EIN, amount, agency, program, council member, source) agrees. Paired, not counted "
           "as a removal plus an addition."), ""]
    if d["renumbered"]:
        pfx = Counter((_prefix(o["mocs_id"]), _prefix(n["mocs_id"])) for o, n in d["renumbered"])
        L += ["| old prefix | new prefix | rows |", "|---|---|---:|"]
        for (a, b), k in sorted(pfx.items()):
            L.append(f"| `{a}` | `{b}` | {k:,} |")
        L += ["", "| old MOCS ID | new MOCS ID | EIN | legal name | status (old → new) | amount |",
              "|---|---|---|---|---|---:|"]
        for o, n in sorted(d["renumbered"], key=lambda p: p[0]["mocs_id"])[:limit]:
            L.append(f"| {o['mocs_id']} | {n['mocs_id']} | {n['ein']} | {n['legal_name']} | "
                     f"{o['status_norm']} → {n['status_norm']} | {_usd(n['amount'])} |")
        if len(d["renumbered"]) > limit:
            L.append(f"| … {len(d['renumbered']) - limit:,} more | | | | | |")
    if d["composite_field_changes"]:
        L += ["", "Fields outside the key changed on composite-key pairs: "
              + ", ".join(f"`{f}` {n:,}"
                          for f, n in sorted(d["composite_field_changes"].items()))]
    L += ["", f"## Candidate amount changes (composite-keyed rows) — {len(d['candidates']):,}", "",
          "One removed and one added row that agree on every key field except amount. A "
          "nomination to check in the workbooks; **not** counted as an amount change.", ""]
    for o, n in d["candidates"][:limit]:
        L.append(f"- {_row(o)} → {_usd(n['amount'])} (new row {n['source_row']})")
    for title, rows in (("Added", d["added"]), ("Removed", d["removed"])):
        L += ["", f"## {title} — {len(rows):,}", ""]
        if rows:
            L += ["| row | MOCS ID | EIN | legal name | source | status | amount |",
                  "|---|---|---|---|---|---|---:|"]
            for r in sorted(rows, key=lambda r: int(r["source_row"]))[:limit]:
                L.append("| " + _row(r) + " |")
            if len(rows) > limit:
                L.append(f"| … {len(rows) - limit:,} more | | | | | | |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", help="write the markdown report here instead of stdout")
    ap.add_argument("--limit", type=int, default=200, help="rows listed per section")
    a = ap.parse_args(argv)
    fy_o, old, lo = load(a.old)
    fy_n, new, ln = load(a.new)
    if fy_o != fy_n:
        raise SystemExit(f"refusing to compare FY{fy_o} with FY{fy_n}")
    text = report(fy_o, lo, ln, diff(old, new), a.limit)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
