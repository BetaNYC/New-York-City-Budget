#!/usr/bin/env python3
"""
Hermetic regression tests for agency_budget_cleanup.py — no live API.

Mock SODA payloads mirror the DOCUMENTED response shape (Engineering Standard sec 0):
Socrata .json serializes `number`-typed fields as JSON strings, so mock rows use string
values for fiscal_year / amounts, exactly as the live endpoint returns them.

The year-mapping fixtures use real figures from Open Data mwzb-yiwb and OMB's printed FY2026
Adopted Budget, Expense/Revenue/Contract volume (adopt25/erc6-25.pdf, page 182E, Manhattan
Community Board 1, agency 341), so a regression to the old off-by-one labels fails here.

Run:  python -m pytest code/test_agency_budget_cleanup.py
      (or, from code/: python3 -m unittest test_agency_budget_cleanup)
"""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import agency_budget_cleanup as m

# The committed CSV the agency explorer loads. In this repo it must exist: the class below used
# to skip when it was missing, which would let a lost file pass CI.
CSV_PATH = m.DEFAULT_OUT / "nyc_budget.csv"


class _Years:
    """Context manager: temporarily narrow FISCAL_YEARS."""

    def __init__(self, years):
        self.years = years

    def __enter__(self):
        self.orig = m.FISCAL_YEARS
        m.FISCAL_YEARS = list(self.years)

    def __exit__(self, *exc):
        m.FISCAL_YEARS = self.orig


def _row(tag, agency, unit, adopted, modified, finplan,
         agency_name="MANHATTAN COMMUNITY BOARD #1", unit_name="PERSONAL SERVICES"):
    return {
        "agency_number": agency, "agency_name": agency_name,
        "unit_appropriation_number": unit, "unit_appropriation_name": unit_name,
        "fiscal_year": str(tag),
        "adopted": str(adopted), "modified": str(modified), "finplan": str(finplan),
    }


# Real Open Data June-release rows for MN01 (agency 341), units 001 PS and 002 OTPS.
# Release tagged 2026 (20250630) == OMB FY2026 Adopted Budget, page 182E.
MN01_ROWS = [
    # tag 2025 (20240630): finplan = FY2025 adopted
    _row(2025, "341", "001", 268673, 232431, 267484),
    _row(2025, "341", "002", 7245, 183353, 27245, unit_name="OTHER THAN PERSONAL SERVICES"),
    # tag 2026 (20250630): adopted = FY2025 adopted, modified = FY2025 modified (June 2025),
    #                      finplan = FY2026 adopted
    _row(2026, "341", "001", 267484, 249484, 275060),
    _row(2026, "341", "002", 27245, 190939, 27245, unit_name="OTHER THAN PERSONAL SERVICES"),
    # tag 2027 (20260630): modified = FY2026 modified (June 2026), finplan = FY2027 adopted
    _row(2027, "341", "001", 275060, 258560, 275060),
    _row(2027, "341", "002", 27245, 212939, 27245, unit_name="OTHER THAN PERSONAL SERVICES"),
]
MN01_RELEASES = {2025: "20240630", 2026: "20250630", 2027: "20260630"}


def _by_unit(records):
    return {(r[m.AGENCY_KEY], r["Department ID"]): r for r in records}


class DiscoverJuneReleaseTests(unittest.TestCase):
    def _run(self, fake_rows, years):
        orig_get = m.soda_get
        m.soda_get = lambda params: fake_rows
        try:
            with _Years(years):
                return m.discover_june_releases()
        finally:
            m.soda_get = orig_get

    def test_picks_june_release_per_tag(self):
        fake = [
            {"fiscal_year": "2026", "publication_date": "20250116"},  # Preliminary
            {"fiscal_year": "2026", "publication_date": "20250501"},  # Executive
            {"fiscal_year": "2026", "publication_date": "20250630"},  # Adopted (June)
            {"fiscal_year": "2027", "publication_date": "20260217"},
            {"fiscal_year": "2027", "publication_date": "20260630"},
            {"fiscal_year": "1999", "publication_date": "19990101"},  # out of range
        ]
        self.assertEqual(self._run(fake, [2026, 2027]), {2026: "20250630", 2027: "20260630"})

    def test_next_tag_included_when_adopted(self):
        """The tag after the last shown year supplies the newest Modified, if adopted."""
        fake = [
            {"fiscal_year": "2026", "publication_date": "20250630"},
            {"fiscal_year": "2027", "publication_date": "20260630"},
        ]
        self.assertEqual(self._run(fake, [2026]), {2026: "20250630", 2027: "20260630"})

    def test_next_tag_ignored_while_only_preliminary(self):
        """A January release of the next tag is not an adoption release; don't use it."""
        fake = [
            {"fiscal_year": "2027", "publication_date": "20260630"},
            {"fiscal_year": "2028", "publication_date": "20270115"},  # Preliminary only
        ]
        self.assertEqual(self._run(fake, [2027]), {2027: "20260630"})

    def test_earliest_tag_june_release_counts(self):
        """FY2017's first two releases were April and June 2016; June is the one to use."""
        fake = [
            {"fiscal_year": "2017", "publication_date": "20160426"},
            {"fiscal_year": "2017", "publication_date": "20160615"},
        ]
        self.assertEqual(self._run(fake, [2017]), {2017: "20160615"})

    def test_missing_june_release_aborts(self):
        fake = [
            {"fiscal_year": "2026", "publication_date": "20250630"},
            {"fiscal_year": "2027", "publication_date": "20260217"},  # not adopted yet
        ]
        with self.assertRaises(SystemExit):
            self._run(fake, [2026, 2027])


class BuildWhereTests(unittest.TestCase):
    def test_or_of_tag_and_publication_date(self):
        self.assertEqual(
            m.build_where({2027: "20260630", 2026: "20250630"}),
            "(fiscal_year=2026 AND publication_date='20250630') OR "
            "(fiscal_year=2027 AND publication_date='20260630')",
        )


class NormCodeTests(unittest.TestCase):
    def test_pads_pre_2023_codes(self):
        self.assertEqual(m.norm_code("1"), "001")
        self.assertEqual(m.norm_code("40"), "040")
        self.assertEqual(m.norm_code("040"), "040")
        self.assertEqual(m.norm_code(" 341 "), "341")


class YearMappingTests(unittest.TestCase):
    """The off-by-one fix: each label must describe the fiscal year it names."""

    def _records(self, years=(2025, 2026, 2027), releases=MN01_RELEASES):
        with _Years(years):
            return _by_unit(m.pivot(MN01_ROWS, releases))

    def test_omb_page_182e_mn01(self):
        recs = self._records()
        ps, otps = recs[("341", "001")], recs[("341", "002")]
        self.assertEqual(ps["Adopted 2025"], "267484")
        self.assertEqual(ps["Modified 2025"], "249484")
        self.assertEqual(otps["Modified 2025"], "190939")
        self.assertEqual(ps["Adopted 2026"], "275060")
        self.assertEqual(otps["Adopted 2026"], "27245")

    def test_old_off_by_one_values_are_gone(self):
        """Before the fix, 'Adopted 2026' showed FY2025's $267,484."""
        self.assertNotEqual(self._records()[("341", "001")]["Adopted 2026"], "267484")

    def test_modified_comes_from_next_release(self):
        self.assertEqual(self._records()[("341", "001")]["Modified 2026"], "258560")

    def test_newest_modified_is_empty_not_zero(self):
        recs = self._records()
        self.assertEqual(recs[("341", "001")]["Modified 2027"], "")
        self.assertEqual(recs[("341", "001")]["Adopted 2027"], "275060")

    def test_earliest_year_does_not_use_prior_year_adopted(self):
        """The release tagged 2025's adopted_budget_amount (268,673) is FY2024; it must not
        appear under any label when 2025 is the first year shown."""
        ps = self._records()[("341", "001")]
        self.assertNotIn("268673", ps.values())

    def test_padded_and_unpadded_codes_merge(self):
        rows = [
            _row(2022, "341", "1", 0, 0, 100),     # pre-2023 style
            _row(2023, "341", "001", 100, 90, 110),  # padded
        ]
        with _Years([2022]):
            recs = m.pivot(rows, {2022: "20210630", 2023: "20220614"})
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["Department ID"], "001")
        self.assertEqual(recs[0]["Adopted 2022"], "100")
        self.assertEqual(recs[0]["Modified 2022"], "90")

    def test_sums_within_group(self):
        rows = MN01_ROWS + [_row(2026, "341", "001", 0, 0, 40)]
        with _Years([2026]):
            recs = _by_unit(m.pivot(rows, MN01_RELEASES))
        self.assertEqual(recs[("341", "001")]["Adopted 2026"], "275100")

    def test_latest_release_name_wins(self):
        rows = list(MN01_ROWS)
        rows[4] = dict(rows[4], unit_appropriation_name="PERSONAL SERVICES (RENAMED)")
        with _Years([2026]):
            recs = _by_unit(m.pivot(rows, MN01_RELEASES))
        self.assertEqual(recs[("341", "001")]["Department"], "PERSONAL SERVICES (RENAMED)")


class CrossCheckTests(unittest.TestCase):
    def test_both_routes_agree_on_real_rows(self):
        with _Years([2025, 2026, 2027]):
            diffs = m.check_release_agreement(MN01_ROWS, MN01_RELEASES)
        self.assertEqual(diffs, {2025: 0.0, 2026: 0.0})

    def test_disagreement_aborts(self):
        rows = list(MN01_ROWS)
        rows[0] = dict(rows[0], finplan="999")
        with _Years([2025, 2026, 2027]), self.assertRaises(SystemExit):
            m.check_release_agreement(rows, MN01_RELEASES)


class GateTests(unittest.TestCase):
    def _records(self, **override):
        rec = {c: "" for c in m.STATIC_COLUMNS}
        rec[m.AGENCY_KEY] = "999"
        rec["Department ID"] = "001"
        for y in m.FISCAL_YEARS:
            rec[f"Adopted {y}"] = "0"
            rec[f"Modified {y}"] = "0"
        rec["Adopted 2026"] = str(117_791_473_676 - 275_060 - 27_245)
        rec["Adopted 2025"] = str(114_384_991_832 - 267_484 - 27_245)
        rec["Modified 2025"] = str(123_844_584_236 - 249_484 - 190_939)
        rec.update(override)
        ps = {c: "0" for c in rec} | {
            m.AGENCY_KEY: "341", "Department ID": "001",
            "Adopted 2025": "267484", "Modified 2025": "249484", "Adopted 2026": "275060"}
        otps = {c: "0" for c in rec} | {
            m.AGENCY_KEY: "341", "Department ID": "002",
            "Adopted 2025": "27245", "Modified 2025": "190939", "Adopted 2026": "27245"}
        return [rec, ps, otps]

    def test_passes_on_omb_numbers(self):
        seen = m.validate_gate(self._records())
        self.assertEqual(round(seen["Adopted 2026"]), 117_791_473_676)

    def test_gate_constants_match_omb_gross_totals(self):
        self.assertEqual(m.GATE_CITYWIDE[("Adopted", 2026)], 117_791_473_676)
        self.assertEqual(m.GATE_CITYWIDE[("Adopted", 2025)], 114_384_991_832)
        self.assertEqual(m.GATE_CITYWIDE[("Modified", 2025)], 123_844_584_236)

    def test_old_off_by_one_total_aborts(self):
        """The pre-fix CSV called $114.4B 'Adopted 2026'. That must now fail."""
        recs = self._records(**{"Adopted 2026": str(114_384_991_832 - 302_305)})
        with self.assertRaises(SystemExit):
            m.validate_gate(recs)

    def test_triple_count_aborts(self):
        with self.assertRaises(SystemExit):
            m.validate_gate(self._records(**{"Adopted 2026": "343000000000"}))


class FormatTests(unittest.TestCase):
    def test_whole_dollars_are_ints(self):
        self.assertEqual(m._fmt_amount(100.0), "100")
        self.assertEqual(m._fmt_amount(117791473676.0), "117791473676")

    def test_cents_preserved_when_present(self):
        self.assertEqual(m._fmt_amount(100.25), "100.25")

    def test_no_currency_or_comma_formatting(self):
        out = m._fmt_amount(1234567.0)
        self.assertNotIn("$", out)
        self.assertNotIn(",", out)


class HeaderContractTests(unittest.TestCase):
    def test_year_columns_are_plain_year_pairs(self):
        cols = m.year_columns()
        self.assertIn("Adopted 2017", cols)
        self.assertIn("Modified 2027", cols)
        self.assertNotIn("FY2017", cols)
        self.assertEqual((m.APROP_LABEL, m.EXPEND_LABEL), ("Adopted", "Modified"))
        self.assertLess(cols.index("Adopted 2020"), cols.index("Modified 2020"))

    def test_internal_agency_key_not_written(self):
        self.assertNotIn(m.AGENCY_KEY, m.STATIC_COLUMNS + m.year_columns())

    def test_look_at_cook_leftover_columns_are_gone(self):
        # #266: Control Officer equaled Fund on all 764 rows; the other three were empty.
        for col in m.REMOVED_COLUMNS:
            self.assertNotIn(col, m.STATIC_COLUMNS)


class ShippedCsvTests(unittest.TestCase):
    """The CSV the site actually loads must carry OMB's published figures."""

    @classmethod
    def setUpClass(cls):
        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            cls.rows = list(csv.DictReader(f))

    def _total(self, col):
        return round(sum(float(r[col]) for r in self.rows if r[col] != ""))

    def _mn01(self, unit, col):
        rows = [r for r in self.rows
                if r["Fund"] == "MANHATTAN COMMUNITY BOARD #1" and r["Department ID"] == unit]
        self.assertEqual(len(rows), 1, f"expected one MN01 unit {unit} row")
        return int(rows[0][col])

    def test_citywide_fy2026_adopted(self):
        self.assertEqual(self._total("Adopted 2026"), 117_791_473_676)

    def test_citywide_fy2025(self):
        self.assertEqual(self._total("Adopted 2025"), 114_384_991_832)
        self.assertEqual(self._total("Modified 2025"), 123_844_584_236)

    def test_mn01_omb_page_182e(self):
        self.assertEqual(self._mn01("001", "Adopted 2025"), 267_484)
        self.assertEqual(self._mn01("001", "Modified 2025"), 249_484)
        self.assertEqual(self._mn01("002", "Modified 2025"), 190_939)
        self.assertEqual(self._mn01("001", "Adopted 2026"), 275_060)
        self.assertEqual(self._mn01("002", "Adopted 2026"), 27_245)

    def test_department_ids_are_three_digit(self):
        self.assertTrue(all(len(r["Department ID"]) == 3 for r in self.rows))

    def test_csv_has_no_look_at_cook_leftover_columns(self):
        for col in m.REMOVED_COLUMNS:
            self.assertNotIn(col, self.rows[0], col)

    def test_newest_modified_empty(self):
        last = m.FISCAL_YEARS[-1]
        self.assertTrue(all(r[f"Modified {last}"] == "" for r in self.rows))


if __name__ == "__main__":
    unittest.main()
