#!/usr/bin/env python3
"""
Tests for the FY09 OCR pipeline.

Deliberately split by dependency weight. The grid, header-mapping and validator tests are
pure numpy/OpenCV and run in the plain `.venv` -- they cover the logic that decides which
column a dollar figure belongs to, which is where a silent error would do real damage. The
docTR end-to-end test is skipped unless the `.venv-ocr` stack is importable, so the default
suite stays runnable for contributors who never install torch.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr import assemble, headers  # noqa: E402

cv2 = pytest.importorskip("cv2", reason="opencv (requirements-ocr.txt) not installed")
np = pytest.importorskip("numpy")

from ocr import classify, grid as gridmod, recognize  # noqa: E402
import parse_transparency_reso_fy09 as fy09           # noqa: E402


# --------------------------------------------------------------------------- fixtures

def synthetic_table(rows=6, cols=5, cell_w=120, cell_h=40, margin=50, thickness=2):
    """A blank ruled lattice with known geometry -- the ground truth grid.py must recover."""
    h = margin * 2 + rows * cell_h
    w = margin * 2 + cols * cell_w
    img = np.full((h, w), 255, np.uint8)
    xs = [margin + c * cell_w for c in range(cols + 1)]
    ys = [margin + r * cell_h for r in range(rows + 1)]
    for x in xs:
        cv2.line(img, (x, ys[0]), (x, ys[-1]), 0, thickness)
    for y in ys:
        cv2.line(img, (xs[0], y), (xs[-1], y), 0, thickness)
    return img, xs, ys


# ----------------------------------------------------------------------------- dewarp

def _bowed_table(rows=6, cols=5, cell_w=140, cell_h=44, margin=60, bow_px=8, thickness=2):
    """A ruled table whose horizontal rules bow by `bow_px` — a parabola in x, zero at the
    edges, maximum in the middle — mimicking the FY09 scanner warp. Returns (img, xs, ys)
    where ys are the rules' intended STRAIGHT y positions."""
    from ocr import orient  # noqa: F401 (import guard: dewarp lives in orient)
    h = margin * 2 + rows * cell_h
    w = margin * 2 + cols * cell_w
    img = np.full((h, w), 255, np.uint8)
    xs = [margin + c * cell_w for c in range(cols + 1)]
    ys = [margin + r * cell_h for r in range(rows + 1)]
    xc = (xs[0] + xs[-1]) / 2.0
    half = (xs[-1] - xs[0]) / 2.0

    def bow(x):  # 0 at the table edges, +bow_px in the middle
        return int(round(bow_px * (1 - ((x - xc) / half) ** 2)))

    for y in ys:                       # curved horizontal rules
        pts = [(x, y + bow(x)) for x in range(xs[0], xs[-1] + 1)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            cv2.line(img, (x0, y0), (x1, y1), 0, thickness)
    for x in xs:                       # verticals follow the same vertical shift
        pts = [(x, y + bow(x)) for y in range(ys[0], ys[-1] + 1)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            cv2.line(img, (x0, y0), (x1, y1), 0, thickness)
    return img, xs, ys


def test_estimate_warp_measures_a_bow():
    """The bow is real and measurable even though the component-based grid detector below is
    robust to it -- dewarp uses this to straighten cell CONTENT for OCR, not to rescue grid
    detection."""
    from ocr import orient
    img, xs, ys = _bowed_table(bow_px=8)
    warp = orient.estimate_warp(img)
    assert warp is not None
    targets, dev = warp
    assert abs(dev).max() >= orient.DEWARP_MIN_DEV_PX


def test_dewarp_straightens_bowed_rules():
    """After dewarp the rules are flat (near-zero residual bow), so axis-aligned cell boxes
    line up with the row content."""
    from ocr import orient
    img, xs, ys = _bowed_table(bow_px=8)
    flat, max_dev = orient.dewarp(img, orient.estimate_warp(img))
    assert max_dev >= orient.DEWARP_MIN_DEV_PX          # the warp was detected and applied
    residual = orient.estimate_warp(flat)
    if residual is not None:                            # rules now straight -> tiny residual
        _, rdev = residual
        assert abs(rdev).max() < max_dev / 2
    g = gridmod.detect_grid(flat)
    assert g is not None and g.nrows == len(ys) - 1 and g.ncols == len(xs) - 1


def _faint_column_table(rows=10, cols=6, cell_w=150, cell_h=44, margin=80):
    """A table whose VERTICAL rules slowly WANDER in x over the page height — solid (so they
    survive the rule-isolating opening and stay one 8-connected full-height component), but
    spread across ~7 columns so no single column carries more than a small fraction of the
    height. This is the FY09 page-11 condition: a per-column-sum span test misses these
    columns; the component-based detector must still find them. Horizontal rules are solid
    and straight."""
    h = margin * 2 + rows * cell_h
    w = margin * 2 + cols * cell_w
    img = np.full((h, w), 255, np.uint8)
    xs = [margin + c * cell_w for c in range(cols + 1)]
    ys = [margin + r * cell_h for r in range(rows + 1)]
    for y in ys:
        cv2.line(img, (xs[0], y), (xs[-1], y), 0, 2)          # solid horizontal rules
    yy = np.arange(ys[0], ys[-1] + 1)
    drift = np.round(3 * np.sin(yy / 60.0)).astype(int)       # ±3px wander, slow enough to
    for x in xs:                                              # keep long same-column runs
        for y, dx in zip(yy, drift):
            img[y, x + dx] = 0
    return img, xs, ys


def test_detect_grid_finds_faint_full_height_column_rules():
    """Guards the page-11 fix: faint interior column rules whose densest column is well
    under the 60% span threshold are still recovered, because each is a full-height
    connected component."""
    img, xs, ys = _faint_column_table()
    g = gridmod.detect_grid(img)
    assert g is not None
    assert g.ncols == len(xs) - 1                       # every faint column recovered
    assert g.nrows == len(ys) - 1


def test_dewarp_is_a_noop_on_a_flat_table():
    """A page whose rules are already straight must not be resampled — no invented blur."""
    from ocr import orient
    img, _, _ = synthetic_table(rows=6, cols=5)
    flat, max_dev = orient.dewarp(img, orient.estimate_warp(img))
    assert max_dev < orient.DEWARP_MIN_DEV_PX
    assert flat is img                                  # returned unchanged, not a copy


def test_estimate_warp_returns_none_without_enough_rules():
    """Narrative / divider pages have too few rules to model a warp — leave them alone."""
    from ocr import orient
    blank = np.full((900, 700), 255, np.uint8)
    cv2.line(blank, (60, 400), (640, 400), 0, 2)        # a single rule
    assert orient.estimate_warp(blank) is None


# ------------------------------------------------------------------------------- grid

def test_detect_grid_recovers_known_lattice():
    img, xs, ys = synthetic_table()
    g = gridmod.detect_grid(img)
    assert g is not None
    assert g.ncols == len(xs) - 1
    assert g.nrows == len(ys) - 1
    for got, want in zip(g.xs, xs):
        assert abs(got - want) <= 2
    for got, want in zip(g.ys, ys):
        assert abs(got - want) <= 2


def test_detect_grid_ignores_text_and_underlines():
    """Glyph strokes and a short underline must not be mistaken for separators -- that is
    the whole point of the long-kernel opening plus the span test."""
    img, xs, ys = synthetic_table()
    cv2.putText(img, "Little Sheppard's Community Center, Inc.", (xs[0] + 6, ys[1] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0, 1)
    cv2.line(img, (xs[1] + 5, ys[2] - 6), (xs[1] + 60, ys[2] - 6), 0, 2)   # short underline
    g = gridmod.detect_grid(img)
    assert g is not None
    assert (g.nrows, g.ncols) == (len(ys) - 1, len(xs) - 1)


def test_detect_grid_returns_none_on_a_page_with_no_rules():
    img = np.full((800, 600), 255, np.uint8)
    cv2.putText(img, "EXHIBIT I", (120, 400), cv2.FONT_HERSHEY_SIMPLEX, 3, 0, 6)
    assert gridmod.detect_grid(img) is None


def test_grid_locate_and_cell_round_trip(tmp_path):
    img, xs, ys = synthetic_table()
    g = gridmod.detect_grid(img)
    x0, y0, x1, y1 = g.cell(2, 3)
    assert g.locate((x0 + x1) // 2, (y0 + y1) // 2) == (2, 3)
    assert g.locate(1, 1) is None                       # in the margin, outside the table
    path = tmp_path / "grid.json"
    g.save(path)
    assert gridmod.Grid.load(path).to_dict() == g.to_dict()


# --------------------------------------------------------------------------- classify

def test_classify_distinguishes_the_three_page_kinds():
    # A chart page is decided by rule COUNT, with no grid passed in -- stage 2 must stand
    # alone, not depend on stage 3's lattice.
    table, _, _ = synthetic_table(rows=8, cols=6)
    assert classify.classify_page(table) == classify.KIND_CHART

    divider = np.full((1100, 850), 255, np.uint8)
    cv2.putText(divider, "EXHIBIT I", (140, 600), cv2.FONT_HERSHEY_SIMPLEX, 5, 0, 12)
    assert classify.classify_page(divider) == classify.KIND_DIVIDER

    narrative = np.full((1100, 850), 255, np.uint8)
    for i in range(30):
        cv2.putText(narrative, "Resolution approving the new designation and changes",
                    (60, 80 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 0, 1)
    assert classify.classify_page(narrative) == classify.KIND_NARRATIVE


# ---------------------------------------------------------------------------- headers

LONG_HEADER = ["Member", "Organization", "EIN Number", "Agency", "Amount", "Agy #", "U/A",
               "Fiscal Conduit/Sponsoring Organization", "Fiscal Conduit EIN", "",
               "Status (Council, MOC, etc)"]
SHORT_HEADER = ["Organization", "EIN Number", "Agency", "Amount", "Agy #", "U/A", ""]


def test_map_header_long_chart_shape():
    widths = [200] * len(LONG_HEADER)
    widths[9] = 20                                     # the unlabelled asterisk column
    m = headers.map_header(LONG_HEADER, widths, page_width=2200)
    assert m.ok
    assert m.get("member") == 0
    assert m.get("organization") == 1
    assert m.get("ein") == 2
    assert m.get("amount") == 4
    assert m.get("conduit_org") == 7
    assert m.get("conduit_ein") == 8          # must NOT steal the plain 'ein' slot
    assert m.get(headers.STAR) == 9
    assert m.get("status") == 10


def test_map_header_short_chart_shape():
    widths = [400, 200, 120, 160, 90, 90, 18]
    m = headers.map_header(SHORT_HEADER, widths, page_width=1300)
    assert m.ok
    assert m.get("member") is None            # initiative charts have no member column
    assert m.get("organization") == 0
    assert m.get("ua") == 5


def test_map_header_survives_realistic_ocr_corruption():
    corrupted = ["Membor", "Organizaton", "EIN Numbor", "Agoncy", "Amount", "Agy tt", "U/A"]
    m = headers.map_header(corrupted, [200] * 7, page_width=1400)
    assert m.ok
    assert m.get("agy_num") == 5
    assert m.get("ua") == 6


def test_map_header_refuses_to_guess_when_a_required_column_is_missing():
    """The failure that matters: rather than assign dollar amounts positionally, the page
    must be reported unmapped so a human looks at it."""
    m = headers.map_header(["Member", "???", "####", "Agency", "%%%%"],
                           [200] * 5, page_width=1200)
    assert not m.ok
    assert "amount" in m.missing and "ein" in m.missing
    assert m.unmapped


def test_compatible_layout_matches_same_chart_geometry_only():
    base = [0.05, 0.30, 0.45, 0.60, 0.75, 0.90]           # normalized column separators
    assert headers.compatible_layout(base, list(base))               # identical -> same chart
    assert headers.compatible_layout(base, [x + 0.01 for x in base]) # ~1% drift -> still same
    assert not headers.compatible_layout(base, [x + 0.05 for x in base])  # 5% shift -> different
    assert not headers.compatible_layout(base, base[:-1])            # different column count


def test_is_headerless_only_true_when_no_labels_were_read():
    # a genuine no-header continuation page: band above the grid is empty
    assert headers.is_headerless(["", "", "", "", "", "", ""])
    # OCR speckle (single stray chars) is not a header
    assert headers.is_headerless(["", ".", "", "'", "", "", ""])
    # a page that DID pull real header labels is NOT headerless -> must not borrow a mapping,
    # even if those labels fail to map the required columns (the "Sponsor Name" red-flag case)
    assert not headers.is_headerless(
        ["Sponsor Name", "Program Name", "EIN Number", "Agency", "Amount", "Agy #", "UIA"])
    assert not headers.is_headerless(["", "Organization", "EIN Number", "", "", "", ""])


def _word(text, x0, y0, x1, y1):
    return {"text": text, "conf": 0.99, "bbox": (x0, y0, x1, y1)}


def test_header_reconstructed_from_the_band_above_the_grid():
    """FY09 headers float above the ruled area (no top border), so they are NOT grid row 0.
    header_row_texts must pull them from the band above the grid, drop the 'CHART n:' caption
    line, bin words into columns by x, and join multi-word header cells."""
    grid = gridmod.Grid(xs=[100, 300, 500, 700], ys=[400, 440, 480, 520], bbox=(100, 400, 700, 520))
    words = [
        # caption line, higher up — must be excluded
        _word("CHART", 100, 240, 180, 270), _word("1:", 190, 240, 220, 270),
        _word("Local", 230, 240, 330, 270), _word("Initiatives", 340, 240, 480, 270),
        # header line, just above the grid top (y0=400)
        _word("Member", 150, 350, 250, 390),
        _word("Organization", 330, 350, 470, 390),
        _word("EIN", 520, 350, 580, 390), _word("Number", 590, 350, 690, 390),
        # a data row INSIDE the grid — must be ignored (below y0)
        _word("Vann", 150, 410, 250, 435), _word("Boys Bunch", 330, 410, 470, 435),
    ]
    texts = recognize.header_row_texts(words, grid)
    assert texts == ["Member", "Organization", "EIN Number"]


def test_add_page_treats_grid_row_zero_as_data():
    """With the header reconstructed externally, the first grid row is the first award and
    must not be skipped."""
    asm = assemble.Assembler(1, "2008-08-14", set(), {"DYCD"})
    cells = _cells({
        (0, 0): "Vann", (0, 1): "Boys Bunch", (0, 2): "13-6400434",
        (0, 3): "DYCD", (0, 4): "$5,000.00", (0, 5): "260", (0, 6): "005",
    })
    asm.add_page(9, "Local Initiatives", cells, _mapping(ORDER), _FakeGrid(1, 7))
    assert len(asm.rows) == 1                            # row 0 is data, not dropped as header
    assert asm.rows[0]["organization"] == "Boys Bunch"
    assert asm.rows[0]["ein"] == "136400434"


# ------------------------------------------------------------------------- validators

@pytest.mark.parametrize("text,expected", [
    ("$15,000.00", 15000),
    ("$5,000", 5000),
    ("($3,500.00)", -3500),
    ("$0.00", 0),
    ("$500,000.00", 500000),
    ("{$10,000.00}", -10000),          # OCR bracket variant: unambiguous, so folded
])
def test_parse_amount_accepts_printed_forms(text, expected):
    value, ok = assemble.parse_amount(text)
    assert ok and value == expected


@pytest.mark.parametrize("text", [
    "S15,000.00",       # 'S' for '$' is ambiguous with a digit -- never guessed
    "$15,0O0.00",       # letter O for zero
    "$15,000.37",       # non-zero cents: every other year is whole dollars
    "", "n/a", "-",
])
def test_parse_amount_refuses_ambiguous_readings(text):
    value, ok = assemble.parse_amount(text)
    assert not ok and value is None


def test_parse_ein_drops_the_hyphen_like_the_other_years():
    assert assemble.parse_ein("13-3608977") == ("133608977", True)
    assert assemble.parse_ein("133608977") == ("133608977", True)
    assert assemble.parse_ein("13-36089")[1] is False
    assert assemble.parse_ein("l3-3608977")[1] is False


def test_agency_vocabulary_is_a_real_dictionary_check(tmp_path):
    src = tmp_path / "fy10_transparency_all.csv"
    src.write_text("ein,amount,agency\n133608977,100,DYCD\n133608977,100,DFTA\n")
    vocab = assemble.load_agency_vocab([str(src)])
    assert "DYCD" in vocab and "DFTA" in vocab
    assert "DYGD" not in vocab          # a plausible OCR slip fails, as it must


# --------------------------------------------------------------------- row assembly

def _cells(mapping_texts, grid_like_rect=(0, 0, 10, 10)):
    return {(r, c): assemble.Cell(t, 0.99, grid_like_rect)
            for (r, c), t in mapping_texts.items()}


class _FakeGrid:
    def __init__(self, nrows, ncols):
        self.nrows, self.ncols = nrows, ncols

    def cell(self, r, c):
        return (c * 10, r * 10, c * 10 + 10, r * 10 + 10)


def _mapping(order):
    return headers.HeaderMapping({name: i for i, name in enumerate(order)}, [], [])


ORDER = ["member", "organization", "ein", "agency", "amount", "agy_num", "ua"]


def test_assembler_builds_a_schema_row_and_signs_rescissions():
    asm = assemble.Assembler(1, "2008-08-14", set(), {"DYCD"})
    cells = _cells({
        (1, 0): "Baez", (1, 1): "Common Cents New York, Inc.", (1, 2): "13-3422660",
        (1, 3): "DYCD", (1, 4): "$15,000.00", (1, 5): "260", (1, 6): "312",
        (2, 0): "Baez", (2, 1): "Love Gospel Assembly", (2, 2): "13-3062521",
        (2, 3): "DYCD", (2, 4): "($20,000.00)", (2, 5): "260", (2, 6): "312",
    })
    asm.add_page(9, "Youth Discretionary", cells, _mapping(ORDER), _FakeGrid(3, 7))

    assert [r["action"] for r in asm.rows] == ["designate", "rescind"]
    assert [r["amount"] for r in asm.rows] == [15000, -20000]
    assert asm.rows[0]["ein"] == "133422660"
    assert asm.rows[0]["fiscal_year"] == assemble.FISCAL_YEAR
    assert asm.rows[0]["chart"] == "Youth Discretionary"
    assert set(asm.rows[0]) == set(assemble.COLS)
    assert not any(r["flags"] for r in asm.rows)


def test_assembler_flags_and_queues_a_bad_value_instead_of_shipping_it():
    asm = assemble.Assembler(1, "2008-08-14", set(), {"DYCD"})
    cells = _cells({
        (1, 0): "Baez", (1, 1): "Real World Foundation, Inc.", (1, 2): "13-36l9036",
        (1, 3): "DYGD", (1, 4): "$1O,000.00", (1, 5): "260", (1, 6): "312",
    })
    asm.add_page(9, "Youth Discretionary", cells, _mapping(ORDER), _FakeGrid(2, 7))

    row = asm.rows[0]
    assert assemble.FLAG_EIN in row["flags"]
    assert assemble.FLAG_AMOUNT in row["flags"]
    assert assemble.FLAG_AGENCY in row["flags"]
    assert row["amount"] == ""                       # never a guessed number
    queued = {(q["column"], q["flag"]) for q in asm.reviews}
    assert ("ein", assemble.FLAG_EIN) in queued
    assert ("amount", assemble.FLAG_AMOUNT) in queued


def test_assembler_captures_a_printed_chart_total_for_reconciliation():
    asm = assemble.Assembler(1, "2008-08-14", set(), {"CUNY"})
    cells = _cells({
        (1, 1): "New Era Veterans", (1, 2): "13-3695481", (1, 3): "CUNY",
        (1, 4): "$92,831.00", (1, 5): "042", (1, 6): "001",
        (2, 4): "$92,831.00",                        # the printed TOTAL line
    })
    asm.add_page(12, "Veterans Resource Center", cells, _mapping(ORDER), _FakeGrid(3, 7))

    assert len(asm.rows) == 1
    assert asm.totals == [{"chart": "Veterans Resource Center", "page": 12,
                           "printed": 92831, "raw": "$92,831.00"}]


def test_fiscal_conduit_columns_go_to_the_sidecar_not_the_main_schema():
    order = ORDER + ["conduit_org", "conduit_ein", "status"]
    asm = assemble.Assembler(1, "2008-08-14", set(), {"DYCD"})
    cells = _cells({
        (1, 0): "Vacca", (1, 1): "AARP Minneford Chapter", (1, 2): "94-2713639",
        (1, 3): "DFTA", (1, 4): "$500.00", (1, 5): "125", (1, 6): "003",
        (1, 7): "Neighborhood Initiatives Development Corporation (NIDC)",
        (1, 8): "13-3110811", (1, 9): "Approved",
    })
    asm.add_page(9, "Local Initiatives", cells, _mapping(order), _FakeGrid(2, 10))

    assert set(asm.rows[0]) == set(assemble.COLS)     # schema stays exactly 16 columns
    assert asm.conduits[0]["conduit_ein"] == "133110811"
    assert asm.conduits[0]["status"] == "Approved"
    assert set(asm.conduits[0]) == set(assemble.CONDUIT_COLS)


def test_assembler_surfaces_a_cell_span_carried_flag():
    """A cell whose text came from the OCR stage's cross-cell disambiguation re-read (see
    recognize.find_cell_span_conflicts) carries assemble.FLAG_CELLSPAN forward -- it must show
    up in the row's flags and be queued for review, the same as every other flag here, even
    though the value itself is otherwise well-formed."""
    asm = assemble.Assembler(6, "2009-04-02", set(), {"DYCD"})
    rect = (0, 0, 10, 10)
    cells = {
        (1, 0): assemble.Cell("Sanders, Jr", 0.9, rect),
        (1, 1): assemble.Cell("82nd Street Academics", 0.85, rect, flag=assemble.FLAG_CELLSPAN),
        (1, 2): assemble.Cell("20-0788352", 0.9, rect),
        (1, 3): assemble.Cell("DYCD", 0.9, rect),
        (1, 4): assemble.Cell("$10,000.00", 0.9, rect),
        (1, 5): assemble.Cell("260", 0.9, rect),
        (1, 6): assemble.Cell("312", 0.9, rect),
    }
    asm.add_page(9, "Youth Discretionary", cells, _mapping(ORDER), _FakeGrid(2, 7))

    row = asm.rows[0]
    assert assemble.FLAG_CELLSPAN in row["flags"]
    queued = {(q["column"], q["flag"]) for q in asm.reviews}
    assert ("organization", assemble.FLAG_CELLSPAN) in queued


# ------------------------------------------------------------------- cell assignment

def test_words_are_binned_into_cells_by_centroid():
    img, xs, ys = synthetic_table(rows=3, cols=3)
    g = gridmod.detect_grid(img)
    words = [
        {"text": "Baez", "conf": 0.99, "bbox": (xs[0] + 10, ys[1] + 8, xs[0] + 60, ys[1] + 30)},
        {"text": "$15,000.00", "conf": 0.95,
         "bbox": (xs[2] + 10, ys[2] + 8, xs[2] + 90, ys[2] + 30)},
        {"text": "stray", "conf": 0.5, "bbox": (2, 2, 20, 14)},          # in the margin
    ]
    cells, orphans = recognize.assign_words(words, g)
    assert cells[(1, 0)][0]["text"] == "Baez"
    assert cells[(2, 2)][0]["text"] == "$15,000.00"
    assert [o["text"] for o in orphans] == ["stray"]


def test_find_cell_span_conflicts_catches_an_unambiguous_straddle():
    img, xs, ys = synthetic_table(rows=3, cols=3)
    g = gridmod.detect_grid(img)
    # A word box centered close to the column rule between col 0 and col 1, split roughly
    # 40/60 between them -- a real straddle, not edge bleed.
    rule_x = xs[1]
    straddler = {"text": "82nd Street", "conf": 0.9,
                "bbox": (rule_x - 30, ys[1] + 8, rule_x + 45, ys[1] + 30)}
    conflicts = recognize.find_cell_span_conflicts([straddler], g)
    assert set(conflicts) == {(1, 0), (1, 1)}
    assert conflicts[(1, 0)] == [straddler]
    assert conflicts[(1, 1)] == [straddler]


def test_find_cell_span_conflicts_ignores_small_edge_bleed():
    img, xs, ys = synthetic_table(rows=3, cols=3)
    g = gridmod.detect_grid(img)
    # Almost entirely inside col 1; only a ~8% sliver (antialiasing/descender bleed) crosses
    # the rule into col 0 -- well under SPAN_MIN_FRAC, so this must NOT be reported.
    rule_x = xs[1]
    grazer = {"text": "Baez", "conf": 0.9,
             "bbox": (rule_x - 5, ys[1] + 8, rule_x + 55, ys[1] + 30)}
    assert recognize.find_cell_span_conflicts([grazer], g) == {}


def test_cell_text_reads_a_wrapped_organization_name_in_order():
    words = [
        {"text": "Ralph's", "conf": 0.9, "bbox": (10, 10, 60, 26)},
        {"text": "Educational", "conf": 0.8, "bbox": (65, 10, 150, 26)},
        {"text": "Services,", "conf": 0.7, "bbox": (10, 32, 80, 48)},
        {"text": "Inc.", "conf": 0.95, "bbox": (85, 32, 115, 48)},
    ]
    text, conf = recognize.cell_text(words)
    assert text == "Ralph's Educational Services, Inc."
    assert conf == 0.7          # a cell is only as good as its weakest word


def test_debug_overlays_render_without_error():
    """Smoke test for the debug-image builders: they must produce a 3-channel image the
    size of the page. (Guards against import/name slips inside these rarely-unit-tested
    drawing helpers.)"""
    img, xs, ys = synthetic_table(rows=4, cols=4)
    g = gridmod.detect_grid(img)
    words = [{"text": "Baez", "conf": 0.99, "bbox": (xs[0] + 5, ys[1] + 5, xs[0] + 60, ys[1] + 30)},
             {"text": "low", "conf": 0.40, "bbox": (xs[1] + 5, ys[2] + 5, xs[1] + 50, ys[2] + 30)}]

    det = recognize.draw_detection_overlay(img, words, g, low_conf=0.80)
    assert det.shape == (img.shape[0], img.shape[1], 3)
    assert recognize.draw_detection_overlay(img, words, grid=None).shape[2] == 3   # grid optional

    ocr = recognize.draw_ocr_overlay(img, g, {(1, 0): "Baez"}, {(1, 0): 0.4}, low_conf=0.80)
    assert ocr.shape == (img.shape[0], img.shape[1], 3)


# ---------------------------------------------------- targeted re-OCR (fake engine, no docTR)

class _FakeRecoEngine:
    """Stub for recognize.Engine: reread_cell only ever calls .read_crop(upscaled_image)."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def read_crop(self, img):
        self.calls += 1
        return self.result


def test_reread_span_conflicts_rereads_the_cells_own_rect_and_tags_the_flag():
    gray = np.full((100, 100), 255, np.uint8)
    rect_a, rect_b = (0, 0, 40, 40), (40, 0, 80, 40)
    cells = {
        (0, 0): assemble.Cell("82n", 0.4, rect_a),
        (0, 1): assemble.Cell("d Street", 0.4, rect_b),
    }
    conflicts = {(0, 0): ["word"], (0, 1): ["word"]}
    engine = _FakeRecoEngine(("FIXED", 0.97))

    fixed = fy09._reread_span_conflicts(engine, gray, cells, conflicts)

    assert fixed == 2
    assert engine.calls == 2               # once per implicated cell, not once per word
    assert cells[(0, 0)].text == "FIXED" and cells[(0, 0)].conf == 0.97
    assert cells[(0, 0)].flag == assemble.FLAG_CELLSPAN
    assert cells[(0, 1)].text == "FIXED" and cells[(0, 1)].flag == assemble.FLAG_CELLSPAN
    # each cell keeps ITS OWN rect, not the word's -- the whole point of this fallback
    assert cells[(0, 0)].rect == rect_a
    assert cells[(0, 1)].rect == rect_b


def test_reread_failing_numerics_preserves_a_pre_existing_carried_flag():
    """A cell already corrected by the span-conflict pass, then also re-read by the numeric-
    shape pass, must not lose its ocr:cellspan provenance to the second overwrite."""
    gray = np.full((100, 100), 255, np.uint8)
    rect = (0, 0, 40, 40)
    cells = {(1, 0): assemble.Cell("13-36l9036", 0.5, rect, flag=assemble.FLAG_CELLSPAN)}
    mapping = _mapping(["ein"])
    grid = _FakeGrid(2, 1)
    engine = _FakeRecoEngine(("133619036", 0.95))

    fy09._reread_failing_numerics(engine, gray, cells, mapping, grid)

    assert cells[(1, 0)].text == "133619036"
    assert cells[(1, 0)].flag == assemble.FLAG_CELLSPAN


# ---------------------------------------------------------------- docTR end-to-end

doctr_available = True
try:                                            # pragma: no cover - environment probe
    import doctr  # noqa: F401
except Exception:                               # pragma: no cover
    doctr_available = False

TRUTH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "testdata", "fy09_ocr_truth")


def _truth_csvs():
    if not os.path.isdir(TRUTH_DIR):
        return []
    return sorted(f for f in os.listdir(TRUTH_DIR) if f.endswith(".csv"))


@pytest.mark.skipif(not doctr_available,
                    reason="docTR not installed (see code/requirements-ocr.txt / .venv-ocr)")
@pytest.mark.skipif(not _truth_csvs(), reason="no hand-labelled truth pages yet")
@pytest.mark.parametrize("truth_csv", _truth_csvs())
def test_ocr_matches_hand_labelled_truth(truth_csv):
    """End-to-end on hand-labelled pages. EIN and amount must match EXACTLY -- those are
    the columns the repo's credibility rests on. Text fields are reported, not asserted."""
    import csv as _csv
    from ocr.recognize import Engine

    with open(os.path.join(TRUTH_DIR, truth_csv), newline="") as f:
        meta = _csv.DictReader(f)
        expected = list(meta)
    assert expected, f"{truth_csv} is empty"

    pdf = expected[0]["source_pdf"]
    page = int(expected[0]["page"])
    from ocr import render as render_mod
    (_, raw), = render_mod.render_pdf(pdf, "build/ocr", pages=[page])
    gray = cv2.imread(raw, cv2.IMREAD_GRAYSCALE)

    engine = Engine()
    up, _ = orient_module().orient_page(gray, engine)
    g = gridmod.detect_grid(up)
    assert g is not None, "no table detected on a page known to carry one"

    word_cells, _ = recognize.assign_words(engine.words(up), g)
    texts = {rc: recognize.cell_text(ws)[0] for rc, ws in word_cells.items()}
    mapping = headers.map_header([texts.get((0, c), "") for c in range(g.ncols)],
                                 [g.xs[c + 1] - g.xs[c] for c in range(g.ncols)],
                                 up.shape[1])
    assert mapping.ok, f"header did not map: {mapping.missing}"

    got_eins = {assemble.parse_ein(texts.get((r, mapping.get("ein")), ""))[0]
                for r in range(1, g.nrows)}
    got_amounts = {assemble.parse_amount(texts.get((r, mapping.get("amount")), ""))[0]
                   for r in range(1, g.nrows)}
    for row in expected:
        assert row["ein"] in got_eins, f"missing EIN {row['ein']}"
        assert int(row["amount"]) in got_amounts, f"missing amount {row['amount']}"


def orient_module():
    from ocr import orient
    return orient
