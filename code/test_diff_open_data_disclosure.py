"""Tests for diff_open_data_disclosure.py (GitHub #85). Synthetic rows only; no network, no
cache. Each test names the outcome that would make it fail."""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diff_open_data_disclosure as D


def od(ein="131111111", amount="5000", **kw):
    r = {":id": kw.pop("id", "row-1"), "fiscal_year": kw.pop("fy", "2015"), "ein": ein,
         "amount": amount, "status": kw.pop("status", "Cleared"),
         "legal_name_of_organization": kw.pop("name", "Org, Inc."),
         "source": kw.pop("source", "Local"), "agency": kw.pop("agency", "DYCD"),
         "council_member": kw.pop("member", "Levin"), "mocs_id": kw.pop("mocs", "FY15 0001")}
    r.update(kw)
    return D.norm_od(r)


def ours(ein="131111111", amount="5000", **kw):
    r = {"fiscal_year": kw.pop("fy", "2015"), "mocs_id": "", "ein": ein, "amount": amount,
         "status": kw.pop("status", "Cleared"), "status_norm": kw.pop("status_norm", "cleared"),
         "legal_name": kw.pop("name", "Org, Inc."), "source": kw.pop("source", "Local"),
         "agency": kw.pop("agency", "DYCD"), "council_member": kw.pop("member", "Levin"),
         "source_file": "f.xlsx", "source_row": kw.pop("row", "2")}
    r.update(kw)
    return D.norm_ours(r)


def test_eight_digit_open_data_ein_is_padded_and_counted():
    r = od(ein="61629188")
    assert r["ein"] == "061629188" and r["ein_padded"] and r["ein_raw"] == "61629188"
    res = D.compare([r], [ours(ein="061629188")])
    assert res["matched"] == 1 and res["ein_padded_od"] == 1   # FAILS if padding is dropped


def test_hyphenated_ein_matches():
    assert D.compare([od(ein="13-1111111")], [ours()])["matched"] == 1


def test_multiset_counts_a_repeated_pair_twice():
    res = D.compare([od(), od(id="row-2")], [ours()])
    assert res["matched"] == 1 and len(res["od_only"]) == 1   # FAILS if keyed as a set


def test_never_matches_on_ein_alone():
    res = D.compare([od(amount="5000")], [ours(amount="6000")])
    assert res["matched"] == 0 and len(res["od_only"]) == 1 and len(res["ours_only"]) == 1


def test_member_is_not_part_of_the_key():
    res = D.compare([od(member="Richards")], [ours(member="Brooks-Powers")])
    assert res["matched"] == 1 and res["field_diff"]["council_member"] == 1


def test_rounding_to_dollars_is_a_separate_tier():
    res = D.compare([od(amount="5438")], [ours(amount="5437.5")])
    assert res["matched"] == 0 and res["matched_rounded_dollars"] == 1
    assert not res["od_only"] and not res["ours_only"]


def test_rounding_to_cents_is_a_separate_tier():
    res = D.compare([od(amount="7481.3")], [ours(amount="7481.296758")])
    assert res["matched_rounded_cents"] == 1 and res["matched_rounded_dollars"] == 0


def test_rounding_is_half_up_not_bankers():
    assert D.q(Decimal("8437.5"), 0) == Decimal(8438)       # banker's rounding gives 8438
    assert D.q(Decimal("23296.5"), 0) == Decimal(23297)     # banker's rounding gives 23296


def test_a_dollar_off_is_not_a_rounding_match():
    res = D.compare([od(amount="5439")], [ours(amount="5437.5")])
    assert res["matched_rounded_dollars"] == 0 and len(res["od_only"]) == 1


def test_nominations_are_not_matches():
    res = D.compare([od(ein="133407104", amount="2500", name="Friends")],
                    [ours(ein="113407104", amount="2500", name="Friends")])
    assert res["matched"] == 0 and len(res["od_only"]) == 1
    assert [k for k, _, _ in res["nominations"]] == ["ein_differs"]


def test_grantee_differs_nomination_on_same_slot():
    res = D.compare([od(ein="061629188", name="Mirabal", member="Levine", agency="HPD")],
                    [ours(ein="800209989", name="Palante", member="Levine", agency="HPD")])
    assert [k for k, _, _ in res["nominations"]] == ["grantee_differs"]


def test_status_norm_puts_extra_values_in_other_but_keeps_raw():
    r = od(status="Government")
    assert r["status_norm"] == "other" and r["status"] == "Government"
    n, t = D.totals([r, od(status="Revoked", id="r2"), od(status="Pending", id="r3")])
    assert n == {"other": 2, "pending": 1} and t["other"] == Decimal(10000)


def test_field_diffs_only_on_unambiguous_pairs():
    a = [od(name="A"), od(name="B", id="r2")]
    b = [ours(name="X"), ours(name="Y", row="3")]
    res = D.compare(a, b)
    assert res["matched"] == 2 and res["unique_pairs"] == 0
    assert res["field_diff"]["legal_name"] == 0     # FAILS if repeated keys are paired blindly


def test_text_is_cleaned_like_the_parser():
    r = od(name="Org, Inc.\u200b ")
    assert r["legal_name"] == "Org, Inc."


def test_summary_csv_has_one_row_per_year():
    res = D.compare([od()], [ours()])
    text = D.summary_csv([(2015, "x", res)])
    assert text.splitlines()[1].startswith("2015,x,1,1,0,1,")
