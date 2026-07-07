#!/usr/bin/env python3
"""
Parse an NYC Council FY2026 'Transparency Resolution' PDF into structured rows.

Transparency Resolutions are the Council's post-adoption discretionary designations:
throughout the fiscal year they assign (and rescind/transfer) money the adopted budget
held as "to be designated post-adoption." Each PDF is a stack of CHARTs; every chart
header names an initiative and a fiscal year (e.g. "CHART #34: Artificial Intelligence
Community Engagement - Fiscal 2026"). Rows are award lines:

    Member  Organization - Program  EIN  Agency  Amount  Agy#  U/A

The leading column varies by chart (Member / Borough / Borough/Member / absent for
citywide initiatives). "Purpose of Funds Changes" charts use a different layout with a
leading Source column and a trailing free-text Purpose column.

Extraction is deterministic: every money value is read from an EIN+$amount anchor at a
fixed position in the line (never model-transcribed). Negative amounts print in
parentheses -> rescissions; they are preserved as negatives.

RECONCILIATION: these documents print NO per-chart or grand totals. There is nothing to
reconcile the parsed rows against, so the output is labeled NOT RECONCILABLE (against
printed totals). The one internal check available -- new/rescind designations within a
transfer net out -- is reported as an informational net figure, not a reconciliation.

Emits (to --outdir, prefixed with --prefix):
  *_transparency_designations.csv   resolution,date,chart,fiscal_year,action,source,
                                     council_member,organization,program,ein,amount,
                                     agency,agy_num,ua,purpose,flags
  *_transparency_reconciliation.txt
"""
import re, csv, os, argparse

# EIN (##-#######) then optional agency code then $amount (parenthesised => negative).
# Agency codes are 2-6 uppercase letters, optionally slashed (DSS/HRA). The amount is the
# anchor; everything before the EIN is the member/org blob.
ANCHOR = re.compile(r'(\d{2}-\d{7})\s+([A-Z][A-Za-z/&.\- ]{0,14}?)?\s*(\(?\$[\d,]+\)?)')
CHART  = re.compile(r'(?i)^CHART\s*#?\s*\d+\s*:\s*(.+)$')
FY     = re.compile(r'(?i)\bFiscal\s*(\d{4})\b')
TAIL   = re.compile(r'^\s*(\d{3})\s+(\d{3})\b')          # Agy#  U/A  after amount
PAGEFOOT = re.compile(r'(?i)^page\s+\d+$|^page\s+\d+\s+of\s+\d+$')
FOOTNOTE = re.compile(r'^\s*\*+\s*(Indicates|Requires)', re.I)

def money(s):
    s = s.strip()
    neg = s.startswith('(')
    v = int(re.sub(r'[(),$]', '', s))
    return -v if neg else v

def clean(s):
    return re.sub(r'\s+', ' ', s).strip()

def split_org_program(text):
    text = clean(text)
    if ' - ' in text:
        org, prog = text.split(' - ', 1)
        return org.strip(), prog.strip()
    return text, ''

def strip_flags(text):
    """Pull trailing ***/**/* prequalification/budget-mod markers off an org blob."""
    flags = ''
    m = re.search(r'(\*+)\s*$', text)
    if m:
        flags = m.group(1)
        text = text[:m.start()].strip()
    return text, flags

def load_lines(pdf):
    """Return the document as ordered text lines, rebuilt from pdfplumber word coordinates
    (cluster words by y, sort each row by x). This is layout-aware: on some charts the PDF's
    text layer emits the organization names out of order (displaced to the page bottom), and
    pypdf.extract_text() reproduces that scramble -- coordinate clustering restores the true
    reading order so every award row keeps its org on the same line as its EIN/amount."""
    import pdfplumber
    from collections import defaultdict
    out = []
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            rows = defaultdict(list)
            for w in words:
                # ~5pt row bucket: wide enough to keep a wrapped org head on the same line as
                # its EIN/amount in dense charts (Food Pantries), narrow enough that two
                # distinct award rows never merge (verified: 0 two-anchor lines across all 10).
                rows[round(w['top'] / 5.0)].append(w)
            for y in sorted(rows):
                line = ' '.join(w['text'] for w in sorted(rows[y], key=lambda w: w['x0']))
                s = line.strip()
                if s:
                    out.append(s)
    return out

def load_schedule_c_roster(path):
    """Authoritative FY2026 NYC Council member roster, taken from the repo's already-parsed
    and printed-total-reconciled Schedule C awards CSV (the `member` column). Same Council,
    same fiscal year, same designations -- so this is the correct, cite-able reference rather
    than a name list guessed from memory or reconstructed heuristically from these PDFs
    (leading-token frequency cannot separate a surname like 'Narcisse' from an org word like
    'Neighborhood'). Returns a set of member names, e.g. {'Brannan','De La Rosa','Speaker'}."""
    import csv
    roster = set()
    if path and os.path.exists(path):
        with open(path, newline='') as f:
            for r in csv.DictReader(f):
                m = (r.get('member') or '').strip()
                # keep surname designators; drop borough-delegation placeholders (they are
                # not row-leading tokens in the transparency charts)
                if m and 'Delegation' not in m and m not in (
                        'Brooklyn', 'Bronx', 'Queens', 'Manhattan', 'Staten Island'):
                    roster.add(m)
    roster.add('Speaker')
    return roster

def parse(pdf, resolution, date, roster_csv=None):
    lines = load_lines(pdf)
    roster = load_schedule_c_roster(roster_csv)
    rows = []
    chart = ''; fiscal = ''; is_purpose = False; has_source = False; has_member = True
    last_member = ''
    buf = []                                  # accumulates wrapped member/org lines
    i = 0
    while i < len(lines):
        s = lines[i]; i += 1
        cm = CHART.match(s)
        if cm:
            title = clean(re.sub(r'\s*\(continued\)\s*$', '', cm.group(1), flags=re.I))
            chart = title
            fm = FY.search(title)
            fiscal = fm.group(1) if fm else ''
            is_purpose = 'purpose of funds' in title.lower()
            last_member = ''; buf = []
            continue
        if PAGEFOOT.match(s) or FOOTNOTE.match(s):
            continue
        # header row of a chart -> reset context. The leading column word tells us the
        # chart's shape: Source (purpose charts), Member/Borough (member-allocated), or
        # Organization (citywide initiative -- NO member column, e.g. AICE).
        if re.search(r'EIN Number\s+Agency', s):
            lead = s.strip().lower()
            has_source = lead.startswith('source')
            has_member = not lead.startswith('organization')
            last_member = ''; buf = []
            continue

        m = ANCHOR.search(s)
        if not m:
            buf.append(s)
            continue

        ein = m.group(1)
        agency = (m.group(2) or '').strip()
        amount = money(m.group(3))
        pre = clean(' '.join(buf) + ' ' + s[:m.start()])
        tail = s[m.end():].strip()
        buf = []

        # member/org blob = pre. Peel a Source keyword (purpose charts) then the member.
        source = ''
        if is_purpose or has_source:
            ms = re.match(r'^(Local|Aging|Youth|Speaker[\'’]s|Anti-?Poverty|[A-Z][A-Za-z]+)\s+', pre)
            if ms and ms.group(1) in ('Local', 'Aging', 'Youth', 'Anti-Poverty', 'AntiPoverty'):
                source = ms.group(1); pre = pre[ms.end():].strip()

        if not has_member:
            member = ''
            org_blob = pre             # citywide chart: whole blob is the organization
        else:
            member = detect_member(pre, roster)
            if member:
                last_member = member
                org_blob = pre[len(member):].strip()
            else:
                org_blob = pre
                member = last_member   # carry-down continuation row

        org_blob, flags = strip_flags(org_blob)
        org, program = split_org_program(org_blob)

        # tail: for standard charts "Agy#  U/A"; for purpose charts, free-text purpose that
        # may wrap onto following lines until the next anchor / chart / footnote.
        agy_num = ua = ''; purpose = ''
        tm = TAIL.match(tail)
        if tm:
            agy_num, ua = tm.group(1), tm.group(2)
            purpose = tail[tm.end():].strip()
        else:
            purpose = tail
        if is_purpose:
            # Gather wrapped purpose text. Stop at the next record: a CHART/header/footnote,
            # a line that itself carries an anchor, OR a line that is the WRAPPED ORG HEAD of
            # the next record -- i.e. the following line carries an anchor. Leaving that org
            # head in place lets the next loop iteration pick it up via buf (otherwise the
            # next record's organization is swallowed into this record's purpose and comes
            # out empty).
            extra = []
            while i < len(lines):
                nxt = lines[i]
                if CHART.match(nxt) or ANCHOR.search(nxt) or PAGEFOOT.match(nxt) \
                   or FOOTNOTE.match(nxt) or re.search(r'EIN Number\s+Agency', nxt):
                    break
                if i + 1 < len(lines) and ANCHOR.search(lines[i + 1]) \
                   and not re.search(r'EIN Number\s+Agency', lines[i + 1]):
                    break                      # nxt is the next record's wrapped org head
                extra.append(nxt); i += 1
            purpose = clean(purpose + ' ' + ' '.join(extra))

        action = 'purpose_change' if is_purpose else ('rescind' if amount < 0 else 'designate')

        rows.append(dict(
            resolution=resolution, date=date, chart=chart, fiscal_year=fiscal,
            action=action, source=source, council_member=member,
            organization=org, program=program, ein=ein.replace('-', ''),
            amount=amount, agency=agency, agy_num=agy_num, ua=ua,
            purpose=purpose, flags=flags,
        ))
    return rows

def detect_member(pre, roster):
    """Match the longest roster surname that leads the blob (so 'De La Rosa' wins over a
    hypothetical 'De'). Roster names are authoritative (from Schedule C), so a leading match
    is a real member; anything else is an organization / continuation row."""
    toks = pre.split()
    for k in (3, 2, 1):
        cand = ' '.join(toks[:k])
        if cand in roster:
            return cand
    return ''

COLS = ['resolution', 'date', 'chart', 'fiscal_year', 'action', 'source',
        'council_member', 'organization', 'program', 'ein', 'amount', 'agency',
        'agy_num', 'ua', 'purpose', 'flags']

def write_csv(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r.get(c, '') for c in COLS])

# The 10 FY2026 Transparency Resolutions, in order, with their adoption dates. Filenames in
# --srcdir are matched by sorted order (zero-padded 'Transparency-Reso-NN-YYYY-MM-DD.pdf').
FY26_META = [
    (1, '2025-08-14'), (2, '2025-09-25'), (3, '2025-10-29'), (4, '2025-11-25'),
    (5, '2025-12-18'), (6, '2026-02-12'), (7, '2026-03-10'), (8, '2026-04-16'),
    (9, '2026-05-20'), (10, '2026-06-30'),
]

def default_roster():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'fy26', 'schedule_c', 'fy26_schedule_c_awards.csv')

def batch(srcdir, outdir, roster_csv):
    """Parse all 10 FY26 resolutions -> per-reso CSVs + combined + reconciliation notes."""
    import glob
    os.makedirs(outdir, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(srcdir, 'Transparency-Reso-*.pdf')))
    if len(pdfs) != 10:
        raise SystemExit(f'expected 10 PDFs in {srcdir}, found {len(pdfs)}')
    per, allrows = [], []
    for pdf, (num, date) in zip(pdfs, FY26_META):
        rows = parse(pdf, num, date, roster_csv)
        write_csv(os.path.join(outdir, f'reso{num:02d}_transparency_designations.csv'), rows)
        per.append((num, date, os.path.basename(pdf), rows)); allrows.extend(rows)
    write_csv(os.path.join(outdir, 'fy26_transparency_all.csv'), allrows)
    report = reconciliation_report(per, allrows)
    open(os.path.join(outdir, 'fy26_transparency_reconciliation.txt'), 'w').write(report + '\n')
    print(report)

def reconciliation_report(per, allrows):
    from collections import Counter
    L = ['FY2026 NYC COUNCIL TRANSPARENCY RESOLUTIONS - PARSE + RECONCILIATION NOTES',
         '=' * 78, '',
         'RECONCILIATION STATUS: NOT RECONCILABLE (against printed totals).',
         'These documents print NO per-chart or grand totals -- only award rows. There is',
         'nothing in the source to reconcile parsed dollar sums against. The figures below',
         'are parse counts, not reconciled totals. The one internal consistency check the',
         'documents permit is the transfer net-out: within a chart a rescission (negative)',
         'and its paired re-designation (positive) should net to ~0. Reported as "net".', '',
         f'{"reso":>4} {"date":<11} {"rows":>6} {"designate$":>15} {"rescind$":>15} {"net$":>13}',
         '-' * 70]
    gr = gd = gs = 0
    for num, date, fn, rows in per:
        d = sum(r['amount'] for r in rows if r['amount'] > 0)
        s = sum(r['amount'] for r in rows if r['amount'] < 0)
        gr += len(rows); gd += d; gs += s
        L.append(f'{num:>4} {date:<11} {len(rows):>6} {d:>15,} {s:>15,} {d+s:>13,}')
    L += ['-' * 70,
          f'{"ALL":>4} {"":<11} {gr:>6} {gd:>15,} {gs:>15,} {gd+gs:>13,}', '',
          'rows by action:  ' + '  '.join(f'{k}={v}' for k, v in sorted(Counter(r['action'] for r in allrows).items())),
          'rows by fiscal year:  ' + '  '.join(f'{k or "?"}={v}' for k, v in sorted(Counter(r['fiscal_year'] for r in allrows).items()))]
    # data-quality note: unresolved organizations (dense-chart coordinate artifacts)
    miss = [r for r in allrows if not r['organization'].strip() and r['ein'] != '136400434']
    L += ['', f'unresolved organization (dense-chart text-layer artifacts): {len(miss)} of {len(allrows)} rows '
          f'({100*len(miss)/max(len(allrows),1):.2f}%) -- amount/EIN/agency captured, org name orphaned']
    # AICE spotlight
    aice = [r for r in allrows if 'Artificial Intelligence' in r['chart']]
    L += ['', 'SPOTLIGHT - Artificial Intelligence Community Engagement (AICE, $1M initiative):']
    if aice:
        recips = [r for r in aice if r['amount'] > 0]
        resc = [r for r in aice if r['amount'] < 0]
        L.append(f'  resolution {aice[0]["resolution"]} ({aice[0]["date"]}), {len(aice)} rows, '
                 f'net ${sum(r["amount"] for r in aice):,}')
        L.append(f'  rescinded from pool: ${sum(r["amount"] for r in resc):,} '
                 f'({"; ".join(r["organization"] for r in resc)})')
        L.append(f'  designated to {len(recips)} named recipients (${sum(r["amount"] for r in recips):,}):')
        for r in recips:
            L.append(f'    ${r["amount"]:>9,}  {r["organization"]}')
    else:
        L.append('  NOT FOUND in any parsed resolution.')
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pdf', nargs='?', help='single resolution PDF (omit with --batch)')
    ap.add_argument('--resolution'); ap.add_argument('--date')
    ap.add_argument('--outdir', required=True); ap.add_argument('--prefix')
    ap.add_argument('--batch', metavar='SRCDIR',
                    help='parse all 10 FY26 resolutions found in SRCDIR')
    ap.add_argument('--roster-csv', default=default_roster(),
                    help='Schedule C awards CSV whose member column is the authoritative FY26 roster')
    a = ap.parse_args()
    if a.batch:
        batch(a.batch, a.outdir, a.roster_csv)
        return
    if not (a.pdf and a.resolution and a.date and a.prefix):
        ap.error('single-PDF mode requires: pdf --resolution --date --prefix')
    os.makedirs(a.outdir, exist_ok=True)
    rows = parse(a.pdf, a.resolution, a.date, a.roster_csv)
    write_csv(os.path.join(a.outdir, f'{a.prefix}_transparency_designations.csv'), rows)
    print(f'{a.prefix}: {len(rows)} rows')

if __name__ == '__main__':
    main()
