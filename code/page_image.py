"""
The page-image rule (decided 2026-10-22 in #209; PLAN.md decision 19): where the page and the
PDF's text layer disagree, a person checks the page in review; if confirmed, the value a reader sees
on the page is used, flagged "read from the page image". The reader never swaps a value on its own.

A review decision carries the confirmed value, in the decisions file's own columns:

    decision  read_from_page_image
    note      page shows <field>: "<value>"   (the reviewer's own words may follow)

`<field>` is one of FIELDS, and the review row must name one data row (Schedule C `award_id`,
transparency `row_id`). code/validate_review_decisions.py checks both. The readers apply it
(code/parse_schedule_c_v2.py, code/parse_transparency_v2.py) before the disclosure alignment, so
everything downstream sees the page's value. The text layer's value stays where it was read
(`ein_printed`, `<field>_raw`), and the row's `read_from_page_image` lists the fields read from the
page image. Amounts are not in FIELDS: a page-read amount would also move the printed totals the
reader ties, which this rule does not yet cover.
"""
import re

DECISION = "read_from_page_image"
FIELDS = ("ein", "org", "member", "agency", "purpose")
NOTE = re.compile(r'page shows (\w+): "([^"]+)"')
EIN = re.compile(r"^(\d{2}-\d{7}|\d{9})$")


def parse(note):
    """(field, value) from a decision's note; ValueError saying what is wrong otherwise."""
    m = NOTE.search(note or "")
    if not m:
        raise ValueError('the note must say what the page shows: page shows <field>: "<value>"')
    field, value = m.groups()
    if field not in FIELDS:
        raise ValueError(f"field {field!r} cannot be read from the page image; allowed: "
                         + ", ".join(FIELDS))
    if field == "ein" and not EIN.match(value):
        raise ValueError(f"{value!r} is not an EIN (12-3456789 or 123456789)")
    return field, value


def apply(row, field, value):
    """Use the page's value for `field` on a data row; flag it in `read_from_page_image`."""
    row[field] = value.replace("-", "") if field == "ein" else value
    done = [f for f in (row.get("read_from_page_image") or "").split(";") if f]
    if field not in done:
        done.append(field)
    row["read_from_page_image"] = ";".join(done)


def apply_decisions(review_rows, rows_by_id, id_column):
    """Apply every read_from_page_image decision in a family's review rows (each carrying its
    `decision` and `note`) to the data row its `id_column` names. Returns the rows changed.
    Raises ValueError on a decision that cannot be applied: the run stops, nothing is guessed."""
    changed = []
    for rv in review_rows:
        if rv.get("decision") != DECISION:
            continue
        row = rows_by_id.get(rv.get(id_column) or "")
        if row is None:
            raise ValueError(f"review {rv['review_id']}: {DECISION} needs a review row naming one "
                             f"data row ({id_column})")
        field, value = parse(rv.get("note"))
        apply(row, field, value)
        changed.append(row)
    return changed
