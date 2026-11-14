#!/usr/bin/env python3
"""
Retiring the old Backbone app at agencies/ (#270, done in #288; docs in #289).

PENDING #288: every test here is skipped while viz/agencies/index.html still loads Backbone.
They run, unchanged, the day it becomes the forwarding page.

  python3 -m unittest viz/test_agencies_retired.py    (stdlib only)
  pytest viz/test_agencies_retired.py

What they guard:
  1. agencies/index.html loads none of the old app's libraries, and its script forwards to the
     explorer's Agency budgets view (old hash links can only be read in the browser: GitHub Pages
     never sees the #fragment).
  2. A visitor without JavaScript gets a plain link to the new view.
  3. Links stay relative (the site lives under /New-York-City-Budget/), and the site shell stays.
  4. The CSV download keeps its address; the FAQ and community board pages load no old library.
  5. No page still says the City agency budgets are missing from the MCP.
"""
from __future__ import annotations

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AGENCIES = os.path.join(HERE, "agencies")


def _read(*parts: str) -> str:
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


# The old app's libraries (viz/agencies/lib/ and js/). None may be loaded once it is retired.
OLD_LIBS = ("backbone", "jquery", "highcharts", "datatables", "underscore", "accounting.min",
            "fuse.min", "spin.min", "budget_highcharts", "js/app.js", "modelbinder")

RETIRED = not re.search(r"backbone", _read("agencies", "index.html"), re.I)
PENDING = "PENDING #288: viz/agencies/index.html is still the Backbone app"


def _srcs(html: str) -> list[str]:
    return re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["']""", html, re.I)


@unittest.skipUnless(RETIRED, PENDING)
class AgenciesRetired(unittest.TestCase):
    def test_index_loads_no_old_library(self):
        # FAILS if the forwarding page still pulls in the old app (and its Highcharts licence).
        srcs = [s.lower() for s in _srcs(_read("agencies", "index.html"))]
        self.assertEqual([s for s in srcs if any(lib in s for lib in OLD_LIBS)], [])

    def test_index_forwards_old_routes_to_the_explorer_view(self):
        # FAILS if the script does not send #fund-detail/..., #control-officer-detail/... and
        # #?year=Y to the explorer's Agency budgets view.
        html = _read("agencies", "index.html")
        self.assertIn("../explorer/", html)
        self.assertIn("view=agencies", html)
        for route in ("fund-detail", "control-officer-detail", "year"):
            self.assertIn(route, html, route)
        self.assertRegex(html, r"location\.(replace|assign)\(|location\.href\s*=")

    def test_index_has_a_plain_link_for_no_javascript(self):
        # FAILS if a visitor with scripts off sees a blank page.
        html = _read("agencies", "index.html")
        self.assertRegex(html, r"""<a[^>]+href=["']\.\./explorer/#view=agencies""")

    def test_index_links_are_relative(self):
        # FAILS if a link starts with "/", which leaves /New-York-City-Budget/.
        html = _read("agencies", "index.html")
        urls = re.findall(r"""\b(?:href|src)=["']([^"']+)["']""", html)
        self.assertEqual([u for u in urls if u.startswith("/") and not u.startswith("//")], [])

    def test_index_keeps_the_site_shell(self):
        # FAILS if the forwarding page drops the shared top bar and footer (viz/site_shell.py).
        html = _read("agencies", "index.html")
        self.assertIn("site-shell:top:start", html)
        self.assertIn("site-shell:bottom:start", html)

    def test_csv_download_keeps_its_address(self):
        # FAILS if agencies/data/nyc_budget.csv moves: scripts and spreadsheets fetch it by URL.
        path = os.path.join(AGENCIES, "data", "nyc_budget.csv")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            self.assertTrue(f.readline().startswith("Fund,Department,Department ID,Adopted 2017,Modified 2017"))

    def test_other_agency_pages_load_no_old_library(self):
        # FAILS if the FAQ or the community board page still depends on the retired libraries.
        for page in ("faq.html", "boards.html"):
            if not os.path.exists(os.path.join(AGENCIES, page)):
                continue
            srcs = [s.lower() for s in _srcs(_read("agencies", page))]
            self.assertEqual([s for s in srcs if any(lib in s for lib in OLD_LIBS)], [], page)

    def test_no_page_says_agency_budgets_are_not_in_the_mcp(self):
        # FAILS if viz/mcp.html (or another page) still says the MCP lacks agency budgets (#289).
        for page in ("index.html", "about.html", "mcp.html"):
            self.assertNotRegex(_read(page), r"agency budgets[^<.]*not in the MCP", page)


if __name__ == "__main__":
    unittest.main()
