#!/usr/bin/env python3
"""
Tests for diff_disclosure_snapshots.py. Every fixture is a COPY of a real committed disclosure
file (CSV or workbook) with known mutations applied here, so the expected counts are known
exactly. Nothing is downloaded.

Each docstring says what result would FAIL the test.

Run: pytest code/test_diff_disclosure_snapshots.py
"""
import csv
import os
import re
import sys
import zipfile
from decimal import Decimal

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import diff_disclosure_snapshots as D  # noqa: E402
import parse_expense_disclosure as P  # noqa: E402

CSV27 = os.path.join(P.out_dir(2027), "fy27_expense_awards.csv")
CSV20 = os.path.join(P.out_dir(2020), "fy20_expense_awards.csv")
XLSX27 = os.path.join(P.SRC_DIR, "funded_disclosure_FY2027.xlsx")


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=P.OUT_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return str(path)


def _run(old, new):
    fo, ro, _ = D.load(old)
    fn, rn, _ = D.load(new)
    assert fo == fn
    return D.diff(ro, rn)


def _flip(r, to):
    r["status_norm"] = to
    r["status"] = to.title()


# ---------------------------------------------------------------- FY2024+: MOCS ID

def test_workbook_and_its_csv_are_the_same_snapshot():
    """FAILS if loading a workbook and loading the CSV written from it disagree on anything."""
    d = _run(XLSX27, CSV27)
    assert d["pairs"] == d["paired_by_mocs"] == len(_read(CSV27))
    assert not (d["transitions"] or d["amount_changes"] or d["added"] or d["removed"]
                or d["field_changes"])


def test_mocs_keyed_changes_are_counted_exactly(tmp_path):
    """FY2027 copy with 3 pending->cleared, 1 cleared->pending, 2 amount changes, 2 removals
    and 1 addition. FAILS if any count is off, or if the status-total deltas are not exactly
    the dollars moved."""
    rows = _read(CSV27)
    new = [dict(r) for r in rows]
    pend = [r for r in new if r["status_norm"] == "pending"]
    clr = [r for r in new if r["status_norm"] == "cleared"]
    moved = Decimal(0)
    for r in pend[:3]:
        _flip(r, "cleared")
        moved += Decimal(r["amount"])
    _flip(clr[0], "pending")
    back = Decimal(clr[0]["amount"])
    clr[1]["amount"] = str(Decimal(clr[1]["amount"]) + 1000)
    clr[2]["amount"] = str(Decimal(clr[2]["amount"]) - 500)
    gone = [new.pop(new.index(pend[10])), new.pop(new.index(pend[11]))]
    extra = dict(clr[5], mocs_id="FY27 99999", source_row="10042")
    new.append(extra)
    d = _run(CSV27, _write(tmp_path / "new.csv", new))

    assert d["transitions"] == {("pending", "cleared"): 3, ("cleared", "pending"): 1}
    assert sorted(n["amount"] - o["amount"] for o, n in d["amount_changes"]) == [-500, 1000]
    assert {r["mocs_id"] for r in d["removed"]} == {g["mocs_id"] for g in gone}
    assert [r["mocs_id"] for r in d["added"]] == ["FY27 99999"]
    assert d["ambiguous_groups"] == 0 and d["candidates"] == []

    ot, nt = d["old_totals"], d["new_totals"]
    gone_amt = sum(Decimal(g["amount"]) for g in gone)
    assert nt["cleared"][1] - ot["cleared"][1] == moved - back + 500 + Decimal(extra["amount"])
    assert nt["pending"][1] - ot["pending"][1] == -moved + back - gone_amt
    assert nt["cleared"][0] - ot["cleared"][0] == 3 - 1 + 1
    assert nt["pending"][0] - ot["pending"][0] == -3 + 1 - 2


def test_a_repeated_mocs_id_falls_back_and_is_counted(tmp_path):
    """FAILS if a MOCS ID repeated inside a snapshot is still used as a key (it would pair one
    row arbitrarily and report the other as added)."""
    rows = _read(CSV27)
    new = [dict(r) for r in rows]
    new[1]["mocs_id"] = new[0]["mocs_id"]     # two rows now share one ID
    d = _run(CSV27, _write(tmp_path / "new.csv", new))
    # old: row 0 cannot key (its ID repeats in new); row 1 keeps a usable ID that new lacks.
    assert d["mocs_fallback"] == (1, 2)
    assert not (d["added"] or d["removed"] or d["transitions"])
    # row 1 was re-numbered: paired, and listed as such -- not as a field change
    assert [(o["source_row"], n["source_row"]) for o, n in d["renumbered"]] == \
        [(rows[1]["source_row"], rows[1]["source_row"])]
    assert d["field_changes"] == {}


def test_a_reprefixed_mocs_id_is_reported_as_renumbered_not_as_a_mocs_pair_change(tmp_path):
    """The 2026-10-12 shape: the Council moved 129 FY2026 IDs from 'FY26 NNNNN' to
    'FY26GP NNNNN'. FAILS if a re-numbered row is reported under 'Other fields changed on
    MOCS-ID pairs' (a pair keyed on the MOCS ID cannot have a different one -- the pre-fix
    report said `mocs_id` 129 there), if it is reported as a removal plus an addition, or if a
    change outside the composite key on such a pair goes unreported."""
    rows = _read(CSV27)
    new = [dict(r) for r in rows]
    num = new[0]["mocs_id"].split(" ", 1)[1]
    new[0]["mocs_id"] = f"FY27GP {num}"
    new[0]["purpose"] = new[0]["purpose"] + " (revised)"
    d = _run(CSV27, _write(tmp_path / "new.csv", new))
    assert d["pairs"] == len(rows) and d["paired_by_mocs"] == len(rows) - 1
    assert not (d["added"] or d["removed"] or d["transitions"] or d["amount_changes"])
    assert "mocs_id" not in d["field_changes"] and d["field_changes"] == {}
    assert [(o["mocs_id"], n["mocs_id"]) for o, n in d["renumbered"]] == \
        [(rows[0]["mocs_id"], f"FY27GP {num}")]
    assert d["composite_field_changes"] == {"purpose": 1}
    text = D.report(2027, "old", "new", d)
    assert "Other fields changed on MOCS-ID pairs" not in text
    assert "## Re-numbered (paired by the composite key; MOCS ID differs) — 1" in text
    assert "| `FY27` | `FY27GP` | 1 |" in text
    assert f"| {rows[0]['mocs_id']} | FY27GP {num} |" in text
    assert "Fields outside the key changed on composite-key pairs: `purpose` 1" in text


def test_workbook_amount_edit_is_found(tmp_path):
    """A copy of the real FY2027 workbook with one Amount cell rewritten in the sheet XML.
    FAILS if the workbook path through the diff misses it or reports anything else."""
    src = zipfile.ZipFile(XLSX27)
    xml = src.read("xl/worksheets/sheet1.xml").decode()
    m = re.search(r'(<c r="H2"[^>]*>)<v>(\d+)</v>', xml)
    assert m, "H2 is expected to be a numeric Amount cell"
    xml = xml.replace(m.group(0), f"{m.group(1)}<v>{int(m.group(2)) + 1}</v>", 1)
    out = tmp_path / "funded_disclosure_FY2027.xlsx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in src.infolist():
            data = xml.encode() if item.filename == "xl/worksheets/sheet1.xml" else \
                src.read(item.filename)
            z.writestr(item, data)
    d = _run(XLSX27, str(out))
    assert len(d["amount_changes"]) == 1
    o, n = d["amount_changes"][0]
    assert o["source_row"] == "2" and n["amount"] - o["amount"] == 1
    assert not (d["added"] or d["removed"] or d["transitions"])


# ---------------------------------------------------------------- before FY2024: composite

def _unique_rows(rows):
    """Rows whose composite key occurs once -- their pairing is never a choice."""
    from collections import Counter
    c = Counter(tuple(r[f] for f in D.COMPOSITE) for r in rows)
    return [r for r in rows if c[tuple(r[f] for f in D.COMPOSITE)] == 1]


def test_composite_status_flip_and_amount_change(tmp_path):
    """FY2020 copy (no MOCS ID). Two unique rows flip status; one unique row's amount changes.
    FAILS if the flips are not transitions, if the amount change is reported as an amount
    change (it cannot be known as one under a key that contains amount), or if it is not
    nominated as a candidate."""
    rows = _read(CSV20)
    new = [dict(r) for r in rows]
    uniq = [r for r in _unique_rows(new) if r["status_norm"] == "cleared"]
    _flip(uniq[0], "pending")
    _flip(uniq[1], "pending")
    uniq[2]["amount"] = str(Decimal(uniq[2]["amount"]) + 250)
    d = _run(CSV20, _write(tmp_path / "new.csv", new))
    assert d["paired_by_mocs"] == 0
    assert d["transitions"] == {("cleared", "pending"): 2}
    assert d["amount_changes"] == []
    assert len(d["removed"]) == len(d["added"]) == 1
    assert len(d["candidates"]) == 1
    o, n = d["candidates"][0]
    assert n["amount"] - o["amount"] == 250


def test_composite_duplicates_are_a_multiset(tmp_path):
    """Remove ONE row of a key printed several times with one status. FAILS if the whole key
    is reported removed (set semantics) or the removal is flagged ambiguous."""
    from collections import defaultdict
    rows = _read(CSV20)
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[f] for f in D.COMPOSITE)].append(r)
    k, g = next((k, g) for k, g in groups.items()
                if len(g) >= 2 and len({r["status_norm"] for r in g}) == 1)
    new = [r for r in rows if r is not g[0]]
    d = _run(CSV20, _write(tmp_path / "new.csv", new))
    assert len(d["removed"]) == 1 and not d["added"]
    assert d["ambiguous_groups"] == 0


def test_mixed_status_duplicate_group_is_flagged_ambiguous(tmp_path):
    """A key with two rows, one Cleared one Pending, whose new snapshot has one Cleared row:
    either old row could be the survivor. FAILS if this is not counted as ambiguous."""
    rows = _read(CSV20)
    base = dict(_unique_rows(rows)[0])
    a, b = dict(base, source_row="90001"), dict(base, source_row="90002")
    _flip(a, "cleared")
    _flip(b, "pending")
    c = dict(base, source_row="90003")
    _flip(c, "cleared")
    rest = [r for r in rows if r["source_row"] != base["source_row"]]
    d = _run(_write(tmp_path / "old.csv", rest + [a, b]), _write(tmp_path / "new.csv",
                                                                rest + [c]))
    assert d["ambiguous_groups"] == 1 and d["ambiguous_rows"] == 3
    assert d["transitions"] == {} and len(d["removed"]) == 1


def test_different_years_are_refused(tmp_path):
    """FAILS if two different fiscal years are compared."""
    with pytest.raises(SystemExit, match="refusing"):
        D.main([CSV20, CSV27, "--out", str(tmp_path / "x.md")])


def test_report_names_each_snapshot_by_hash(tmp_path):
    """Two snapshots of one year share a file name. FAILS if the report header cannot tell
    them apart (it must carry each file's sha256 prefix, the key into the manifests)."""
    rows = _read(CSV27)
    new = [dict(r) for r in rows]
    new[0]["amount"] = str(Decimal(new[0]["amount"]) + 1)
    other = _write(tmp_path / "fy27_expense_awards.csv", new)
    _, _, lo = D.load(CSV27)
    _, _, ln = D.load(other)
    assert lo == f"fy27_expense_awards.csv (sha256 {P.sha256(CSV27)[:12]})"
    assert ln != lo and P.sha256(other)[:12] in ln


def test_report_labels_itself_as_a_file_comparison(tmp_path):
    """FAILS if the report presents the diff as a Council statement, or drops the per-status
    totals table."""
    out = tmp_path / "r.md"
    D.main([CSV27, CSV27, "--out", str(out)])
    text = out.read_text(encoding="utf-8")
    assert "not a statement by the Council" in text
    assert "| cleared |" in text and "| pending |" in text and "| other |" in text
