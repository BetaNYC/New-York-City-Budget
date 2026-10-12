#!/usr/bin/env python3
"""
Tests for parse_expense_disclosure.py -- the Council expense-disclosure dataset
(data/fyNN/expense_disclosure/).

Two kinds of test:
  * unit tests on the row classifier and the cell cleaners, using tiny synthetic workbooks
    built here with zipfile (no network, no download);
  * corpus tests against the real workbooks committed under source/expense-funding-disclosure/.
    These pin the numbers the docs quote, so a figure in a doc always comes from committed code
    run on fixed inputs.

Each test's docstring says what result would FAIL it. FY2013 is a legacy .xls and needs xlrd;
its tests skip, loudly, when xlrd is not installed (pip install -r code/requirements.txt).

Run: pytest code/test_parse_expense_disclosure.py
"""
import csv
import os
import subprocess
import sys
import zipfile
from decimal import Decimal
from xml.sax.saxutils import escape

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import parse_expense_disclosure as P  # noqa: E402

SRC = P.SRC_DIR


def _xlsx(path, rows, sheet="FY99 (01-01-99)"):
    """Write a minimal single-sheet .xlsx. Strings go inline, ints/floats as numeric cells."""
    def cell(ref, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return f'<c r="{ref}"><v>{v}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
    body = []
    for i, row in enumerate(rows, start=1):
        cells = "".join(cell(f"{P._col_letter(j)}{i}", v) for j, v in enumerate(row))
        body.append(f'<row r="{i}">{cells}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml",
                   f'<workbook {ns}><sheets><sheet name="{sheet}" sheetId="1"/></sheets>'
                   f'</workbook>')
        z.writestr("xl/worksheets/sheet1.xml",
                   f'<worksheet {ns}><sheetData>{"".join(body)}</sheetData></worksheet>')
    return path


HDR = ["MOCS ID#", "Fiscal Year", "Source", "Council Member", "Legal Name", "Tax ID", "Status",
       "Amount", "Agency", "Program Name", "Grantee Street Address 1",
       "Grantee Street Address 2", "City", "State", "Postal Code", "Purpose of Funds",
       "Fiscal Conduit", "Fiscal Conduit EIN"]


def _row(name, ein, status, amount, mocs="FY99 00001"):
    return [mocs, 2099, "Local", "Doe", name, ein, status, amount, "DYCD"] + [""] * 9


# ---------------------------------------------------------------- the row classifier

def test_classify_decides_on_status_not_on_label_wording():
    """FAILS if a row is decided by its label text: a summary row with an unfamiliar label and
    no organization must still be stripped, and a real award must not be stripped because its
    purpose happens to contain the word 'total'."""
    assert P.classify("Cleared", "Acme Inc.", "5000") == "award"
    assert P.classify("PENDING ", "Acme Inc.", "5000") == "award"
    assert P.classify("Grand Sum Of Everything:", "", "999") == "stripped"
    assert P.classify("", "", "454755") == "stripped"          # FY2024 orphan shape
    assert P.classify("", "", "") == "stripped"


def test_classify_keeps_an_unknown_status_award_as_other():
    """Decision 2 (keep every row). FAILS if a named, valued row with a status the Council has
    never used is dropped instead of kept for the 'other' bucket."""
    assert P.classify("Withdrawn", "Acme Inc.", "5000") == "award"
    assert P.norm_status("Withdrawn") == "other"


def test_classify_stops_on_a_clearance_row_with_no_name_or_amount():
    """FAILS if a Cleared/Pending row missing its organization or amount is silently dropped
    (that would mean the published schema moved under us)."""
    with pytest.raises(ValueError):
        P.classify("Cleared", "", "5000")
    with pytest.raises(ValueError):
        P.classify("Pending", "Acme Inc.", "n/a")


def test_norm_status_folds_case_and_whitespace_only():
    """FAILS if status_norm is anything but cleared/pending/other, or if case or padding
    changes the bucket."""
    assert [P.norm_status(s) for s in ("Cleared", "CLEARED", " cleared ", "Pending",
                                       "PENDING", "", "Schedule C Total:")] == \
        ["cleared", "cleared", "cleared", "pending", "pending", "other", "other"]


# ---------------------------------------------------------------- cell cleaners

def test_clean_ein_rules():
    """FAILS if a hyphen survives, if a numeric 8-digit EIN is not padded, or if a TEXT
    8-digit EIN is padded (that would invent a digit)."""
    assert P.clean_ein("13-6400434", False) == ("136400434", False)
    assert P.clean_ein("10596502", True) == ("010596502", True)
    assert P.clean_ein("10596502", False) == ("10596502", False)
    assert P.clean_ein("\u200b136400434", False) == ("136400434", False)
    assert P.clean_ein(None, False) == ("", False)


def test_amounts_take_the_shortest_spelling_of_the_same_double():
    """FAILS if the xlsx 17-digit spelling leaks into the CSV, or if an integral amount gains
    a decimal point."""
    assert P.parse_amount_text("22320.420999999998") == Decimal("22320.421")
    assert P.format_amount(P.parse_amount_text("5000")) == "5000"
    assert P.format_amount(P.parse_amount_text("1864000.0")) == "1864000"
    assert P.format_amount(P.parse_amount_text("13881.76")) == "13881.76"
    assert P.parse_amount_text("Schedule C Total:") is None
    assert P.parse_amount_text("") is None


def test_clean_keeps_no_break_space_as_a_separator():
    """FAILS if a no-break space is deleted (it glued 'Center,' to 'Inc.' in an earlier
    version), if a zero-width space survives, or if a line break survives into the CSV."""
    assert P._clean("Youth Design Center,\xa0Inc.") == "Youth Design Center, Inc."
    assert P._clean("\u200b\u200bFunding will") == "Funding will"
    assert P._clean("Line one\nline  two ") == "Line one line two"


def test_clean_deletes_every_invisible_format_character_but_the_soft_hyphen():
    """FAILS if a left-to-right mark (U+200E, FY2015 row 3174 purpose), a zero-width space or a
    BOM survives into the CSV, or if a visible hyphen is touched."""
    assert P._clean("\u200eProgram\ufeff") == "Program"
    assert P._clean("13\u200b1234567") == "131234567"
    assert P._clean("12-11 40th Avenue") == "12-11 40th Avenue"


def test_soft_hyphen_in_an_address_is_a_hyphen_issue_68():
    """Issue #68. FAILS if the Queens house number '12<SHY>11 40th Avenue' (FY2018 row 2796)
    comes out as anything but '12-11 40th Avenue' -- the earlier parser deleted the soft hyphen
    and published '1211 40th Avenue', a different address -- or if a soft hyphen next to a
    visible '-' (169 address cells read '12-<SHY>11') doubles it into '12--11'."""
    assert P._clean("12\xad11 40th Avenue") == "12-11 40th Avenue"
    assert P._clean("12-\xad11 40th Avenue") == "12-11 40th Avenue"
    assert P._clean("12\xad-11 40th Avenue") == "12-11 40th Avenue"
    assert P._clean("12\xad\xad11") == "12-11"


def test_soft_hyphen_in_purpose_follows_the_same_rule():
    """The 25 purpose cells holding a soft hyphen, decided case by case (DATA-DICTIONARY):
    every one is a hyphenated word or a range, so '-' is right; next to '/' or '-' it is
    deleted. FAILS if 'after<SHY>school' loses its hyphen, 'ages 12<SHY>19' becomes '1219',
    or 'disposal/<SHY>destruction' gains a '-' after the slash."""
    assert P._clean("an after\xadschool college access program") == \
        "an after-school college access program"
    assert P._clean("students ages 12\xad19") == "students ages 12-19"
    assert P._clean("girls ages 8-\xad18") == "girls ages 8-18"
    assert P._clean("recycling E\xad-waste.") == "recycling E-waste."
    assert P._clean("document disposal/\xaddestruction") == "document disposal/destruction"


def test_committed_address_keeps_the_queens_hyphen():
    """Corpus pin, read from the committed CSV. FAILS if FY2018 rows 2796-2811 lose the hyphen
    of '12-11 40th Avenue'. (The workbook-vs-CSV hyphen count for every address is audit
    question D13.)"""
    import csv as _csv
    path = os.path.join(P.DATA_DIR, "fy18", "expense_disclosure", "fy18_expense_awards.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = {int(r["source_row"]): r for r in _csv.DictReader(fh)}
    for rn in range(2796, 2812):
        assert rows[rn]["address1"] == "12-11 40th Avenue", (rn, rows[rn]["address1"])


def test_committed_csvs_hold_no_invisible_format_character():
    """Corpus pin. FAILS if any committed disclosure CSV cell holds a Unicode Cf character
    (the 2026-10-12 red-team found 213 soft hyphens and 2 LRMs the docs said were removed)."""
    import glob
    import unicodedata
    bad = []
    for f in glob.glob(os.path.join(P.DATA_DIR, "fy*", "expense_disclosure", "*_awards.csv")):
        with open(f, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if any(unicodedata.category(ch) == "Cf" for ch in line):
                    bad.append(f"{os.path.basename(f)}:{i}")
    assert not bad, bad[:10]


# ---------------------------------------------------------------- synthetic workbooks

def test_synthetic_footer_is_stripped_and_listed(tmp_path):
    """A workbook shaped like FY2024: two awards, then a blank-Status footer whose label sits in
    a different column. FAILS if the footer is summed in, or if it is dropped without being
    listed with its cells."""
    p = _xlsx(str(tmp_path / "funded_disclosure_FY2099.xlsx"), [
        HDR,
        _row("Acme Inc.", "136400434", "Cleared", 5000),
        _row("Beta Org", "010596502", "Pending", 2500.5, mocs="FY99 00002"),
        [None] * 18,
        [None] * 7 + [7500.5, None, None, "New Total"],
    ])
    aw, rep = P.parse_year(p)
    assert [a.legal_name for a in aw] == ["Acme Inc.", "Beta Org"]
    assert rep.n_blank == 1 and rep.n_stripped == 1
    assert rep.stripped[0]["row"] == 5 and rep.stripped[0]["letters"]["K"] == "New Total"
    assert P.total_decimal(aw) == Decimal("7500.5")
    assert rep.amount_by_status["cleared"] == 5000 and rep.amount_by_status["pending"] == \
        Decimal("2500.5")
    assert aw[1].ein == "010596502"        # text cell: leading zero kept, never re-padded


def test_unregistered_printed_total_is_a_stop(tmp_path):
    """FAILS if a year that starts printing a total is reported as 'NO PRINTED TOTAL' (that
    would hide the Council's own number) instead of stopping until RECONCILE_TO names it."""
    p = _xlsx(str(tmp_path / "funded_disclosure_FY2099.xlsx"), [
        HDR, _row("Acme Inc.", "136400434", "Cleared", 5000),
        [None] * 6 + ["Grand Total:", 5000],
    ])
    aw, rep = P.parse_year(p)
    with pytest.raises(ValueError, match="RECONCILE_TO"):
        P.reconcile(aw, rep)


def test_unmapped_header_is_a_stop(tmp_path):
    """FAILS if a column the parser does not recognize is silently ignored."""
    p = _xlsx(str(tmp_path / "funded_disclosure_FY2099.xlsx"),
              [HDR + ["Brand New Column"], _row("Acme Inc.", "136400434", "Cleared", 5000)])
    with pytest.raises(ValueError, match="unmapped header"):
        P.parse_year(p)


def test_unknown_status_row_is_kept_and_counted_as_other(tmp_path):
    """FAILS if a named, valued row with an unknown status is stripped, or if its dollars do
    not appear in the 'other' bucket of the totals."""
    p = _xlsx(str(tmp_path / "funded_disclosure_FY2099.xlsx"), [
        HDR, _row("Acme Inc.", "136400434", "Cleared", 5000),
        _row("Gamma Org", "111111111", "Withdrawn", 700, mocs="FY99 00003"),
    ])
    aw, rep = P.parse_year(p)
    assert rep.n_stripped == 0 and rep.by_status == {"cleared": 1, "other": 1}
    assert rep.amount_by_status["other"] == 700
    assert aw[1].status == "Withdrawn" and aw[1].status_norm == "other"


# ---------------------------------------------------------------- the real corpus

@pytest.fixture(scope="module")
def corpus():
    return {r.fiscal_year: (aw, r) for aw, r in P.parse_all()}


def test_fy2026_no_longer_prints_a_total_but_still_equals_the_one_it_printed(corpus):
    """The 2026-07-15 FY2026 workbook printed Master List Total (=SUM(H2:H11762)) and a typed
    Updated Total, both 716,213,155; the 2026-10-12 one has no footer rows. FAILS if the
    current workbook's verdict claims a printed total it does not have, if the kept rows no
    longer equal the earlier printed figure, or if the report drops the earlier figure or
    presents it as this workbook's own."""
    aw, rep = corpus[2026]
    assert not rep.printed and not rep.stripped
    assert P.reconcile(aw, rep) == ("NO PRINTED TOTAL", [])
    assert P.total_decimal(aw) == Decimal(716213155)
    assert [v for _, _, v in P.PRIOR_PRINTED[2026]] == [Decimal(716213155)] * 2
    text = P.reconciliation_text(aw, rep)
    assert "printed total: NO PRINTED TOTAL" in text
    assert "snapshot 2026-07-15 'Master List Total': 716,213,155 vs kept rows 716,213,155  SAME" \
        in text
    assert "They are NOT this" in text


def test_prior_printed_total_says_different_when_it_is(corpus):
    """FAILS if a changed year total would still be reported as SAME as the earlier snapshot."""
    aw, rep = corpus[2026]
    text = P.reconciliation_text(aw[1:], rep)
    assert "SAME" not in text and text.count("DIFFERENT") == 2


def test_fy2024_equals_its_new_total_and_lists_the_orphan(corpus):
    """FAILS if the kept rows differ from 'New Total' (=SUM(H2:H10818), and =Adoption Total +
    Admin New Add), or if the unlabeled 454,755 cell is summed in or dropped unlisted."""
    aw, rep = corpus[2024]
    assert P.reconcile(aw, rep)[0] == "RECONCILED"
    assert P.total_decimal(aw) == Decimal(527971414)
    orphan = [p for p in rep.printed if p["value"] == 454755]
    assert len(orphan) == 1 and orphan[0]["label"] == "" and orphan[0]["formula"] == ""


def test_exactly_these_rows_are_stripped(corpus):
    """FAILS if the strip predicate widens or narrows by a single row anywhere in 15 years."""
    got = {fy: [s["row"] for s in r.stripped] for fy, (_, r) in corpus.items() if r.stripped}
    assert got == {2024: [10818, 10819, 10820, 10821, 10829]}


def test_every_row_is_accounted_for(corpus):
    """FAILS if any row after the header is neither an award, a blank, nor a listed strip."""
    for fy, (aw, r) in corpus.items():
        if r.skipped:
            continue
        assert r.n_rows_present == r.n_awards + r.n_blank + r.n_stripped, fy
        assert r.sheet_rows == r.n_rows_present + 1, fy


def test_only_fy2024_prints_a_total(corpus):
    """FAILS if a computed sum is ever presented as the Council's: every other year must say
    NO PRINTED TOTAL and that its sums are not a Council figure."""
    for fy, (aw, r) in corpus.items():
        if r.skipped:
            continue
        verdict = P.reconcile(aw, r)[0]
        if fy == 2024:
            assert verdict == "RECONCILED", fy
        else:
            assert verdict == "NO PRINTED TOTAL", fy
            assert "not a figure published by the Council" in P.reconciliation_text(aw, r)


def test_status_buckets_partition_each_year(corpus):
    """FAILS if cleared + pending + other does not add back to the year's total, in rows and in
    dollars -- i.e. if a status bucket loses or double-counts a row."""
    for fy, (aw, r) in corpus.items():
        if r.skipped:
            continue
        assert sum(r.by_status.values()) == r.n_awards, fy
        assert sum(r.amount_by_status.values()) == P.total_decimal(aw), fy


def test_fy2027_figures_and_cleared_is_the_headline(corpus):
    """Pins the figures the docs quote for FY2027 (2026-10-12 snapshot; the 2026-07-15 one was
    5,037 cleared / 5,003 pending). FAILS if status is mis-bucketed."""
    aw, r = corpus[2027]
    assert r.by_status == {"cleared": 8870, "pending": 1537}
    assert r.amount_by_status["cleared"] == Decimal(590253954)
    assert r.amount_by_status["pending"] == Decimal(115450046)


def test_nonintegral_amount_count(corpus):
    """Pins the docstring figure in parse_amount_text. FAILS if amounts are rounded."""
    n = sum(1 for aw, r in corpus.values() for a in aw if "." in a.amount_text)
    if corpus[2013][1].skipped:
        pytest.skip("FY2013 needs xlrd")
    assert n == 281


def test_fy2013_reads_through_xlrd(corpus):
    """FAILS if FY2013 is not parsed, if its numeric EIN cells lose their leading zero, or if
    its hyphenated EINs keep the hyphen."""
    pytest.importorskip("xlrd")
    aw, r = corpus[2013]
    assert r.skipped == "" and r.sheet_name == "MASTER" and r.format == "xls"
    assert r.n_awards == 4987 and r.n_stripped == 0
    assert r.by_status == {"cleared": 2343, "pending": 2644}
    assert r.amount_by_status["cleared"] == Decimal("18201784.75")
    assert list(r.ein_padded) == [15, 1449, 1644]
    by_row = {a.source_row: a for a in aw}
    assert all(by_row[n].ein.startswith("0") and len(by_row[n].ein) == 9 for n in r.ein_padded)
    assert all(e == "" or (e.isdigit() and len(e) == 9) for e in (a.ein for a in aw))
    assert sum(1 for a in aw if not a.ein) == 2
    assert by_row[2].postal_code == "" and by_row[4987].postal_code == "10301"  # not "10301.0"


def test_module_imports_and_degrades_without_xlrd():
    """Decision 4: the parser stays importable without xlrd. FAILS if importing needs xlrd, if
    FY2014+ stop parsing without it, if FY2013 is dropped without a reason, or if --write would
    publish a partial dataset."""
    code = (
        "import sys; sys.modules['xlrd'] = None\n"
        f"sys.path.insert(0, {HERE!r})\n"
        "import parse_expense_disclosure as P\n"
        "res = P.parse_all()\n"
        "r13 = [r for _, r in res if r.fiscal_year == 2013][0]\n"
        "assert r13.skipped and 'xlrd' in r13.skipped, r13\n"
        "assert all(r.n_awards > 0 for _, r in res if r.fiscal_year != 2013)\n"
        "try:\n"
        "    P.outputs(res)\n"
        "except SystemExit as e:\n"
        "    assert 'partial' in str(e); print('REFUSED')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "REFUSED"


# ---------------------------------------------------------------- committed outputs

def test_committed_outputs_and_manifest_are_current():
    """FAILS if anyone hand-edits a committed disclosure CSV, reconciliation report or the
    manifest, or changes the parser without re-running --write."""
    pytest.importorskip("xlrd")
    results = P.parse_all()
    files = P.outputs(results)
    files[P.MANIFEST] = P.manifest_text(P.manifest_rows(results, previous=P.read_manifest()))
    assert P.stale(files) == []


def test_manifest_hashes_are_the_files_on_disk():
    """The snapshot baseline. FAILS if a workbook is replaced without the manifest moving, or
    if a file in the folder is missing from the manifest."""
    rows = P.read_manifest()
    files = sorted(f for f in os.listdir(SRC) if f not in P.NOT_SOURCE
                   and not f.startswith("."))
    assert [r["file"] for r in rows] == files
    for r in rows:
        assert P.sha256(os.path.join(SRC, r["file"])) == r["sha256"], r["file"]
        assert int(r["bytes"]) == os.path.getsize(os.path.join(SRC, r["file"]))
        assert r["retrieved"] == "2026-10-12"


def test_manifest_never_infers_a_retrieval_date(tmp_path):
    """FAILS if a new or changed file gets a retrieved date nobody supplied."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "funded_disclosure_FY2099.xlsx").write_bytes(b"not really a workbook")
    with pytest.raises(SystemExit, match="--retrieved"):
        P.manifest_rows([], src_dir=str(src), retrieved=None, previous=[])


def test_csv_keeps_ein_as_text_with_leading_zeros():
    """FAILS if the published CSV drops a leading zero (spreadsheet-style number coercion)."""
    pytest.importorskip("xlrd")
    path = os.path.join(P.out_dir(2013), "fy13_expense_awards.csv")
    with open(path, newline="", encoding="utf-8") as f:
        rows = {r["source_row"]: r for r in csv.DictReader(f)}
    assert rows["15"]["ein"].startswith("0") and len(rows["15"]["ein"]) == 9
    assert list(rows["2"].keys()) == P.OUT_FIELDS


# ---------------------------------------------------------------- re-pulls: --verified, history

JULY_SHA = {  # the 2026-07-15 snapshot of the four files the 2026-10-12 re-pull replaced
    "Capital-Database.xlsx":
        "8c63ed6739b5bb0a68952036af6853a4cd6e9a3fec34fb5ce435fa297d84cf28",
    "funded_disclosure_FY2025.xlsx":
        "b3c646dd4e2c387b8d74e86763921c5e417d58288005a9d86381cd2bf2fe1a51",
    "funded_disclosure_FY2026.xlsx":
        "4691c42bd3e74846c84ffeba942ab914cdecac4b8b967e8a32116530df47fb59",
    "funded_disclosure_FY2027.xlsx":
        "d15f058a38ea24163b42678dc1e411af90398c7e54762e50f617953bafb67777",
}


def test_history_keeps_the_hashes_of_overwritten_workbooks():
    """FAILS if a superseded snapshot's hash is no longer traceable once its workbook has been
    overwritten in place, or if the history claims a file that is still current was replaced
    by different bytes."""
    with open(P.MANIFEST_HISTORY, newline="", encoding="utf-8") as f:
        hist = list(csv.DictReader(f))
    assert list(hist[0].keys()) == P.HISTORY_FIELDS
    current = {r["file"]: r["sha256"] for r in P.read_manifest()}
    july = {r["file"]: r for r in hist if r["retrieved"] == "2026-07-15"}
    assert set(july) == set(current)                       # all 16 July rows kept
    for fname, sha in JULY_SHA.items():
        assert july[fname]["sha256"] == sha and current[fname] != sha, fname
        assert july[fname]["superseded_on"] == "2026-10-12"
    for fname in set(current) - set(JULY_SHA):            # re-verified, byte-identical
        assert july[fname]["sha256"] == current[fname], fname


def _one_file_src(tmp_path, payload=b"bytes"):
    src = tmp_path / "src"
    src.mkdir()
    (src / "Capital-Database.xlsx").write_bytes(payload)  # not a zip: no sheet is read
    return str(src)


def test_verified_restamps_unchanged_files_only(tmp_path):
    """FAILS if --verified moves the date of an unchanged file anywhere but to the verified
    date, or if it is accepted as the download date of a CHANGED file."""
    src = _one_file_src(tmp_path)
    digest = P.sha256(os.path.join(src, "Capital-Database.xlsx"))
    prev = [{"file": "Capital-Database.xlsx", "sha256": digest, "retrieved": "2026-07-15"}]
    assert P.manifest_rows([], src_dir=src, previous=prev)[0]["retrieved"] == "2026-07-15"
    assert P.manifest_rows([], src_dir=src, previous=prev,
                           verified="2026-10-12")[0]["retrieved"] == "2026-10-12"
    changed = [dict(prev[0], sha256="0" * 64)]
    with pytest.raises(SystemExit, match="--retrieved"):
        P.manifest_rows([], src_dir=src, previous=changed, verified="2026-10-12")


def test_history_is_append_only_and_skips_unchanged_rows(tmp_path):
    """FAILS if an unchanged manifest row is written to the history, if a changed one is not,
    or if appending rewrites any existing history line."""
    src = _one_file_src(tmp_path)
    digest = P.sha256(os.path.join(src, "Capital-Database.xlsx"))
    row = P.manifest_rows([], src_dir=src, previous=[
        {"file": "Capital-Database.xlsx", "sha256": digest, "retrieved": "2026-07-15"}])[0]
    same = {k: str(v) for k, v in row.items()}
    assert P.superseded_rows([same], [row]) == []
    old = dict(same, sha256="a" * 64, retrieved="2026-01-01")
    gone = dict(same, file="Gone.xlsx")
    out = P.superseded_rows([old, gone], [row])
    assert [(r["file"], r["superseded_on"]) for r in out] == [
        ("Capital-Database.xlsx", row["retrieved"]), ("Gone.xlsx", "removed")]
    first = P.history_text("", out[:1])
    second = P.history_text(first, out[1:])
    assert second.startswith(first) and second.count("\n") == 3
    assert first.splitlines()[0] == ",".join(P.HISTORY_FIELDS)
