import { HowWeCheck, StateBadge } from "../components/OpenData.jsx";
import { docUrl, REPO_URL } from "../paths.js";

/** What the data is, where it comes from, and what is missing. Readable before the data loads. */
export default function About({ manifest }) {
  const commit = manifest?.source_commit;
  return (
    <section className="prose">
      <h2>About the data</h2>
      <p>
        This explorer shows the NYC Council's discretionary designations from the Council's own expense funding disclosure spreadsheets, its capital workbooks,
        and NYC Open Data. It is built from exactly the index the <a href="https://www.npmjs.com/package/@betanyc/nyc-budget-mcp">@betanyc/nyc-budget-mcp</a>{" "}
        server answers from, and a test checks, year by year, that the two hold the same rows and the same totals.
      </p>
      {manifest?.include_reviewed ? (
        <>
          <p>
            It also shows <strong>tables read from the Council's budget PDFs</strong>: Schedule C, transparency resolutions, the capital book and Terms and
            Conditions, FY2018 on. These are the only data here read from a PDF. More below.
          </p>
          <p>The PDF tables load only when you open their page, so the first page opens faster.</p>
        </>
      ) : (
        <p>Nothing in this build is extracted from a PDF.</p>
      )}
      <h3>Expense awards</h3>
      <ul>
        <li>FY2009 and FY2011–FY2027, one row per designation the Council's workbook prints, with clearance status and the grantee's mailing address.</li>
        <li>
          <strong>FY2010 is not included.</strong> The reason is recorded in <a href={docUrl(commit, "data/disclosure_years.csv")}>data/disclosure_years.csv</a>{" "}
          and shown wherever FY2010 comes up.
        </li>
        <li>
          <strong>Early snapshots</strong> (FY2009, FY2013) were frozen while many designations were still pending. Their Cleared totals are labeled and never
          shown as headline figures.
        </li>
        <li>
          <code>council_member</code> is the roster when the workbook was exported, not necessarily the sponsor at adoption. Addresses are mailing addresses,
          not where services were delivered.
        </li>
        <li>The disclosure is the Council's later, award-level list. It is not the adopted budget's Schedule C, and its totals are not Schedule C totals.</li>
      </ul>
      <h3>Capital</h3>
      <ul>
        <li>
          Council capital lists for FY2015–FY2017 and FY2019–FY2027, from the Council's workbooks and NYC Open Data t474-a92g.{" "}
          <strong>FY2018 is missing</strong> from every source found; nothing before FY2015 is in this dataset. See{" "}
          <a href={docUrl(commit, "data/capital/README.md")}>data/capital/README.md</a>.
        </li>
        <li>The comparison with OMB's adopted capital budget is by budget line only, the one key the two share.</li>
      </ul>
      {manifest?.include_reviewed ? (
        <>
          <h3>Tables read from the PDFs</h3>
          <ul>
            <li>
              Only tables re-read by our checked process are shown. Each is read from the PDF's own text and ruled lines, checked against a second reading of
              the page image and against every total the PDF prints, and every doubt goes to a person to decide. How:{" "}
              <a href={docUrl(commit, "PDF-RECIPE.md")}>PDF-RECIPE.md</a>. The older PDF parser's output is never shown.
            </li>
            <li>
              Each row says where its year stands. <em>Checked, review in progress</em>: the table is checked, and a person is still deciding some flagged
              rows. <em>Checked and reviewed</em>: a person has decided every flagged row. Each year's status is in{" "}
              <a href={docUrl(commit, "data/pdf_years.csv")}>data/pdf_years.csv</a>.
            </li>
            <li>
              Values are shown as the PDF prints them, never corrected. Where a row needs a second look, it says why in plain words, and gives the decision
              once a person has made it. Where we have a question for the Council's Finance Division, the row says whether it has been sent, and the answer
              when there is one.
            </li>
            <li>
              Text that is in the PDF but can't be seen on the printed page is shown on its own, always labeled <em>hidden text</em>.
            </li>
            <li>
              The capital book's total is its Part I. Part II lists again the Part I projects that went to non-city groups. Rows printed only in Part II are
              listed apart and never added. Borough codes A and C are shown as printed: their meaning is unclear, and it is an{" "}
              <a href={`${REPO_URL}/issues/227`}>open question</a>.
            </li>
            <li>Every row links to its page in the PDF, with the row highlighted.</li>
          </ul>
        </>
      ) : null}
      <h3>Is it on NYC Open Data?</h3>
      <p>
        Each row says one of four things: <StateBadge state="found" />, <StateBadge state="maybe" />, <StateBadge state="notfound" /> or{" "}
        <StateBadge state="nocheck" />. Each names the date of the copy we checked.
      </p>
      <HowWeCheck />
      <h3>Every row cites its file</h3>
      <p>
        Each award and capital row links to the spreadsheet it came from, at the commit this site was built from, with the sheet, row, retrieval date and
        sha256. Column definitions: <a href={docUrl(commit, "DATA-DICTIONARY.md")}>DATA-DICTIONARY.md</a>.
      </p>
      <h3>Download or ask</h3>
      <ul>
        <li>
          The data: <a href={REPO_URL}>the New-York-City-Budget repository</a>.
        </li>
        <li>
          Ask an AI assistant: the <a href={`${REPO_URL}/blob/main/mcp/README.md`}>nyc-budget-mcp README</a>. Its PDF tables are an optional download (
          <code>npx @betanyc/nyc-budget-mcp download --pdf-tables</code>) from the repository's <a href={`${REPO_URL}/releases`}>data releases</a>.
        </li>
      </ul>
      <h3>Credits</h3>
      <p>
        Built by <a href="https://beta.nyc">BetaNYC</a>. The app's structure (DuckDB-WASM over Parquet, URL-hash state, query building) is adapted from
        BetaNYC's <a href="https://github.com/BetaNYC/nyc-eo-explorer">nyc-eo-explorer</a>, MIT License. Source documents are © the City of New York. Queries run
        in your browser with <a href="https://github.com/duckdb/duckdb-wasm">DuckDB-WASM</a>.
      </p>
    </section>
  );
}
