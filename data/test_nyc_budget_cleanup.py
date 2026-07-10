#!/usr/bin/env python3
"""
Hermetic regression tests for nyc_budget_cleanup.py — no live API.

Mock SODA payloads mirror the DOCUMENTED response shape (Engineering Standard sec 0):
Socrata .json serializes `number`-typed fields as JSON strings, so mock rows use string
values for fiscal_year / amounts, exactly as the live endpoint returns them.

Run:  python3 -m unittest test_nyc_budget_cleanup   (or: pytest)
"""

from __future__ import annotations

import unittest

import nyc_budget_cleanup as m


class DiscoverAdoptedSnapshotTests(unittest.TestCase):
    def test_picks_latest_publication_date_per_fiscal_year(self):
        """The Adopted snapshot is the max publication_date; earlier snapshots are dropped."""
        # Two FYs, each with Preliminary/Executive/Adopted snapshots (documented pattern).
        fake_rows = [
            {"fiscal_year": "2026", "publication_date": "20250116"},  # Preliminary
            {"fiscal_year": "2026", "publication_date": "20250501"},  # Executive
            {"fiscal_year": "2026", "publication_date": "20250630"},  # Adopted (max)
            {"fiscal_year": "2027", "publication_date": "20260217"},
            {"fiscal_year": "2027", "publication_date": "20260630"},  # Adopted (max)
            {"fiscal_year": "1999", "publication_date": "19990101"},  # out of range -> ignored
        ]
        orig_fy, orig_get = m.FISCAL_YEARS, m.soda_get
        m.FISCAL_YEARS = [2026, 2027]
        m.soda_get = lambda params: fake_rows
        try:
            adopted = m.discover_adopted_snapshots()
        finally:
            m.FISCAL_YEARS, m.soda_get = orig_fy, orig_get
        self.assertEqual(adopted, {2026: "20250630", 2027: "20260630"})

    def test_missing_snapshot_aborts(self):
        orig_fy, orig_get = m.FISCAL_YEARS, m.soda_get
        m.FISCAL_YEARS = [2026, 2027]
        m.soda_get = lambda params: [{"fiscal_year": "2026", "publication_date": "20250630"}]
        try:
            with self.assertRaises(SystemExit):
                m.discover_adopted_snapshots()  # FY2027 absent -> abort
        finally:
            m.FISCAL_YEARS, m.soda_get = orig_fy, orig_get


class BuildWhereTests(unittest.TestCase):
    def test_or_of_fy_and_publication_date(self):
        orig_fy = m.FISCAL_YEARS
        m.FISCAL_YEARS = [2026, 2027]
        try:
            where = m.build_where({2026: "20250630", 2027: "20260630"})
        finally:
            m.FISCAL_YEARS = orig_fy
        self.assertEqual(
            where,
            "(fiscal_year=2026 AND publication_date='20250630') OR "
            "(fiscal_year=2027 AND publication_date='20260630')",
        )


class PivotTests(unittest.TestCase):
    def _rows(self):
        # One agency, one unit, two FYs — appropriations != expenditures (the two series).
        return [
            {
                "agency_number": "040", "agency_name": "DEPARTMENT OF EDUCATION",
                "unit_appropriation_number": "402", "unit_appropriation_name": "GEN ED",
                "fiscal_year": "2026",
                "appropriations": "100.0", "expenditures": "120.0",
            },
            {
                "agency_number": "040", "agency_name": "DEPARTMENT OF EDUCATION",
                "unit_appropriation_number": "402", "unit_appropriation_name": "GEN ED",
                "fiscal_year": "2027",
                "appropriations": "110.0", "expenditures": "110.0",
            },
        ]

    def test_schema_contract_and_value_mapping(self):
        orig_fy = m.FISCAL_YEARS
        m.FISCAL_YEARS = [2026, 2027]
        try:
            recs = m.pivot(self._rows())
        finally:
            m.FISCAL_YEARS = orig_fy
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["Fund"], "DEPARTMENT OF EDUCATION")
        self.assertEqual(rec["Department"], "GEN ED")
        self.assertEqual(rec["Control Officer"], "DEPARTMENT OF EDUCATION")  # v1 placeholder
        self.assertEqual(rec["Department ID"], "402")
        self.assertEqual(rec["Short Title"], "")
        # adopted_budget_amount -> "Adopted", current_modified_budget_amount -> "Modified"
        self.assertEqual(rec["Adopted 2026"], "100")
        self.assertEqual(rec["Modified 2026"], "120")
        self.assertEqual(rec["Adopted 2027"], "110")

    def test_sums_within_group_not_across_snapshots(self):
        """Two line items in the SAME (agency, unit, fy) sum; they do NOT triple-count."""
        rows = self._rows()
        # A second FY2026 line item for the same group.
        rows.append({
            "agency_number": "040", "agency_name": "DEPARTMENT OF EDUCATION",
            "unit_appropriation_number": "402", "unit_appropriation_name": "GEN ED",
            "fiscal_year": "2026", "appropriations": "50.0", "expenditures": "5.0",
        })
        orig_fy = m.FISCAL_YEARS
        m.FISCAL_YEARS = [2026, 2027]
        try:
            recs = m.pivot(rows)
        finally:
            m.FISCAL_YEARS = orig_fy
        self.assertEqual(recs[0]["Adopted 2026"], "150")  # 100 + 50

    def test_latest_year_name_wins_on_rename(self):
        rows = self._rows()
        rows[1]["unit_appropriation_name"] = "GENERAL EDUCATION (RENAMED)"  # FY2027 label
        orig_fy = m.FISCAL_YEARS
        m.FISCAL_YEARS = [2026, 2027]
        try:
            recs = m.pivot(rows)
        finally:
            m.FISCAL_YEARS = orig_fy
        self.assertEqual(recs[0]["Department"], "GENERAL EDUCATION (RENAMED)")


class GateTests(unittest.TestCase):
    def _rec(self, fy2026_appr: float):
        rec = {c: "" for c in m.STATIC_COLUMNS}
        for y in m.FISCAL_YEARS:
            rec[f"Adopted {y}"] = "0"
            rec[f"Modified {y}"] = "0"
        rec["Adopted 2026"] = str(fy2026_appr)
        return rec

    def test_passes_near_114b(self):
        self.assertAlmostEqual(
            m.validate_gate([self._rec(114_384_991_832)]), 114_384_991_832, delta=1
        )

    def test_triple_count_would_abort(self):
        """If filtering failed and the total triple-counted (~$343B), the gate aborts."""
        with self.assertRaises(SystemExit):
            m.validate_gate([self._rec(343_000_000_000)])


class FormatTests(unittest.TestCase):
    def test_whole_dollars_are_ints(self):
        self.assertEqual(m._fmt_amount(100.0), "100")
        self.assertEqual(m._fmt_amount(114384991832.0), "114384991832")

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
        self.assertNotIn("FY2017", cols)  # guards against the pre-correction schema
        # These prefixes MUST match js/app.js apropTitle / expendTitle (column/label coupling).
        self.assertEqual((m.APROP_LABEL, m.EXPEND_LABEL), ("Adopted", "Modified"))
        # Adopted precedes its Modified for each year.
        self.assertLess(cols.index("Adopted 2020"), cols.index("Modified 2020"))


if __name__ == "__main__":
    unittest.main()
