"""
Transparency resolutions from the PDFs, checked (GitHub #103, epic #101).

Built on the Schedule C toolkit (code/schedc/, code/schedc_cv/): the same vector lattice from
pdfplumber's drawn borders, the same cell text rule, Christian Moscardi's image grid as the
independent check, and the same ink-coverage check. What is new here is what transparency
charts need and Schedule C did not:

  - text is read by *runs* (characters drawn one after another on a line), because Excel
    clips a cell's overflowing text at the next drawn rule. The hidden letters are still in
    the text layer; reading by single characters would paste them into the neighbouring cell.
  - a data cell that spans two header columns (no rule drawn between them) is split by run.
  - a header column with no drawn cell in a row gets a cell made from the header's x-range.

Every year-specific fact lives in config/transparency/fyNNNN.toml.
"""
