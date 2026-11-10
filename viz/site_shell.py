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
        "revised": "2026-11-09",
    },
    {
        "path": "agencies/index.html", "root": "../", "current": "agencies", "skip": "content",
        "source": AGENCY_SOURCE, "revised": "2026-11-09",
    },
    {
        "path": "agencies/faq.html", "root": "../", "current": "agencies", "skip": "content",
        "source": AGENCY_SOURCE, "revised": "2026-11-09",
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

NAV = [
    ("home", "", "Home"),
    ("agencies", "agencies/", "City agency budgets"),
    ("council", "explorer/", "Council discretionary funding"),
    ("which", "#which-tool", "Which tool answers my question?"),
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
  .bnyc-shell ul a { font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 700; }
  .bnyc-shell a { color: #FFFFFF; }
  .bnyc-shell a:focus-visible { outline: 3px solid #B8D6FF; outline-offset: 2px; }
  .bnyc-shell-foot a:focus-visible, .bnyc-skip:focus-visible { outline: 3px solid #2359a8; outline-offset: 2px; }
  .bnyc-shell a[aria-current="page"] { text-decoration-thickness: 3px; text-underline-offset: 4px; }
  .bnyc-shell-foot { background: #EEF4FF; color: #414141; border-top: 1px solid #949494; font-size: 14px; margin-top: 2rem; }
  .bnyc-shell-foot-in { display: block; padding: 1rem 1.25rem; }
  .bnyc-shell-foot p { margin: 0.3rem 0; }
  .bnyc-shell-foot a { color: #2359a8; }
  @media (max-width: 600px) { .bnyc-shell-in { padding: 0.4rem 1.25rem 0.2rem; } .bnyc-shell ul { gap: 0 1.1rem; } .bnyc-shell ul a { display: inline-flex; align-items: center; min-height: 44px; } }
</style>"""

TOP_START, TOP_END = "<!-- site-shell:top:start (written by viz/site_shell.py; do not edit) -->", "<!-- site-shell:top:end -->"
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
        '    <ul>',
        *items,
        '    </ul>',
        '  </div>',
        '</nav>',
        TOP_END,
    ])


def bottom_block(page: dict) -> str:
    return "\n".join([
        BOT_START,
        '<div class="bnyc-shell-foot" role="region" aria-label="About this data">',
        '  <div class="bnyc-shell-foot-in">',
        f'    <p><strong>Fiscal year.</strong> {html.escape(FISCAL_YEAR)}</p>',
        f'    <p><strong>Source.</strong> {page["source"]}</p>',
        f'    <p><strong>Last revised:</strong> {page["revised"]}. Built by <a href="https://beta.nyc">BetaNYC</a>. '
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
