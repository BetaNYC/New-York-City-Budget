import * as pdfjs from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

const $ = (id) => document.getElementById(id)
const el = (tag, cls, txt) => {
  const n = document.createElement(tag)
  if (cls) n.className = cls
  if (txt != null) n.textContent = txt
  return n
}
const usd = (n) => '$' + Number(n || 0).toLocaleString('en-US')

// A DEFECT is a field that is wrong. An OBSERVATION is a field that is empty for a reason the
// schema allows — a citywide initiative row has no sponsoring member. Only defects count against
// "clean"; mixing them scored FY2016 at 0% when its organization fields were sound.
const DEFECTS = new Set(['org_merged', 'org_prose', 'org_blank'])
const FLAG_HELP = {
  org_merged: 'organization text carries another row’s EIN or dollar figure — the row boundary was lost, so this row’s amount may belong to a different organization',
  org_prose: 'organization holds purpose prose rather than a name',
  org_blank: 'no organization name at all',
  member_blank: 'no sponsoring member — correct for a citywide initiative row, missing for a member item',
  initiative_blank: 'an initiative_provider row with no initiative named',
}

const state = { manifest: null, doc: null, page: 1, pdf: null, pageList: [], selected: null }

/* ---------------------------------------------------------------- data --- */

async function loadManifest() {
  const r = await fetch('/data/index.json')
  if (!r.ok) throw new Error('no index.json — run: python3 review-ui/build_index.py')
  state.manifest = await r.json()
  const sel = $('year')
  sel.innerHTML = ''
  for (const y of state.manifest.years) {
    sel.appendChild(el('option', null, `FY${y.fiscal_year}`)).value = y.fiscal_year
  }
  sel.onchange = () => loadYear(Number(sel.value))
  await loadYear(state.manifest.years[0].fiscal_year)
}

async function loadYear(fy) {
  const r = await fetch(`/data/fy${fy}.json`)
  state.doc = await r.json()
  state.selected = null
  renderSummary()
  renderQA()
  renderPipeline()
  renderUnplaced()
  rebuildPageList()
  state.pdf = null
  await gotoPage(firstInterestingPage())
}

/* ------------------------------------------------------------- summary --- */

function renderSummary() {
  const s = state.doc.summary
  const box = $('summary')
  box.innerHTML = ''
  const add = (label, value, cls) => {
    const d = el('div', 'stat' + (cls ? ' ' + cls : ''))
    d.appendChild(el('span', 'v', value))
    d.appendChild(el('span', 'k', label))
    box.appendChild(d)
  }
  add('rows', s.rows.toLocaleString())
  add('dollars', usd(s.dollars))
  add('clean', s.pct_clean + '%', s.pct_clean >= 95 ? 'good' : s.pct_clean >= 80 ? 'warn' : 'bad')
  add('defective', s.rows_defective.toLocaleString(), s.rows_defective ? 'bad' : 'good')
  add('repaired', s.repairs.toLocaleString())
  add('unplaced', s.rows_unplaced.toLocaleString(), s.rows_unplaced ? 'warn' : 'good')
  add('pages', state.doc.page_count.toLocaleString())
}

/* ---------------------------------------------------------------- page --- */

function rebuildPageList() {
  const onlyRows = $('onlyRows').checked
  const onlyFlagged = $('onlyFlagged').checked
  state.pageList = state.doc.pages
    .filter((p) => {
      if (onlyFlagged) return p.rows.some((r) => r.flags.some((f) => DEFECTS.has(f)))
      if (onlyRows) return p.rows.length > 0
      return true
    })
    .map((p) => p.page)
  if (!state.pageList.length) state.pageList = state.doc.pages.map((p) => p.page)
}

function firstInterestingPage() {
  const p = state.doc.pages.find((x) => x.rows.length)
  return p ? p.page : 1
}

async function ensurePdf() {
  if (state.pdf) return state.pdf
  state.pdf = await pdfjs.getDocument(`/pdf/${state.doc.fiscal_year}.pdf`).promise
  return state.pdf
}

async function renderPdfPage(n) {
  const wrap = $('pdfWrap')
  try {
    const pdf = await ensurePdf()
    const page = await pdf.getPage(n)
    const canvas = $('pdf')
    const avail = wrap.clientWidth - 24
    const base = page.getViewport({ scale: 1 })
    const viewport = page.getViewport({ scale: Math.max(0.4, avail / base.width) })
    canvas.width = viewport.width
    canvas.height = viewport.height
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
  } catch (e) {
    wrap.innerHTML = ''
    const msg = el('div', 'err')
    msg.textContent = `Could not render the PDF: ${e.message}. The dev server serves it from source/ — check that the file exists and that vite.config.js maps FY${state.doc.fiscal_year}.`
    wrap.appendChild(msg)
  }
}

async function gotoPage(n) {
  const max = state.doc.page_count
  state.page = Math.min(Math.max(1, n), max)
  const p = state.doc.pages[state.page - 1]
  $('pageLabel').textContent = `page ${state.page} / ${max}` + (p ? ` · ${p.section}` : '')
  $('pageText').textContent = p ? p.text : ''
  $('anchorLabel').textContent = p ? `${p.anchors} anchor match${p.anchors === 1 ? '' : 'es'} on this page` : ''
  renderRows(p ? p.rows : [])
  await renderPdfPage(state.page)
}

function step(dir) {
  const list = state.pageList
  const i = list.findIndex((p) => p === state.page)
  if (i === -1) return gotoPage(state.page + dir)
  const next = list[Math.min(Math.max(0, i + dir), list.length - 1)]
  return gotoPage(next)
}

/* ---------------------------------------------------------------- rows --- */

function flagPills(flags) {
  const box = el('span', 'pills')
  for (const f of flags) {
    const pill = el('span', 'pill ' + (DEFECTS.has(f) ? 'bad' : 'note'), f)
    pill.title = FLAG_HELP[f] || f
    box.appendChild(pill)
  }
  return box
}

function renderRows(rows) {
  const box = $('rows')
  box.innerHTML = ''
  $('rowsLabel').textContent = `${rows.length} row${rows.length === 1 ? '' : 's'} from this page`
  if (!rows.length) {
    box.appendChild(el('p', 'note', 'No extracted row is attributed to this page. If the page prints award rows, that is the finding.'))
    return
  }
  for (const r of rows) box.appendChild(rowCard(r))
}

function rowCard(r) {
  const card = el('div', 'row' + (r.flags.some((f) => DEFECTS.has(f)) ? ' bad' : '') + (r.repairs.length ? ' repaired' : ''))
  const head = el('div', 'row-head')
  head.appendChild(el('strong', null, r.organization || '(no organization)'))
  head.appendChild(el('span', 'amt', usd(r.amount)))
  card.appendChild(head)

  const meta = el('div', 'row-meta')
  const bits = [
    ['EIN', r.ein], ['member', r.member], ['program', r.program],
    ['agency', r.agency], ['initiative', r.initiative], ['type', r.award_type],
  ].filter(([, v]) => v)
  for (const [k, v] of bits) {
    const s = el('span', 'kv')
    s.appendChild(el('span', 'k', k))
    s.appendChild(el('span', 'v', v))
    meta.appendChild(s)
  }
  card.appendChild(meta)

  if (r.flags.length) card.appendChild(flagPills(r.flags))
  if (r.ambiguous) {
    const a = el('div', 'warnline', `this (EIN, amount) is printed on ${r.pages.length} pages: ${r.pages.join(', ')} — page attribution is not certain`)
    card.appendChild(a)
  }
  if (r.repairs.length) {
    card.appendChild(el('div', 'warnline ok', `${r.repairs.length} post-extraction repair${r.repairs.length === 1 ? '' : 's'} applied — click to see what changed`))
  }
  card.onclick = () => showDetail(r)
  return card
}

/* -------------------------------------------------------------- detail --- */

function showDetail(r) {
  state.selected = r
  const d = $('detail')
  d.hidden = false
  d.innerHTML = ''
  const close = el('button', 'close', '×')
  close.onclick = () => { d.hidden = true }
  d.appendChild(close)

  d.appendChild(el('h2', null, r.organization || '(no organization)'))
  d.appendChild(el('p', 'muted', `${r.file}:${r.line} · ${r.stream} · ${usd(r.amount)} · EIN ${r.ein}`))

  // Stage 1 — the printed line
  const stage = (n, title, body) => {
    const s = el('div', 'stage')
    s.appendChild(el('h3', null, `${n}. ${title}`))
    if (typeof body === 'string') s.appendChild(el('pre', null, body))
    else s.appendChild(body)
    d.appendChild(s)
  }

  const page = state.doc.pages[(r.pages[0] || state.page) - 1]
  const line = page ? (page.text.split('\n').find((l) => l.includes(r.ein) || l.replace(/\D/g, '').includes(r.ein)) || '(line not located in the cached text)') : '(page text unavailable)'
  stage(1, `Printed on page ${r.pages[0] || '?'} — pypdf text layer`, line.trim())

  stage(2, 'What the anchor captured', `EIN     ${r.ein}\namount  ${r.amount}\nagency  ${r.agency || '(none)'}`)

  const f3 = el('table', 'kvtable')
  for (const k of ['category', 'initiative', 'award_type', 'member', 'organization', 'program', 'purpose']) {
    const tr = el('tr')
    tr.appendChild(el('th', null, k))
    tr.appendChild(el('td', null, r[k] || '—'))
    f3.appendChild(tr)
  }
  stage(3, 'Fields the parser derived around it', f3)

  if (r.repairs.length) {
    const t = el('table', 'kvtable')
    const hr = el('tr')
    for (const h of ['column', 'defect', 'source', 'before', 'after']) hr.appendChild(el('th', null, h))
    t.appendChild(hr)
    for (const rep of r.repairs) {
      const tr = el('tr')
      for (const k of ['column', 'defect', 'source', 'before', 'after']) tr.appendChild(el('td', null, rep[k] || '—'))
      t.appendChild(tr)
    }
    stage(4, 'Post-extraction repairs', t)
  } else {
    stage(4, 'Post-extraction repairs', 'None. This row is the parser’s own output, unmodified.')
  }

  const q = el('div')
  if (!r.flags.length) q.appendChild(el('p', 'ok', 'No QA flag on this row.'))
  else {
    for (const f of r.flags) {
      const p = el('p', DEFECTS.has(f) ? 'bad' : 'note')
      p.appendChild(el('strong', null, f + ': '))
      p.appendChild(document.createTextNode(FLAG_HELP[f] || ''))
      q.appendChild(p)
    }
  }
  stage(5, 'QA verdict', q)
}

/* ------------------------------------------------------------------ QA --- */

function renderQA() {
  const s = state.doc.summary
  const box = $('qa')
  box.innerHTML = ''
  box.appendChild(el('h2', null, `FY${state.doc.fiscal_year} QA`))

  const bar = (label, n, total, cls) => {
    const row = el('div', 'bar-row')
    row.appendChild(el('span', 'bar-label', label))
    const track = el('div', 'bar-track')
    const fill = el('div', 'bar-fill ' + (cls || ''))
    fill.style.width = total ? `${Math.min(100, (n / total) * 100)}%` : '0%'
    track.appendChild(fill)
    row.appendChild(track)
    row.appendChild(el('span', 'bar-n', `${n.toLocaleString()} (${total ? ((n / total) * 100).toFixed(1) : 0}%)`))
    box.appendChild(row)
  }

  box.appendChild(el('h3', null, 'Defects — a field that is wrong'))
  for (const k of ['org_merged', 'org_prose', 'org_blank']) bar(k, s.by_flag[k] || 0, s.rows, 'bad')
  box.appendChild(el('h3', null, 'Observations — empty for a reason the schema allows'))
  for (const k of ['member_blank', 'initiative_blank']) bar(k, s.by_flag[k] || 0, s.rows, 'note')

  box.appendChild(el('h3', null, 'Page attribution'))
  bar('placed on a page', s.rows_placed, s.rows, 'good')
  bar('ambiguous (printed on >1 page)', s.rows_ambiguous, s.rows, 'note')
  bar('unplaced (printed on no page)', s.rows_unplaced, s.rows, 'warn')

  box.appendChild(el('h3', null, 'Rows by stream'))
  for (const [k, v] of Object.entries(s.by_stream)) bar(k, v, s.rows)

  box.appendChild(el('h3', null, 'Reconciliation, as the parser recorded it'))
  box.appendChild(el('pre', 'recon', state.doc.reconciliation || '(none)'))
}

/* ------------------------------------------------------------ pipeline --- */

function renderPipeline() {
  const s = state.doc.summary
  const box = $('pipeline')
  box.innerHTML = ''
  box.appendChild(el('h2', null, `FY${state.doc.fiscal_year} pipeline`))
  const steps = [
    ['Source PDF', `${state.doc.pdf} — ${state.doc.page_count} pages`,
      'The adopted Schedule C. Everything downstream is derived from this and nothing else.'],
    ['Text layer', 'pypdf extract_text(), page by page',
      'What the parser actually reads. Where a page yields no text, no row can be extracted from it — visible under "Text layer the parser read" on the Page review tab.'],
    ['Anchor', `${s.anchors_in_pdf.toLocaleString()} matches across the document`,
      'An EIN followed by an amount. This is the only thing that creates a row, so an amount format the anchor does not accept costs every row on the page (issue #59).'],
    ['Fields', `${s.rows.toLocaleString()} rows written`,
      'Member, organization, program and purpose are split out of the text around each anchor, using the roster the document itself names.'],
    ['Repairs', `${s.repairs.toLocaleString()} cells changed after extraction`,
      'Applied from the Council’s own disclosure spreadsheets on an (EIN, amount) key. Every one is listed per row under stage 4 of a row detail.'],
    ['QA', `${s.rows_defective.toLocaleString()} rows carry a defect · ${s.pct_clean}% clean`,
      'validate_data.py’s own detectors, run here so this view cannot disagree with the repo’s QA report.'],
  ]
  for (const [i, [t, v, why]] of steps.entries()) {
    const s2 = el('div', 'pstep')
    s2.appendChild(el('span', 'pnum', String(i + 1)))
    const b = el('div')
    b.appendChild(el('h3', null, t))
    b.appendChild(el('p', 'pval', v))
    b.appendChild(el('p', 'muted', why))
    s2.appendChild(b)
    box.appendChild(s2)
  }
}

function renderUnplaced() {
  const box = $('unplaced')
  box.innerHTML = ''
  const u = state.doc.unplaced || []
  if (!u.length) { box.appendChild(el('p', 'ok', 'Every row is printed on a page of this PDF.')); return }
  for (const r of u) box.appendChild(rowCard(r))
}

/* ----------------------------------------------------------------- UI ---- */

$('prev').onclick = () => step(-1)
$('next').onclick = () => step(1)
$('pageJump').onchange = (e) => gotoPage(Number(e.target.value))
$('onlyRows').onchange = () => { rebuildPageList(); gotoPage(state.pageList[0] || 1) }
$('onlyFlagged').onchange = () => { rebuildPageList(); gotoPage(state.pageList[0] || 1) }
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (e.key === 'ArrowLeft') step(-1)
  if (e.key === 'ArrowRight') step(1)
  if (e.key === 'Escape') $('detail').hidden = true
})
for (const b of document.querySelectorAll('#tabs button')) {
  b.onclick = () => {
    for (const x of document.querySelectorAll('#tabs button')) x.classList.toggle('on', x === b)
    for (const t of document.querySelectorAll('.tab')) t.classList.toggle('on', t.id === 'tab-' + b.dataset.tab)
  }
}

loadManifest().catch((e) => {
  document.querySelector('main').innerHTML =
    `<div class="err"><h2>Index not built</h2><p>${e.message}</p>
     <pre>cd review-ui && python3 build_index.py</pre></div>`
})
