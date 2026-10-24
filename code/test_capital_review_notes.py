"""Tests for the capital review notes in data/capital/README.md and RECONCILIATION.md (#199,
#208). Every figure is recomputed from the committed data, so a note that goes missing or stale
fails here. Each test names the outcome that would make it fail."""
import collections
import csv
import gzip
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_capital_council as C     # noqa: E402

ROOT = os.path.dirname(HERE)


def text(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return " ".join(f.read().split())


def read_csv(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def part1(fy):
    yy = str(fy)[2:]
    return [r for r in read_csv(f"data/fy{yy}/pdf/capital_sd/fy{yy}_capital_sd_projects.csv")
            if r["part"] == "I"]


def pdf_vs_omb(fy):
    """{line: (pdf, omb)} where the PDF's first-year total and OMB's adopted one differ."""
    pdf = collections.Counter()
    for r in part1(fy):
        if r[f"fy{fy}"]:
            pdf[C.norm_line(r["budget_line"])] += int(r[f"fy{fy}"])
    out = {}
    for v in read_csv("data/capital/council_vs_omb_by_budget_line.csv"):
        if int(v["report_year"]) == fy:
            omb = int(v["omb_y1"] or 0)
            if omb != pdf.get(v["budget_line_norm"], 0):
                out[v["budget_line_norm"]] = (pdf.get(v["budget_line_norm"], 0), omb)
    return out


def test_reconciliation_states_the_pdf_gaps_to_omb():
    """FAILS if RECONCILIATION §3 lacks the FY2020 and FY2023 PDF-vs-OMB gaps (#208), or a
    figure there no longer matches the promoted PDF rows and OMB's adopted release."""
    rec = text("data/capital/RECONCILIATION.md")
    d20 = pdf_vs_omb(2020)
    gap = sum(o - p for p, o in d20.values())
    higher = [k for k, (p, o) in d20.items() if p]
    none = [k for k, (p, o) in d20.items() if not p]
    assert all(o > p for p, o in d20.values())                  # "The PDF has no amount OMB lacks"
    assert (f"FY2020: OMB is ${gap:,} higher than the PDF on {len(d20)} budget lines: "
            f"{len(higher)} where OMB is higher") in rec
    assert f"and {len(none)} with no PDF row" in rec
    for k in d20:
        assert f"`{k}`" in rec.split("FY2020: OMB is")[1].split("FY2023")[0], k
    p, o = d20["E D001"]
    assert f"`E D001` ${o - p:,} after" in rec
    d23 = pdf_vs_omb(2023)
    assert list(d23) == ["E D001"]
    p, o = d23["E D001"]
    assert f"FY2023: `E D001` is ${o - p:,} lower in the PDF than in OMB" in rec


def test_reconciliation_pdf_additions_are_the_broken_t474_records():
    """FAILS if the IDs RECONCILIATION names as the PDF's additions are not t474's broken records
    on `E D001` with the amounts it gives."""
    rec = text("data/capital/RECONCILIATION.md")
    for fy, ids, total in ((2020, ("E CN817", "E CN832"), 470_000), (2023, ("E CN136",), 150_000)):
        rows = [r for r in part1(fy) if " ".join(r["sub_id"].split()) in ids]
        assert len(rows) == len(ids) and {C.norm_line(r["budget_line"]) for r in rows} == {"E D001"}
        assert sum(int(r[f"fy{fy}"]) for r in rows) == total
        for i in ids:
            assert f"ID `{i}`, line `E D001`" in rec, i     # a broken record, listed in §2
        assert f"${total:,}" in rec


def reused(rows, id_key, line_key):
    by = collections.defaultdict(list)
    for r in rows:
        by[" ".join(r[id_key].split())].append(r[line_key])
    return {i: ls for i, ls in by.items() if len(ls) > 1}


@pytest.mark.parametrize("fy,ids", [
    (2019, ["LB CN001", "LB CN002", "LB CN003", "LB CN004", "LB CN005", "LB CN006"]),
    (2020, ["P CN967", "TF CN90"]),
    (2022, ["E CN884", "PV NC101"]),
    (2025, ["E CN810", "ED NC128", "HN CN018", "HN CN020", "HN CN021", "HO CN019"]),
])
def test_readme_lists_every_id_the_pdf_prints_twice(fy, ids):
    """FAILS if the README's list of project IDs printed twice (#208) is not exactly what the
    promoted PDF and data/capital hold for that year."""
    assert sorted(reused(part1(fy), "sub_id", "budget_line")) == sorted(ids)
    awards = [r for r in read_csv("data/capital/council_capital_awards.csv")
              if int(r["report_year"]) == fy and r["amount_fy"] == r["report_year"]]
    assert sorted(reused(awards, "project_id", "budget_line")) == sorted(ids)      # t474 agrees
    readme = text("data/capital/README.md")
    note = readme.split("`project_id` is not a key")[1].split("- **")[0]
    assert f"FY{fy} {len(ids)}" in note
    for i in [f"`{ids[0]}`–`{ids[-1]}`"] if fy == 2019 else [f"`{i}`" for i in ids]:
        assert i in note, i


def test_readme_names_the_workbook_repeats_and_shared_numbers():
    """FAILS if the README's workbook repeats (FY2017, FY2026) or FY2023's shared ID numbers do
    not match data/capital and the FY2023 PDF."""
    awards = read_csv("data/capital/council_capital_awards.csv")
    first = collections.defaultdict(list)
    for r in awards:
        if r["amount_fy"] == r["report_year"]:
            first[int(r["report_year"])].append(r)
    note = text("data/capital/README.md").split("`project_id` is not a key")[1].split("- **")[0]
    r17 = reused(first[2017], "project_id", "budget_line")
    assert f"FY2017 {len(r17)} IDs" in note
    assert f"{sum(i.startswith('E CN7') for i in r17)} of them" in note
    assert list(reused(first[2026], "project_id", "budget_line")) == ["HN CN1451"]
    shared = collections.defaultdict(set)
    for r in part1(2023):
        i = " ".join(r["sub_id"].split())
        shared[(i.split(" ")[-1], C.norm_line(r["budget_line"]))].add(i)
    pairs = {k: v for k, v in shared.items() if len(v) > 1}
    assert pairs == {("NC040", "HD D020"): {"HD NC040", "HR NC040"},
                     ("CN001", "HA D001"): {"HA CN001", "P CN001"}}
    assert "`HD NC040` / `HR NC040` on `HD D020`, `HA CN001` / `P CN001` on `HA D001`" in note


def t474():
    path = os.path.join(ROOT, "source", "open-data-t474-a92g", "t474-a92g.csv.gz")
    with gzip.open(path) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))


def test_readme_garbled_accents_are_the_source_and_decode_as_stated():
    """FAILS if the README lacks the garbled-accent note (#199), or its examples are not in t474
    as published, or do not decode with the character sets it names."""
    note = text("data/capital/README.md").split("Accented names are garbled in t474")[1].split("- **")[0]
    sponsors = collections.defaultdict(set)
    for t in t474():
        sponsors[t["reported"]].update(t["sponsor"].replace(",", " ").split())
    assert "OssΘ" in sponsors["2025"] and "Cabßn" in sponsors["2025"]
    for y in ("2023", "2024", "2026"):
        assert "Oss├⌐" in sponsors[y] and "Avil├⌐s" in sponsors[y], y
    assert "OssΘ".encode("cp437").decode("cp1252") == "Ossé"
    assert "Oss├⌐".encode("cp437").decode("utf-8") == "Ossé"
    assert "Cab├ín".encode("cp437").decode("utf-8") == "Cabán"
    assert "CAF‚".encode("cp1252").decode("cp437") == "CAFé"
    for s in ("`OssΘ`", "`Oss├⌐`", "`Avil├⌐s`", "`Cab├ín`", "Windows-1252 read as code page 437",
              "UTF-8 read as code page 437", '.decode("cp1252")'):
        assert s in note, s
    # the counts of accented sponsor rows the note gives
    n = collections.Counter(r["report_year"] for r in read_csv("data/capital/council_capital_awards.csv")
                            if r["source_kind"] == "open_data_t474" and any(ord(c) > 127 for c in r["sponsor"]))
    assert min(n) == "2023"
    assert f"FY2023 {n['2023']}, FY2024 {n['2024']}, FY2025 {n['2025']}" in note
