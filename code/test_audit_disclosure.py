#!/usr/bin/env python3
"""
Tests for audit_disclosure.py -- the adversarial audit of the expense-disclosure dataset.

The audit is only worth anything if each of its checks can FAIL. So every detector is tested
twice: on a constructed defect it must catch, and on a near-miss it must leave alone. The
independent reader is tested on synthetic workbooks carrying exactly the spreadsheet hazards the
audit asks about (an interior empty cell, a date-typed cell, an error cell, a hidden row, a
merged range, a second sheet). The corpus-level checks are tested by corrupting a COPY of the
committed data and confirming the corruption is reported.

Each docstring says what result would FAIL the test.

Needs openpyxl and xlrd (code/requirements.txt). Run: pytest code/test_audit_disclosure.py
"""
import csv
import datetime
import os
import shutil
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

openpyxl = pytest.importorskip("openpyxl")
pytest.importorskip("xlrd")

import audit_disclosure as A  # noqa: E402

HDR = ["MOCS ID#", "Fiscal Year", "Source", "Council Member", "Legal Name", "Tax ID", "Status",
       "Amount", "Agency", "Program Name", "Grantee Street Address", "Grantee Street Address (2)",
       "City", "State", "Postal Code", "Purpose of Funds", "Fiscal Conduit", "Fiscal Conduit EIN"]


def _row(name, ein, status, amount, **kw):
    r = dict(zip(HDR, [None] * len(HDR)))
    r.update({"MOCS ID#": kw.get("mocs", "FY99 00001"), "Fiscal Year": 2099, "Source": "Local",
              "Council Member": kw.get("member", "Smith"), "Legal Name": name, "Tax ID": ein,
              "Status": status, "Amount": amount, "Agency": "DYCD", "City": "New York",
              "State": "NY", "Postal Code": kw.get("zip", "10001")})
    return [r[h] for h in HDR]


def _wb(path, rows, extra_sheet=False, hide_row=None, merge=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FY99 (01-01-99)"
    for r in rows:
        ws.append(r)
    if hide_row:
        ws.row_dimensions[hide_row].hidden = True
    if merge:
        ws.merge_cells(merge)
    if extra_sheet:
        wb.create_sheet("Sheet2").append(["x"])
    wb.save(path)
    return str(path)


# ---------------------------------------------------------------- pure detectors

@pytest.mark.parametrize("hit,miss", [
    ("Acme Services, Inc. Brooklyn Youth Partners Corp.", "Education and Assistance Corporation (EAC), Inc."),
    ("Harlem Arts Alliance Inc. Bronx Music Heritage Center, Inc.", "Local Development Corporation of Crown Heights, Inc."),
    ("Harlem Arts Alliance Inc. Bronx Music Heritage Center, Inc.", "Made in Brownsville, Inc d.b.a Youth Design Center, Inc."),
])
def test_merged_name(hit, miss):
    """FAILS if two organizations glued into one cell are not caught (org_merged, #52), or if
    one long legal name with two suffixes is."""
    assert A.merged_name(hit)
    assert not A.merged_name(miss)


@pytest.mark.parametrize("hit,miss", [
    ("Consortium for Worker Education (CWE", "Consortium for Worker Education (CWE)"),
    ("Friends of the Park and", "Friends of the Park"),
    ("Center for Arts,", "Lower East Side Tenement Museum, The"),
    ('"Quoted Name', '"Quoted" Name'),
])
def test_looks_truncated(hit, miss):
    """FAILS if a cut-off name (unbalanced bracket/quote, trailing connective) is missed, or if
    the Council's ', The' convention is called a cut."""
    assert A.looks_truncated(hit)
    assert not A.looks_truncated(miss)


@pytest.mark.parametrize("hit,miss", [
    (".00 Funds will support seniors", "$500 to every High School PTA."),
    ("107167", "107th Street Block Association"),
    ("12,500.00", "To provide 12,500 meals"),
])
def test_amountish(hit, miss):
    """FAILS if a cents tail or a bare amount in a text column is missed (fy18_aging_shift), or
    if prose that merely mentions money is flagged."""
    assert A.AMOUNTISH.search(hit)
    assert not A.AMOUNTISH.search(miss)


def test_prose_and_placeholder_and_canon():
    """FAILS if purpose prose in a name is missed or a real name is flagged; if a placeholder
    EIN is missed or a real one flagged; or if canon_name stops folding suffixes/articles."""
    assert A.PROSE.search("Funds will be used to provide meals")
    assert not A.PROSE.search("Fund for the City of New York, Inc.")
    assert A.is_placeholder_ein("000000000") and A.is_placeholder_ein("123456789")
    assert not A.is_placeholder_ein("136400434")
    assert A.canon_name("The Children's Aid Society, Inc.") == A.canon_name("Childrens Aid Society")


def test_canon_header_maps_every_layout_and_refuses_the_unknown():
    """FAILS if any of the Council's header spellings across FY2013-FY2027 maps wrongly (the
    FY2016 'Legal Name of Organization Requesting Funding' exact-match miss), if the conduit EIN
    is taken for the grantee EIN, or if an unknown header is guessed rather than refused."""
    cases = {
        "Legal Name of Organization Requesting Funding": "legal_name", "Legal Name": "legal_name",
        "EIN": "ein", "Tax ID": "ein", "FC EIN": "fiscal_conduit_ein",
        "Fiscal Conduit EIN": "fiscal_conduit_ein", "Fiscal Conduit Name": "fiscal_conduit",
        "Amount ($": "amount", "Council Members": "council_member", "MOCS ID#": "mocs_id",
        "Address 2 (optional": "address2", "Grantee Street Address": "address1",
        "Zip Code": "postal_code", "Purpose to be listed in Schedule C": "purpose",
        "CM Purpose of Funds": "purpose", "Fiscal Year": "fiscal_year_col", "Source": "source",
    }
    for h, f in cases.items():
        assert A.canon_header(h) == f, h
    assert A.canon_header("Adoption Total") is None
    assert A.canon_header("") is None


# ---------------------------------------------------------------- the independent reader

def test_reader_positions_cells_by_reference_and_sees_spreadsheet_hazards(tmp_path):
    """A workbook with an interior EMPTY cell (Program Name), a date-typed cell, an error cell,
    a hidden row, a merged range and a second sheet. FAILS if the reader shifts a value left
    across the gap (the positional-shift defect), or misses any of the five hazards."""
    rows = [HDR, _row("Acme Inc.", "136400434", "Cleared", 5000),
            _row("Beta Org", "010596502", "Pending", 2500.5, mocs="FY99 00002")]
    p = _wb(tmp_path / "funded_disclosure_FY2099.xlsx", rows, extra_sheet=True, hide_row=3,
            merge="P2:Q2")
    wb = openpyxl.load_workbook(p)
    ws = wb.active
    ws["L2"] = datetime.datetime(2015, 2, 2)
    ws["O3"] = "#N/A"
    ws["O3"].data_type = "e"
    wb.save(p)
    s = A.Sheet(p)
    assert s.get(2, "legal_name").value == "Acme Inc."
    assert s.get(2, "program_name") is None             # the gap stays a gap
    assert A.text_of(s.get(2, "agency")) == "DYCD"      # ...and nothing shifted into it
    assert s.get(2, "address2").kind == "d"
    assert A.excel_serial(s.get(2, "address2").value) == 42037
    assert s.get(3, "postal_code").kind == "e"
    assert s.hidden_rows == [3]
    assert s.merged == ["P2:Q2"]
    assert [x[0] for x in s.sheets] == ["FY99 (01-01-99)", "Sheet2"]
    assert A.is_award_row(s, 2) and A.is_award_row(s, 3)


def _ctx_for(tmp_path, rows, csv_rows, manifest_retrieved="2099-01-01"):
    """A one-workbook context: src dir, data dir with a CSV, a manifest."""
    src = tmp_path / "src"
    src.mkdir(parents=True)
    _wb(src / "funded_disclosure_FY2099.xlsx", rows)
    data = tmp_path / "data"
    d = data / "fy99" / "expense_disclosure"
    d.mkdir(parents=True)
    with open(d / "fy99_expense_awards.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=A.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(csv_rows)
    (d / "fy99_expense_reconciliation.txt").write_text("Stripped rows (0):\n  none\n\n")
    man = tmp_path / "MANIFEST.csv"
    man.write_text("file,retrieved,award_rows,total_amount\n"
                   f"funded_disclosure_FY2099.xlsx,{manifest_retrieved},{len(csv_rows)},"
                   f"{sum(float(r['amount']) for r in csv_rows):g}\n")
    return A.build_context(str(src), str(data), str(man))


def _csv_row(rn, name, ein, status, amount, **kw):
    r = {f: "" for f in A.FIELDS}
    r.update(fiscal_year="2099", mocs_id=kw.get("mocs", "FY99 00001"), source="Local",
             council_member=kw.get("member", "Smith"), legal_name=name, ein=ein, status=status,
             status_norm=status.lower(), amount=str(amount), agency="DYCD", city="New York",
             state="NY", postal_code=kw.get("zip", "10001"),
             source_file="funded_disclosure_FY2099.xlsx", source_row=str(rn))
    return r


def test_cell_by_cell_check_catches_a_shifted_or_edited_cell(tmp_path):
    """FAILS if A6 passes a CSV whose legal_name differs from the workbook cell, or flags a CSV
    that matches it exactly."""
    wb_rows = [HDR, _row("Acme Inc.", "136400434", "Cleared", 5000)]
    good = [_csv_row(2, "Acme Inc.", "136400434", "Cleared", 5000)]
    assert A.q_cell_by_cell(_ctx_for(tmp_path / "a", wb_rows, good))["status"] == "pass"
    bad = [_csv_row(2, "Acme", "136400434", "Cleared", 5000)]
    r = A.q_cell_by_cell(_ctx_for(tmp_path / "b", wb_rows, bad))
    assert r["status"] == "finding" and r["count"] == 1 and "legal_name" in r["examples"][0]


def test_row_accounting_and_totals_catch_a_dropped_row(tmp_path):
    """FAILS if a workbook award row missing from the CSV passes A5 (row accounting) or B1 (the
    independent sum per year x status)."""
    wb_rows = [HDR, _row("Acme Inc.", "136400434", "Cleared", 5000),
               _row("Beta Org", "010596502", "Pending", 2500)]
    full = [_csv_row(2, "Acme Inc.", "136400434", "Cleared", 5000),
            _csv_row(3, "Beta Org", "010596502", "Pending", 2500)]
    ok = _ctx_for(tmp_path / "a", wb_rows, full)
    assert A.q_row_accounting(ok)["status"] == "pass" and A.q_totals(ok)["status"] == "pass"
    short = _ctx_for(tmp_path / "b", wb_rows, full[:1])
    assert A.q_row_accounting(short)["status"] == "finding"
    assert A.q_totals(short)["status"] == "finding"


def test_numeric_ein_and_zip_leading_zero_loss_is_reported(tmp_path):
    """FAILS if an EIN or ZIP stored as a NUMBER with too few digits (Excel ate the leading
    zero) is not reported, or if a 5-digit numeric ZIP is."""
    wb_rows = [HDR, _row("Acme Inc.", 10596502, "Cleared", 5000, zip=7083),
               _row("Beta Org", "136400434", "Cleared", 100, zip=10001)]
    ctx = _ctx_for(tmp_path, wb_rows, [_csv_row(2, "Acme Inc.", "010596502", "Cleared", 5000, zip="7083"),
                                       _csv_row(3, "Beta Org", "136400434", "Cleared", 100)])
    r = A.q_numeric_ids(ctx)
    assert r["count"] == 2
    assert any("ein stored as number 10596502" in e for e in r["examples"])
    assert any("postal_code stored as number 7083" in e for e in r["examples"])


def test_duplicates_count_identical_rows_only(tmp_path):
    """FAILS if two rows identical in every field but source_row are not counted (F1), or if
    rows that differ in their MOCS ID are counted as that kind of duplicate."""
    rows = [_csv_row(2, "Acme", "136400434", "Cleared", 5000),
            _csv_row(3, "Acme", "136400434", "Cleared", 5000),
            _csv_row(4, "Acme", "136400434", "Cleared", 5000, mocs="FY99 00009")]
    ctx = {"csv": rows, "csv_by_fy": {2099: rows}}
    r = A.q_exact_dups(ctx)
    assert r["count"] == 1 and "funded_disclosure_FY2099.xlsx:2 & funded_disclosure_FY2099.xlsx:3" in r["examples"][0]


def test_address_hyphen_question_catches_a_lost_or_doubled_hyphen(tmp_path):
    """Issue #68, audit question D13. FAILS if a CSV address that dropped the soft hyphen of
    '12<SHY>11 40th Avenue' (published '1211 40th Avenue') passes, if one that doubled
    '12-<SHY>11' into '12--11' passes, or if the correct '12-11 40th Avenue' is flagged."""
    ai = HDR.index("Grantee Street Address")

    def wb_row(addr):
        r = _row("Acme Inc.", "136400434", "Cleared", 5000)
        r[ai] = addr
        return r

    wb_rows = [HDR, wb_row("12\xad11 40th Avenue"), wb_row("12-\xad11 40th Avenue")]

    def run(a2, a3, sub):
        rows = [_csv_row(2, "Acme Inc.", "136400434", "Cleared", 5000),
                _csv_row(3, "Acme Inc.", "136400434", "Cleared", 5000)]
        rows[0]["address1"], rows[1]["address1"] = a2, a3
        return A.q_address_hyphens(_ctx_for(tmp_path / sub, wb_rows, rows))

    assert run("12-11 40th Avenue", "12-11 40th Avenue", "ok")["status"] == "pass"
    lost = run("1211 40th Avenue", "12-11 40th Avenue", "lost")
    assert lost["count"] == 1 and ":2 address1" in lost["examples"][0]
    doubled = run("12-11 40th Avenue", "12--11 40th Avenue", "doubled")
    assert doubled["count"] == 1 and ":3 address1" in doubled["examples"][0]


def test_duplicate_flag_question_checks_the_csv_flag_issue_69():
    """Issue #69, audit question F3. FAILS if a correctly flagged pair (both rows naming row 2)
    is reported, or if a copy left unflagged, a unique row flagged, or a group named by a row
    other than its first passes."""
    def rows(flags):
        out = [_csv_row(2, "Acme", "136400434", "Cleared", 5000),
               _csv_row(3, "Acme", "136400434", "Cleared", 5000),
               _csv_row(4, "Beta", "136400434", "Cleared", 10)]
        for r, f in zip(out, flags):
            r["duplicate_group"] = f
        return {"csv": out}
    assert A.q_dup_flag(rows(["2", "2", ""]))["status"] == "pass"
    for flags in (["2", "", ""], ["2", "2", "4"], ["3", "3", ""]):
        r = A.q_dup_flag(rows(flags))
        assert r["status"] == "finding" and r["count"] >= 1, flags


def test_zip_question_catches_a_blind_pad_issue_70():
    """Issue #70, audit question G7, against the committed Census table. FAILS if a correctly
    padded Brookline ZIP ('2446', MA -> 02446) is reported, or if padding the Bronx '7083' to
    New Jersey's 07083, calling '#N/A' valid, or calling a non-ZCTA ZIP valid passes."""
    def row(raw, state, z, st):
        r = _csv_row(2, "Acme", "136400434", "Cleared", 5000, zip=raw)
        r.update(state=state, zip=z, zip_status=st)
        return r
    good = [row("2446", "MA", "02446", "padded"), row("10008", "NY", "10008", "not_a_zcta"),
            row("#N/A", "", "", "invalid"), row("10001", "NY", "10001", "valid")]
    assert A.q_zip({"csv": good})["status"] == "pass"
    for bad in (row("7083", "NY", "07083", "padded"), row("#N/A", "", "", "valid"),
                row("10008", "NY", "10008", "valid")):
        assert A.q_zip({"csv": [bad]})["count"] == 1, bad


def test_zip_trim_question_issue_70():
    """Audit question G11 and G7's trimmed rule, against the committed Census table. FAILS if a
    correct trim ('11203-' in NY -> 11203) is reported, or if trimming into another state's ZCTA,
    trimming a non-hyphenated value ('11231=1020'), trimming with no state, or leaving a
    trimmable ragged ZIP+4 invalid passes."""
    def row(raw, state, z, st):
        r = _csv_row(2, "Acme", "136400434", "Cleared", 5000, zip=raw)
        r.update(state=state, zip=z, zip_status=st)
        return r
    good = [row("11203-", "NY", "11203", "trimmed"), row("11217-11217", "New YorkNY", "11217", "trimmed"),
            row("11231=1020", "NY", "", "invalid"), row("11203-", "NC", "", "invalid"),
            row("10001-1234", "NY", "10001", "valid")]
    assert A.q_zip_trim({"csv": good})["status"] == "pass"
    assert A.q_zip({"csv": good})["status"] == "pass"
    for bad in (row("11203-", "NC", "11203", "trimmed"), row("11231=1020", "NY", "11231", "trimmed"),
                row("11203-", "", "11203", "trimmed"), row("11203-", "NY", "", "invalid")):
        assert A.q_zip_trim({"csv": [bad]})["count"] == 1, bad
    for bad in good[:1]:
        wrong = dict(bad, zip="11204")
        assert A.q_zip({"csv": [wrong]})["count"] == 1


def test_member_id_questions_issue_72():
    """Issue #72, audit questions G8-G10, against the committed roster extract. FAILS if Levin
    (7567) in FY2016 is reported, or if Levin carrying Levine's ID (7634) passes G10, if one ID
    on two names in a year passes G9, or if a row typed member whose person did not vote that
    year (Wong, 7900, first voted FY2026) passes G8."""
    def row(rn, member, pid, typ="member", fy="2016"):
        r = _csv_row(rn, "Acme", "136400434", "Cleared", 5000, member=member)
        r.update(fiscal_year=fy, council_member_id=pid, council_member_type=typ)
        return r
    ok = {"csv": [row(2, "Levin", "7567"), row(3, "Levine", "7634"),
                  row(4, "Wong", "7900", "member_outside_fy", "2025")]}
    assert A.q_member_substring_ids(ok)["status"] == "pass"
    assert A.q_member_id_shared(ok)["status"] == "pass"
    g8 = A.q_member_in_office(ok)
    assert g8["count"] == 1 and "member_outside_fy" in g8["examples"][0]
    assert "0 rows typed member fail" in g8["note"]
    bad = {"csv": [row(2, "Levin", "7634"), row(3, "Levine", "7634")]}
    assert A.q_member_substring_ids(bad)["count"] == 1
    assert A.q_member_id_shared(bad)["count"] == 1
    wrong = {"csv": [row(2, "Wong", "7900", "member", "2025")]}
    assert "1 rows typed member fail" in A.q_member_in_office(wrong)["note"]


def test_member_bleed_requires_corroboration():
    """FAILS if 'Levin Brooklyn Youth Fund' is not flagged when the same EIN is published as
    'Brooklyn Youth Fund' elsewhere, or if it is flagged without that corroboration."""
    a = _csv_row(2, "Levin Brooklyn Youth Fund", "111111112", "Cleared", 1, member="Levin")
    b = _csv_row(3, "Brooklyn Youth Fund", "111111112", "Cleared", 1, member="Levin")
    assert A.q_member_bleed({"csv": [a, b]})["count"] == 1
    assert A.q_member_bleed({"csv": [a]})["count"] == 0


def test_member_substring_ambiguity():
    """FAILS if 'Levin' is not reported as also matching 'Levine' in the same year (#51)."""
    rows = [_csv_row(2, "X", "1", "Cleared", 1, member="Levin"),
            _csv_row(3, "Y", "2", "Cleared", 1, member="Levine"),
            _csv_row(4, "Z", "3", "Cleared", 1, member="Chin")]
    r = A.q_member_substring({"csv": rows})
    assert r["count"] == 1 and "'Levin' also matches ['Levine']" in r["examples"][0]


def test_report_provenance_catches_a_stale_retrieval_date(tmp_path):
    """FAILS if a report naming a retrieval date MANIFEST.csv does not hold passes H1 (the
    coverage report said 2026-07-15 after the 2026-10-12 re-pull)."""
    root = tmp_path
    (root / "data").mkdir()
    (root / "data" / "DISCLOSURE-COVERAGE.md").write_text("built from workbooks, retrieved 2026-07-15) and")
    man = [{"file": "funded_disclosure_FY2027.xlsx", "retrieved": "2026-10-12"}]
    r = A.q_report_provenance({"data_dir": str(root / "data"), "manifest": man})
    assert r["status"] == "finding"
    (root / "data" / "DISCLOSURE-COVERAGE.md").write_text("retrieved 2026-10-12, per MANIFEST")
    assert A.q_report_provenance({"data_dir": str(root / "data"), "manifest": man})["status"] == "pass"


def test_mocs_claim_check_catches_a_stable_key_claim(tmp_path):
    """FAILS if a doc calling the MOCS ID 'a stable per-award key' passes H2, or if the
    corrected wording ('Not stable ... unverified') is flagged."""
    (tmp_path / "data").mkdir()
    (tmp_path / "README.md").write_text("- MOCS ID#: a stable per-award key and the join to registered contracts.\n")
    ctx = {"data_dir": str(tmp_path / "data")}
    assert A.q_mocs_claims(ctx)["count"] == 1
    (tmp_path / "README.md").write_text("- MOCS ID#: not stable across snapshots; its join to registered contracts is unverified.\n")
    assert A.q_mocs_claims(ctx)["count"] == 0


# ---------------------------------------------------------------- the committed report

@pytest.fixture(scope="module")
def real():
    ctx = A.build_context()
    return ctx, A.run(ctx)


def test_committed_report_is_current(real):
    """FAILS if data/DISCLOSURE-AUDIT.md is not what the audit produces from the committed files
    today (a re-pull, a parser change or a new question without --write)."""
    ctx, results = real
    with open(A.REPORT, encoding="utf-8") as fh:
        committed = fh.read()
    assert A.report_text(results, ctx) == committed, "stale: run python3 code/audit_disclosure.py --write"


def test_corpus_pins(real):
    """Pins the answers the report gives, so a regression in the data or the reader shows up as
    a changed number, not as a silently different report. FAILS if the dataset stops matching
    the workbooks cell for cell (A6), loses a row (A5/B1), regains an invisible character (D8
    soft hyphens), or if the snapshot diff keys on the member again (H3)."""
    _, results = real
    by = {r["id"]: r for r in results}
    for qid in ("A1", "A2", "A3", "A4", "A5", "A6", "A10", "A13", "A14", "A15", "B1", "B2",
                "B4", "C3", "C6", "D1", "D2", "D6", "D7", "D9", "D13", "E1", "G1", "H1", "H2", "H3"):
        assert by[qid]["status"] == "pass", (qid, by[qid]["examples"][:3])
    assert "2,372,452 cells compared" in by["A6"]["note"]
    assert by["F1"]["count"] == 321 and "341 surplus rows, $8,549,772" in by["F1"]["note"]
    assert by["E2"]["count"] == 64
    assert "7 are binary float residue" in by["E2"]["note"] and "1 of those is still a live formula" in by["E2"]["note"]
    assert by["C1"]["count"] == 6
    assert by["A9"]["count"] == 37
    assert not any("\\xad" in e for e in by["D8"]["examples"])
    # Issue #68: 186 workbook address cells hold a soft hyphen; none loses or doubles a hyphen.
    assert by["D13"]["status"] == "pass" and "186 workbook address cells" in by["D13"]["note"]
    # Issue #69: the CSV flag marks exactly F1's groups.
    assert by["F3"]["status"] == "pass" and "FY2020 75 groups / 154 rows / 79 surplus" in by["F3"]["note"]
    # Issue #70: every ZIP status agrees with the Census table.
    assert by["G7"]["status"] == "pass" and "'padded': 13" in by["G7"]["note"]
    assert "'trimmed': 32" in by["G7"]["note"] and "'invalid': 232" in by["G7"]["note"]
    assert by["G11"]["status"] == "pass" and "32 rows trimmed (7 values" in by["G11"]["note"]
    # Issue #72: only the 3 export-time names (341 rows) fall outside their year; no shared IDs;
    # Levin != Levine.
    assert by["G8"]["count"] == 341 and "0 rows typed member fail" in by["G8"]["note"]
    assert by["G9"]["status"] == "pass" and by["G10"]["status"] == "pass"


def test_every_question_names_its_class_origin_and_independence():
    """FAILS if a question is added without saying which earlier defect it re-asks, whether it
    is harvested or new, and whether its evidence is independent of the parser."""
    ids = [q["id"] for q in A.QUESTIONS]
    assert len(ids) == len(set(ids))
    for q in A.QUESTIONS:
        assert q["defect_class"] and q["method"], q["id"]
        assert q["origin"] in ("harvested", "new"), q["id"]
        assert q["independent"] in ("yes", "partial", "circular"), q["id"]
    assert {m[0] for m in A.MCP_QUESTIONS} == {f"M{i}" for i in range(1, 13)}
    # FAILS on the 3.11/3.14 split: 3.13+ dedents docstrings, 3.11 keeps the indentation, and
    # the committed report must be byte-identical on both ends of the range.
    assert all("  " not in q["method"] for q in A.QUESTIONS)


def test_cli_check_detects_a_stale_report(tmp_path, monkeypatch):
    """FAILS if --check exits 0 when the committed report differs from a fresh run."""
    copy = tmp_path / "DISCLOSURE-AUDIT.md"
    shutil.copy(A.REPORT, copy)
    copy.write_text(copy.read_text() + "\nedited by hand\n")
    monkeypatch.setattr(A, "REPORT", str(copy))
    assert A.main(["--check"]) == 1
