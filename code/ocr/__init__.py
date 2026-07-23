"""
OCR pipeline for scanned NYC Council budget documents.

Built for the FY2009 Transparency Resolutions (`source/FY09/transparency-resolutions/`),
which are 300-dpi bitonal Xerox scans with NO text layer, whose data pages are landscape
tables rotated into portrait -- in BOTH directions, varying page to page within one file.

The pipeline is a chain of stages, each of which writes its artifacts to a cache directory
so any stage can be re-run in isolation while iterating:

    0 render     PDF page            -> PNG                          (render.py)
    1 orient     PNG                 -> deskewed, upright PNG        (orient.py)
    2 classify   upright PNG         -> narrative/divider/chart      (classify.py)
    3 grid       chart PNG           -> ruled-line cell rectangles   (grid.py)
    4 recognize  PNG + grid          -> per-cell text + confidence   (recognize.py)
    5 headers    header-row cells    -> canonical column mapping     (headers.py)
    6 assemble   cells + mapping     -> schema rows + review queue   (assemble.py)
    7 report     rows                -> reconciliation + QA report   (report.py)

Column identity comes from the ruled grid (geometry), never from regex-guessing at a
reflowed text line -- that is the whole reason this beats the FY10-FY13 text-layer output.

Only render.py, orient.py, classify.py and recognize.py touch heavy dependencies, and they
import them lazily inside functions, so grid.py / headers.py / assemble.py (and their
tests) run in the plain `.venv` with no torch installed.
"""
