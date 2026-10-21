"""open_data_registry.py -- the NYC Open Data datasets the repo tracks (research/2026-10-21-
open-data-tracking/PLAN.md §3, approved by Noel Hidalgo 2026-10-21).

One entry per tier 1 and tier 2 dataset. Tier 3 (held) datasets are not listed, so nothing
watches or pulls them. Shared by code/open_data_watch.py (metadata only) and
code/fetch_open_data_snapshots.py (rows).

  columns    the schema verified against the dataset's live metadata (/api/views/<id>.json) on
             2026-10-21; a row or a metadata read with any other field is a stop.
  policy     `every_change`: every snapshot whose rowsUpdatedAt moved is kept (small datasets);
             `latest_only`: only the latest snapshot is kept (the two big OMB datasets), PLAN Q3.
  where      a SoQL $where for a Council-relevant extract (PLAN Q2); recorded in the MANIFEST.
  fetcher    which script writes the snapshot (the four 2026-10-14 pulls keep their scripts).
"""

DOMAIN = "https://data.cityofnewyork.us"

DATASETS = {
    # ---- tier 1: record-level --------------------------------------------------------------
    "4d7f-74pe": {
        "name": "City Council Discretionary Funding", "tier": 1, "family": "expense",
        "cadence": "quarterly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_4d7f74pe.py"},
    "ujre-m2tj": {
        "name": "Discretionary Award Tracker", "tier": 1, "family": "expense",
        "cadence": "quarterly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_snapshots.py",
        "publisher": "Mayor's Office of Contract Services (MOCS)",
        "columns": ["post_date", "mocs_award_number", "agency", "vendor_name", "amount", "source",
                    "statussummary"],
        "dictionary": ("3b29ecda-dcfb-49ab-846a-79544c99d4de",
                       "DICTIONARY Discretionary Award Tracker.xlsx")},
    "t474-a92g": {
        "name": "City Council Capital Budget", "tier": 1, "family": "capital_award",
        "cadence": "monthly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_capital.py"},
    # ---- tier 2: line-level or project-level context ---------------------------------------
    "46m8-77gv": {
        "name": "Capital Budget", "tier": 2, "family": "capital_line",
        "cadence": "monthly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_capital.py"},
    "2cmn-uidm": {
        "name": "Capital Commitment Plan", "tier": 2, "family": "capital_line",
        "cadence": "monthly", "policy": "latest_only",
        "fetcher": "code/fetch_open_data_capital.py"},
    "djxg-kcfi": {
        "name": "Capital Projects Database (CPDB) - Commitments", "tier": 2,
        "family": "capital_line", "cadence": "monthly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_snapshots.py",
        "publisher": "Department of City Planning (DCP)",
        "columns": ["ccpversion", "maprojid", "magency", "projectid", "projectdescription",
                    "sagencyacro", "sagencyname", "budgetline", "projecttype", "plancommdate",
                    "commitmentdescription", "commitmentcode", "typc", "typcname", "ccnonexempt",
                    "ccexempt", "totalcityplannedcommit", "nccstate", "nccfederal", "nccother",
                    "totalnoncityplannedcommit", "totalplannedcommit"],
        "dictionary": None},
    "mwzb-yiwb": {
        "name": "Expense Budget", "tier": 2, "family": "terms_unit",
        "cadence": "monthly", "policy": "latest_only",
        "fetcher": "code/fetch_open_data_snapshots.py",
        "publisher": "Mayor's Office of Management & Budget (OMB)",
        "columns": ["publication_date", "fiscal_year", "agency_number", "agency_name",
                    "unit_appropriation_number", "unit_appropriation_name", "budget_code_number",
                    "budget_code_name", "object_class_number", "object_class_name", "object_code",
                    "object_code_name", "intra_city_purchase_code", "responsibility_center_code",
                    "responsibility_center_name",
                    "personal_service_other_than_personal_service_indicator",
                    "financial_plan_savings_flag", "adopted_budget_amount",
                    "current_modified_budget_amount", "financial_plan_amount",
                    "adopted_budget_position", "current_modified_budget_position",
                    "financial_plan_position", "adopted_budget_number_of_contracts",
                    "current_modified_budget_number_of_contracts",
                    "financial_plan_number_of_contracts"],
        "dictionary": ("6b9fbf29-84db-4da3-bb2e-b78a61169c6c", "Expense_Budget_Data_Dictionary.xlsx"),
        # Filled by code/fetch_open_data_snapshots.py from the T&C files (terms_extract_where).
        "where": "terms"},
    "uvw5-9znb": {
        "name": "City Council Members (1999 to Present)", "tier": 2, "family": "reference",
        "cadence": "monthly", "policy": "every_change",
        "fetcher": "code/fetch_open_data_snapshots.py",
        "publisher": "City Council (NYCC)",
        "columns": ["name", "council_member_id", "term_start", "term_end", "district", "office_id"],
        "dictionary": ("1952f7f0-94a1-4c1c-aed3-5377b64cb7f1",
                       "City_Council_Members_Data_Dictionary.xlsx")},
}
