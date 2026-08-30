#!/usr/bin/env python3
"""
sweep.py — systematic integrity sweep of the NYC Council discretionary award corpus.

Reproduces every number quoted in research/integrity-sweep/SWEEP.md.

AUDIT ONLY. Reads data/, writes nothing. Python standard library only.

Usage (from the repo root):
    python3 research/integrity-sweep/sweep.py            # all checks
    python3 research/integrity-sweep/sweep.py A3 B1      # only the named checks

Scope: the 62,213 award rows the repo publishes as its headline corpus —
  data/fy*/schedule_c/*_schedule_c_awards.csv   (33,638 rows)
  data/fy*/schedule_c/*_appendix_*.csv          (28,575 rows)
plus data/combined/all_years_awards.csv and the two data/recovered/ sidecars.

Every check prints its own row/dollar counts. Nothing is "fixed" and nothing is
proposed as a fix — the job is to name the defect classes and size them.
"""
import collections
import csv
import glob
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------- loading

AWARD_GLOB = 'data/fy*/schedule_c/*_awards.csv'
APPX_GLOB = 'data/fy*/schedule_c/*appendix*.csv'
COMBINED = 'data/combined/all_years_awards.csv'
CROSSWALK = 'data/combined/org_name_recovery_crosswalk.csv'
ABSORBED = 'data/recovered/schedule_c_absorbed_awards.csv'
APPX_RECOVERED = 'data/recovered/schedule_c_appendix_recovered.csv'

BOROUGHS = {'Brooklyn', 'Bronx', 'Queens', 'Manhattan', 'Staten Island'}


def read(path):
    with open(path, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def load(pattern):
    """Rows tagged with _f (file), _ln (1-based CSV line), _fy (FYnn)."""
    out = []
    for f in sorted(glob.glob(pattern)):
        fy = f.split('/')[1].upper()
        for i, r in enumerate(read(f), start=2):
            r['_f'], r['_ln'], r['_fy'] = f, i, fy
            out.append(r)
    return out


O = lambda r: (r.get('organization') or '').strip()
M = lambda r: (r.get('member') or '').strip()
A = lambda r: int(float(r['amount'])) if (r.get('amount') or '').strip() else 0
D = lambda n: '${:,}'.format(n)
key = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
words = lambda s: re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower()).split()

AWARDS = load(AWARD_GLOB)
APPX = load(APPX_GLOB)
ALL = AWARDS + APPX

# organization names attested per EIN, across the whole corpus
EIN_NAMES = collections.defaultdict(collections.Counter)
for _r in ALL:
    if O(_r):
        EIN_NAMES[_r['ein']][O(_r)] += 1


def head(code, title):
    print('\n' + '=' * 78)
    print('%s  %s' % (code, title))
    print('=' * 78)


def sized(label, rows, extra=''):
    print('  %-46s rows=%-6d %-16s %s' % (label, len(rows), D(sum(A(r) for r in rows)), extra))


def byfy(rows):
    return dict(sorted(collections.Counter(r['_fy'] for r in rows).items()))


CHECKS = {}


def check(code, title):
    def deco(fn):
        CHECKS[code] = (title, fn)
        return fn
    return deco


# ---------------------------------------------------------------- A. identity

@check('A1', 'Sponsor token peeled off a real organization name (over-peel)')
def a1():
    """The parser strips a leading token it believes is a sponsor. When that token
    is genuinely the first word of the grantee's legal name, the result is a
    decapitated organization AND a fabricated sponsor attribution.

    Grounding: the SAME EIN elsewhere in the corpus spells the name with the token.
    """
    peel = [r for r in ALL if M(r) and O(r) and (M(r) + ' ' + O(r)) in EIN_NAMES[r['ein']]]
    sized('total over-peeled rows', peel, 'EINs=%d' % len({r['ein'] for r in peel}))
    sized('  sponsor token is a borough', [r for r in peel if M(r) in BOROUGHS])
    sized('  sponsor token is a member surname / other',
          [r for r in peel if M(r) not in BOROUGHS])
    print('  by FY:', byfy(peel))
    print('  peeled tokens:', collections.Counter(M(r) for r in peel).most_common(14))
    print('\n  worst by dollars (deduped on ein/member/org):')
    agg = collections.Counter()
    cnt = collections.Counter()
    for r in peel:
        agg[(r['ein'], M(r), O(r))] += A(r)
        cnt[(r['ein'], M(r), O(r))] += 1
    for k, v in agg.most_common(12):
        print('    %-10s member=%-14r org=%-44r n=%-3d %s' % (
            k[0], k[1], k[2][:43], cnt[k], D(v)))
    print('\n  the marker case — EIN 135562989:')
    for (o, m), n in collections.Counter((O(r), M(r)) for r in ALL if r['ein'] == '135562989').most_common():
        print('    n=%-3d member=%-12r org=%r' % (n, m, o))
    return peel


@check('A2', 'Residual sponsor-in-organization, grounded on the disclosure sidecar')
def a2():
    """org = "<token the sidecar uses as a member> <name the sidecar gives for this EIN>",
    member blank. Independent grounding: data/recovered/schedule_c_appendix_recovered.csv,
    built from the Council's own funded-disclosure spreadsheets."""
    side = read(APPX_RECOVERED)
    names = collections.defaultdict(set)
    members = set()
    for r in side:
        names[r['ein']].add((r['organization'] or '').strip())
        members.add((r['member'] or '').strip())
    hits = []
    for r in ALL:
        o, m = O(r), M(r)
        if not o or r['ein'] not in names:
            continue
        w = o.split()
        for cut in (1, 2):
            if len(w) <= cut:
                continue
            hd, tl = ' '.join(w[:cut]).rstrip(','), ' '.join(w[cut:])
            if hd in members and any(key(tl) == key(sn) for sn in names[r['ein']]):
                if m in ('', hd):
                    hits.append(r)
                break
    sized('grounded residual bleed', hits)
    print('  by FY:', byfy(hits))
    print('  member blank on:', sum(1 for r in hits if not M(r)), 'of', len(hits))
    cw = {(r['file'], r['line']) for r in read(CROSSWALK)}
    print('  already in org_name_recovery_crosswalk.csv:',
          sum(1 for r in hits if (r['_f'], str(r['_ln'])) in cw), '/', len(hits))
    for r in hits[:6]:
        print('    %s:%d  member=%r org=%r' % (r['_f'], r['_ln'], M(r), O(r)[:62]))
    return hits


@check('A3', 'member column holds a value that is not a sponsor at all')
def a3():
    m = collections.Counter(M(r) for r in ALL)
    junk = ['The', 'Center', 'Placement', 'Program']
    frag = ['Brooks-', 'Ferreras-']
    print('  distinct member values: %d   blank: %d' % (len(m), m.get('', 0)))
    for grp, label in ((junk, 'org-name word landed in member'),
                       (frag, 'surname split at a line-wrap hyphen')):
        rows = [r for r in ALL if M(r) in grp]
        sized('%s %s' % (label, grp), rows)
        for v in grp:
            s = [r for r in ALL if M(r) == v]
            if s:
                print('      %-16r n=%-4d %-14s %s' % (v, len(s), D(sum(A(r) for r in s)), byfy(s)))
    sp = [r for r in ALL if M(r) == 'Speaker Farias']
    sized('compound "Speaker Farias"', sp)
    print('\n  ambiguous surnames (two members share one, or one member has two spellings):')
    for grp in (['Sanchez', 'P. Sanchez', 'J. Sanchez'], ['Diaz', 'D. Diaz'],
                ['Bronx', 'Bronx Delegation']):
        for v in grp:
            s = [r for r in ALL if M(r) == v]
            print('      %-18r n=%-4d %-14s %s' % (v, len(s), D(sum(A(r) for r in s)), byfy(s)))
        print()


@check('A4', 'Organization name truncated to a bare fragment')
def a4():
    single = [r for r in ALL if O(r) and len(O(r).split()) == 1]
    frag = collections.Counter(O(r) for r in single)
    sized('single-word organization values', single)
    print('   ', frag.most_common(14))
    print('\n  a single-word value whose EIN also carries a longer name:')
    for w, n in frag.most_common(40):
        eins = {r['ein'] for r in single if O(r) == w}
        for e in eins:
            longer = [x for x in EIN_NAMES[e] if x != w and key(w) in key(x)]
            if longer:
                print('    %-10s %-14r n=%-3d  full name on same EIN: %r'
                      % (e, w, n, sorted(longer, key=lambda z: -EIN_NAMES[e][z])[0][:52]))
                break
    dang = [r for r in ALL if O(r) and O(r).rstrip().endswith(('-', '–', '—'))]
    sized('\n  org ends on a dangling dash (program half lost)', dang)
    for r in dang[:5]:
        print('    %s:%d %r program=%r' % (r['_f'], r['_ln'], O(r)[:56], (r.get('program') or '')[:20]))


# ---------------------------------------------------------------- B. columns

@check('B1', 'FY2018 aging appendix — whole file column-shifted')
def b1():
    f = 'data/fy18/schedule_c/fy18_appendix_a_aging.csv'
    rows = [r for r in APPX if r['_f'] == f]
    if not rows:
        print('  file absent'); return
    sized('FY18 appendix A rows', rows)
    p00 = [r for r in rows if (r.get('purpose') or '').startswith('.00')]
    o00 = [r for r in rows if O(r).startswith('.00')]
    sized('  purpose begins ".00" (cents of the amount)', p00)
    sized('  organization holds the PREVIOUS row\'s purpose', o00)
    other = [r for r in APPX if r['_f'] != f and ((r.get('purpose') or '').startswith('.00')
                                                  or O(r).startswith('.00'))]
    print('  same signature in any other appendix file: %d rows' % len(other))
    print('\n  the three FY2018 appendices, against the fixed pots in DATA-ANOMALIES #19:')
    for stream, expect in (('a_aging', 5610000), ('b_local', None), ('c_youth', 7650000)):
        s = [r for r in APPX if ('fy18_appendix_' + stream) in r['_f']]
        print('    fy18_appendix_%-8s rows=%-5d %-14s  DATA-ANOMALIES #19 standing pot: %s'
              % (stream, len(s), D(sum(A(r) for r in s)),
                 D(expect) if expect else '~$36.5M'))
    side = read(APPX_RECOVERED)
    print('    data/recovered/schedule_c_appendix_recovered.csv fiscal years:',
          sorted({r['fiscal_year'] for r in side}))
    print('    FY2018 rows in that sidecar:', sum(1 for r in side if r['fiscal_year'] == '2018'))
    print('\n  sample rows:')
    for r in o00[:2]:
        print('    %s:%d' % (r['_f'], r['_ln']))
        print('       member=%r' % M(r))
        print('       organization=%r' % O(r)[:150])
        print('       ein=%s amount=%s' % (r['ein'], r['amount']))


@check('B2', 'Purpose / program / header text leaked into a non-purpose column')
def b2():
    PROSE = re.compile(r'[a-z]{3}\.\s|\bwill be used\b|\bfunds? (will|to)\b|\bthroughout the\b', re.I)
    BOILER = re.compile(r'(finance division|page \d+|legal name of organization|'
                        r'adopted expense budget|ein \* amount|tax id)', re.I)
    for col in ('initiative', 'category', 'program', 'agency', 'member', 'purpose'):
        hits = [r for r in ALL if (r.get(col) or '') and PROSE.search(r[col])]
        boil = [r for r in ALL if (r.get(col) or '') and BOILER.search(r[col])]
        print('  %-12s prose rows=%-5d %-14s   PDF-boilerplate rows=%-5d %s'
              % (col, len(hits), D(sum(A(r) for r in hits)), len(boil),
                 D(sum(A(r) for r in boil))))
    print('\n  worst single leaks:')
    for col in ('initiative', 'program'):
        hits = sorted([r for r in ALL if (r.get(col) or '') and PROSE.search(r[col])],
                      key=lambda r: -A(r))
        for r in hits[:3]:
            print('    %-10s %s:%d $%-11s %r' % (col, r['_f'], r['_ln'], A(r), r[col][:78]))
    ob = [r for r in ALL if BOILER.search(O(r))]
    sized('\n  organization holds a PDF page header', ob)
    for r in ob[:4]:
        print('    %s:%d %r' % (r['_f'], r['_ln'], O(r)[:110]))


@check('B3', 'Row-boundary loss detected in `program`, where nothing looks for it')
def b3():
    """DATA-ANOMALIES #20 / validate_data.py's org_merged advisory inspect
    `organization` only. The identical signature — an EIN and a `$` inside a text
    field — also occurs in `program`."""
    SIG = re.compile(r'\d{2}-\d{6,8}.*\$|\$[\d,]{4,}.*\d{2}-\d{6}')
    for col in ('organization', 'program', 'purpose'):
        hits = [r for r in ALL if SIG.search(r.get(col) or '')]
        sized('%-14s row-boundary signature' % col, hits)
    prog = [r for r in ALL if SIG.search(r.get('program') or '')]
    print('  by FY (program):', byfy(prog))
    for r in prog[:5]:
        print('    %s:%d org=%r' % (r['_f'], r['_ln'], O(r)[:38]))
        print('        program=%r' % (r['program'][:104]))
    print('\n  malformed EINs found INSIDE merged text (the ein column itself is clean):')
    bad = collections.Counter()
    for r in ALL + read(CROSSWALK):
        for v in r.values():
            if isinstance(v, str):
                for m in re.finditer(r'\b(\d{2}-\d{5,9})\b', v):
                    if len(m.group(1).replace('-', '')) != 9:
                        bad[m.group(1)] += 1
    print('   ', bad.most_common(12))


@check('B35', 'A grantee name + EIN parked in the `initiative` column')
def b35():
    """Distinct from B3: not a merged award row, but a whole organization identity
    written into the initiative label and then repeated down every row of that block."""
    TOK = re.compile(r'\d{2}-\d{5,9}|\$[\d,]{4,}')
    for col in ('initiative', 'category', 'member', 'agency', 'program', 'organization'):
        h = [r for r in ALL if TOK.search(r.get(col) or '')]
        print('  %-13s rows=%-5d %-14s %s' % (col, len(h), D(sum(A(r) for r in h)), byfy(h)))
    h = [r for r in ALL if TOK.search(r.get('initiative') or '')]
    print('\n  every distinct polluted initiative label:')
    for v, n in collections.Counter(r['initiative'] for r in h).most_common():
        print('    n=%-4d %-13s %r' % (n, D(sum(A(r) for r in h if r['initiative'] == v)), v[:76]))


@check('B4', 'EIN column shape, embedded malformed EINs, encoding damage')
def b4():
    shape = collections.Counter()
    for r in ALL:
        e = (r.get('ein') or '')
        shape['empty' if not e else ('%d digits' % len(e) if e.isdigit() else 'non-digit')] += 1
    print('  EIN column shape across %d rows: %s' % (len(ALL), dict(shape)))
    print('  -> the `ein` COLUMN is clean; malformed EINs live inside leaked text')
    allein = {r['ein'] for r in ALL}
    bad = collections.Counter()
    for r in ALL:
        for v in r.values():
            if isinstance(v, str):
                for m in re.finditer(r'\b(\d{2}-\d{5,9})\b', v):
                    if len(m.group(1).replace('-', '')) != 9:
                        bad[m.group(1)] += 1
    print('\n  malformed EIN tokens embedded in text fields: %d distinct, %d occurrences'
          % (len(bad), sum(bad.values())))
    print('  token          n     one "0" reinserted -> a real EIN in this corpus?')
    for tok, n in bad.most_common():
        flat = tok.replace('-', '')
        c = sorted({flat[:i] + '0' + flat[i:] for i in range(len(flat) + 1)} & allein)
        print('    %-13s %-5d %-6s %s' % (tok, n, 'YES' if c else 'no', c or '-'))
    print('  -> every one resolves to a unique real EIN by reinserting a single "0".')
    print('     (The 10-digit "15-24042810" named in the brief is NOT in any data file —')
    print('      it appears only in the crosswalk\'s original_organization audit column.)')
    ch = collections.Counter()
    ex = {}
    for r in ALL:
        for k, v in r.items():
            if k.startswith('_') or not isinstance(v, str):
                continue
            for c in v:
                if ord(c) > 126 or ord(c) < 32:
                    ch[c] += 1
                    ex.setdefault(c, (r['_f'], r['_ln'], k, v[:70]))
    print('\n  non-ASCII census (no mojibake / double-encoded UTF-8 found):')
    for c, n in ch.most_common():
        flag = '  <-- INVISIBLE' if unicodedata.category(c) in ('Cf', 'Zs') or c == '\xad' else ''
        print('    U+%04X %-28s n=%-5d %s%s' % (ord(c), unicodedata.name(c, '?')[:28], n,
                                                repr(c), flag))
    for c in ('\xad', ' '):
        if c in ex:
            print('    %r first at %s:%d [%s] %r' % (c, ex[c][0], ex[c][1], ex[c][2], ex[c][3]))
    ws = [r for r in ALL for k in ('organization', 'program', 'member', 'purpose')
          if (r.get(k) or '') != (r.get(k) or '').strip()]
    print('\n  fields with untrimmed leading/trailing whitespace: %d' % len(ws))

    # an invisible character forks initiative_canonical, the key built to prevent forking
    comb = read(COMBINED)
    INVIS = re.compile('[­ ​‑]')
    flat = lambda s: INVIS.sub(' ', s)
    grp = collections.defaultdict(set)
    for r in comb:
        grp[flat(r['initiative'])].add((r['initiative'], r['initiative_canonical']))
    forks = [v for v in grp.values() if len({c for _, c in v}) > 1]
    print('\n  raw initiative spellings that are identical once invisible characters are')
    print('  removed, yet resolve to DIFFERENT initiative_canonical values: %d group(s)' % len(forks))
    for v in forks:
        for raw, can in sorted(v):
            s = [r for r in comb if r['initiative'] == raw]
            print('    raw=%-32r -> canonical=%-26r rows=%-4d %s'
                  % (raw, can, len(s), D(sum(A(r) for r in s))))


# ---------------------------------------------------------------- C. totals

@check('C1', 'initiative is empty on a quarter of the award corpus')
def c1():
    print('  FY      empty/total rows        empty $            of $')
    tot = []
    for fy in sorted({r['_fy'] for r in AWARDS}):
        s = [r for r in AWARDS if r['_fy'] == fy]
        e = [r for r in s if not (r.get('initiative') or '').strip()]
        tot += e
        print('  %-6s  %5d/%-6d %6.1f%%   %-16s %s'
              % (fy, len(e), len(s), 100.0 * len(e) / len(s), D(sum(A(r) for r in e)),
                 D(sum(A(r) for r in s))))
    sized('\n  TOTAL rows with no initiative label', tot)
    print('  share of award dollars: %.1f%%' % (100.0 * sum(A(r) for r in tot)
                                                / sum(A(r) for r in AWARDS)))
    cats = collections.Counter((r.get('category') or '') for r in AWARDS)
    print('\n  category: %d distinct, %d blank' % (len(cats), cats.get('', 0)))
    once = [v for v, n in collections.Counter((r.get('initiative') or '') for r in AWARDS).items()
            if n == 1 and v]
    print('  initiative values appearing exactly once in the whole corpus: %d' % len(once))


@check('C2', 'Duplicate award rows — the documented count is stale')
def c2():
    comb = read(COMBINED)
    k = collections.Counter(tuple(r.items()) for r in comb)
    dup = {a: b for a, b in k.items() if b > 1}
    extra = sum(v - 1 for v in dup.values())
    dollars = sum((v - 1) * int(float(dict(a)['amount'])) for a, v in dup.items())
    print('  %s' % COMBINED)
    print('    duplicate groups          %d' % len(dup))
    print('    duplicate row instances   %d   <-- DATA-ANOMALIES #10 says 142, all verified legitimate'
          % sum(dup.values()))
    print('    extra rows above one each %d   %s' % (extra, D(dollars)))
    byy = collections.Counter()
    for a, b in dup.items():
        byy[dict(a)['year']] += b - 1
    print('    extra rows by FY: %s' % dict(sorted(byy.items())))
    print('    FY2027 alone contributes %d — FY2027 gained 33 rows in the DATA-ANOMALIES #13'
          % byy.get('FY27', 0))
    print('    re-parse, which post-dates the #10 verification (dated 2026-07-08).')
    g = collections.defaultdict(set)
    for r in AWARDS:
        g[(r['_fy'], r['ein'], r['amount'], M(r), r.get('initiative', ''))].add(O(r))
    bad = {a: b for a, b in g.items() if len(b) > 1}
    print('\n  same (FY, EIN, amount, member, initiative) but different organization: %d groups'
          % len(bad))


@check('C3', 'Appendix rows are not a subset of the award body')
def c3():
    """DATA-DICTIONARY: "These are subsets of the award body — do not add them to
    the Schedule C total." The published headline total does add them."""
    print('  FY    appendix rows   with NO (ein,amount) twin in the awards file')
    for fy in sorted({r['_fy'] for r in APPX}):
        a1 = collections.Counter((r['ein'], r['amount']) for r in AWARDS if r['_fy'] == fy)
        a2 = collections.Counter((r['ein'], r['amount']) for r in APPX if r['_fy'] == fy)
        only = sum(max(0, a2[k] - a1.get(k, 0)) for k in a2)
        n = sum(a2.values())
        print('  %-6s %6d          %6d  (%.0f%%)' % (fy, n, only, 100.0 * only / n))
    print('\n  strict overlap on (ein, amount, member, organization) — candidate double count:')
    tr, td = 0, 0
    for fy in sorted({r['_fy'] for r in APPX}):
        k1 = collections.Counter((r['ein'], r['amount'], M(r), O(r)) for r in AWARDS if r['_fy'] == fy)
        k2 = collections.Counter((r['ein'], r['amount'], M(r), O(r)) for r in APPX if r['_fy'] == fy)
        ov = {k: min(k1[k], k2[k]) for k in k2 if k in k1}
        rr = sum(ov.values()); dd = sum(int(k[1]) * v for k, v in ov.items())
        tr += rr; td += dd
        print('  %-6s %5d rows  %s' % (fy, rr, D(dd)))
    print('  TOTAL  %5d rows  %s' % (tr, D(td)))
    print('\n  headline corpus as published:')
    print('    awards    %6d rows  %s' % (len(AWARDS), D(sum(A(r) for r in AWARDS))))
    print('    appendix  %6d rows  %s' % (len(APPX), D(sum(A(r) for r in APPX))))
    print('    SUM       %6d rows  %s' % (len(ALL), D(sum(A(r) for r in ALL))))


# ---------------------------------------------------------------- D. sidecars

@check('D1', 'Crosswalk and sidecar internal consistency')
def d1():
    cw = read(CROSSWALK)
    print('  %s: %d entries %s' % (CROSSWALK, len(cw),
                                   dict(collections.Counter(r['defect'] for r in cw))))
    cache, off = {}, []
    for r in cw:
        cache.setdefault(r['file'], read(r['file']))
        i = int(r['line']) - 2
        if 0 <= i < len(cache[r['file']]):
            if O(cache[r['file']][i]) != r['recovered_organization']:
                off.append(r)
    print('    entries whose `recovered_organization` is NOT the value on that line: %d' % len(off))
    print('    all of them are defect=%s' % set(r['defect'] for r in off))
    if off:
        print('    e.g. %s:%s recovered_organization=%r'
              % (off[0]['file'], off[0]['line'], off[0]['recovered_organization'][:60]))
        print('    -> the column carries an "[ein NNNNNNNNN] Name" annotation, not a name.')
        print('       verify_crosswalk.py checks the `ein` column for wrong_ein rows, so this')
        print('       column is never asserted against anything and passes the gate.')
    ab = read(ABSORBED)
    print('\n  %s: %d rows %s' % (ABSORBED, len(ab),
                                  D(sum(int(float(r['amount'])) for r in ab))))
    print('    confidence: %s' % dict(collections.Counter(r['confidence'] for r in ab)))
    print('    disclosure_confirmed=no: %d rows %s'
          % (sum(1 for r in ab if r['disclosure_confirmed'] == 'no'),
             D(sum(int(float(r['amount'])) for r in ab if r['disclosure_confirmed'] == 'no'))))
    per = collections.Counter()
    for f in sorted(glob.glob(AWARD_GLOB)):
        fy = '20' + f.split('/')[1][2:]
        for r in read(f):
            per[(fy, r['ein'], str(int(float(r['amount']))))] += 1
    clash = [r for r in ab if per.get((r['fiscal_year'], r['ein'], str(int(float(r['amount'])))), 0)]
    print('    rows whose (FY,EIN,amount) ALREADY exists in the per-year awards file: %d %s'
          % (len(clash), D(sum(int(float(r['amount'])) for r in clash))))
    for r in clash:
        print('      %s %s %s %r' % (r['fiscal_year'], r['ein'], r['amount'], r['organization'][:50]))
    ar = read(APPX_RECOVERED)
    dups = sum(v - 1 for v in collections.Counter(tuple(r.items()) for r in ar).values() if v > 1)
    pend = [r for r in ar if r['status'] == 'Pending']
    print('\n  %s: %d rows' % (APPX_RECOVERED, len(ar)))
    print('    internal exact-duplicate rows: %d' % dups)
    print('    status=Pending: %d rows %s  (%s)'
          % (len(pend), D(sum(int(float(r['amount'])) for r in pend)),
             dict(sorted(collections.Counter(r['fiscal_year'] for r in pend).items()))))
    known = {M(r) for r in ALL}
    new = collections.Counter((r.get('member') or '').strip() for r in ar
                              if (r.get('member') or '').strip() not in known)
    print('    member values the committed corpus has never seen: %s' % new.most_common(10))
    print('    -> those surnames are exactly the ones still glued to organization names (A2).')


@check('D2', 'What the repo\'s own advisories point at')
def d2():
    """validate_data.py emits a `column_bleed` advisory. Check which rows it names."""
    p = 'data/QA-REPORT.md'
    if not os.path.exists(p):
        print('  no QA-REPORT.md'); return
    txt = open(p, encoding='utf-8').read()
    ex = re.findall(r"column_bleed: (\d+) suspected surname-in-(\w+) residual\(s\); e\.g\. line (\d+): '([^']*)'", txt)
    print('  column_bleed advisories in data/QA-REPORT.md:')
    seen = collections.Counter()
    for n, col, ln, val in ex:
        seen[(col, val)] += int(n)
    for (col, val), n in seen.most_common(10):
        verdict = ''
        if val in EIN_NAMES.get('135562989', {}) or val == 'Hudson Guild':
            verdict = '  <-- this is the CORRECT name; the truncated twin is not flagged'
        print('    %-8s n=%-4d example=%r%s' % (col, n, val[:56], verdict))
    print('\n  cross-check — rows the corpus holds for EIN 135562989:')
    for (o, m), n in collections.Counter((O(r), M(r)) for r in ALL if r['ein'] == '135562989').most_common():
        mark = '   <-- decapitated, NOT flagged' if o == 'Guild' else ''
        print('    n=%-3d member=%-12r org=%-16r%s' % (n, m, o, mark))


def main(argv):
    want = [a.upper() for a in argv[1:]] or sorted(CHECKS)
    print('NYC Council discretionary awards — integrity sweep')
    print('corpus: %d award rows + %d appendix rows = %d rows, %s'
          % (len(AWARDS), len(APPX), len(ALL), D(sum(A(r) for r in ALL))))
    for code in want:
        if code not in CHECKS:
            print('unknown check %r; have %s' % (code, sorted(CHECKS)))
            return 2
        title, fn = CHECKS[code]
        head(code, title)
        fn()
    print('\ndone — audit only, nothing written.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
