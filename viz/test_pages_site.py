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
  3. legacy.html, the retired first explorer, is a short "this moved" page in the site shell
     (#304): noindex, one main and one h1, no look-at-cook asset, links to the explorer and the
     data sources.
  4. It forwards the old app's links (#fund-detail/..., #control-officer-detail/..., #?year=Y)
     into the explorer's Schedule C search, reading only the old app's own data file.
  5. (Folded into 3 since #304: the old retired banner went with the app.)
  6. The notice links once to the in-browser explorer (explorer/), whose source and site
     assembly script exist in viz/explorer/.
  7. The City agency budgets pages (agencies/): since #288 agencies/index.html forwards old links
     to the explorer's view (viz/test_agencies_retired.py checks the forwarding). Every local file
     the pages load exists, the data file stays, and no link or asset path starts with "/" (the
     site lives under /New-York-City-Budget/, so "/" leaves it).
  8. The Look at Cook leftovers stay gone (#266): no "Who controls it?" in the FAQ, NYC labels,
     no Cook County columns in the CSV, the DataMade credit in the FAQ, no empty hidden image, no
     Cook County images, and sharing tags on both pages.
  9. One site shell (#267): every page carries the same top bar and footer (site_shell.py
     --check), reaches every other page in one click, and states the fiscal year, its source
     and when it was last revised.
"""
from __future__ import annotations

import importlib.util
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
    # The data gaps moved to the About page with the rest of the detail (2026-11-10); the front
    # page keeps the link to the frozen copy and to the MCP server.
    html = _read("index.html")
    about = _read("about.html")
    assert "FY2010 is not included" in about
    # FY2018 Council capital is PDF-derived since #202, and the page says where it comes from.
    assert "FY2018 has no workbook and is not on NYC Open Data" in about
    assert 'href="legacy.html"' in html
    # The front page links the MCP's own page, which names the package (2026-11-10).
    assert 'href="mcp.html"' in html and "@betanyc/nyc-budget-mcp" in _read("mcp.html")
    assert 'href="about.html"' in html


def test_index_links_to_the_explorer():
    html = _read("index.html")
    # The front page has two doors (#267): the Council explorer and the agency explorer, each
    # linked from its door and from "Use it" (and the site bar, written as ./explorer/).
    assert html.count('href="explorer/"') >= 1, "the front page links to the Council explorer"
    assert html.count('href="explorer/#view=agencies"') >= 1, "the front page links to City agency budgets (#288)"
    # The explorer's source lives in viz/explorer/; the deploy builds it into explorer/ beside
    # this page (.github/workflows/deploy-viz.yml, viz/explorer/scripts/assemble-site.mjs).
    assert os.path.exists(os.path.join(HERE, "explorer", "index.html"))
    assert os.path.exists(os.path.join(HERE, "explorer", "scripts", "assemble-site.mjs"))


# The look-at-cook app's files. legacy.html loads none of them since it was retired (#304).
OLD_APP = ("backbone", "jquery", "highcharts", "datatables", "underscore", "accounting.min", "fuse.min",
           "spin.min", "budget_highcharts", "budget_helpers", "js/app.js", "modelbinder", "bootstrap")


def test_legacy_is_a_this_moved_page():
    # #304 (Noel, 2026-11-13): legacy.html is a short page in the site shell, not the frozen app.
    html = _read("legacy.html")
    r = _refs("legacy.html")
    assert '<meta name="robots" content="noindex">' in html
    assert r.scripts == [] and r.styles == [], "no script or stylesheet file: the page is self-contained"
    assert not [u for u in r.urls if any(lib in u.lower() for lib in OLD_APP)], "no look-at-cook asset"
    assert html.count("<main") == 1 and html.count("<h1") == 1
    assert "site-shell:top:start" in html and "site-shell:bottom:start" in html
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).lower()
    assert "retired" in text and "october 16, 2026" in text and "do not cite" in text
    # Links to Council discretionary funding and to the data sources, relative to the site.
    assert 'href="explorer/"' in html
    assert 'href="about.html#sources"' in html
    assert not [u for u in r.urls if u.startswith("/") and not u.startswith("//")]


def test_legacy_forwards_old_links_into_the_explorer():
    # Old links can only be read in the browser (GitHub Pages never sees the #fragment); the
    # script maps them (viz/explorer/e2e/legacy.spec.js follows real ones).
    js = "".join(_refs("legacy.html").inline)
    for route in ("fund-detail", "control-officer-detail", "year="):
        assert route in js, route
    for key in ("view=schedc", "scfy=", "sccat=", "scagency=", "scinit="):
        assert key in js, key
    assert re.search(r"location\.replace\(", js)
    # It reads only the old app's own data, to turn its slugs back into names.
    assert re.findall(r"fetch\(\"([^\"]+)\"\)", js) == ["data/schedule_c.csv"]
    assert os.path.exists(os.path.join(HERE, "data", "schedule_c.csv")), "the old app's data stays (frozen)"
    # No old link: the page shows, and stays put on its own skip link.
    assert 'if (!h || h === "content") return;' in js


AGENCY_PAGES = [os.path.join("agencies", "index.html"), os.path.join("agencies", "faq.html")]
BOARDS_PAGE = os.path.join("agencies", "boards.html")


def _is_external(u):
    return bool(re.match(r"^([a-z]+:|//|#)", u))


def test_agency_pages_load_only_files_that_exist():
    # #288: agencies/index.html is the forwarding page (no app); the FAQ keeps its stylesheets.
    for page in AGENCY_PAGES:
        r = _refs(page)
        local = [u for u in r.scripts + r.styles + r.imgs if u and not _is_external(u)]
        missing = [u for u in local if not os.path.exists(os.path.join(HERE, "agencies", u.split("?")[0]))]
        assert not missing, f"{page} loads missing files: {missing}"
    assert os.path.exists(os.path.join(HERE, "agencies", "data", "nyc_budget.csv")), "the CSV keeps its address"
    assert not os.path.exists(os.path.join(HERE, "agencies", "js", "app.js")), "the Backbone app is retired (#288)"
    assert not os.path.exists(os.path.join(HERE, "agencies", "lib")), "the old libraries are retired (#288)"


def test_agencies_explorer_uses_relative_links_only():
    # The site is served from /New-York-City-Budget/. A path starting with "/" (not "//") points
    # at betanyc.github.io itself and breaks. nyc-budget-viz's index.html had href='/faq.html'.
    for page in AGENCY_PAGES:
        bad = [u for u in _refs(page).urls if u.startswith("/") and not u.startswith("//")]
        assert not bad, f"{page} has root-absolute links: {bad}"


def _agency_text(*names):
    return "\n".join(_read(os.path.join("agencies", *n.split("/"))) for n in names)


def test_agencies_who_controls_it_view_is_gone():
    # Old #control-officer-detail/ links still land on the agency: the forwarding page (#288).
    fwd = _read(os.path.join("agencies", "index.html"))
    assert "control-officer-detail" in fwd and "fund-detail" in fwd
    faq = _read(os.path.join("agencies", "faq.html"))
    assert "richer second dimension" not in faq and "control officer" not in faq.lower()


def test_agencies_labels_are_nyc_words():
    faq = _read(os.path.join("agencies", "faq.html"))
    assert 'What are "agency" and "unit of appropriation"?' in faq
    assert 'What are "Fund" and "Department" in this tool?' not in faq


def test_agencies_no_empty_description_panel_or_columns():
    header = _read(os.path.join("agencies", "data", "nyc_budget.csv")).split("\n", 1)[0]
    for col in ("Control Officer", "Short Title", "Link to Website", "Department Description"):
        assert col not in header, col


def test_agencies_credit_hidden_image_cook_images_and_sharing():
    faq = _read(os.path.join("agencies", "faq.html"))
    assert "Original code by <a href=\"https://datamade.us\">DataMade</a>" in faq
    assert 'look-at-cook">Look at Cook</a>, MIT License' in faq
    for page in AGENCY_PAGES:
        html = _read(page)
        assert not re.search(r"Built by <a[^>]*datamade", html, re.I), f"{page}: old 'Built by DataMade' line"
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


def _shell():
    import importlib.util
    spec = importlib.util.spec_from_file_location("site_shell", os.path.join(HERE, "site_shell.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_page_has_the_current_site_shell():
    shell = _shell()
    for page in shell.PAGES:
        probs = shell.problems(page, _read(page["path"]))
        assert not probs, (page["path"], probs)


def test_every_page_reaches_every_other_in_one_click():
    shell = _shell()
    # City agency budgets is the explorer's view since #288 (agencies/ forwards old links there).
    site_pages = {"": "index.html", "explorer/#view=agencies": "explorer/index.html", "explorer/": "explorer/index.html",
                  "about.html/": "about.html", "mcp.html/": "mcp.html",
                  "agencies/boards.html/": "agencies/boards.html"}
    for page in shell.PAGES:
        here = os.path.dirname(page["path"])
        top = _read(page["path"]).split(shell.TOP_START.split(" (")[0], 1)[1].split(shell.TOP_END, 1)[0]
        reached = set()
        for href in re.findall(r'href="([^"]+)"', top):
            if href.startswith("#"):
                continue
            target = os.path.normpath(os.path.join(here, href.split("#")[0])).replace(os.sep, "/")
            target = "" if target == "." else target.rstrip("/") + "/"
            frag = href.split("#", 1)[1] if "#" in href else ""
            reached.add(target + "#" + frag if frag.startswith("view=") else target)
        for want in site_pages:
            assert want in reached, f"{page['path']}: no one-click link to {want or 'the front page'}"
        # Every relative link goes somewhere that exists in viz/.
        for want in reached:
            assert os.path.exists(os.path.join(HERE, site_pages.get(want, want))), want


def test_every_page_dates_its_text_and_points_to_the_sources():
    """FAILS if a page's footer loses its last-revised date or its link to the data sources, or
    the About page loses the fiscal year, the sources, or how current the data is. Noel,
    2026-11-10: the sources and the fiscal year live on the About page, not in every footer."""
    shell = _shell()
    for page in shell.PAGES:
        foot = _read(page["path"]).split(shell.BOT_START.split(" (")[0], 1)[1]
        assert re.search(r"Last revised:</strong> [A-Z][a-z]+ \d{1,2}, \d{4}\.", foot), page["path"]
        assert re.search(r'href="[./]*about\.html#sources"', foot), page["path"]
    about = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _read("about.html")))
    assert "runs July 1 to June 30 and is named for the year it ends" in about
    assert "through the release of June 30, 2026" in about
    assert "pdf-tables-2026-10-24-260d16e" in about

def test_about_offers_the_download_and_it_exists():
    """FAILS if the About page's download section, or a file it links, is missing."""
    about = _read("about.html")
    assert 'id="download"' in about
    for href in re.findall(r'href="([^":#]+\.csv)"', about):
        assert os.path.exists(os.path.join(HERE, href)), href

def test_every_footer_has_the_site_and_betanyc():
    """FAILS if a page's footer loses one of its columns (2026-11-10): every page of the site, and
    About BetaNYC with its links."""
    shell = _shell()
    for page in shell.PAGES:
        foot = _read(page["path"]).split(shell.BOT_START.split(" (")[0], 1)[1]
        for h in (">This site<", ">About BetaNYC<"):
            assert h in foot, (page["path"], h)
        for _key, _href, label in shell.NAV:
            assert f">{label}<" in foot, (page["path"], label)
        for url, _t in shell.BETANYC_LINKS:
            assert url in foot, (page["path"], url)


def test_site_nav_order_and_labels():
    """FAILS if the primary nav, top bar or footer, on any page, is not in Noel's order with Noel's
    labels (2026-11-12, #300)."""
    want = ["Home", "City agency budgets", "Community board budgets", "Council discretionary funding", "Budget MCP", "About"]
    shell = _shell()
    assert [label for _k, _h, label in shell.NAV] == want
    for page in shell.PAGES:
        text = _read(page["path"])
        top = text.split('<nav class="bnyc-shell"', 1)[1].split("</nav>", 1)[0]
        foot = text.split(shell.BOT_START.split(" (")[0], 1)[1].split('id="bnyc-foot-h-site"', 1)[1].split("</ul>", 1)[0]
        for where, part in (("top", top), ("footer", foot)):
            got = re.findall(r"<li><a [^>]*>([^<]+)</a></li>", part)
            assert got == want, (page["path"], where, got)

def test_mcp_page_names_every_tool_and_our_other_servers():
    """FAILS if the budget MCP's page (Noel, 2026-11-10) misses a tool the server registers
    (mcp/src), its setup line, or one of BetaNYC's other MCP servers."""
    page = _read("mcp.html")
    src = ""
    for root, _dirs, files in os.walk(os.path.join(HERE, "..", "mcp", "src")):
        for name in files:
            if name.endswith(".ts"):
                with open(os.path.join(root, name), encoding="utf-8") as fh:
                    src += fh.read()
    tools = set(re.findall(r'name: "((?:search|list|compare)_[a-z_]+)"', src))
    assert len(tools) >= 8, tools
    for tool in tools:
        assert f"<code>{tool}</code>" in page, tool
    assert "@betanyc/nyc-budget-mcp@2" in page and "download --pdf-tables" in page
    for repo in ("nyc-checkbook-mcp", "nyc-council-mcp", "nyc-record-mcp", "nyc-311-mcp",
                 "nys-openlegislation-mcp", "ny-data-registry-mcp", "mta-mcp"):
        assert f"https://github.com/BetaNYC/{repo}" in page, repo
    assert 'href="mcp.html"' in _read("index.html")


def test_about_has_the_glossary_and_every_source():
    """FAILS if the About page loses the fiscal year definition, a glossary term, or a dataset the
    repository reads (code/open_data_registry.py)."""
    about = _read("about.html")
    assert 'id="glossary"' in about and 'id="sources"' in about
    assert "runs July 1 to June 30 and is named for the year it ends" in about
    for term in ("fiscal-year", "adopted", "modified", "year-rule", "unit-of-appropriation", "intra-city",
                 "net-and-gross", "schedule-c", "transparency-resolution", "disclosure", "community-board"):
        assert f'id="{term}"' in about, term
    spec = importlib.util.spec_from_file_location(
        "open_data_registry", os.path.join(HERE, "..", "code", "open_data_registry.py"))
    reg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reg)
    for ds in reg.DATASETS:
        assert f"/d/{ds}" in about, f"{ds} not listed on the About page"


def test_no_stale_citywide_total_in_copy():
    for name in ("legacy.html", "README.md", "index.html", os.path.join("agencies", "index.html")):
        assert "$114B" not in _read(name), name


def test_community_board_page_loads_its_csv_relatively_and_offers_the_download():
    # #269: the table reads data/community_boards.csv (code/build_community_boards.py) and
    # offers it for download; relative paths only.
    html = _read(BOARDS_PAGE)
    r = _refs(BOARDS_PAGE)
    assert r.scripts == [] and r.styles == [], "self-contained page"
    assert 'fetch("data/community_boards.csv")' in html
    assert 'href="data/community_boards.csv" download' in html
    assert os.path.exists(os.path.join(HERE, "agencies", "data", "community_boards.csv"))
    bad = [u for u in r.urls if u.startswith("/") and not u.startswith("//")]
    assert not bad, bad
    assert 'href="agencies/boards.html"' in _read("index.html"), "front page links the table"
    assert 'href="boards.html"' in _read(os.path.join("agencies", "index.html"))


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
