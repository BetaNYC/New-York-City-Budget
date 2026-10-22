"""
Tests for the Schedule C toolkit (code/schedc/, code/schedc_cv/, code/parse_schedule_c_v2.py).

Unit tests use synthetic input. Golden rows read single FY2027 pages straight from the PDF in
source/ and compare with values written down by reading the rendered page (not copied from
parser output). The snapshot tests read the committed outputs in the review folder (config `review_dir`).

Run: pytest code/test_schedc.py
"""
import csv
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schedc import config, disclosure, review, structure, vector  # noqa: E402

CFG = config.load(2027)
OUT = os.path.join(config.ROOT, CFG["review_dir"], "data")


# --- unit ---------------------------------------------------------------------------------------
def test_clean_text_rules():
    assert structure.clean_text("Home-\nDelivered Meals") == ("Home-Delivered Meals", ["wrap_hyphen"])
    assert structure.clean_text("Inc. -\nCouncil") == ("Inc. - Council", ["line_join"])
    assert structure.clean_text("a  b") == ("a b", ["ws_collapse"])
    assert structure.clean_text("plain") == ("plain", [])


def test_parse_amount_strict():
    assert structure.parse_amount("$5,000") == 5000
    assert structure.parse_amount("$135,000") == 135000
    for bad in ("5,000", "$5,00", "$5000,0", "-$5", "$ 5,000x"):
        assert structure.parse_amount(bad) is None


def test_statement_kinds_from_config():
    k = lambda t: structure.statement_kind(t, CFG)
    assert k("The Council has designated the following providers for Fiscal 2027:") == ("full", None, None)
    assert k("The Council will designate $275,000 post-adoption and has designated $4,225,000 "
             "to the following providers for Fiscal 2027:") == ("partial", 275000, 4225000)
    assert k("The Council will designate $750,000 post-adoption for Fiscal 2027.") == \
        ("reserve_only", 750000, None)
    assert k("The Council will designate $750,000 post-adoption for Fiscal 2027. Public Safety")[0] \
        == "unknown"


def test_chars_to_text_lines_and_gaps():
    c = lambda t, x0, top: dict(text=t, x0=x0, x1=x0 + 5, top=top, bottom=top + 10)
    chars = [c("a", 0, 0), c("b", 5, 0.5), c("c", 20, 0), c("d", 0, 14)]
    assert vector.chars_to_text(chars) == "ab c\nd"


def test_city_ein_name_rule():
    assert disclosure.name_ok("136400434", "Department of Education", "Department of Education - PS 1")
    assert not disclosure.name_ok("136400434", "Department of Parks and Recreation",
                                  "Department of Youth and Community Development")
    assert disclosure.name_ok("131111111", "Anything", "Something else")


def test_review_id_stable():
    assert review.review_id(2027, "H8.lattice", 463, 0, 6, "ein") == \
        review.review_id(2027, "H8.lattice", 463, 0, 6, "ein")
    assert review.review_id(2027, "H8.lattice", 463, 0, 6, "ein") != \
        review.review_id(2027, "H8.lattice", 463, 0, 7, "ein")


def test_ink_regions_find_a_dot():
    np = pytest.importorskip("numpy")
    from schedc_cv import ink
    m = np.zeros((200, 200), dtype=bool)
    assert ink.find_uncovered_regions(m, 16, 64, (0, 0)) == []
    m[50:60, 70:80] = True          # one 10x10 px glyph-sized blob
    regs = ink.find_uncovered_regions(m, 16, 64, (100, 1000))
    assert regs == [{"bbox": [170, 1050, 180, 1060], "ink_px": 100}]


# --- golden rows (read from the page images, 2026-10-20) -----------------------------------------
@pytest.fixture(scope="module")
def pages():
    return {p["page"]: p for p in vector.read_pdf(CFG["_pdf_abs"], pages={7, 205, 279, 306, 463})}


def _rows(pages, pns):
    return structure.build([pages[p] for p in pns], CFG)["awards"]


@pytest.mark.parametrize("pn,member,org,ein,amount,agency", [
    (279, "Felder", "Medicare Rights Center, Inc.", "133505372", 135000, "DFTA"),
    (7, "Joseph", "Access Justice Brooklyn, Inc. - Legal Assistance - Council District 40",
     "113155182", 5000, "DSS/HRA"),
    (306, "Brooks-Powers", "100 Suits for 100 Men, Inc. - Council District 31", "462971279", 7000, ""),
])
def test_golden_landscape_rows(pages, pn, member, org, ein, amount, agency):
    rows = [r for r in _rows(pages, [pn]) if r["ein"] == ein and r["amount"] == amount]
    assert len(rows) == 1
    r = rows[0]
    assert (r["member"] or r["sponsor"]) == member
    assert r["org"] == org
    assert r["agency"] == agency


def test_golden_portrait_rows_attach_to_box(pages):
    rows = _rows(pages, [205])
    amudim = [r for r in rows if r["org"] == "Amudim Community Resources, Inc."]
    assert len(amudim) == 1 and amudim[0]["ein"] == "470984801" and amudim[0]["amount"] == 50000
    assert amudim[0]["initiative"] == "Opioid Prevention and Treatment"
    aids = [r for r in rows if r["ein"] == "133562071"]
    assert {r["initiative"] for r in aids} == {"Peer Specialists Support"}
    assert sorted(r["amount"] for r in aids) == [75000, 125000]
    assert sum(r["amount"] for r in rows if r["initiative"] == "Opioid Prevention and Treatment") \
        == 3075000


def test_golden_p463_overflow_hyphen(pages):
    r = [r for r in _rows(pages, [463]) if r["award_id"] == "fy27-p463-t00-r006"][0]
    assert r["ein"] == "134113613" and "ein_overflow_hyphen" in r["row_flags"]


# --- snapshot of the committed outputs -----------------------------------------------------------
def _read(name):
    with open(os.path.join(OUT, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.skipif(not os.path.exists(OUT), reason="FY2027 outputs not built")
def test_snapshot_rows_and_total():
    rows = _read("fy27_sc_awards.csv")
    assert len(rows) == 9979
    assert sum(int(r["amount"]) for r in rows) == 655045412
    by = {}
    for r in rows:
        by[r["section"]] = by.get(r["section"], 0) + int(r["amount"])
    assert by == {"body": 605246412, "appendix_a": 5610000, "appendix_b": 36539000,
                  "appendix_c": 7650000}
    assert any(r["org"] == "Medicare Rights Center, Inc." and r["amount"] == "135000" for r in rows)


@pytest.mark.skipif(not os.path.exists(OUT), reason="FY2027 outputs not built")
def test_snapshot_checks_pass():
    txt = open(os.path.join(OUT, "fy27_sc_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "acceptance on p.279" in txt and "(PASS)" in txt
    assert "matched without the City-EIN name rule (the 2026-10-19 prototype's H17 floor, 9,859): 9,859" in txt


# --- FY2026 (config/schedule_c/fy2026.toml) ----------------------------------------------------
CFG26 = config.load(2026)
OUT26 = os.path.join(config.ROOT, CFG26["review_dir"], "data")


def test_fy2027_config_leaves_fy2026_switches_off():
    s = CFG["structure"]
    for k in ("split_merged_tables", "continuation_rows", "headerless_continuation",
              "box_amount_on_second_row", "amount_without_dollar"):
        assert not s.get(k)
    assert not CFG["image"].get("carry_header")


def test_clean_text_drops_unmapped_glyph():
    assert structure.clean_text("District 36.(cid:9)") == ("District 36.", ["cid_glyph"])


def test_fy2026_statement_kinds():
    k = lambda t: structure.statement_kind(t, CFG26)[0]
    assert k("The City Council will designate awards post-adoption.") == "reserve_all"
    assert k("The Council will designate $8,300,000 post-adoption and has designated "
             "$16,600,000 to the following providers:") == "partial"
    assert k("The City Council will designate $1,500,000 post-adoption and has designate d "
             "$1,500,000 to the following provider for Fiscal 2026:") == "partial"
    assert k("The City Council has designated directly to the City University of New York.") \
        == "direct"
    assert k("The City Council has designated $4,800,000 to the following providers for "
             "Fiscal 2026:") == "designated"
    assert k("The City Council h as designated the following providers for Fiscal 2026 :") \
        == "full"
    assert k("The City Council will designate $5,000,000 post adoption for Fiscal 2026.") \
        == "reserve_only"


def _cell(x0, x1, text):
    return dict(bbox=[x0, 0, x1, 0], text_raw=text, char_boxes=[])


def test_split_merged_table_synthetic():
    row = lambda i, top, cells: dict(row_index=i, top=top, bottom=top + 10,
                                     cells=[dict(c, bbox=[c["bbox"][0], top, c["bbox"][2],
                                                          top + 10]) for c in cells])
    t = dict(table_index=0, bbox=[0, 0, 100, 60], rows=[
        row(0, 0, [_cell(0, 80, "Box Title"), _cell(80, 100, "$5,000")]),
        row(1, 10, [_cell(0, 100, "Designation Method: The Council has designated the")]),
        row(2, 20, [_cell(0, 100, "following providers for Fiscal 2026:")]),
        row(3, 30, [_cell(0, 60, "Legal Name of Organization – Program Name"),
                    _cell(60, 80, "EIN"), _cell(80, 100, "Amount")]),
        row(4, 40, [_cell(0, 60, "Org"), _cell(60, 80, "13-1234567"), _cell(80, 100, "$5,000")]),
    ])
    page = dict(page=1, tables=[t], lines=[], orphans=[])
    out = structure.split_merged_tables([page], CFG26)[0]
    assert [len(x["rows"]) for x in out["tables"]] == [1, 2]
    assert [ln["text"] for ln in out["lines"]] == [
        "Designation Method: The Council has designated the",
        "following providers for Fiscal 2026:"]
    assert page["tables"][0]["table_index"] == 0 and len(page["tables"][0]["rows"]) == 5
    assert structure.split_merged_tables([page], CFG)[0] is page      # off for FY2027


# Golden rows, read from the rendered FY2026 pages (2026-10-21), not copied from output.
@pytest.fixture(scope="module")
def pages26():
    ps = vector.read_pdf(CFG26["_pdf_abs"], pages={36, 111, 130, 156, 157, 175, 176, 218},
                         x_tolerance=CFG26["x_tolerance"])
    return {p["page"]: p for p in structure.split_merged_tables(ps, CFG26)}


def _rows26(pages26, pns):
    return structure.build([pages26[p] for p in pns], CFG26)


def test_golden26_merged_table_p36(pages26):
    S = _rows26(pages26, [36])
    ini = [i for i in S["initiatives"] if i["initiative"] == "AAPI Community Support"]
    assert len(ini) == 1 and ini[0]["amount"] == 5060000 and ini[0]["statement_kind"] == "full"
    r = [a for a in S["awards"] if a["org"] == "A Place for Kids, Inc."]
    assert len(r) == 1 and r[0]["ein"] == "133624631" and r[0]["amount"] == 50000
    assert r[0]["initiative"] == "AAPI Community Support"


def test_golden26_two_line_name_p130(pages26):
    r = [a for a in _rows26(pages26, [130])["awards"] if a["ein"] == "131635308"]
    assert len(r) == 1 and r[0]["amount"] == 50000
    assert r[0]["org"] == ("Young Men's and Young Women's Hebrew Association of Washington "
                           "Heights and Inwood")
    assert any(f.startswith("continuation_row") for f in r[0]["row_flags"])


def test_golden26_headerless_carry_over_p157(pages26):
    S = _rows26(pages26, [156, 157])
    r = [a for a in S["awards"] if a["ein"] == "264417161"]
    assert len(r) == 1 and r[0]["amount"] == 98469 and "headerless_table" in r[0]["row_flags"]
    assert r[0]["org"] == "Tell Every Amazing Lady About Ovarian Cancer Foundation"
    hb = [i for i in S["initiatives"] if i["initiative"].startswith("Healthy Beginnings")]
    assert len(hb) == 1 and hb[0]["amount"] == 4393244


def test_golden26_bronx_defenders_p176(pages26):
    S = _rows26(pages26, [175, 176])
    r = [a for a in S["awards"] if a["pdf_page"] == 176 and a["ein"] in
         ("133931074", "113305406", "135562265") and a["amount"] > 5000000]
    assert sorted(a["amount"] for a in r) == [5533333, 5533333, 5533334]
    assert {a["org"] for a in r} == {"Bronx Defenders, The", "Brooklyn Defender Services",
                                     "Legal Aid Society"}


def test_golden26_amount_without_dollar_p111(pages26):
    r = [a for a in _rows26(pages26, [111])["awards"] if a["ein"] == "134127229"]
    assert len(r) == 1 and r[0]["amount"] == 75000 and r[0]["amount_printed"] == "75,000"
    assert "amount_no_dollar" in r[0]["row_flags"]


def test_golden26_box_in_one_cell_p218(pages26):
    ini = {i["initiative"]: i["amount"] for i in _rows26(pages26, [218])["initiatives"]}
    assert ini["BID Containerization"] == 5000000
    assert ini["Chamber on the Go and Small Business Assistance"] == 2252267


@pytest.mark.skipif(not os.path.exists(OUT26), reason="FY2026 outputs not built")
def test_snapshot26_rows_and_checks():
    with open(os.path.join(OUT26, "fy26_sc_awards.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9765
    assert sum(int(r["amount"]) for r in rows) == 545669395
    txt = open(os.path.join(OUT26, "fy26_sc_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "acceptance on p.176" in txt and "(PASS)" in txt
    assert "H17 floor, 9,529): 9,529" in txt


# --- FY2025 (config/schedule_c/fy2025.toml) ----------------------------------------------------
CFG25 = config.load(2025)
OUT25 = os.path.join(config.ROOT, CFG25["review_dir"], "data")
FY25_SWITCHES = ("header_two_bands", "box_title_letters", "amount_sliver_join",
                 "amount_odd_format", "header_span_cells", "split_boxes", "box_amount_cells",
                 "statement_in_cell")


def test_fy2025_switches_off_for_fy2026_and_fy2027():
    for c in (CFG, CFG26):
        for k in FY25_SWITCHES:
            assert not c["structure"].get(k)
        assert not c.get("vector_pages") and not c.get("no_summary")
        assert not c["image"].get("extra_roles")


def test_statement_amount_millions():
    assert structure.statement_amount("4.1 million") == 4100000
    assert structure.statement_amount("1 million") == 1000000
    assert structure.statement_amount("1,120,000") == 1120000
    assert structure.statement_amount(None) is None


def test_fy2025_statement_kinds():
    k = lambda t: structure.statement_kind(t, CFG25)
    assert k("The City Council will designate $490,000 post-adoption and has designated $4.1 "
             "million to the following providers for Fiscal 2025:") == ("partial", 490000, 4100000)
    assert k("The City Council for Fiscal 2025 and will designate $69,000 post-adoption and has "
             "designated $4.1 million to the following providers:")[0] == "partial"
    assert k("The City Council will designate $1,580,000 post-adoption and has designated and "
             "has designated $12.7 million to the following providers for Fiscal 2025:") \
        == ("partial", 1580000, 12700000)
    assert k("The City Council will designate $7,201,000 post-adoption and has designated "
             "$1,059,000 to the following organizations for Fiscal 2025:")[0] == "partial"
    assert k("This funding is directly allocated to the Research Library.")[0] == "direct"
    assert k("The City Council has designated directly to the City University of New York for "
             "the following institutes.")[0] == "direct"
    assert k("The City Council will designate awards post-adoption:")[0] == "reserve_all"


# Golden rows, read from the rendered FY2025 pages (2026-10-21), not copied from output.
@pytest.fixture(scope="module")
def pages25():
    ps = vector.read_pdf(CFG25["_pdf_abs"], pages={35, 36, 131, 149, 156, 157, 167, 168, 169,
                                                     183, 222, 233, 260},
                         x_tolerance=CFG25["x_tolerance"],
                         page_settings={v["page"]: {"snap_tolerance": v["snap_tolerance"]}
                                        for v in CFG25["vector_pages"]})
    return {p["page"]: p for p in structure.split_merged_tables(ps, CFG25)}


def _rows25(pages25, pns):
    return structure.build([pages25[p] for p in pns], CFG25)


def test_golden25_bronx_defenders_p169(pages25):
    S = _rows25(pages25, [169])
    r = [a for a in S["awards"] if a["amount"] and a["amount"] > 5000000]
    assert sorted((a["org"], a["ein"], a["amount"]) for a in r) == [
        ("Bronx Defenders, The", "133931074", 5533333),
        ("Brooklyn Defender Services", "113305406", 5533333),
        ("Legal Aid Society", "135562265", 5533334)]
    assert {a["initiative"] for a in r} == {"New York Immigrant Family Unity Project"}


def test_golden25_council_member_header_two_bands_p131(pages25):
    r = [a for a in _rows25(pages25, [131])["awards"] if a["ein"] == "611682898"]
    assert len(r) == 1 and r[0]["member"] == "Farias" and r[0]["amount"] == 35000
    assert r[0]["org"] == "ArtBridge Projects, Inc. - Council District 18"


def test_golden25_box_titles_p36_p149(pages25):
    titles = {i["initiative"] for i in _rows25(pages25, [36, 149])["initiatives"]}
    assert "Digital Inclusion and Literacy Initiative" in titles
    assert "Ending the Epidemic" in titles


def test_golden25_box_split_in_table_p35_and_amount_cells_p157(pages25):
    ini = {i["initiative"]: i["amount"] for i in _rows25(pages25, [35, 157])["initiatives"]}
    assert ini["Adult Literacy Pilot Project"] == 2500000
    assert ini["CUNY Social Work Fellows"] == 500000


def test_golden25_name_column_snap_p167(pages25):
    r = [a for a in _rows25(pages25, [167])["awards"] if a["ein"] == "113534833"]
    assert len(r) == 1 and r[0]["org"] == "Ansob Center for Refugees, Inc." and r[0]["amount"] == 45000


def test_golden25_odd_amount_p168(pages25):
    r = [a for a in _rows25(pages25, [168])["awards"] if a["ein"] == "112423857"]
    assert len(r) == 1 and r[0]["amount"] == 77000 and r[0]["amount_printed"] == "$77,000.00"
    assert "amount_odd_format" in r[0]["row_flags"]


def test_golden25_name_left_of_header_centre_p183(pages25):
    r = [a for a in _rows25(pages25, [183])["awards"] if a["ein"] == "141397918"]
    assert len(r) == 1 and r[0]["org"] == "Astor Services for Children & Families"
    assert r[0]["amount"] == 673888


def test_golden25_amount_last_digit_past_rule_p222_p260(pages25):
    r = [a for a in _rows25(pages25, [222])["awards"] if a["ein"] == "800259180"]
    assert len(r) == 1 and r[0]["amount"] == 200000 and r[0]["org"] == "Destination Tomorrow, Inc."
    ini = {i["initiative"]: i["amount"] for i in _rows25(pages25, [260])["initiatives"]}
    assert ini["HRA Teen RAPP"] == 250000


def test_golden25_section20_row_comes_back_split_p233(pages25):
    # DATA-ANOMALIES §20: the old parse put Corbin Hill's purpose into Council For Unity's name.
    r = {a["ein"]: a for a in _rows25(pages25, [233])["awards"]}
    assert r["112880221"]["org"] == "Council For Unity, Inc." and r["112880221"]["amount"] == 50000
    assert r["461206478"]["org"] == "Corbin Hill Food Project, Inc., The"
    assert "farm shares" in r["461206478"]["purpose"]


@pytest.mark.skipif(not os.path.exists(OUT25), reason="FY2025 outputs not built")
def test_snapshot25_rows_and_checks():
    with open(os.path.join(OUT25, "fy25_sc_awards.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9579
    assert sum(int(r["amount"]) for r in rows) == 471876698
    txt = open(os.path.join(OUT25, "fy25_sc_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "acceptance on p.169" in txt and "(PASS)" in txt


# --- FY2024 (config/schedule_c/fy2024.toml) ----------------------------------------------------
CFG24 = config.load(2024)
OUT24 = os.path.join(config.ROOT, CFG24["review_dir"], "data")
FY24_SWITCHES = ("hrule_tables", "open_top_rows", "loose_header", "split_boxes_after_rows",
                 "statement_loose_text")


def test_fy2024_switches_off_for_other_years():
    for c in (CFG, CFG26, CFG25):
        for k in FY24_SWITCHES:
            assert not c["structure"].get(k)
        assert not c.get("initiative_pages") and not c["image"].get("band_check")


def test_statement_designated_parts_add():
    k = structure.statement_kind(
        "The City Council has designated $1 million to Food Bank for New York City for school "
        "pantries, $59,000 to two community-based food organizations, and will designate $6.2 "
        "million post-adoption to additional community-based food organizations for Fiscal "
        "2024:", CFG24)
    assert k == ("partial", 6200000, 1059000)
    assert structure.statement_kind("The City Council will designate $418,442 post adoption The "
                                    "City Council has designated the following providers for "
                                    "Fiscal 2024:", CFG24) == ("reserve_rows", 418442, None)


def test_check_bands():
    from schedc_cv import imagegrid
    a = dict(award_id="x", bbox_pt=[0, 100, 10, 114])
    assert imagegrid.check_bands([a], [100.2, 113.9], 1.0)["x"] == ("bands_agree", [])
    assert imagegrid.check_bands([a], [113.9], 1.0)["x"][1] == ["no_rule_at_top"]
    assert imagegrid.check_bands([a], [100, 107, 114], 1.0)["x"][1] == ["rule_inside_row"]


# Golden rows, read from the rendered FY2024 pages (2026-10-21), not copied from output.
@pytest.fixture(scope="module")
def pages24():
    ps = vector.read_pdf(CFG24["_pdf_abs"], pages={35, 36, 40, 41, 63, 122, 124, 129, 130, 145,
                                                     176, 177, 178, 234, 242, 261},
                         x_tolerance=CFG24["x_tolerance"], hrule=True, open_top=True)
    return {p["page"]: p for p in structure.split_merged_tables(ps, CFG24)}


def _rows24(pages24, pns):
    return structure.build([pages24[p] for p in pns], CFG24)


def _one(S, ein, amount):
    r = [a for a in S["awards"] if a["ein"] == ein and a["amount"] == amount]
    assert len(r) == 1, (ein, amount, len(r))
    return r[0]


def test_golden24_hrule_table_p36_p63(pages24):
    r = _one(_rows24(pages24, [35, 36]), "113580935", 50000)   # p.36 continues p.35
    assert r["org"] == "Chhaya Community Development Corporation" and "hrule_table" in r["row_flags"]
    r = _one(_rows24(pages24, [63]), "133267496", 48000)
    assert r["org"] == "Avenues For Justice, Inc." and r["initiative"] == \
        "Alternatives to Incarceration (ATIs)"
    r = _one(_rows24(pages24, [124]), "135562167", 425000)
    assert r["org"] == "Bank Street College of Education"
    r = _one(_rows24(pages24, [176]), "134170232", 25000)
    assert r["org"] == "Adaptive Design Association, Inc." and r["initiative"] == "Autism Awareness"


def test_golden24_open_top_row_p41(pages24):
    r = _one(_rows24(pages24, [40, 41]), "814237999", 45000)
    assert r["member"] == "Salamanca" and r["agency"] == "DYCD"
    assert r["org"] == "Bronx Community Foundation, Inc., The - Council District 17"


def test_golden24_white_filled_columns_p178(pages24):
    r = _one(_rows24(pages24, [176, 177, 178]), "133149298", 45000)
    assert r["org"] == "New Alternatives for Children, Inc."


def test_golden24_two_boxes_in_one_table_p122(pages24):
    S = _rows24(pages24, [122])
    saves = sorted(i["amount"] for i in S["initiatives"]
                   if i["initiative"] == "Supportive Alternatives to Violent Encounters (SAVE)")
    assert saves == [600000, 1850000]
    assert _one(S, "020694269", 600000)["org"] == "Connect, Inc."


def test_golden24_landscape_inserts_belong_to_nyc_cleanup(pages24):
    S = _rows24(pages24, [129, 130, 145])
    moved = [a for a in S["awards"] if a["pdf_page"] == 130]
    assert moved and {a["initiative"] for a in moved} == {"NYC Cleanup"}
    assert all("reattributed" in a["row_flags"] for a in moved)
    r = [a for a in S["awards"] if a["ein"] == "134355067" and a["member"] == "Caban"]
    assert len(r) == 1 and r[0]["amount"] == 10000 and r[0]["initiative"] == "A Greener NYC"


def test_golden24_ein_as_printed_p261_and_section20_p234(pages24):
    r = _one(_rows24(pages24, [261]), "472288307", 107627)
    assert r["org"] == "Drama Club, Inc."          # the PDF repeats Digital Girl's EIN
    S = _rows24(pages24, [234])
    assert _one(S, "112880221", 50000)["org"] == "Council For Unity, Inc."
    assert _one(S, "461206478", 50000)["org"] == "Corbin Hill Food Project, Inc., The"


def test_golden24_mediabox_offset_p242(pages24):
    # p.242's MediaBox starts at (-18.03, 17.97); bbox_pt is from its top-left corner, so the
    # row's text is found there by pdfium, which reads from the same corner.
    import pypdfium2 as pdfium
    r = _one(_rows24(pages24, [242]), "133505372", 100000)
    assert r["org"].startswith("Medicare Rights Center")
    doc = pdfium.PdfDocument(CFG24["_pdf_abs"])
    pg = doc[241]
    x0, y0, x1, y1 = pg.get_mediabox()
    b = r["bbox_pt"]
    t = pg.get_textpage().get_text_bounded(left=x0 + b[0], bottom=y1 - b[3], right=x0 + b[2],
                                           top=y1 - b[1])
    doc.close()
    assert "Medicare Rights Center" in t and "133505372" in t


@pytest.mark.skipif(not os.path.exists(OUT24), reason="FY2024 outputs not built")
def test_snapshot24_rows_and_checks():
    with open(os.path.join(OUT24, "fy24_sc_awards.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9291
    assert sum(int(r["amount"]) for r in rows) == 453858561
    txt = open(os.path.join(OUT24, "fy24_sc_checks.txt"), encoding="utf-8").read()
    assert "FAIL" not in txt.replace("(FAIL)", "")
    assert "acceptance on p.242" in txt and "(PASS)" in txt
