#!/usr/bin/env python3
"""
Tests for verify_crosswalk.py — the audit-trail gate.

A gate that only ever passes is not a gate, so each test deliberately corrupts the crosswalk in
one specific way and asserts the checker FAILS. The three failure modes correspond to real bugs
that occurred while building this: a dry run recording unapplied edits (COMPLETE), an entry whose
"fix" changed nothing (GROUNDED), and a second run duplicating entries (UNIQUE).

Run: pytest code/test_verify_crosswalk.py
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FIELDS = ["file", "line", "ein", "amount", "defect", "source", "match_key",
          "original_organization", "recovered_organization"]
AWARD_HDR = "category,initiative,award_type,member,organization,program,ein,amount,agency,purpose"


def _tree(tmp_path, org="Acme Org Inc.", ein="132612524"):
    d = tmp_path / "data" / "fy20" / "schedule_c"
    d.mkdir(parents=True)
    (d / "fy20_schedule_c_awards.csv").write_text(
        AWARD_HDR + "\n" + f"EDU,Init A,initiative_provider,,{org},,{ein},50000,DOE,\n",
        encoding="utf-8")
    (tmp_path / "data" / "combined").mkdir(parents=True)
    return tmp_path


def _crosswalk(root, rows):
    p = root / "data" / "combined" / "org_name_recovery_crosswalk.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def _run(root):
    return subprocess.run([sys.executable, os.path.join(HERE, "verify_crosswalk.py")],
                          cwd=root, capture_output=True, text=True)


def _entry(**kw):
    base = dict(file="data/fy20/schedule_c/fy20_schedule_c_awards.csv", line="2",
                ein="132612524", amount="50000", defect="org_prose",
                source="council_disclosure", match_key="ein+amount",
                original_organization="Funds will support operations",
                recovered_organization="Acme Org Inc.")
    base.update(kw)
    return base


def test_passes_when_the_trail_is_exact(tmp_path):
    root = _tree(tmp_path)
    _crosswalk(root, [_entry()])
    r = _run(root)
    assert r.returncode == 0, r.stdout
    assert "the audit trail is exact" in r.stdout


def test_fails_when_an_entry_was_never_applied(tmp_path):
    """The dry-run bug: crosswalk claims a substitution the data never received."""
    root = _tree(tmp_path, org="Funds will support operations")   # never actually fixed
    _crosswalk(root, [_entry()])
    r = _run(root)
    assert r.returncode == 1, r.stdout
    assert "do not match the data" in r.stdout


def test_fails_on_a_noop_entry(tmp_path):
    """An entry whose 'fix' changed nothing inflates the apparent repair count."""
    root = _tree(tmp_path)
    _crosswalk(root, [_entry(original_organization="Acme Org Inc.")])
    r = _run(root)
    assert r.returncode == 1, r.stdout
    assert "no-op" in r.stdout


def test_fails_on_duplicate_entries(tmp_path):
    """A second pass re-recording the same line, as happened when the crosswalk was rebuilt."""
    root = _tree(tmp_path)
    _crosswalk(root, [_entry(), _entry()])
    r = _run(root)
    assert r.returncode == 1, r.stdout
    assert "duplicate" in r.stdout


def test_wrong_ein_entries_check_the_ein_column(tmp_path):
    """wrong_ein repairs `ein`, not `organization` — the checker must look at the right column."""
    root = _tree(tmp_path, ein="112652331")
    _crosswalk(root, [_entry(defect="wrong_ein", ein="112652331", match_key="name+amount",
                             original_organization="[ein 112412584] Acme Org Inc.",
                             recovered_organization="[ein 112652331] Acme Org Inc.")])
    r = _run(root)
    assert r.returncode == 0, r.stdout


def test_accounted_catches_an_unrecorded_edit(tmp_path, monkeypatch):
    """The corruption the first three checks all missed: data silently changed with no entry.

    Uses a real throwaway git repo, because ACCOUNTED compares against a ref rather than a file.
    """
    import subprocess
    root = _tree(tmp_path)
    _crosswalk(root, [_entry()])
    run = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, text=True)
    run("init", "-q"); run("config", "user.email", "t@t"); run("config", "user.name", "t")
    run("add", "-A"); run("commit", "-qm", "base")
    run("branch", "-M", "main")

    # silently rewrite an organization with no crosswalk entry for it
    p = root / "data" / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("Acme Org Inc.", "Totally Different Org"),
                 encoding="utf-8")
    # and point the crosswalk's single entry at the new value so COMPLETE still passes
    _crosswalk(root, [_entry(recovered_organization="Totally Different Org")])

    r = subprocess.run([sys.executable, os.path.join(HERE, "verify_crosswalk.py")],
                       cwd=root, capture_output=True, text=True,
                       env={**os.environ, "CROSSWALK_BASELINE": "main"})
    assert "COMPLETE  1/1" in r.stdout, r.stdout          # the old checks are fooled
    assert r.returncode == 1, r.stdout                     # ACCOUNTED is not
    assert "unexplained" in r.stdout


def test_accounted_never_permits_an_amount_change(tmp_path):
    """No repair may move money, even with a crosswalk entry present for that line."""
    import subprocess
    root = _tree(tmp_path)
    _crosswalk(root, [_entry()])
    run = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, text=True)
    run("init", "-q"); run("config", "user.email", "t@t"); run("config", "user.name", "t")
    run("add", "-A"); run("commit", "-qm", "base"); run("branch", "-M", "main")

    p = root / "data" / "fy20" / "schedule_c" / "fy20_schedule_c_awards.csv"
    p.write_text(p.read_text(encoding="utf-8").replace(",50000,", ",99999,"), encoding="utf-8")

    r = subprocess.run([sys.executable, os.path.join(HERE, "verify_crosswalk.py")],
                       cwd=root, capture_output=True, text=True,
                       env={**os.environ, "CROSSWALK_BASELINE": "main"})
    assert r.returncode == 1, r.stdout
    assert "amount" in r.stdout
