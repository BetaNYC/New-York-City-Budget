#!/usr/bin/env python3
"""
Regression tests for the GitHub Pages site in viz/ after the 2.0.0 retirement.

Dual-mode like test_schedulec_cleanup.py: `python3 viz/test_pages_site.py` (stdlib only) or
`pytest viz/test_pages_site.py`.

What these guard (each would have failed before the change that introduced it):
  1. The site root (index.html) is the retirement notice: it loads no data file, no script
     but its own inline one, and no look-at-cook asset, so it cannot present PDF-derived figures.
  2. It states the 2.0 coverage gaps (FY2010 disclosure, FY2018 capital) and links to the
     retired copy.
  3. The retired explorer (legacy.html) carries the retired banner above everything else, is
     marked noindex, and its title and logo say retired.
  4. Every local file legacy.html and the app load exists (the move from index.html broke
     nothing), and the breadcrumb no longer points at "/".
"""
from __future__ import annotations

import os
import re
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


class _Refs(HTMLParser):
    """Collect script srcs, stylesheet hrefs, img srcs, and inline script bodies."""

    def __init__(self):
        super().__init__()
        self.scripts, self.styles, self.imgs, self.inline = [], [], [], []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            if a.get("src"):
                self.scripts.append(a["src"])
            else:
                self._in_script = True
        elif tag == "link" and "stylesheet" in (a.get("rel") or ""):
            self.styles.append(a.get("href"))
        elif tag == "img" and a.get("src"):
            self.imgs.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False

    def handle_data(self, data):
        if self._in_script:
            self.inline.append(data)


def _refs(name):
    p = _Refs()
    p.feed(_read(name))
    return p


def test_index_is_the_retirement_notice_and_loads_no_data():
    html = _read("index.html")
    r = _refs("index.html")
    assert r.scripts == [], f"index.html must load no external script: {r.scripts}"
    assert r.styles == [], f"index.html must load no stylesheet file: {r.styles}"
    assert "schedule_c.csv" not in html and "app.js" not in html
    assert 'id="retired-notice"' in html
    assert "do not cite figures" in html.lower()
    # The only inline script reads the hash and fills one link; it fetches nothing.
    js = "".join(r.inline)
    assert not re.search(r"\b(fetch|XMLHttpRequest|\$\.|ajax|import)\b", js), js


def test_index_states_the_gaps_and_links_to_the_retired_copy():
    html = _read("index.html")
    assert "FY2010 is not included" in html
    assert "FY2018 is missing" in html
    assert 'href="legacy.html"' in html
    assert "@betanyc/nyc-budget-mcp" in html


def test_legacy_page_is_marked_retired():
    html = _read("legacy.html")
    banner = html.find('id="retired-banner"')
    header = html.find("id='header'")
    assert banner != -1, "legacy.html lost its retired banner"
    assert banner < header, "the banner must come before the explorer's header"
    assert '<meta name="robots" content="noindex">' in html
    assert re.search(r"<title>RETIRED", html)
    assert "NYC Council Discretionary Funding (retired)" in html


def test_every_local_asset_legacy_loads_exists():
    r = _refs("legacy.html")
    local = [u for u in r.scripts + r.styles + r.imgs if u and not re.match(r"^(https?:)?//", u)]
    assert local, "premise: legacy.html loads local assets"
    missing = [u for u in local if not os.path.exists(os.path.join(HERE, u))]
    assert not missing, f"missing: {missing}"
    app = _read(os.path.join("js", "app.js"))
    m = re.search(r"dataSource\s*=\s*'([^']+)'", app)
    assert m and os.path.exists(os.path.join(HERE, m.group(1))), "app.js data file"
    assert '<a href="/">' not in app, 'breadcrumb must not point at "/" (the notice since 2.0.0)'


def _run_standalone():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
