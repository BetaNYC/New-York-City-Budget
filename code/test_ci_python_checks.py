#!/usr/bin/env python3
"""
CI runs the Python checks the PDF tables depend on (#200): .github/workflows/python-checks.yml.

Run: pytest code/test_ci_python_checks.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORKFLOW = os.path.join(REPO, ".github", "workflows", "python-checks.yml")

# The paths #200 names: a pull request touching any of them runs the checks.
PATHS = ["code/**", "config/**", "data/fy*/pdf/**", "data/pdf_years.csv", "research/*/data/**"]
COMMANDS = ["python -m pytest code",
            "python code/build_pdf_promoted.py --check",
            "python code/build_review_suggestions.py --check"]


def read():
    with open(WORKFLOW, encoding="utf-8") as f:
        return f.read()


def triggers(text, event):
    """The `paths:` list under one `on:` event (pull_request or push)."""
    block = re.search(rf"^  {event}:\n((?:    .*\n)+)", text, re.M)
    assert block, f"no {event} trigger"
    return re.findall(r'^      - "([^"]+)"', block.group(1), re.M)


def run_lines(text):
    return [m.strip() for m in re.findall(r"^\s+run: (.+)$", text, re.M)]


def jobs(text):
    """{job id: its block of lines}, from the top-level `jobs:` map."""
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([A-Za-z0-9_-]+):\n", body, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def test_workflow_runs_the_three_python_checks():
    runs = run_lines(read())
    for c in COMMANDS:
        assert c in runs, c


def test_every_job_installs_then_checks_on_the_platform_the_data_is_built_on():
    # The promoted tables are built on macOS arm64; on Linux x86_64 the image checks count a few
    # pixels differently (H9.ink, fy22/fy24 transparency), so a Linux run drifts on correct data.
    js = jobs(read())
    assert set(js) == {"tests", "promoted"}
    for name, block in js.items():
        assert re.search(r"^    runs-on: macos-\d+$", block, re.M), name
        assert re.search(r"^    timeout-minutes: \d+$", block, re.M), name
        assert "fetch-depth: 0" in block, name      # test_diff_disclosure_snapshots needs history
        runs = run_lines(block)
        assert "pip install" in runs[0], name       # install before any check runs
    assert COMMANDS[0] in run_lines(js["tests"]) and COMMANDS[2] in run_lines(js["tests"])
    assert run_lines(js["promoted"])[1:] == [COMMANDS[1]]


def test_pushes_to_main_are_never_cancelled():
    text = read()
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text


def test_workflow_runs_on_pull_requests_touching_the_pdf_paths():
    text = read()
    for event in ("pull_request", "push"):
        paths = triggers(text, event)
        assert set(PATHS) <= set(paths), (event, set(PATHS) - set(paths))
        assert ".github/workflows/python-checks.yml" in paths
    assert "branches: [main]" in text


def test_workflow_installs_the_recipe_requirements():
    installs = [r for r in run_lines(read()) if "pip install" in r]
    assert len(installs) == 2
    for r in installs:
        assert "-r code/requirements.txt" in r and "-r code/requirements-cv.txt" in r
