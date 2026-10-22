"""
The page-image rule (decided 2026-10-22 in #209; PLAN.md decision 19): where the page and the
PDF's text layer disagree, a person checks the page in review; if confirmed, the value a reader sees
on the page is used, flagged "read from the page image". The reader never swaps a value on its own.

A review decision carries the confirmed value, in the decisions file's own columns:

    decision  read_from_page_image
    note      page shows <field>: "<value>"   (the reviewer's own words may follow)

`<field>` is one of FIELDS and, when the review row names a field, that field; the review row
must name one data row (Schedule C `award_id`, transparency `row_id`; not yet a sub-award).
code/validate_review_decisions.py checks all three. The readers apply it
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


# Row flags that say the text layer's EIN could not be read (Schedule C `ein_unreadable`,
# transparency `ein_blank` / `ein_odd`): once a person reads the EIN from the page, the row says
# that instead (its check id is the same, so the row stays linked to its review item).
EIN_TEXT_FLAGS = ("ein_unreadable", "ein_blank", "ein_odd")
EIN_PAGE_FLAG = "ein_read_from_page_image"


def is_subaward(row_id):
    """A Schedule C sub-award id (fyNN-sub-...): not a data row this rule can change yet."""
    return "-sub-" in (row_id or "")


def parse(note, row_field=""):
    """(field, value) from a decision's note; ValueError saying what is wrong otherwise. When the
    review row names a field (`row_field`), the note must name the same one."""
    m = NOTE.search(note or "")
    if not m:
        raise ValueError('the note must say what the page shows: page shows <field>: "<value>"')
    field, value = m.groups()
    if field not in FIELDS:
        raise ValueError(f"field {field!r} cannot be read from the page image; allowed: "
                         + ", ".join(FIELDS))
    if field == "ein" and not EIN.match(value):
        raise ValueError(f"{value!r} is not an EIN (12-3456789 or 123456789)")
    if row_field and row_field != field:
        raise ValueError(f"the review item is about {row_field!r}; the note names {field!r}")
    return field, value


def apply(row, field, value):
    """Use the page's value for `field` on a data row; flag it in `read_from_page_image`."""
    row[field] = value.replace("-", "") if field == "ein" else value
    if field == "ein":
        # The row must not still say its EIN is unreadable: the text layer's verdict becomes
        # "read from the page image" (row flag) and, in transparency, ein_format says so too.
        flags = row.get("row_flags")
        if isinstance(flags, list):
            row["row_flags"] = list(dict.fromkeys(EIN_PAGE_FLAG if f in EIN_TEXT_FLAGS else f
                                                  for f in flags))
        if "ein_format" in row:
            row["ein_format"] = "page_image"
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
        if is_subaward(rv.get(id_column)):
            raise ValueError(f"review {rv['review_id']}: {DECISION} is not supported on a "
                             "sub-award row yet")
        row = rows_by_id.get(rv.get(id_column) or "")
        if row is None:
            raise ValueError(f"review {rv['review_id']}: {DECISION} needs a review row naming one "
                             f"data row ({id_column})")
        field, value = parse(rv.get("note"), rv.get("field") or "")
        apply(row, field, value)
        changed.append(row)
    return changed
