/**
 * open-data.mjs — "is this record on NYC Open Data?" (research/2026-10-21-open-data-tracking/PLAN.md
 * §5, approved 2026-10-21), loaded into the index by build-index.mjs from data/open_data/, which
 * code/build_open_data_crosswalk.py writes from committed snapshots (no network here or there).
 *
 *   open_data_crosswalk   one row per (record, dataset) where the dataset covers the record's year
 *   open_data_coverage    per family, dataset and fiscal year: our records by status, the portal's
 *                         rows and portal-only rows (PLAN Q5: counted, never listed)
 *   open_data_datasets    each dataset's name, snapshot date and last check (source/open-data-watch.csv)
 *   open_data_rules       the match rules, by id (a crosswalk row stores the id, not the sentence)
 *
 * Kept compact, because this index ships in the npm package: the record key is stored split
 * (fiscal_year, record_row, record_amount_fy), the rule as an id, and an ambiguous row keeps the
 * number of portal candidates, not their ids (data/open_data/crosswalk_*.csv lists them).
 *
 * Every row is checked: a status, family or dataset outside the vocabulary is a stop, and so is a
 * record key that does not name a row the index holds (expense -> disclosure, capital award ->
 * capital_council or a loaded pdf_capital_sd row, T&C unit -> a loaded pdf_terms_units row).
 *
 * The gate follows the PDF families' (scripts/pdf-families.mjs): a crosswalk row about a PDF-derived
 * record (T&C units; `pdf|` capital rows) loads only when that family and year are loaded, so the
 * default index (status = closed only) carries none of them.
 */

const T = "TEXT";
const I = "INTEGER";

export const OPEN_DATA_FAMILIES = ["expense", "capital_award", "capital_line", "terms_unit"];
export const OPEN_DATA_STATUSES = ["same", "differs", "ambiguous", "absent", "context", "not_covered"];
export const OPEN_DATA_DATASETS = {
  "4d7f-74pe": "expense", "ujre-m2tj": "expense", "t474-a92g": "capital_award",
  "46m8-77gv": "capital_line", "2cmn-uidm": "capital_line", "djxg-kcfi": "capital_line",
  "mwzb-yiwb": "terms_unit", "uvw5-9znb": "reference",
};

const XW_CSV = ["family", "record_key", "fiscal_year", "dataset_id", "snapshot_date", "portal_row_id",
  "match_status", "match_rule", "differing_fields", "portal_value", "portal_status", "portal_as_of"];
const COV_CSV = ["family", "dataset_id", "fiscal_year", "snapshot_date", "covered", "records", "same",
  "differs", "ambiguous", "ambiguous_present", "absent", "context", "not_covered", "portal_rows", "portal_only", "note"];

export const OPEN_DATA_SCHEMA = {
  open_data_crosswalk: [
    ["family", T], ["fiscal_year", I],
    // The key split for joins: expense (fiscal_year, record_row = source_row); capital award
    // (fiscal_year = report year, record_row = source_row or SUB ID, record_amount_fy).
    ["record_row", T], ["record_amount_fy", I], ["record_pdf", I],
    // T&C: "agency|unit" (the agency is "A+B" where a retired CSV does not say whose unit it is).
    // PDF capital: "p<page>r<row>" where one SUB ID is printed on two Part I rows, else null.
    ["record_part", T],
    ["dataset_id", T], ["portal_row_id", T], ["candidates", I], ["match_status", T],
    ["rule_id", I], ["differing_fields", T], ["portal_value", T], ["portal_status", T],
    ["portal_as_of", T],
  ],
  open_data_rules: [["rule_id", I], ["match_rule", T]],
  open_data_coverage: [
    ["family", T], ["dataset_id", T], ["fiscal_year", I], ["snapshot_date", T], ["covered", I],
    // ambiguous_present: the ambiguous rows whose presence is certain (no more of ours than
    // portal rows in the bucket); the rest are only possibly on the portal.
    ["records", I], ["same", I], ["differs", I], ["ambiguous", I], ["ambiguous_present", I], ["absent", I], ["context", I],
    ["not_covered", I], ["portal_rows", I], ["portal_only", I], ["note", T],
  ],
  open_data_datasets: [
    ["dataset_id", T], ["family", T], ["name", T], ["url", T], ["snapshot_date", T],
    ["rows_updated_at", T], ["checked_at", T], ["verdict", T],
  ],
};
export const OPEN_DATA_TABLES = Object.keys(OPEN_DATA_SCHEMA);

export function openDataSchemaSql() {
  return Object.entries(OPEN_DATA_SCHEMA)
    .map(([t, cols]) => `CREATE TABLE ${t} (${cols.map(([c, ty]) => `${c} ${ty}`).join(", ")});`)
    .join("\n");
}

function int(v, where) {
  if (v === "" || v === undefined) return null;
  const n = Number(v);
  if (!Number.isInteger(n)) throw new Error(`${where}: ${JSON.stringify(v)} is not an integer`);
  return n;
}

function header(rows, want, rel) {
  if (rows.length && Object.keys(rows[0]).join(",") !== want.join(",")) {
    throw new Error(`${rel}: columns ${Object.keys(rows[0]).join(",")}; expected ${want.join(",")}`);
  }
}

/**
 * @param loadedPdf [{fiscal_year, family}] from loadPdfFamilies(); gates PDF-derived records.
 * @returns {counts} for meta.counts
 */
export function loadOpenData(db, io, loadedPdf) {
  const has = (family, fy) => loadedPdf.some((l) => l.family === family && l.fiscal_year === fy);
  const counts = Object.fromEntries(OPEN_DATA_TABLES.map((t) => [t, 0]));

  const rules = new Map();
  const snapshots = new Map();
  const ruleId = (text) => {
    if (!rules.has(text)) rules.set(text, rules.size + 1);
    return rules.get(text);
  };
  const insX = db.prepare(`INSERT INTO open_data_crosswalk VALUES (${OPEN_DATA_SCHEMA.open_data_crosswalk.map(() => "?").join(", ")})`);
  db.transaction(() => {
    for (const fam of OPEN_DATA_FAMILIES) {
      const rel = `data/open_data/crosswalk_${fam}.csv`;
      const rows = io.readCsv(rel);
      header(rows, XW_CSV, rel);
      rows.forEach((r, i) => {
        const at = `${rel} row ${i + 2}`;
        if (r.family !== fam) throw new Error(`${at}: family ${JSON.stringify(r.family)}`);
        if (!OPEN_DATA_STATUSES.includes(r.match_status) || r.match_status === "not_covered") {
          throw new Error(`${at}: match_status ${JSON.stringify(r.match_status)}`);
        }
        if (OPEN_DATA_DATASETS[r.dataset_id] !== fam) throw new Error(`${at}: dataset ${JSON.stringify(r.dataset_id)} for ${fam}`);
        const fy = int(r.fiscal_year, `${at} fiscal_year`);
        const k = r.record_key.split("|");
        let row = null, amountFy = null, pdf = 0, part = null;
        if (fam === "expense") {
          if (k.length !== 2 || Number(k[0]) !== fy) throw new Error(`${at}: record_key ${JSON.stringify(r.record_key)}`);
          row = k[1];
        } else if (fam === "capital_award") {
          if (k[0] === "pdf") {
            pdf = 1;
            if (!has("capital_sd", fy)) return;     // a PDF-derived record: only with its family
            // pdf|fy|SUB ID|amount fy, or pdf|fy|SUB ID|p<page>r<row>|amount fy where the PDF
            // prints one SUB ID on two Part I rows (FY2025); the place goes in record_part.
            if (k.length === 5 && !/^p\d+r\d+$/.test(k[3]) || k.length < 4 || k.length > 5) {
              throw new Error(`${at}: record_key ${JSON.stringify(r.record_key)}`);
            }
            row = k[2];
            if (k.length === 5) part = k[3];
            amountFy = int(k[k.length - 1], `${at} record_key`);
          } else {
            if (k.length !== 3 || Number(k[0]) !== fy) throw new Error(`${at}: record_key ${JSON.stringify(r.record_key)}`);
            row = k[1];
            amountFy = int(k[2], `${at} record_key`);
          }
        } else if (fam === "terms_unit") {
          pdf = 1;
          if (!has("terms", fy)) return;
          row = k[1];                                  // item number
          part = `${k[2]}|${k[3].replace(/#\d+$/, "")}`;
        } else {
          row = k[1];                                  // budget line
        }
        if (snapshots.has(r.dataset_id) && snapshots.get(r.dataset_id) !== r.snapshot_date) {
          throw new Error(`${at}: ${r.dataset_id} has two snapshot dates in one crosswalk`);
        }
        snapshots.set(r.dataset_id, r.snapshot_date);
        const ids = r.portal_row_id === "" ? [] : r.portal_row_id.split(";");
        const amb = r.match_status === "ambiguous";
        if (["same", "differs"].includes(r.match_status) && ids.length !== 1) {
          throw new Error(`${at}: ${ids.length} portal rows on a ${r.match_status} row`);
        }
        // An ambiguous row's candidate list is capped in the CSV ("…" marks more); the rule text
        // carries the full count where it is a bucket.
        const m = /(\d+) on the portal/.exec(r.match_rule);
        insX.run(r.family, fy, row, amountFy, pdf, part, r.dataset_id, amb ? "" : r.portal_row_id,
          amb ? (m ? Number(m[1]) : ids.length) : ids.length,
          r.match_status, ruleId(r.match_rule), r.differing_fields, r.portal_value, r.portal_status, r.portal_as_of);
        counts.open_data_crosswalk++;
      });
    }
  })();

  const covRel = "data/open_data/coverage.csv";
  const cov = io.readCsv(covRel);
  header(cov, COV_CSV, covRel);
  const insC = db.prepare(`INSERT INTO open_data_coverage VALUES (${OPEN_DATA_SCHEMA.open_data_coverage.map(() => "?").join(", ")})`);
  db.transaction(() => {
    cov.forEach((r, i) => {
      const at = `${covRel} row ${i + 2}`;
      if (!OPEN_DATA_FAMILIES.includes(r.family) || OPEN_DATA_DATASETS[r.dataset_id] !== r.family) {
        throw new Error(`${at}: family ${r.family} / dataset ${r.dataset_id}`);
      }
      const fy = int(r.fiscal_year, `${at} fiscal_year`);
      if (r.family === "terms_unit" && !has("terms", fy)) return;
      if (!["yes", "no"].includes(r.covered)) throw new Error(`${at}: covered ${JSON.stringify(r.covered)}`);
      const n = (c) => int(r[c], `${at} ${c}`);
      const sum = OPEN_DATA_STATUSES.reduce((s, c) => s + n(c), 0);
      if (sum !== n("records")) throw new Error(`${at}: statuses add to ${sum}, records ${r.records}`);
      insC.run(r.family, r.dataset_id, fy, r.snapshot_date, r.covered === "yes" ? 1 : 0, n("records"), n("same"),
        n("differs"), n("ambiguous"), n("ambiguous_present"), n("absent"), n("context"), n("not_covered"), n("portal_rows"), n("portal_only"), r.note);
      counts.open_data_coverage++;
    });
  })();

  // The newest metadata check of each dataset (source/open-data-watch.csv is append-only).
  const watchRel = "source/open-data-watch.csv";
  const watch = io.readCsv(watchRel);
  const latest = new Map();
  for (const w of watch) {
    if (!(w.dataset_id in OPEN_DATA_DATASETS)) throw new Error(`${watchRel}: unknown dataset ${w.dataset_id}`);
    if (!latest.has(w.dataset_id) || w.checked_at > latest.get(w.dataset_id).checked_at) latest.set(w.dataset_id, w);
  }
  const insD = db.prepare("INSERT INTO open_data_datasets VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
  const insR = db.prepare("INSERT INTO open_data_rules VALUES (?, ?)");
  for (const c of cov) if (!snapshots.has(c.dataset_id)) snapshots.set(c.dataset_id, c.snapshot_date);
  db.transaction(() => {
    for (const [id, w] of [...latest.entries()].sort()) {
      insD.run(id, OPEN_DATA_DATASETS[id], w.name, `https://data.cityofnewyork.us/d/${id}`, snapshots.get(id) ?? "",
        w.rows_updated_at, w.checked_at, w.verdict);
      counts.open_data_datasets++;
    }
    for (const [text, id] of rules) {
      insR.run(id, text);
      counts.open_data_rules++;
    }
  })();
  return { counts };
}

/** Every crosswalk row names a record the index holds. Returns problems (strings). */
export function verifyOpenData(db) {
  const problems = [];
  const orphan = (sql, what) => {
    const n = db.prepare(sql).get().n;
    if (n) problems.push(`open_data_crosswalk: ${n} ${what} rows name no record in the index`);
  };
  orphan(`SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'expense' AND NOT EXISTS
          (SELECT 1 FROM disclosure d WHERE d.fiscal_year = x.fiscal_year AND d.source_row = CAST(x.record_row AS INTEGER))`, "expense");
  orphan(`SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'capital_award' AND record_pdf = 0 AND NOT EXISTS
          (SELECT 1 FROM capital_council c WHERE c.report_year = x.fiscal_year AND c.source_row = x.record_row
             AND (c.amount_fy = x.record_amount_fy OR (c.amount_fy IS NULL AND x.record_amount_fy IS NULL)))`, "capital award");
  orphan(`SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'capital_award' AND record_pdf = 1 AND NOT EXISTS
          (SELECT 1 FROM pdf_capital_sd p WHERE p.fiscal_year = x.fiscal_year AND p.sub_id = x.record_row AND p.part = 'I')`, "PDF capital");
  orphan(`SELECT COUNT(*) n FROM open_data_crosswalk x WHERE family = 'terms_unit' AND NOT EXISTS
          (SELECT 1 FROM pdf_terms p WHERE p.fiscal_year = x.fiscal_year AND p.item_number = CAST(x.record_row AS INTEGER))`, "T&C");
  for (const t of ["open_data_crosswalk", "open_data_coverage", "open_data_datasets", "open_data_rules"]) {
    if (db.prepare(`SELECT COUNT(*) n FROM ${t}`).get().n === 0) problems.push(`${t}: 0 rows`);
  }
  return problems;
}
