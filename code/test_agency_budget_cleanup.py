#!/usr/bin/env python3
"""
Tests for the City agency budgets download, viz/agencies/data/nyc_budget.csv — no network.

Since #288 code/agency_budget_cleanup.py does no year math: the file is written from the MCP
index (mcp/scripts/agency-budget.mjs, the one loader, then viz/explorer/scripts/agency-csv.mjs),
and viz/explorer/test/agency-csv.test.mjs checks it equals the index byte for byte. These tests
check the shipped file against OMB's printed Adopted Budget (adopt25/erc6-25.pdf, page 182E for
Manhattan Community Board 1), and that the script keeps no year rule of its own.

Run:  python -m pytest code/test_agency_budget_cleanup.py
      (or, from code/: python3 -m unittest test_agency_budget_cleanup)
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

import agency_budget_cleanup as m

# The committed CSV. In this repo it must exist: a lost file must fail, never skip.
CSV_PATH = m.DEFAULT_OUT / "nyc_budget.csv"


class NoOwnYearRuleTests(unittest.TestCase):
    def test_the_script_does_no_year_math_and_reads_no_open_data(self):
        # FAILS if the year rule comes back here: it lives in mcp/scripts/agency-budget.mjs only.
        src = Path(m.__file__).read_text(encoding="utf-8")
        code = re.sub(r'"""[\s\S]*?"""', "", src)
        for word in ("financial_plan_amount", "current_modified_budget_amount", "adopted_budget_amount",
                     "data.cityofnewyork.us", "urllib", "FISCAL_YEARS"):
            self.assertNotIn(word, code, word)
        self.assertTrue(m.WRITER.exists(), m.WRITER)
        self.assertTrue(m.INDEX_BUILD.exists(), m.INDEX_BUILD)

    def test_look_at_cook_leftover_columns_are_gone(self):
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
        last = max(int(c.split(" ")[1]) for c in self.rows[0] if c.startswith("Adopted "))
        self.assertTrue(all(r[f"Modified {last}"] == "" for r in self.rows))

    def test_header_is_the_contract(self):
        cols = list(self.rows[0])
        self.assertEqual(cols[:3], m.STATIC_COLUMNS)
        self.assertEqual(cols[3:5], ["Adopted 2017", "Modified 2017"])
        self.assertTrue(all(re.fullmatch(r"(Adopted|Modified) \d{4}", c) for c in cols[3:]))


if __name__ == "__main__":
    unittest.main()
