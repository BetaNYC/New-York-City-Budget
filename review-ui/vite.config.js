import { defineConfig } from 'vite'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const REPO = path.dirname(HERE)

// Year -> adopted Schedule C PDF. Kept in step with review-ui/build_index.py; if you add a year,
// add it in both. The PDFs live in source/ and are hundreds of megabytes in total, so they are
// streamed from disk on request rather than copied into public/ where the build would bundle them.
const PDFS = {
  2015: 'source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf',
  2016: 'source/FY16/fy2016-skedcf.pdf',
  2017: 'source/FY17/FY17-Schedule-C.pdf',
  2018: 'source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf',
  2019: 'source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf',
  2020: 'source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf',
  2021: 'source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf',
  2022: 'source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf',
  2023: 'source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf',
  2024: 'source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf',
  2025: 'source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf',
  2026: 'source/FY26/Fiscal-2026-Schedule-C-4.pdf',
  2027: 'source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf',
}

/** Serve the source PDFs read-only, by fiscal year, with range support so PDF.js can seek. */
function sourcePdfs() {
  return {
    name: 'source-pdfs',
    configureServer(server) {
      server.middlewares.use('/pdf/', (req, res, next) => {
        const fy = (req.url || '').replace(/^\//, '').replace(/\.pdf$/, '')
        const rel = PDFS[fy]
        if (!rel) { res.statusCode = 404; return res.end(`no PDF mapped for FY${fy}`) }
        const abs = path.join(REPO, rel)
        if (!fs.existsSync(abs)) { res.statusCode = 404; return res.end(`missing on disk: ${rel}`) }
        const size = fs.statSync(abs).size
        res.setHeader('Content-Type', 'application/pdf')
        res.setHeader('Accept-Ranges', 'bytes')
        const range = req.headers.range
        if (range) {
          const m = /bytes=(\d*)-(\d*)/.exec(range)
          const start = m[1] ? parseInt(m[1], 10) : 0
          const end = m[2] ? parseInt(m[2], 10) : size - 1
          res.statusCode = 206
          res.setHeader('Content-Range', `bytes ${start}-${end}/${size}`)
          res.setHeader('Content-Length', end - start + 1)
          return fs.createReadStream(abs, { start, end }).pipe(res)
        }
        res.setHeader('Content-Length', size)
        fs.createReadStream(abs).pipe(res)
      })
    },
  }
}

export default defineConfig({
  plugins: [sourcePdfs()],
  server: { port: 5180, open: true },
  // pdfjs-dist ships its worker as an ES module; let Vite bundle it rather than fetching a CDN
  // copy, because this tool has to run against local files with no network.
  worker: { format: 'es' },
})
