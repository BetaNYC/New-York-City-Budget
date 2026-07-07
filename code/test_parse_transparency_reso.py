#!/usr/bin/env python3
"""
Regression tests for the FY26 Transparency Resolution parser.

Two layers (mirrors test_parse_capital.py):
  1. Invariants on the committed combined CSV (always run) -- schema, EIN/amount hygiene,
     no member/org column bleed, and the load-bearing AICE fact (the $1M Artificial
     Intelligence Community Engagement pool nets to zero across 23 named recipients).
  2. Re-parse from the source PDFs when present (skipped where the source tree is absent,
     e.g. CI) -- asserts the parser still produces the expected shape from scratch.

These documents print no totals, so there is no printed-total reconciliation to assert;
the strongest available invariant is the AICE transfer net-out.

Run: pytest code/test_parse_transparency_reso.py
 or: python code/test_parse_transparency_reso.py
"""
import csv, os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
COMBINED = os.path.join(REPO, 'data', 'fy26', 'transparency-resolutions',
                        'fy26_transparency_all.csv')
SRC = os.path.join(REPO, 'source', 'FY26', 'transparency-resolutions')

COLS = ['resolution', 'date', 'chart', 'fiscal_year', 'action', 'source',
        'council_member', 'organization', 'program', 'ein', 'amount', 'agency',
        'agy_num', 'ua', 'purpose', 'flags']
ACTIONS = {'designate', 'rescind', 'purpose_change'}


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------- layer 1: committed-CSV invariants ----------

@pytest.mark.skipif(not os.path.exists(COMBINED), reason='combined CSV not built yet')
def test_schema_and_hygiene():
    rows = _rows(COMBINED)
    assert rows, 'combined CSV is empty'
    assert list(rows[0].keys()) == COLS, 'unexpected columns'
    for r in rows:
        assert r['action'] in ACTIONS, f'bad action {r["action"]!r}'
        # EIN is 9 digits (dash stripped)
        assert len(r['ein']) == 9 and r['ein'].isdigit(), f'bad EIN {r["ein"]!r}'
        # amount is a signed integer; rescissions are negative, designations positive
        amt = int(r['amount'])
        if r['action'] == 'rescind':
            assert amt < 0, f'rescind not negative: {amt}'
        elif r['action'] == 'designate':
            assert amt > 0, f'designate not positive: {amt}'
        # council_member must never contain an organization suffix (column-bleed guard)
        assert not any(w in r['council_member'] for w in
                       (', Inc', 'Department', 'Corporation', 'Association', ' LLC')), \
            f'org text bled into member: {r["council_member"]!r}'


@pytest.mark.skipif(not os.path.exists(COMBINED), reason='combined CSV not built yet')
def test_all_ten_resolutions_present():
    resos = {int(r['resolution']) for r in _rows(COMBINED)}
    assert resos == set(range(1, 11)), f'missing resolutions: {set(range(1, 11)) - resos}'


@pytest.mark.skipif(not os.path.exists(COMBINED), reason='combined CSV not built yet')
def test_aice_million_dollar_pool_nets_to_zero():
    """The load-bearing fact: the FY26 Artificial Intelligence Community Engagement $1M
    initiative rescinds $1,000,000 from the DYCD pool and redistributes exactly that to
    named recipients -> net zero, >=20 recipients, all in resolution 3."""
    aice = [r for r in _rows(COMBINED) if 'Artificial Intelligence' in r['chart']]
    assert aice, 'AICE chart not found'
    assert {r['resolution'] for r in aice} == {'3'}
    designated = sum(int(r['amount']) for r in aice if int(r['amount']) > 0)
    rescinded = sum(int(r['amount']) for r in aice if int(r['amount']) < 0)
    recips = [r for r in aice if int(r['amount']) > 0]
    assert designated == 1_000_000, f'AICE designated ${designated:,} != $1,000,000'
    assert rescinded == -1_000_000, f'AICE rescinded ${rescinded:,} != -$1,000,000'
    assert designated + rescinded == 0, 'AICE pool does not net to zero'
    assert len(recips) >= 20, f'expected >=20 AICE recipients, got {len(recips)}'


@pytest.mark.skipif(not os.path.exists(COMBINED), reason='combined CSV not built yet')
def test_unresolved_org_rate_is_small():
    """Dense-chart coordinate artifacts leave a few award rows with an orphaned org name.
    Guard that this stays rare (<1%); a regression that scrambles extraction would spike it."""
    rows = _rows(COMBINED)
    miss = [r for r in rows if not r['organization'].strip() and r['ein'] != '136400434']
    assert len(miss) / len(rows) < 0.01, f'unresolved-org rate too high: {len(miss)}/{len(rows)}'


# ---------- layer 2: re-parse from source (skipped when PDFs absent) ----------

@pytest.mark.skipif(not os.path.isdir(SRC), reason='source PDFs not present')
def test_reparse_from_source_matches():
    sys.path.insert(0, HERE)
    import parse_transparency_reso as P
    import glob
    pdfs = sorted(glob.glob(os.path.join(SRC, 'Transparency-Reso-*.pdf')))
    assert len(pdfs) == 10, f'expected 10 source PDFs, found {len(pdfs)}'
    roster = P.default_roster()
    # parse resolution 3 (contains AICE) and re-check the net-out from scratch
    reso3 = next(p for p in pdfs if '-03-' in os.path.basename(p))
    rows = P.parse(reso3, 3, '2025-10-29', roster)
    aice = [r for r in rows if 'Artificial Intelligence' in r['chart']]
    assert sum(r['amount'] for r in aice) == 0, 'AICE net-out failed on fresh parse'
    assert sum(r['amount'] for r in aice if r['amount'] > 0) == 1_000_000


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v']))
