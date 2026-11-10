#!/usr/bin/env python3
"""
site_shell.py — the shared top bar and footer of every page on the GitHub Pages site (#267).

The site has two halves, City agency budgets (agencies/) and Council discretionary funding
(explorer/), plus the front page and the frozen legacy.html. Each page keeps its own design; this
script writes the same two blocks into each one:

  top     a skip link and a "NYC budget data" nav bar that links every page to every other
  bottom  a footer that states the fiscal year, the page's source and data date, and when the
          page was last revised

The blocks sit between marker comments, so the script replaces only its own text. Paths are
relative (./, ../), because the site lives under /New-York-City-Budget/. The style is inline in
each block: the front page loads no stylesheet file (test_pages_site.py), and the explorer's page
is bundled by Vite.

Stdlib only.

  python3 viz/site_shell.py           # write the blocks into every page
  python3 viz/site_shell.py --check   # exit 1, listing pages whose blocks are missing or stale
"""
from __future__ import annotations

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

FISCAL_YEAR = ("New York City's fiscal year runs July 1 to June 30 and is named for the year it "
               "ends: FY2026 is July 1, 2025 to June 30, 2026.")

AGENCY_SOURCE = ('City agency budgets: NYC Open Data, Expense Budget '
                 '(<a href="https://data.cityofnewyork.us/d/mwzb-yiwb">mwzb-yiwb</a>), the June '
                 'release of each year, through the release of 2026-06-30 (FY2027 adopted). '
                 'FY2027 modified is not yet published.')
COUNCIL_SOURCE = ("Council discretionary funding: the Council's expense funding disclosure and "
                  "capital lists, NYC Open Data, and the tables read from the Council's budget "
                  "PDFs (data release pdf-tables-2026-10-24-260d16e).")

# Each page: its path under viz/, the prefix that reaches the site root from it, which nav item
# is the current page, the id the skip link jumps to, what the footer says about its data, and
# when its text was last revised.
PAGES = [
    {
        "path": "index.html", "root": "./", "current": "home", "skip": "main",
        "source": AGENCY_SOURCE + "<br>" + COUNCIL_SOURCE,
        "revised": "2026-11-10",
    },
    {
        "path": "agencies/index.html", "root": "../", "current": "agencies", "skip": "content",
        "source": AGENCY_SOURCE, "revised": "2026-11-10", "toc": True,
    },
    {
        "path": "agencies/faq.html", "root": "../", "current": "agencies", "skip": "content",
        "source": AGENCY_SOURCE, "revised": "2026-11-10", "toc": True,
    },
    {
        "path": "about.html", "root": "./", "current": "about", "skip": "main",
        "source": AGENCY_SOURCE + "<br>" + COUNCIL_SOURCE + " Every source: the list on this page.",
        "revised": "2026-11-10",
    },
    {
        # The explorer's source page; Vite builds it into explorer/index.html. Its React app has
        # its own header, <main id="main"> and footer, which stay.
        "path": "explorer/index.html", "root": "../", "current": "council", "skip": "main",
        "source": COUNCIL_SOURCE + " The explorer's own footer gives the date of its data build.",
        "revised": "2026-11-09",
    },
    {
        "path": "legacy.html", "root": "./", "current": "legacy", "skip": "content",
        "source": ("Frozen 2026-10-16: an early parser's reading of the Council's Schedule C PDFs. "
                   "Do not cite. Current Council data: the Council explorer."),
        "revised": "2026-11-09",
    },
]

# The site's pages, in the order Noel set on 2026-11-10: the top bar and the contents list on the
# City budget pages both use it.
NAV = [
    ("home", "", "Home"),
    ("council", "explorer/", "Council discretionary funding"),
    ("agencies", "agencies/", "City budget"),
    ("about", "about.html", "About"),
]

STYLE = """<style>
  /* BetaNYC brand tokens: BetaNYC_AI_Workspace archive/betanyc/brand.md (finalized 2026-05-06),
     the same set as grounding-ai-audit-card's assets/css/betanyc.css. No font files are fetched:
     Poppins and Roboto are used when installed, else the system fallback. */
  .bnyc-shell, .bnyc-shell-foot, .bnyc-skip { font-family: "Poppins", "Helvetica Neue", Helvetica, Arial, sans-serif; line-height: 1.5; box-sizing: border-box; }
  .bnyc-skip { position: absolute; left: -10000px; top: 0; z-index: 1000; background: #FFFFFF; color: #2359a8; border: 2px solid #2359a8; padding: 0.5rem 0.9rem; font-weight: 700; }
  .bnyc-skip:focus { left: 0.5rem; top: 0.5rem; }
  .bnyc-shell { background: #2359a8; color: #FFFFFF; font-size: 15px; }
  .bnyc-shell-in, .bnyc-shell-foot-in { max-width: 1230px; margin: 0 auto; padding: 0.6rem 1.25rem; display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem 1.5rem; }
  .bnyc-shell-name { font-weight: 700; color: #FFFFFF; text-decoration: none; margin-right: 0.5rem; }
  .bnyc-shell ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 0.25rem 1.1rem; }
  .bnyc-shell li { margin: 0; padding: 0; }
  .bnyc-shell ul a { font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 700; }
  .bnyc-shell a { color: #FFFFFF; }
  .bnyc-shell a:focus-visible { outline: 3px solid #B8D6FF; outline-offset: 2px; }
  .bnyc-shell-foot a:focus-visible, .bnyc-skip:focus-visible { outline: 3px solid #2359a8; outline-offset: 2px; }
  .bnyc-shell a[aria-current="page"] { text-decoration-thickness: 3px; text-underline-offset: 4px; }
  .bnyc-shell-foot { background: #EEF4FF; color: #414141; border-top: 1px solid #949494; font-size: 14px; margin-top: 2rem; }
  .bnyc-shell-foot-in { display: block; padding: 1.75rem 1.25rem 1rem; }
  .bnyc-foot-cols { display: grid; grid-template-columns: 2fr 1fr 1.3fr; gap: 1.5rem 2.5rem; }
  .bnyc-shell-foot h2 { font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; color: #2359a8; margin: 0 0 0.5rem; }
  .bnyc-shell-foot ul { list-style: none; margin: 0; padding: 0; }
  .bnyc-shell-foot li { margin: 0; padding: 0; }
  .bnyc-shell-foot li a { display: inline-flex; align-items: center; min-height: 32px; }
  .bnyc-shell-foot li a[aria-current="page"] { font-weight: 700; }
  .bnyc-foot-line { border-top: 1px solid #949494; margin-top: 1.25rem !important; padding-top: 0.75rem; }
  @media (max-width: 781px) { .bnyc-foot-cols { grid-template-columns: 1fr; } .bnyc-shell-foot li a { min-height: 44px; } }
  .bnyc-shell-foot p { margin: 0.3rem 0; }
  .bnyc-shell-foot a { color: #2359a8; }
  .bnyc-toc { margin: 0.75rem 0 1rem; font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif; }
  .bnyc-toc h2 { font-size: 15px; font-weight: 700; color: #414141; margin: 0 0 0.3rem; text-transform: none; }
  .bnyc-toc ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 0.3rem 0.5rem; }
  .bnyc-toc li { margin: 0; }
  .bnyc-toc a, .bnyc-toc a:visited { display: inline-flex; align-items: center; min-height: 44px; padding: 0 0.9rem; border: 1px solid #2359a8; color: #2359a8; background: #FFFFFF; font-weight: 700; text-decoration: none; }
  .bnyc-toc a:hover { background: #EEF4FF; text-decoration: underline; color: #2359a8; }
  /* !important: a page's own link color (the agency page's "#header a") would otherwise win. */
  .bnyc-toc a[aria-current="page"], .bnyc-toc a[aria-current="page"]:visited, .bnyc-toc a[aria-current="page"]:hover { background: #2359a8; color: #FFFFFF !important; }
  .bnyc-toc a:focus-visible { outline: 3px solid #2359a8; outline-offset: 2px; }
  .bnyc-shell-foot .bnyc-dl { display: inline-block; margin: 0.2rem 0.6rem 0.4rem 0; padding: 6px 24px; background: #2359a8; color: #FFFFFF; text-decoration: none; font-weight: 700; }
  .bnyc-shell-foot .bnyc-dl:hover { background: #1c4785; text-decoration: underline; }
  /* Menu button (burger) below 782px, brand.md's tablet breakpoint. Without JavaScript the
     button stays hidden and the links show as a wrapped row, as before. */
  .bnyc-menu-btn { display: none; margin-left: auto; align-items: center; gap: 0.5rem; min-height: 44px; padding: 0 0.85rem; background: transparent; color: #FFFFFF; border: 1px solid #FFFFFF; border-radius: 0; font: 700 15px "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif; cursor: pointer; }
  .bnyc-menu-btn:hover { background: #1c4785; }
  .bnyc-menu-btn:focus-visible { outline: 3px solid #B8D6FF; outline-offset: 2px; }
  .bnyc-menu-btn svg { width: 20px; height: 20px; }
  @media (max-width: 781px) {
    .bnyc-shell-in { flex-wrap: wrap; }
    .bnyc-shell.bnyc-js .bnyc-menu-btn { display: inline-flex; }
    .bnyc-shell.bnyc-js ul { display: none; }
    .bnyc-shell.bnyc-js ul.bnyc-open { display: flex; flex-direction: column; flex-basis: 100%; gap: 0; padding: 0.25rem 0 0.5rem; border-top: 1px solid #B8D6FF; margin-top: 0.4rem; }
    .bnyc-shell ul a { display: flex; align-items: center; min-height: 44px; }
  }
  @media (max-width: 600px) { .bnyc-shell-in { padding: 0.4rem 1.25rem; } .bnyc-shell ul { gap: 0 1.1rem; } }
</style>"""

# The menu button's behavior: show it, hide the list until it is opened, keep aria-expanded
# true to the state, and close on Escape. Inline (the front page loads no script file); it
# fetches nothing.
SCRIPT = """<script>
(function () {
  var nav = document.querySelector(".bnyc-shell"), btn = nav && nav.querySelector(".bnyc-menu-btn"),
      list = nav && nav.querySelector("ul");
  if (!btn || !list) return;
  nav.classList.add("bnyc-js");
  btn.hidden = false;
  function set(open) { list.classList.toggle("bnyc-open", open); btn.setAttribute("aria-expanded", open ? "true" : "false"); }
  btn.addEventListener("click", function () { set(btn.getAttribute("aria-expanded") !== "true"); });
  nav.addEventListener("keydown", function (e) { if (e.key === "Escape" && btn.getAttribute("aria-expanded") === "true") { set(false); btn.focus(); } });
})();
</script>"""

TOP_START, TOP_END = "<!-- site-shell:top:start (written by viz/site_shell.py; do not edit) -->", "<!-- site-shell:top:end -->"
TOC_START, TOC_END = "<!-- site-shell:toc:start (written by viz/site_shell.py; do not edit) -->", "<!-- site-shell:toc:end -->"
BOT_START, BOT_END = "<!-- site-shell:bottom:start (written by viz/site_shell.py; do not edit) -->", "<!-- site-shell:bottom:end -->"


def top_block(page: dict) -> str:
    root = page["root"]
    items = []
    for key, href, label in NAV:
        # The "which tool" table is on the front page: "#which-tool" there, "<root>#which-tool"
        # elsewhere ("./#which-tool" from legacy.html is the front page, not legacy.html).
        target = href if (href.startswith("#") and page["path"] == "index.html") else root + href
        cur = ' aria-current="page"' if key == page["current"] else ""
        items.append(f'      <li><a href="{target}"{cur}>{html.escape(label)}</a></li>')
    return "\n".join([
        TOP_START,
        STYLE,
        f'<a class="bnyc-skip" href="#{page["skip"]}">Skip to content</a>',
        '<nav class="bnyc-shell" aria-label="NYC budget data">',
        '  <div class="bnyc-shell-in">',
        f'    <a class="bnyc-shell-name" href="{root}">BetaNYC · NYC budget data</a>',
        '    <button class="bnyc-menu-btn" type="button" aria-expanded="false" aria-controls="bnyc-menu" hidden>'
        '<svg aria-hidden="true" focusable="false" viewBox="0 0 20 20"><path d="M2 4h16M2 10h16M2 16h16" '
        'stroke="currentColor" stroke-width="2" fill="none"/></svg>Menu</button>',
        '    <ul id="bnyc-menu">',
        *items,
        '    </ul>',
        '  </div>',
        '</nav>',
        SCRIPT,
        TOP_END,
    ])


def _nav_target(page: dict, href: str) -> str:
    return href if (href.startswith("#") and page["path"] == "index.html") else page["root"] + href


def toc_block(page: dict) -> str:
    """The site's pages as a short contents list, under a page's own introduction."""
    items = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == page["current"] else ""
        items.append(f'                <li><a href="{_nav_target(page, href)}"{cur}>{html.escape(label)}</a></li>')
    return "\n".join([
        TOC_START,
        '            <nav class="bnyc-toc" aria-labelledby="bnyc-toc-h">',
        '              <h2 id="bnyc-toc-h">Contents</h2>',
        '              <ul>',
        *items,
        '              </ul>',
        '            </nav>',
        "            " + TOC_END,
    ])


# BetaNYC's own links, in the footer of every page (Noel's 2026-11-10 sketch: "About BetaNYC").
BETANYC_LINKS = [
    ("https://www.beta.nyc/featured-tools/ai-tools-for-nyc-democracy/", "Our MCP servers: AI tools for NYC's democracy"),
    ("https://www.beta.nyc/about/ai-policy/", "Our AI policy"),
    ("https://www.beta.nyc/betabuilders/", "Join BetaBuilders"),
]


def bottom_block(page: dict) -> str:
    """The footer: three columns, as on beta.nyc (brand.md: a column footer), stacked on a phone.
    The data (download, fiscal year, source), this site (every page), About BetaNYC; then a line
    with the date the page's text was last revised."""
    root = page["root"]
    site = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == page["current"] else ""
        site.append(f'          <li><a href="{_nav_target(page, href)}"{cur}>{html.escape(label)}</a></li>')
    beta = [f'          <li><a href="{u}">{html.escape(t)}</a></li>' for u, t in BETANYC_LINKS]
    return "\n".join([
        BOT_START,
        '<div class="bnyc-shell-foot" role="region" aria-label="About this site">',
        '  <div class="bnyc-shell-foot-in">',
        '    <div class="bnyc-foot-cols">',
        '      <section class="bnyc-foot-data" aria-labelledby="bnyc-foot-h-data">',
        '        <h2 id="bnyc-foot-h-data">The data</h2>',
        f'        <p><a class="bnyc-dl" href="{root}about.html#download">Download the data</a></p>',
        f'        <p><strong>Fiscal year.</strong> {html.escape(FISCAL_YEAR)}</p>',
        f'        <p><strong>Source.</strong> {page["source"]} <a href="{root}about.html#sources">Every source</a>.</p>',
        '      </section>',
        '      <section aria-labelledby="bnyc-foot-h-site">',
        '        <h2 id="bnyc-foot-h-site">This site</h2>',
        '        <ul>',
        *site,
        '        </ul>',
        '      </section>',
        '      <section aria-labelledby="bnyc-foot-h-beta">',
        '        <h2 id="bnyc-foot-h-beta">About BetaNYC</h2>',
        "        <p>New York's civic technology and open-data community. We built and maintain this site.</p>",
        '        <ul>',
        *beta,
        '          <li>This site\'s MCP server: <a href="https://www.npmjs.com/package/@betanyc/nyc-budget-mcp">@betanyc/nyc-budget-mcp</a></li>',
        '        </ul>',
        '      </section>',
        '    </div>',
        f'    <p class="bnyc-foot-line"><strong>Last revised:</strong> {page["revised"]}. Built by <a href="https://beta.nyc">BetaNYC</a>. '
        '<a href="https://github.com/BetaNYC/New-York-City-Budget">Code and data on GitHub</a> · '
        '<a href="https://github.com/BetaNYC/New-York-City-Budget/issues">Report a problem</a>.</p>',
        '  </div>',
        '</div>',
        BOT_END,
    ])


def _replace_or_insert(text: str, start: str, end: str, block: str, anchor: str, after: bool) -> str:
    pat = re.compile(re.escape(start.split(" (")[0]) + r".*?" + re.escape(end), re.S)
    if pat.search(text):
        return pat.sub(lambda _m: block, text, count=1)
    m = re.search(anchor, text)
    if not m:
        raise SystemExit(f"site_shell: no {anchor!r} to place the block at")
    i = m.end() if after else m.start()
    return text[:i] + ("\n" if after else "") + block + ("\n" if not after else "\n") + text[i:]


def render(page: dict, text: str) -> str:
    text = _replace_or_insert(text, TOP_START, TOP_END, top_block(page), r"<body[^>]*>", after=True)
    text = _replace_or_insert(text, BOT_START, BOT_END, bottom_block(page), r"\s*</body>", after=False)
    if page.get("toc"):
        # Placed by hand under the page's introduction; the script refreshes what is between.
        text = _replace_or_insert(text, TOC_START, TOC_END, toc_block(page), r"(?!)", after=True)
    return text


def problems(page: dict, text: str) -> list[str]:
    out = []
    if render(page, text) != text:
        out.append("blocks missing or stale (run python3 viz/site_shell.py)")
    sid = page["skip"]
    if page["path"] == "explorer/index.html":
        app = open(os.path.join(HERE, "explorer", "src", "App.jsx"), encoding="utf-8").read()
        if f'id="{sid}"' not in app:
            out.append(f'skip target id="{sid}" not in explorer/src/App.jsx')
    elif not re.search(rf"""id=["']{re.escape(sid)}["']""", text):
        out.append(f'skip target id="{sid}" not in the page')
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    bad = 0
    for page in PAGES:
        path = os.path.join(HERE, page["path"])
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if check:
            for p in problems(page, text):
                print(f"{page['path']}: {p}")
                bad += 1
        else:
            new = render(page, text)
            if new != text:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                print(f"wrote {page['path']}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
