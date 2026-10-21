import { useQueries } from "../duckdb/useDuckDB.js";
import { DISCLOSURE_FLAG_NOTE, STATUS_LABEL, flagNotes, money } from "../format.js";
import { sourceLinks } from "../paths.js";
import * as Q from "../query/sql.js";
import { Notice, Status } from "../components/ui.jsx";
import { ScForAward, scYearsOf } from "./ScheduleC.jsx";

/** Columns in the order shown, with a label and, where the data needs one, a short explanation. */
const FIELDS = [
  ["fiscal_year", "Fiscal year"],
  ["legal_name", "Organization (legal name)"],
  ["ein", "EIN", "Digits only. One EIN can pool many bodies (a fiscal sponsor, or the City itself)."],
  ["amount", "Amount", "The workbook's own value, shown rounded to cents."],
  ["status", "Status (as printed)"],
  ["status_norm", "Status (normalized)"],
  ["council_member", "Council member (as printed)", "The roster when the workbook was exported, not necessarily the sponsor at adoption."],
  ["council_member_id", "Legistar person ID", "Derived; blank unless the printed name resolves to one member for that year."],
  ["council_member_type", "Council member type"],
  ["source", "Funding source"],
  ["agency", "Agency"],
  ["program_name", "Program"],
  ["mocs_id", "MOCS ID (workbook)", "Printed by the Council from FY2024 on."],
  ["od_mocs_id", "MOCS ID (NYC Open Data)", "A cross-reference to NYC Open Data 4d7f-74pe, FY2009–FY2021, set only on an unambiguous match. Not a source."],
  ["od_match", "Open Data amount match"],
  ["address1", "Mailing address"],
  ["address2", "Mailing address (line 2)"],
  ["city", "City"],
  ["state", "State"],
  ["postal_code", "Postal code (as printed)"],
  ["zip", "ZIP (derived)", "Where the grantee gets mail, not where services were delivered."],
  ["zip_status", "ZIP status"],
  ["zip_candidates", "ZIP candidates"],
  ["fiscal_conduit", "Fiscal conduit"],
  ["fiscal_conduit_ein", "Fiscal conduit EIN"],
  ["duplicate_group", "Duplicate group", "Set when the workbook prints exact copies of a row: the source row of the first copy. All copies are counted, as published."],
  ["row_flag", "Row flag"],
];

export default function Award({ state, go, back, manifest, pdfYears }) {
  const q = useQueries(true, `${state.ay}:${state.row}`, () =>
    state.ay != null && state.row != null ? { award: Q.awardQuery(state.ay, state.row) } : null
  );
  return (
    <section>
      <p>
        <button type="button" className="linkish" onClick={back}>
          ← Back to awards
        </button>
      </p>
      <Status loading={q.loading} error={q.error}>
        {!q.data?.award?.length ? (
          <Notice tone="warn">
            No award at FY{state.ay ?? "?"} row {state.row ?? "?"}. The link may predate a data update.
          </Notice>
        ) : (
          <Detail a={q.data.award[0]} manifest={manifest} state={state} go={go} scYears={scYearsOf(pdfYears)} />
        )}
      </Status>
    </section>
  );
}

function Detail({ a, manifest, state, go, scYears }) {
  const links = sourceLinks(manifest.source_commit, a.source_path);
  const flags = flagNotes(a.row_flag, DISCLOSURE_FLAG_NOTE);
  return (
    <>
      <h2>
        {a.legal_name || "(no name printed)"} <span className="muted">FY{a.fiscal_year}</span>
      </h2>
      <p className="big">
        {money(a.amount)} · {STATUS_LABEL[a.status_norm] ?? a.status}
      </p>
      {a.early_snapshot ? (
        <Notice tone="warn">
          FY{a.fiscal_year} is an early snapshot: {a.year_note}
        </Notice>
      ) : null}
      {flags.map((f) => (
        <Notice key={f.flag} tone="warn">
          <code>{f.flag}</code>: {f.note}
        </Notice>
      ))}

      <h3>Source</h3>
      <p>
        Row <strong>{a.source_row}</strong> of sheet <strong>{a.sheet}</strong> in <code>{a.source_path}</code>, retrieved {a.retrieved}
        {a.source_kind === "internet_archive" && a.wayback_timestamp ? `, from an Internet Archive capture (${a.wayback_timestamp})` : ", from the Council's Research & Data site"}.
      </p>
      <ul>
        {links && (
          <li>
            <a href={links.raw}>Download the spreadsheet</a> (as committed at <code>{manifest.source_commit.slice(0, 7)}</code>) ·{" "}
            <a href={links.page}>its page on GitHub</a>
          </li>
        )}
        {a.source_url && (
          <li>
            Published at <a href={a.source_url}>{a.source_url}</a>
          </li>
        )}
        <li>
          sha256 <code>{a.sha256}</code>
        </li>
      </ul>

      <ScForAward a={a} scYears={scYears} state={state} go={go} />
      <h3>Every column</h3>
      <dl className="fields">
        {FIELDS.map(([k, label, note]) => (
          <div key={k}>
            <dt>
              {label} <code className="muted small">{k}</code>
            </dt>
            <dd>
              {k === "amount" ? money(a[k]) : a[k] === null || a[k] === "" ? <span className="muted">blank</span> : String(a[k])}
              {note ? <div className="muted small">{note}</div> : null}
            </dd>
          </div>
        ))}
      </dl>
    </>
  );
}
