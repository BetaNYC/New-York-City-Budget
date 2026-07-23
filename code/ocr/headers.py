"""
Stage 5 -- map a chart's header row onto canonical field names.

FY09 charts come in two shapes:

  long  (Charts 1-3, local / aging / youth discretionary)
        Member | Organization | EIN Number | Agency | Amount | Agy # | U/A |
        Fiscal Conduit/Sponsoring Organization | Fiscal Conduit EIN | * | Status
  short (Charts 4+, per-initiative)
        Organization | EIN Number | Agency | Amount | Agy # | U/A | *

so column positions cannot be hardcoded. They are resolved by fuzzy-matching the OCR'd
header text against a canonical vocabulary.

The one rule that matters: **if a required column does not map, the page is flagged for
review -- never guessed positionally.** A silently mis-assigned column would put real
dollar amounts under the wrong heading, which is exactly the failure mode this whole
grid-based approach exists to avoid.
"""
import re
from difflib import SequenceMatcher

# canonical field -> header spellings seen in the source documents
ALIASES = {
    "member": ["member", "council member", "borough", "borough/member", "boro"],
    "organization": ["organization", "organization name", "organizaton"],
    "ein": ["ein number", "ein", "ein #", "ein no"],
    "agency": ["agency"],
    "amount": ["amount", "amount ($)"],
    "agy_num": ["agy #", "agy num", "agency #", "agy"],
    "ua": ["u/a", "ua", "u a"],
    "conduit_org": ["fiscal conduit/sponsoring organization", "fiscal conduit",
                    "sponsoring organization", "fiscal conduit/sponsoring org"],
    "conduit_ein": ["fiscal conduit ein", "conduit ein"],
    "status": ["status (council, moc, etc)", "status", "status (council, moc, etc.)"],
    "source": ["source"],
    "purpose": ["purpose", "purpose of funds", "purpose of funds changes"],
}

# The unlabelled asterisk column (a prequalification-pending marker) has no header text.
STAR = "star"
STAR_MAX_WIDTH_FRAC = 0.035     # it is the narrowest column on the page by a wide margin

MATCH_THRESHOLD = 0.72          # below this we decline to guess

# Without these a row is not an award row, so a chart missing any of them is unusable.
REQUIRED = ("organization", "ein", "amount")


def normalize(s):
    """Fold the header text to a comparable form. OCR routinely turns '#' into 'tt'/'ff'
    and '/' into '1', so those are normalized away before matching rather than enumerated
    as aliases."""
    s = (s or "").lower()
    s = s.replace("#", " num ").replace("tt", " num ").replace("&", " and ")
    s = re.sub(r"[^a-z0-9/ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _score(text, alias):
    a, b = normalize(text), normalize(alias)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # A long header truncated by a tight crop ("fiscal conduit/sponsoring" for the full
    # phrase) should still match its alias, so reward a clean prefix/containment.
    if a.startswith(b) or b.startswith(a):
        return max(0.9, SequenceMatcher(None, a, b).ratio())
    return SequenceMatcher(None, a, b).ratio()


def best_match(text):
    """(canonical, score) for the closest vocabulary entry."""
    best, best_score = None, 0.0
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            s = _score(text, alias)
            if s > best_score:
                best, best_score = canonical, s
    return best, best_score


class HeaderMapping:
    """Resolved column layout for one chart shape."""

    def __init__(self, columns, unmapped, ambiguous):
        self.columns = columns        # {canonical: column index}
        self.unmapped = unmapped      # [(idx, raw_text, best_guess, score)]
        self.ambiguous = ambiguous    # [(idx, canonical, score)] losers of a duplicate match

    @property
    def missing(self):
        return [c for c in REQUIRED if c not in self.columns]

    @property
    def ok(self):
        return not self.missing

    def get(self, canonical):
        return self.columns.get(canonical)

    def signature(self):
        """Stable key for this layout, so a chart's continuation pages reuse the mapping
        instead of re-deriving it (and possibly disagreeing) page by page."""
        return tuple(sorted(self.columns.items()))

    def __repr__(self):
        cols = ", ".join(f"{k}={v}" for k, v in sorted(self.columns.items(), key=lambda kv: kv[1]))
        return f"<HeaderMapping {cols}{' MISSING=' + ','.join(self.missing) if self.missing else ''}>"


def map_header(texts, widths=None, page_width=None, threshold=MATCH_THRESHOLD):
    """Map header-row cell texts to canonical fields.

    `widths` and `page_width` are optional and used only to recognize the unlabelled
    asterisk column by its distinctive narrowness.
    """
    scored = []
    for idx, text in enumerate(texts):
        canonical, score = best_match(text)
        scored.append((idx, text, canonical, score))

    # Resolve each canonical to its single best column; a runner-up that also matched
    # (e.g. 'Fiscal Conduit EIN' pulling on 'ein') is recorded as ambiguous, not silently
    # dropped, so the report can show why a column went unmapped.
    claims = {}
    for idx, text, canonical, score in scored:
        if canonical is None or score < threshold:
            continue
        prev = claims.get(canonical)
        if prev is None or score > prev[1]:
            claims[canonical] = (idx, score)

    columns = {c: idx for c, (idx, _) in claims.items()}
    taken = set(columns.values())

    unmapped, ambiguous = [], []
    for idx, text, canonical, score in scored:
        if idx in taken:
            continue
        if canonical is not None and score >= threshold:
            ambiguous.append((idx, canonical, round(score, 3)))
            continue
        if _looks_like_star(text, idx, widths, page_width):
            columns[STAR] = idx
            taken.add(idx)
            continue
        unmapped.append((idx, text, canonical, round(score, 3)))

    return HeaderMapping(columns, unmapped, ambiguous)


def _looks_like_star(text, idx, widths, page_width):
    t = (text or "").strip()
    if t and t not in {"*", "**", ".", "-", "'", "+"}:
        return False
    if widths is None or page_width is None or idx >= len(widths):
        return not t          # an empty header with no width evidence: assume the marker
    return widths[idx] <= STAR_MAX_WIDTH_FRAC * page_width
