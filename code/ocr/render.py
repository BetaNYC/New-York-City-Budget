"""
Stage 0 -- render PDF pages to grayscale PNGs.

The FY09 scans are 2560x3296 JBIG2 bitonal images on letter pages, i.e. exactly 300 dpi.
Rendering at 300 dpi is therefore 1:1 with the stored bitmap: no resampling, no ringing,
no invented grey. Do not raise this -- upscaling here would only blur the rules that
grid.py depends on.
"""
import os
import re

DPI = 300


def page_png(cache_dir, stem, page_no, kind="raw"):
    """Cache path for one page image. `kind` is 'raw' (as scanned) or 'upright' (stage 1)."""
    return os.path.join(cache_dir, stem, kind, f"page-{page_no:03d}.png")


def render_pdf(pdf_path, cache_dir, dpi=DPI, pages=None, force=False):
    """Render `pdf_path` to cache_dir/<stem>/raw/page-NNN.png. Returns [(page_no, path)].

    `pages` is an optional 1-based iterable to restrict the render while iterating.
    Existing PNGs are reused unless `force`, so re-running stage 0 is nearly free.
    """
    import pypdfium2 as pdfium
    from PIL import Image

    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    outdir = os.path.join(cache_dir, stem, "raw")
    os.makedirs(outdir, exist_ok=True)

    doc = pdfium.PdfDocument(pdf_path)
    wanted = set(pages) if pages else None
    out = []
    try:
        for i in range(len(doc)):
            page_no = i + 1
            if wanted is not None and page_no not in wanted:
                continue
            path = os.path.join(outdir, f"page-{page_no:03d}.png")
            if os.path.exists(path) and not force:
                out.append((page_no, path))
                continue
            bitmap = doc[i].render(scale=dpi / 72.0, grayscale=True)
            arr = bitmap.to_numpy()
            # A grayscale pdfium render comes back as (h, w, 1); PIL's fromarray cannot map
            # a trailing single channel, so drop it to a plain 2-D (h, w) array.
            if arr.ndim == 3 and arr.shape[2] == 1:
                arr = arr[:, :, 0]
            Image.fromarray(arr).convert("L").save(path)
            out.append((page_no, path))
    finally:
        doc.close()
    return out


def parse_page_spec(spec):
    """'9-12,20' -> {9,10,11,12,20}. Returns None for an empty spec (meaning: all pages)."""
    if not spec:
        return None
    pages = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            pages.update(range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            pages.add(int(part))
    return pages or None
