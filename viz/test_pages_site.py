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
  5. The banner says, in real text, that the page is frozen, why its figures are wrong, and not
     to cite them; it has a heading, and it links to the new data (front page, repo, MCP).
  6. The notice links once to the in-browser explorer (explorer/), whose source and site
     assembly script exist in viz/explorer/.
  7. The City agency budgets explorer (agencies/, from nyc-budget-viz, #265) is in place: every
     local file its pages load exists, its data file exists, and no link or asset path starts
     with "/" (the site lives under /New-York-City-Budget/, so "/" leaves it).
  8. The Look at Cook leftovers stay gone (#266): no "Who controls it?" view, NYC labels instead
     of "Fund"/"Department", no empty description panel, the DataMade credit line, no empty
     hidden image, no Cook County images, and sharing tags on both pages.
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
    """Collect script srcs, stylesheet hrefs, img srcs, every href and src, and inline script
    bodies."""

    def __init__(self):
        super().__init__()
        self.scripts, self.styles, self.imgs, self.inline = [], [], [], []
        self.urls = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            if a.get(k) is not None:
                self.urls.append(a[k])
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


def test_index_links_to_the_explorer():
    html = _read("index.html")
    assert html.count('href="explorer/"') == 1, "one link from the notice to the explorer"
    # The explorer's source lives in viz/explorer/; the deploy builds it into explorer/ beside
    # this page (.github/workflows/deploy-viz.yml, viz/explorer/scripts/assemble-site.mjs).
    assert os.path.exists(os.path.join(HERE, "explorer", "index.html"))
    assert os.path.exists(os.path.join(HERE, "explorer", "scripts", "assemble-site.mjs"))


def test_legacy_page_is_marked_retired():
    html = _read("legacy.html")
    banner = html.find('id="retired-banner"')
    header = html.find("id='header'")
    assert banner != -1, "legacy.html lost its retired banner"
    assert banner < header, "the banner must come before the explorer's header"
    assert '<meta name="robots" content="noindex">' in html
    assert re.search(r"<title>RETIRED", html)
    assert "NYC Council Discretionary Funding (retired)" in html


def _banner(html):
    start = html.find('id="retired-banner"')
    end = html.find("id='header'")
    return html[start:end]


def test_legacy_banner_says_frozen_do_not_cite_and_links_to_new_data():
    banner = _banner(_read("legacy.html"))
    text = re.sub(r"<[^>]+>", " ", banner)
    text = re.sub(r"\s+", " ", text).lower()
    assert re.search(r"<h2[^>]*>", banner), "the banner needs a real heading"
    # A landmark, not a live region: the banner is static, so role="alert" would be announced
    # assertively and often twice (review S6, 2026-10-17).
    assert 'role="region"' in banner and 'aria-labelledby="retired-banner-heading"' in banner
    assert 'role="alert"' not in banner
    assert "frozen" in text and "no longer updated" in text
    assert "do not cite" in text
    assert "found errors" in text
    assert "spreadsheets" in text and "nyc open data" in text
    assert 'href="./"' in banner, "link to the front page"
    assert "github.com/BetaNYC/New-York-City-Budget" in banner, "link to the repo data"
    assert "@betanyc/nyc-budget-mcp" in banner, "link to the MCP"
    assert "<img" not in banner, "the banner must be text, not an image"
    assert html_count_banners(_read("legacy.html")) == 1, "one banner, not two"


def html_count_banners(html):
    return html.count('id="retired-banner"')


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


AGENCY_PAGES = [os.path.join("agencies", "index.html"), os.path.join("agencies", "faq.html")]


def _is_external(u):
    return bool(re.match(r"^([a-z]+:|//|#)", u))


def test_agencies_explorer_is_in_place_and_loads_only_files_that_exist():
    for page in AGENCY_PAGES:
        r = _refs(page)
        local = [u for u in r.scripts + r.styles + r.imgs if u and not _is_external(u)]
        assert local, f"premise: {page} loads local assets"
        missing = [u for u in local if not os.path.exists(os.path.join(HERE, "agencies", u.split("?")[0]))]
        assert not missing, f"{page} loads missing files: {missing}"
    app = _read(os.path.join("agencies", "js", "app.js"))
    m = re.search(r"dataSource\s*=\s*'([^']+)'", app)
    assert m, "agencies/js/app.js names its data file"
    assert not m.group(1).startswith("/"), f"dataSource must be relative: {m.group(1)}"
    assert os.path.exists(os.path.join(HERE, "agencies", m.group(1))), m.group(1)
    tmpl = _read(os.path.join("agencies", "js", "budget_helpers.js"))
    t = re.search(r"tmpl_dir\s*=\s*'([^']+)'", tmpl)
    assert t and os.path.isdir(os.path.join(HERE, "agencies", t.group(1))), "chart templates"


def test_agencies_explorer_uses_relative_links_only():
    # The site is served from /New-York-City-Budget/. A path starting with "/" (not "//") points
    # at betanyc.github.io itself and breaks. nyc-budget-viz's index.html had href='/faq.html'.
    for page in AGENCY_PAGES:
        bad = [u for u in _refs(page).urls if u.startswith("/") and not u.startswith("//")]
        assert not bad, f"{page} has root-absolute links: {bad}"
    for js in ("app.js", "budget_helpers.js"):
        text = _read(os.path.join("agencies", "js", js))
        assert not re.search(r"""href=['"]/[^/]""", text), f"agencies/js/{js} writes a root-absolute link"


def _agency_text(*names):
    return "\n".join(_read(os.path.join("agencies", *n.split("/"))) for n in names)


def test_agencies_who_controls_it_view_is_gone():
    views = _agency_text("js/views/mainChart.html")
    assert "Who controls it" not in views and "breakdown-choice" not in views
    app = _read(os.path.join("agencies", "js", "app.js"))
    assert "'Control Officer Slug'" not in app and '"Control Officer": [' not in app
    # Old links keep working: the route stays, and sends them to the same agency view.
    assert re.search(r"controlDetailRoute: function\(topName, secondName\)\{\s*var fragment = 'fund-detail/'", app)
    assert "fund-detail/:topName" in app, "the agency route (and every existing link) stays"
    faq = _read(os.path.join("agencies", "faq.html"))
    assert "richer second dimension" not in faq and "control officer" not in faq.lower()


def test_agencies_labels_are_nyc_words():
    app = _read(os.path.join("agencies", "js", "app.js"))
    assert "'Fund': 'Agency'" in app and "'Department': 'Unit of appropriation'" in app
    assert '<span id="secondary-title">Agency</span>' in _read(os.path.join("agencies", "index.html"))
    assert "budgetLabel(" in _agency_text("js/views/breakdownDetail.html")
    search = _agency_text("js/views/search.html")
    assert "Department search" not in search and "Search agencies and units" in search
    faq = _read(os.path.join("agencies", "faq.html"))
    assert 'What are "agency" and "unit of appropriation"?' in faq
    assert 'What are "Fund" and "Department" in this tool?' not in faq


def test_agencies_no_empty_description_panel_or_columns():
    detail = _agency_text("js/views/breakdownDetail.html")
    assert "description" not in detail and "Read more on their website" not in detail
    header = _read(os.path.join("agencies", "data", "nyc_budget.csv")).split("\n", 1)[0]
    for col in ("Control Officer", "Short Title", "Link to Website", "Department Description"):
        assert col not in header, col


def test_agencies_credit_hidden_image_cook_images_and_sharing():
    for page in AGENCY_PAGES:
        html = _read(page)
        assert "Built by <a" not in html, f"{page}: old 'Built by DataMade' line"
        assert "Original code by <a href=\"https://datamade.us\">DataMade</a>" in html
        assert 'look-at-cook">Look at Cook</a>, MIT License' in html
        assert not re.search(r"<img[^>]*src=(\"\"|'')", html), f"{page}: empty img src"
        assert 'id="readme"' not in html, f"{page}: hidden readme leftover"
        for tag in ('property="og:image"', 'property="og:url"', 'rel="canonical"'):
            assert tag in html, f"{page} lacks {tag}"
        url = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
        assert url.startswith("https://betanyc.github.io/New-York-City-Budget/agencies/"), url
    assert os.path.exists(os.path.join(HERE, "agencies", "images", "og-image.png"))
    for gone in ("logo.png", "logo-print.png", "look-at-cook-screenshot.jpg", "signature.png"):
        assert not os.path.exists(os.path.join(HERE, "agencies", "images", gone)), gone


def test_agencies_faq_loads_no_app_and_links_the_csv():
    # The FAQ has no chart. Loading app.js there logged "rootEl must be specified" (#266).
    r = _refs(os.path.join("agencies", "faq.html"))
    assert r.scripts == [] or all("html5shiv" in u or "respond" in u for u in r.scripts), r.scripts
    assert 'id="download-button" class="btn btn-primary" href="data/nyc_budget.csv"' in _read(
        os.path.join("agencies", "faq.html"))


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
