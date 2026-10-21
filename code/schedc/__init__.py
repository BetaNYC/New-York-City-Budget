"""
Schedule C from the PDFs: the deterministic core (pdfplumber + pypdfium2 + stdlib).

Plan: research/2026-10-19-schedule-c-pdf-toolkit/PLAN.md. Stage numbers in module docstrings
are that plan's (§3). The optional image-side checks (image lattice, ink coverage) live in
code/schedc_cv/, because they need OpenCV and numpy.

Built first for FY2027 (GitHub #102); every year-specific fact lives in
config/schedule_c/fyNNNN.toml, not in this code.
"""
