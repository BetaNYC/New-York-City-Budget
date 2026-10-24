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


def test_workflow_runs_the_three_python_checks():
    runs = run_lines(read())
    for c in COMMANDS:
        assert c in runs, c


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
