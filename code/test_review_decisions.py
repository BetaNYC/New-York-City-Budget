#!/usr/bin/env python3
"""
Tests for code/validate_review_decisions.py and code/build_review_suggestions.py.

Run: pytest code/test_review_decisions.py
"""
import csv
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_review_suggestions as brs  # noqa: E402
import validate_review_decisions as vrd  # noqa: E402

REVIEW = [{"review_id": "aaa", "check_id": "C1", "pdf_page": "4"},
          {"review_id": "bbb", "check_id": "C2", "pdf_page": "5"},
          {"review_id": "ccc", "check_id": "C3", "pdf_page": "6"}]


def dec(rid, decision="accepted_as_printed", by="Noel Hidalgo", at="2026-10-21"):
    return {"review_id": rid, "decision": decision, "note": "", "decided_by": by, "decided_at": at}


def test_valid_and_open():
    res = vrd.validate(REVIEW, vrd.HEADER, [dec("aaa"), dec("bbb", "needs_info", at="2026-10-21T09:30:00Z")])
    assert res["errors"] == []
    assert [r["review_id"] for r in res["open"]] == ["ccc"]
    assert res["needs_info"] == ["bbb"]


def test_every_problem_is_listed():
    res = vrd.validate(REVIEW, ["review_id", "decision"], [
        dec("zzz"), dec("aaa", "fixed"), dec("aaa"), dec("bbb", by=" "), dec("ccc", at="21/10/2026")])
    text = "\n".join(res["errors"])
    assert "header is review_id,decision" in text
    assert "zzz" in text and "not in the review CSV" in text
    assert "'fixed'" in text
    assert "also on line" in text
    assert "decided_by is blank" in text
    assert "not an ISO date" in text


def test_cli_exit_codes(tmp_path):
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    d = tmp_path / "decisions.csv"
    with open(d, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vrd.HEADER)
        w.writeheader()
        w.writerow(dec("aaa"))
    assert vrd.main(["--review", str(rv), "--decisions", str(d)]) == 0
    assert vrd.main(["--review", str(rv), "--decisions", str(d), "--complete"]) == 2
    with open(d, "a", newline="") as f:
        csv.writer(f).writerow(["nope", "accepted_as_printed", "", "x", "2026-10-21"])
    assert vrd.main(["--review", str(rv), "--decisions", str(d)]) == 1


def test_complete_counts_needs_info_as_open(tmp_path, capsys):
    # #194: needs_info means "can't tell yet", so --complete must not report a family as done
    # while one is outstanding. It exits 2 and lists it, unless --allow-needs-info says so on purpose.
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    d = tmp_path / "decisions.csv"
    d.write_text(vrd.to_csv([dec("aaa"), dec("bbb", "needs_info"), dec("ccc", "source_error")]))
    args = ["--review", str(rv), "--decisions", str(d)]
    assert vrd.main(args) == 0
    capsys.readouterr()
    assert vrd.main(args + ["--complete"]) == 2
    out = capsys.readouterr().out
    assert "needs_info bbb" in out and "C2" in out and "p.5" in out
    assert vrd.main(args + ["--complete", "--allow-needs-info"]) == 0
    d.write_text(vrd.to_csv([dec("aaa"), dec("bbb"), dec("ccc", "source_error")]))
    assert vrd.main(args + ["--complete"]) == 0


def test_committed_decision_files_are_valid():
    # The decisions files committed for each FY2027 and FY2026 family.
    pairs = [
        ("data/fy27/pdf/schedule_c/fy27_sc_review.csv", "research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv"),
        ("data/fy27/pdf/capital_sd/fy27_capital_sd_review.csv", "research/2026-10-20-fy27-capital-terms-review/data/fy27_capital_sd_review_decisions.csv"),
        ("data/fy27/pdf/terms/fy27_terms_review.csv", "research/2026-10-20-fy27-capital-terms-review/data/fy27_terms_review_decisions.csv"),
        ("data/fy26/pdf/capital_sd/fy26_capital_sd_review.csv", "research/2026-10-21-fy26-capital-terms-review/data/fy26_capital_sd_review_decisions.csv"),
        ("data/fy26/pdf/terms/fy26_terms_review.csv", "research/2026-10-21-fy26-capital-terms-review/data/fy26_terms_review_decisions.csv"),
        ("data/fy26/pdf/schedule_c/fy26_sc_review.csv", "research/2026-10-21-fy26-schedule-c-review/data/fy26_sc_review_decisions.csv"),
        ("data/fy26/pdf/transparency/fy26_tr_review.csv", "research/2026-10-21-fy26-transparency-review/data/fy26_tr_review_decisions.csv"),
    ]
    # FY2025 back to FY2018: one decisions file per family and year in data/pdf_years.csv.
    prefix = {"capital_sd": "capital_sd", "terms": "terms", "schedule_c": "sc", "transparency": "tr"}
    with open(os.path.join(REPO, "data", "pdf_years.csv"), newline="") as f:
        for y in csv.DictReader(f):
            if int(y["fiscal_year"]) > 2025:
                continue
            nn, pre = y["fiscal_year"][2:], prefix[y["family"]]
            found = glob.glob(os.path.join(REPO, "research", f"2026-10-2*-fy{nn}-*-review", "data",
                                           f"fy{nn}_{pre}_review_decisions.csv"))
            assert len(found) == 1, (y["fiscal_year"], y["family"], found)
            pairs.append((f"data/fy{nn}/pdf/{y['family']}/fy{nn}_{pre}_review.csv", os.path.relpath(found[0], REPO)))
    for review, decisions in pairs:
        assert vrd.main(["--review", os.path.join(REPO, review), "--decisions", os.path.join(REPO, decisions)]) == 0, decisions


def test_suggestions_cover_every_review_row_and_are_committed():
    text, rows = brs.build()
    with open(brs.OUT, encoding="utf-8") as f:
        assert f.read() == text, "run code/build_review_suggestions.py --write"
    n = 0
    for (fy, fam), rel in brs.REVIEW_FILES.items():
        with open(os.path.join(REPO, rel), newline="", encoding="utf-8") as f:
            n += sum(1 for _ in csv.DictReader(f))
    assert len(rows) == n
    assert {r["suggested_decision"] for r in rows} <= set(brs.DECISIONS) | {""}
    # Only Schedule C rows may be blank, and only where its REVIEW.md suggests nothing.
    assert {r["family"] for r in rows if not r["suggested_decision"]} <= {"schedule_c", "transparency"}
    by = {r["review_id"]: r for r in rows}
    assert by["d68b985e6c58"]["suggested_decision"] == "source_error"
    assert by["01375b88b4c3"]["suggested_decision"] == "accepted_as_printed"


def test_every_promoted_review_row_has_a_suggestion_from_its_own_year():
    # Globbed, not taken from REVIEW_FILES: a year left out of REVIEW_FILES would be skipped
    # without a word, and a year that borrowed another year's rules would cite that year.
    with open(brs.OUT, newline="", encoding="utf-8") as f:
        sugg = {(r["fiscal_year"], r["family"], r["review_id"]): r for r in csv.DictReader(f)}
    paths = glob.glob(os.path.join(REPO, "data", "fy*", "pdf", "*", "*_review.csv"))
    assert len(paths) >= 36
    missing, wrong_year = [], []
    for path in paths:
        fam = os.path.basename(os.path.dirname(path))
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                fy = r["fiscal_year"]
                s = sugg.get((fy, fam, r["review_id"]))
                if s is None:
                    missing.append((fy, fam, r["review_id"]))
                elif f"-fy{fy[2:]}-" not in s["source"]:
                    wrong_year.append((fy, fam, r["review_id"], s["source"]))
    assert missing == [] and wrong_year == []


def test_merge_adds_new_and_never_overwrites(tmp_path):
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    committed = tmp_path / "decisions.csv"
    committed.write_text(vrd.to_csv([dec("aaa", "source_error")]))
    export = tmp_path / "export.csv"
    export.write_text(vrd.to_csv([dec("aaa", "source_error"), dec("bbb")]))
    assert vrd.main(["--review", str(rv), "--decisions", str(committed), "--add", str(export), "--write"]) == 0
    _, rows = vrd.read(str(committed))
    assert [(r["review_id"], r["decision"]) for r in rows] == [("aaa", "source_error"), ("bbb", "accepted_as_printed")]
    # A conflicting decision is a problem and nothing is written.
    export.write_text(vrd.to_csv([dec("aaa", "accepted_as_printed"), dec("ccc")]))
    before = committed.read_text()
    assert vrd.main(["--review", str(rv), "--decisions", str(committed), "--add", str(export), "--write"]) == 1
    assert committed.read_text() == before


def test_accept_as_printed_is_never_needs_info():
    # A suggestion whose note says "Accept as printed" (the REVIEW.md's own words) must not be
    # needs_info: clicking "Accept suggestion" would record something the note does not say.
    _, rows = brs.build()
    bad = [(r["review_id"], r["suggested_note"]) for r in rows
           if "accept as printed" in r["suggested_note"].lower() and r["suggested_decision"] == "needs_info"]
    assert bad == []
    by = {r["review_id"]: r for r in rows}
    assert by["549bba9337ee"]["suggested_decision"] == "accepted_as_printed"
    assert "Council Finance" in by["549bba9337ee"]["suggested_note"]
    for rid in ("0a4bc5e267ec", "138c84722a95", "5f578772c9b9"):   # FY2026, same wording
        assert by[rid]["suggested_decision"] == "accepted_as_printed", rid
    # Real unknowns stay needs_info: FY2027 E CC0598 and E CC1245.
    assert by["1191bd798416"]["suggested_decision"] == "needs_info"
    assert by["4ce0ec50aa88"]["suggested_decision"] == "needs_info"


# ---------------------------------------------------------------- the page-image rule (#209)

PAGE_REVIEW = [{"review_id": "p1", "check_id": "H5.anchors", "pdf_page": "235", "award_id": "fy23-p235-t00-r018", "field": "ein"},
               {"review_id": "p2", "check_id": "T5.anchors", "pdf_page": "46", "row_id": "fy19-tr03-p046-r016", "field": ""},
               {"review_id": "p3", "check_id": "H13.rollup", "pdf_page": "", "award_id": "", "field": ""}]


def page_dec(rid, note):
    return dict(dec(rid, "read_from_page_image"), note=note)


def test_page_image_decision_must_say_what_the_page_shows():
    ok = vrd.validate(PAGE_REVIEW, vrd.HEADER, [
        page_dec("p1", 'page shows ein: "87-0753479"'),
        page_dec("p2", 'Suggestion accepted: page shows ein: "472383238" (hidden tab glyph)')])
    assert ok["errors"] == []
    bad = vrd.validate(PAGE_REVIEW, vrd.HEADER, [
        page_dec("p1", "the page shows 87-0753479"),            # not in the form
        page_dec("p2", 'page shows amount: "12,000"'),          # amounts are not read from the page
        page_dec("p3", 'page shows ein: "87-0753479"')])        # names no data row
    text = "\n".join(bad["errors"])
    assert "line 2" in text and 'page shows <field>: "<value>"' in text
    assert "line 3" in text and "'amount' cannot be read from the page image" in text
    assert "line 4" in text and "names none" in text
    assert "not an EIN" in "\n".join(vrd.validate(PAGE_REVIEW, vrd.HEADER, [page_dec("p1", 'page shows ein: "87-075347"')])["errors"])
    # The note's field must be the review item's field, when the item names one.
    assert "the review item is about 'ein'; the note names 'org'" in "\n".join(
        vrd.validate(PAGE_REVIEW, vrd.HEADER, [page_dec("p1", 'page shows org: "Laundromat"')])["errors"])
    # A sub-award row is refused here, not left to stop the reader.
    sub = [{"review_id": "s1", "check_id": "H8.lattice", "pdf_page": "105",
            "award_id": "fy19-sub-p105-t01-r012", "field": "row_band:12.53pt"}]
    errs = "\n".join(vrd.validate(sub, vrd.HEADER, [page_dec("s1", 'page shows ein: "37-1514651"')])["errors"])
    assert "not supported on a sub-award row" in errs


def test_page_image_decision_is_applied_to_its_row_and_flagged():
    import page_image
    rows = {"fy23-p235-t00-r018": {"ein": "", "ein_printed": "87 0753479", "read_from_page_image": "",
                                   "row_flags": ["ein_unreadable"]},
            "fy23-p235-t00-r019": {"ein": "111111111", "ein_printed": "11-1111111", "read_from_page_image": ""}}
    review = [{"review_id": "p1", "award_id": "fy23-p235-t00-r018", "decision": "read_from_page_image",
               "note": 'Suggestion accepted: page shows ein: "87-0753479"'},
              {"review_id": "x", "award_id": "fy23-p235-t00-r019", "decision": "accepted_as_printed", "note": ""}]
    changed = page_image.apply_decisions(review, rows, "award_id")
    assert len(changed) == 1
    r = rows["fy23-p235-t00-r018"]
    assert (r["ein"], r["ein_printed"], r["read_from_page_image"]) == ("870753479", "87 0753479", "ein")
    assert rows["fy23-p235-t00-r019"]["read_from_page_image"] == ""
    # The row no longer says its EIN is unreadable.
    assert r["row_flags"] == ["ein_read_from_page_image"]
    tr_row = {"ein": "", "ein_format": "odd", "row_flags": ["ein_odd"]}
    page_image.apply(tr_row, "ein", "472383238")
    assert (tr_row["ein_format"], tr_row["row_flags"]) == ("page_image", ["ein_read_from_page_image"])
    # A sub-award decision stops the run with a clear message.
    try:
        page_image.apply_decisions([{"review_id": "s", "award_id": "fy19-sub-p105-t01-r012",
                                     "decision": "read_from_page_image", "note": 'page shows ein: "37-1514651"'}],
                                   rows, "award_id")
        raise AssertionError("expected a stop")
    except ValueError as e:
        assert "sub-award" in str(e)
    # A decision that cannot be applied stops the run; nothing is guessed.
    review[0]["award_id"] = "nope"
    try:
        page_image.apply_decisions(review, rows, "award_id")
        raise AssertionError("expected a stop")
    except ValueError as e:
        assert "names one data row" in str(e) or "needs a review row" in str(e)


def test_page_image_suggestions_for_laundromat_and_himalayan_elders():
    # The two review items #217 names, suggested as read_from_page_image.
    _, rows = brs.build()
    by = {(r["fiscal_year"], r["family"], r["review_id"]): r for r in rows}
    import page_image
    s = by[("2023", "schedule_c", "42eba5fef74a")]
    assert s["suggested_decision"] == "read_from_page_image"
    assert page_image.parse(s["suggested_note"]) == ("ein", "87-0753479")
    s = by[("2019", "transparency", "68a35940ec45")]
    assert s["suggested_decision"] == "read_from_page_image"
    assert page_image.parse(s["suggested_note"]) == ("ein", "472383238")
    # Only those two: no other review row is suggested as read from the page image yet.
    assert sum(r["suggested_decision"] == "read_from_page_image" for r in rows) == 2
    # Decided by Noel Hidalgo on 2026-10-22: exactly these two carry read_from_page_image in the
    # committed decisions files, each naming the same field and value as its suggestion.
    decided = {}
    for path in glob.glob(os.path.join(REPO, "research", "*", "data", "*_review_decisions.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            for d in csv.DictReader(f):
                if d["decision"] == "read_from_page_image":
                    decided[d["review_id"]] = page_image.parse(d["note"])
    assert decided == {"42eba5fef74a": ("ein", "87-0753479"), "68a35940ec45": ("ein", "472383238")}
    # And promotion applied them: each row carries the page's EIN, flagged.
    for path, rid, ein in [
        ("data/fy23/pdf/schedule_c/fy23_sc_awards.csv", "42eba5fef74a", "870753479"),
        ("data/fy19/pdf/transparency/fy19_tr_rows.csv", "68a35940ec45", "472383238"),
    ]:
        with open(os.path.join(REPO, path), newline="", encoding="utf-8") as f:
            row = next(r for r in csv.DictReader(f) if r["review_id"] == rid)
        assert row["ein"] == ein and row["read_from_page_image"] == "ein", path


# ---------------------------------------------------------------- one record of a decision (#195)

FAMILY = {"sc": "schedule_c", "tr": "transparency", "capital_sd": "capital_sd", "terms": "terms"}


def test_review_files_carry_exactly_the_committed_decisions():
    # The decisions CSV is the record; a review file's decision and note columns are copied from
    # it (the readers do it on every run). Both copies, the review folder's and the promoted one,
    # must say what the record says, so a re-run of a decided year changes nothing.
    paths = glob.glob(os.path.join(REPO, "research", "*", "data", "*_review_decisions.csv"))
    assert len(paths) >= 36
    wrong = []
    for path in paths:
        name = os.path.basename(path)[:-len("_review_decisions.csv")]
        yy, pre = name.split("_", 1)
        _, decisions = vrd.read(path)
        record = {d["review_id"]: (d["decision"], d["note"]) for d in decisions}
        for copy in (os.path.join(os.path.dirname(path), f"{name}_review.csv"),
                     os.path.join(REPO, "data", yy, "pdf", FAMILY[pre], f"{name}_review.csv")):
            header, rows = vrd.read(copy)
            if "decision" not in header:
                continue    # capital_sd and terms review files carry no decision column yet
            for r in rows:
                if r["review_id"] != "ok" and (r["decision"], r["note"]) != record.get(r["review_id"], ("", "")):
                    wrong.append((os.path.relpath(copy, REPO), r["review_id"]))
    assert wrong == [], "run code/validate_review_decisions.py --sync (PDF-RECIPE.md Step 7)"


def test_write_copies_the_decisions_into_the_review_files(tmp_path):
    cols = ["review_id", "check_id", "pdf_page", "decision", "note"]
    folder = tmp_path / "data"
    folder.mkdir()
    research = folder / "fy99_sc_review.csv"
    promoted = tmp_path / "promoted_review.csv"
    for p in (research, promoted):
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(dict(r, decision="", note="") for r in REVIEW)
    committed = folder / "fy99_sc_review_decisions.csv"
    committed.write_text(vrd.to_csv([]))
    export = tmp_path / "export.csv"
    export.write_text(vrd.to_csv([dict(dec("bbb", "source_error"), note='The PDF says "x", twice')]))
    assert vrd.main(["--review", str(promoted), "--decisions", str(committed), "--add", str(export), "--write"]) == 0
    for p in (research, promoted):
        _, rows = vrd.read(str(p))
        assert [(r["review_id"], r["decision"], r["note"]) for r in rows] == [
            ("aaa", "", ""), ("bbb", "source_error", 'The PDF says "x", twice'), ("ccc", "", "")], p
    # Nothing else in the file moves: only those two cells.
    assert research.read_text().splitlines()[1] == "aaa,C1,4,,"
    # --sync alone repairs a copy edited out of step, and says so.
    research.write_text(research.read_text().replace("source_error", "parser_bug"))
    assert vrd.main(["--review", str(promoted), "--decisions", str(committed), "--sync"]) == 0
    assert "source_error" in research.read_text() and "parser_bug" not in research.read_text()


def test_sync_leaves_a_committed_review_file_byte_identical(tmp_path):
    # Blank every decision and note in a copy of each committed review file, sync it from its
    # decisions file, and get the committed bytes back: the copy is wholly derived from the record.
    n = 0
    for path in glob.glob(os.path.join(REPO, "research", "*", "data", "*_review_decisions.csv")):
        name = os.path.basename(path)[:-len("_review_decisions.csv")]
        yy, pre = name.split("_", 1)
        _, decisions = vrd.read(path)
        for copy in (os.path.join(os.path.dirname(path), f"{name}_review.csv"),
                     os.path.join(REPO, "data", yy, "pdf", FAMILY[pre], f"{name}_review.csv")):
            header, rows = vrd.read(copy)
            if "decision" not in header:
                continue
            with open(copy, newline="", encoding="utf-8") as f:
                text = f.read()
            assert vrd.review_csv(header, rows) == text, copy
            scratch = tmp_path / f"{n}.csv"
            scratch.write_text(vrd.review_csv(header, [dict(r, decision="", note="") for r in rows]),
                               encoding="utf-8")
            vrd.sync(str(scratch), decisions)
            assert scratch.read_text(encoding="utf-8") == text, copy
            n += 1
    assert n >= 30


def test_add_with_sync_but_no_write_is_refused(tmp_path):
    # --add X --sync without --write would copy an unsaved decision into the review files,
    # the mismatch #195 is about. It is refused and nothing is written.
    cols = ["review_id", "check_id", "pdf_page", "decision", "note"]
    folder = tmp_path / "data"
    folder.mkdir()
    review = folder / "fy99_sc_review.csv"
    with open(review, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(dict(r, decision="", note="") for r in REVIEW)
    committed = folder / "fy99_sc_review_decisions.csv"
    committed.write_text(vrd.to_csv([]))
    export = tmp_path / "export.csv"
    export.write_text(vrd.to_csv([dec("bbb", "source_error")]))
    before = (review.read_text(), committed.read_text())
    assert vrd.main(["--review", str(review), "--decisions", str(committed), "--add", str(export), "--sync"]) == 1
    assert (review.read_text(), committed.read_text()) == before


def test_complete_lets_a_needs_info_close_30_days_after_its_question_was_sent(tmp_path, capsys):
    # PLAN.md "What closed means" 3 (#194): answered, or 30 days since the question was sent.
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    d = tmp_path / "decisions.csv"
    d.write_text(vrd.to_csv([dec("aaa"), dec("bbb", "needs_info"), dec("ccc", "needs_info")]))
    q = tmp_path / "questions.csv"

    def run(bbb_status, bbb_sent, ccc_status="sent", ccc_sent="2026-09-01", today="2026-10-23"):
        q.write_text("question_id,review_ids,issue,sent_on,answered_on,answer,status\n"
                     f"q1,x1;bbb,1,{bbb_sent},,,{bbb_status}\n"
                     f"q2,ccc,2,{ccc_sent},,,{ccc_status}\n")
        return vrd.main(["--review", str(rv), "--decisions", str(d), "--complete",
                         "--questions", str(q), "--today", today])

    assert run("sent", "2026-09-23") == 0              # 30 days exactly: both may close
    assert "may close as printed" in capsys.readouterr().out
    assert run("sent", "2026-09-24") == 2              # 29 days: bbb still blocks
    assert run("draft", "") == 2                       # never sent
    assert run("sent", "") == 2                        # no date: not counted
    assert run("answered", "2026-09-01") == 2          # answered: record the answer instead
    assert run("sent", "2026-09-01", ccc_status="draft", ccc_sent="") == 2
    capsys.readouterr()
    run("sent", "2026-09-24")
    out = capsys.readouterr().out
    assert "not complete: 1 needs_info" in out


def test_an_answered_question_blocks_even_beside_an_older_sent_one(tmp_path, capsys):
    # An item covered by an answered question waits for a person to record the answer, even if
    # another question covering it was sent 30+ days ago.
    rv = tmp_path / "review.csv"
    with open(rv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "check_id", "pdf_page"])
        w.writeheader()
        w.writerows(REVIEW)
    d = tmp_path / "decisions.csv"
    d.write_text(vrd.to_csv([dec("aaa"), dec("bbb", "needs_info"), dec("ccc")]))
    q = tmp_path / "questions.csv"
    q.write_text("question_id,review_ids,issue,sent_on,answered_on,answer,status\n"
                 "q1,bbb,1,2026-08-01,,,sent\n"
                 "q2,bbb,2,2026-09-01,2026-10-01,It is P.S. 199.,answered\n")
    args = ["--review", str(rv), "--decisions", str(d), "--complete", "--questions", str(q)]
    assert vrd.main(args + ["--today", "2026-10-23"]) == 2
    # A bad --today is a clear problem, not a traceback.
    capsys.readouterr()
    assert vrd.main(args + ["--today", "23/10/2026"]) == 1
    assert "--today '23/10/2026' is not an ISO date" in capsys.readouterr().out
