"""
Stage 6 -- turn recognized cells into schema rows, validating every value on the way out.

Two commitments shape this module.

**Schema compatibility.** Output is exactly the 16 columns every other Transparency-
Resolution year uses (`parse_transparency_reso.COLS`). `validate_data.py` treats any extra
column as a hard failure, so FY09's extra `Fiscal Conduit` / `Status` columns go to a
sidecar instead (the `fy25_capital_noncity_by_entity.csv` precedent). Text cleanup,
member detection and money parsing are IMPORTED from `parse_transparency_reso.py` rather
than reimplemented, so FY09 rows are shaped by the same rules as FY10-FY27.

**No quiet repair.** OCR is a model reading numbers, and this repo's whole claim rests on
figures being checkable. So the only normalization applied to a numeric cell is of
characters that cannot occur in the target grammar and have exactly one reading -- bracket
variants, stray whitespace. Letter/digit confusions ('O' for '0', 'S' for '$') are NOT
guessed: the cell is flagged and queued for human review with a crop of the actual pixels.
"""
import csv
import os
import re
import sys

_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

import parse_transparency_reso as tr   # noqa: E402  (path set above)

COLS = tr.COLS
CONDUIT_COLS = ["resolution", "chart", "ein", "conduit_organization", "conduit_ein", "status"]
REVIEW_COLS = ["resolution", "page", "row", "column", "raw_text", "confidence", "flag", "crop"]

FISCAL_YEAR = "2009"

EIN_RE = re.compile(r"^\d{2}-?\d{7}$")
AMOUNT_RE = re.compile(r"^\(?\$?\d{1,3}(,\d{3})*(\.\d{2})?\)?$|^\(?\$?\d+(\.\d{2})?\)?$")
CODE_RE = re.compile(r"^\d{3}$")
TOTAL_LABEL = re.compile(r"(?i)\btotal\b")
NAME_SHAPE = re.compile(r"^[A-Za-z][A-Za-z .,'\-]*$")
FOOTNOTE = re.compile(r"(?i)^\s*\*+\s*(indicates|requires)")

DEFAULT_MIN_CONF = 0.80

FLAG_EIN = "ocr:ein"
FLAG_AMOUNT = "ocr:amt"
FLAG_CODE = "ocr:code"
FLAG_AGENCY = "ocr:agency"
FLAG_MEMBER = "ocr:member"
FLAG_LOWCONF = "ocr:lowconf"


def normalize_numeric(text):
    """Unambiguous character folding only -- brackets and whitespace. Anything that could
    change a digit is deliberately left alone for the review queue to adjudicate."""
    t = (text or "").strip()
    t = t.replace("{", "(").replace("[", "(").replace("}", ")").replace("]", ")")
    return re.sub(r"\s+", "", t)


def parse_amount(text):
    """'($3,500.00)' -> -3500. Returns (dollars, ok).

    Whole dollars, matching every other year: the FY10-FY27 parser's `money()` never sees
    cents (the source's text layer splits them off), and cross-year files must stay
    comparable. A non-zero cents value is therefore a red flag, not something to round.
    """
    t = normalize_numeric(text)
    if not t or not AMOUNT_RE.match(t):
        return None, False
    neg = t.startswith("(") and t.endswith(")")
    body = t.strip("()").lstrip("$").replace(",", "")
    if "." in body:
        whole, cents = body.split(".", 1)
        if cents != "00":
            return None, False
        body = whole
    if not body.isdigit():
        return None, False
    v = int(body)
    return (-v if neg else v), True


def parse_ein(text):
    """'13-3608977' -> ('133608977', True). Hyphen dropped, matching the other years."""
    t = normalize_numeric(text)
    if not EIN_RE.match(t):
        return t.replace("-", ""), False
    return t.replace("-", ""), True


def load_agency_vocab(paths):
    """Agency codes actually printed in the Council's own Transparency Resolutions, taken
    from the years already parsed. A real dictionary check -- an OCR'd 'DYGD' fails against
    it, where a regex over uppercase letters would pass."""
    vocab = set()
    for p in paths:
        try:
            with open(p, newline="") as f:
                for row in csv.DictReader(f):
                    a = (row.get("agency") or "").strip()
                    if a:
                        vocab.add(a.upper())
        except (OSError, csv.Error):
            continue
    return vocab


def discover_agency_sources(data_root):
    """All already-parsed transparency CSVs, for load_agency_vocab()."""
    out = []
    for year in sorted(os.listdir(data_root)) if os.path.isdir(data_root) else []:
        d = os.path.join(data_root, year, "transparency-resolutions")
        if not os.path.isdir(d):
            continue
        out.extend(os.path.join(d, f) for f in sorted(os.listdir(d))
                   if f.endswith("_transparency_all.csv"))
    return out


class Cell:
    """One recognized grid cell: its text, its confidence, and where it is on the page."""

    __slots__ = ("text", "conf", "rect")

    def __init__(self, text="", conf=1.0, rect=None):
        self.text = text
        self.conf = conf
        self.rect = rect

    def __bool__(self):
        return bool(self.text.strip())


def row_cells(cells, mapping, r, ncols):
    """{canonical: Cell} for grid row r."""
    out = {}
    for canonical, c in mapping.columns.items():
        if c < ncols:
            out[canonical] = cells.get((r, c), Cell())
    return out


def is_total_row(rc):
    """A chart's printed total: an amount with no organization and no EIN beside it.

    These matter -- FY09 is the only Transparency-Resolution year that prints totals at
    all, so they are the pipeline's one true reconciliation check.
    """
    amount = rc.get("amount", Cell())
    if not amount:
        return False
    if rc.get("organization", Cell()) and not TOTAL_LABEL.search(rc["organization"].text):
        return False
    return not rc.get("ein", Cell())


def is_blank_row(rc):
    return not any(bool(c) for c in rc.values())


def is_footnote_row(rc):
    return any(FOOTNOTE.match(c.text) for c in rc.values() if c.text)


class Assembler:
    """Builds schema rows for one resolution, accumulating flags and the review queue."""

    def __init__(self, resolution, date, roster, agency_vocab,
                 min_conf=DEFAULT_MIN_CONF, crop_dir=None, gray_provider=None):
        self.resolution = resolution
        self.date = date
        self.roster = roster
        self.agency_vocab = agency_vocab
        self.min_conf = min_conf
        self.crop_dir = crop_dir
        self.gray_provider = gray_provider    # page_no -> image, for review crops
        self.rows = []
        self.conduits = []
        self.reviews = []
        self.totals = []                      # printed chart totals, for reconciliation
        self.member_hits = 0                  # roster agreement, reported as a QA signal
        self.member_misses = 0

    # -- review queue -------------------------------------------------------------
    def _queue(self, page, r, column, cell, flag):
        crop = ""
        if self.crop_dir and cell.rect and self.gray_provider:
            gray = self.gray_provider(page)
            if gray is not None:
                from . import recognize
                path = os.path.join(self.crop_dir,
                                    f"r{self.resolution:02d}-p{page:03d}-row{r:02d}-{column}.png")
                crop = recognize.save_crop(gray, cell.rect, path)
        self.reviews.append({
            "resolution": self.resolution, "page": page, "row": r, "column": column,
            "raw_text": cell.text, "confidence": round(float(cell.conf), 3),
            "flag": flag, "crop": crop,
        })

    # -- one chart page -----------------------------------------------------------
    def add_page(self, page, chart, cells, mapping, grid):
        """Append every award row on one chart page. Returns the count added."""
        added = 0
        # Every grid row is data: the FY09 header is printed above the ruled area (no top
        # border), so it is reconstructed separately, not taken from grid row 0.
        for r in range(grid.nrows):
            rc = row_cells(cells, mapping, r, grid.ncols)
            if is_blank_row(rc) or is_footnote_row(rc):
                continue
            if is_total_row(rc):
                value, ok = parse_amount(rc["amount"].text)
                self.totals.append({"chart": chart, "page": page,
                                    "printed": value if ok else None,
                                    "raw": rc["amount"].text})
                if not ok:
                    self._queue(page, r, "printed_total", rc["amount"], FLAG_AMOUNT)
                continue
            if self._add_row(page, chart, r, rc):
                added += 1
        return added

    def _add_row(self, page, chart, r, rc):
        flags = []

        amount, amount_ok = parse_amount(rc.get("amount", Cell()).text)
        ein, ein_ok = parse_ein(rc.get("ein", Cell()).text)
        if not (amount_ok or ein_ok or rc.get("organization", Cell())):
            return False                        # not an award row at all

        if not ein_ok:
            flags.append(FLAG_EIN)
            self._queue(page, r, "ein", rc.get("ein", Cell()), FLAG_EIN)
        if not amount_ok:
            flags.append(FLAG_AMOUNT)
            self._queue(page, r, "amount", rc.get("amount", Cell()), FLAG_AMOUNT)

        agy_num = normalize_numeric(rc.get("agy_num", Cell()).text)
        ua = normalize_numeric(rc.get("ua", Cell()).text)
        for name, value in (("agy_num", agy_num), ("ua", ua)):
            if value and not CODE_RE.match(value):
                flags.append(FLAG_CODE)
                self._queue(page, r, name, rc.get(name, Cell()), FLAG_CODE)

        agency = tr.clean(rc.get("agency", Cell()).text).upper()
        if agency and self.agency_vocab and agency not in self.agency_vocab:
            flags.append(FLAG_AGENCY)
            self._queue(page, r, "agency", rc.get("agency", Cell()), FLAG_AGENCY)

        # Organization text: the same cleanup the other years get, so names are consistent
        # across the combined files.
        org_raw = tr.clean(rc.get("organization", Cell()).text)
        org_raw, star = tr.strip_flags(org_raw)
        sponsor, org_raw = tr.peel_delegation(org_raw)
        organization, program = tr.split_org_program(org_raw)

        member = tr.clean(rc.get("member", Cell()).text) or sponsor
        if member:
            # Prefer the roster's canonical spelling when it matches, so FY09 members join
            # cleanly to the other years. A miss is NOT a flag on its own: the available
            # rosters come from FY2015+ Schedule C, and the FY2009 Council had members who
            # had left office by then, so absence proves nothing. Only a name that is not
            # name-SHAPED (stray digits, symbols) is evidence of a bad read.
            canonical = tr.detect_member(member, self.roster) if self.roster else ""
            if canonical:
                member = canonical
                self.member_hits += 1
            else:
                self.member_misses += 1
                if not NAME_SHAPE.match(member):
                    flags.append(FLAG_MEMBER)
                    self._queue(page, r, "member", rc.get("member", Cell()), FLAG_MEMBER)

        # Confidence gate applies to every populated cell in the row, not just the numbers:
        # a garbled organization name is a data-quality fact readers deserve to see.
        low = [k for k, c in rc.items() if c and c.conf < self.min_conf]
        if low:
            flags.append(FLAG_LOWCONF)
            for k in low:
                self._queue(page, r, k, rc[k], FLAG_LOWCONF)

        # The prequalification marker reaches us two ways: as trailing asterisks on the
        # organization name (older charts) or as its own unlabelled narrow column.
        star = star or (rc.get("star", Cell()).text.strip() if rc.get("star") else "")
        if star:
            flags.insert(0, star)

        self.rows.append({
            "resolution": self.resolution,
            "date": self.date,
            "chart": chart,
            "fiscal_year": FISCAL_YEAR,
            "action": "rescind" if (amount is not None and amount < 0) else "designate",
            "source": tr.clean(rc.get("source", Cell()).text),
            "council_member": member,
            "organization": organization,
            "program": program,
            "ein": ein,
            "amount": amount if amount is not None else "",
            "agency": agency,
            "agy_num": agy_num,
            "ua": ua,
            "purpose": tr.clean(rc.get("purpose", Cell()).text),
            "flags": ";".join(f for f in flags if f),
        })

        conduit_org = tr.clean(rc.get("conduit_org", Cell()).text)
        conduit_ein, _ = parse_ein(rc.get("conduit_ein", Cell()).text)
        status = tr.clean(rc.get("status", Cell()).text)
        if conduit_org or conduit_ein or status:
            self.conduits.append({
                "resolution": self.resolution, "chart": chart, "ein": ein,
                "conduit_organization": conduit_org, "conduit_ein": conduit_ein,
                "status": status,
            })
        return True


def write_sidecar(path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])
