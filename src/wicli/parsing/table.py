# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of WiCLIpedia.
#
# WiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with WiCLIpedia.  If not, see <https://www.gnu.org/licenses/>.

"""Module implementing the parsing of tables in Wikipedia wikitext.

This module converts the raw `{|...|}` wikitext block captured by the lexer
into a structured `ParsedTable`, and provides an encode/decode round trip so
that this structured data can travel through `parser.py`'s `blocks` list
(which otherwise only holds plain strings) up to `render.py`.

The encoding does not reuse the `\x00LABEL\x00value\x00` marker scheme used
elsewhere in the project, because a table carries structured data (rows of
cells, each with its own header flag) rather than a single opaque string.

Known limitations: `colspan` is not merged; cells using it are rendered as-is
in their own column. `rowspan` is fully supported: spanned values are inherited
into subsequent rows at the correct column position.
"""

import re
from dataclasses import dataclass

_ROW_SEP = "\x01"
_CELL_SEP = "\x02"
_HEADER_MARK = "\x03"
_CAPTION_SEP = "\x04"


@dataclass
class TableCell:
    text: str
    is_header: bool
    rowspan: int = 1


@dataclass
class ParsedTable:
    rows: list[list[TableCell]]
    caption: str | None = None


def parse_table(raw: str) -> ParsedTable:
    """Parse a raw `{| ... |}` wikitext block into a `ParsedTable` object.

    The first line (table-level attributes, e.g., `{| class="wikitable"`) is
    always discarded. Cells with `rowspan` propagate their value into subsequent
    rows at the correct column position. Rows are padded to uniform width.
    """

    lines = raw.splitlines()
    rows: list[list[TableCell]] = []
    current_cells: list[TableCell] = []
    caption: str | None = None
    # Maps column index -> {"cell": TableCell, "remaining": int}
    active_spans: dict = {}

    for line in lines[1:]:
        stripped = line.strip()

        if stripped.startswith("|}"):
            break

        if stripped.startswith("|-"):
            row, active_spans = _finalize_row(current_cells, active_spans)
            if row:
                rows.append(row)
            current_cells = []
            continue

        # Handle caption lines (`|+`) before processing generic cell lines,
        # so that the caption is not included in the first row of cells.
        if stripped.startswith("|+"):
            caption = stripped[2:].strip()
            continue

        if stripped.startswith("!"):
            current_cells.extend(_split_cells(stripped[1:], "!!", is_header=True))

        elif stripped.startswith("|"):
            current_cells.extend(_split_cells(stripped[1:], "||", is_header=False))

    # Flush any remaining cells after the loop
    row, _ = _finalize_row(current_cells, active_spans)
    if row:
        rows.append(row)

    # Pad short rows so every row has the same number of columns for rendering.
    max_cols = max((len(r) for r in rows), default=0)
    for r in rows:
        r.extend(TableCell("", False) for _ in range(max_cols - len(r)))

    return ParsedTable(rows=rows, caption=caption)


def _finalize_row(
    new_cells: list[TableCell],
    active_spans: dict,
) -> tuple[list[TableCell], dict]:
    """Build a finalized row by inserting inherited rowspan cells at the correct
    column positions, and return the updated active spans for the next row."""

    finalized: dict[int, TableCell] = {}

    # Place inherited cells at their fixed column positions
    for col, span_info in active_spans.items():
        finalized[col] = span_info["cell"]

    # Place new cells in the first unoccupied column each time
    col = 0
    next_span_updates: dict = {}
    for cell in new_cells:
        while col in finalized:
            col += 1
        finalized[col] = TableCell(cell.text, cell.is_header)
        if cell.rowspan > 1:
            next_span_updates[col] = {
                "cell": TableCell(cell.text, cell.is_header),
                "remaining": cell.rowspan - 1,
            }
        col += 1

    if not finalized:
        return [], {}

    row = [finalized.get(i, TableCell("", False)) for i in range(max(finalized) + 1)]

    # Compute next active spans: decrement existing, merge new
    next_spans = {
        c: {"cell": s["cell"], "remaining": s["remaining"] - 1}
        for c, s in active_spans.items()
        if s["remaining"] > 1
    }
    next_spans.update(next_span_updates)

    return row, next_spans


def encode_table(table: ParsedTable) -> str:
    """Flatten a `ParsedTable` into a single string for transport through parsing."""

    rows = []
    for row in table.rows:
        cells = [(_HEADER_MARK if c.is_header else "") + c.text for c in row]
        rows.append(_CELL_SEP.join(cells))

    body = _ROW_SEP.join(rows)
    return f"{table.caption or ''}{_CAPTION_SEP}{body}"


def decode_table(encoded: str) -> ParsedTable:
    """Reverse `encode_table`, reconstructing the `ParsedTable`."""

    caption, _, body = encoded.partition(_CAPTION_SEP)

    rows = []
    for row_str in body.split(_ROW_SEP):
        cells = []
        for cell_str in row_str.split(_CELL_SEP):
            is_header = cell_str.startswith(_HEADER_MARK)
            text = cell_str[1:] if is_header else cell_str
            cells.append(TableCell(text, is_header))
        rows.append(cells)

    return ParsedTable(rows=rows, caption=caption or None)


def _split_cells(text: str, separator: str, is_header: bool) -> list[TableCell]:
    cells = []
    for part in text.split(separator):
        cell_text, rowspan = _strip_attrs(part)
        cells.append(TableCell(cell_text, is_header, rowspan))
    return cells


def _strip_attrs(part: str) -> tuple[str, int]:
    """Strip cell-level attributes (e.g., `style="..."`) from a cell's content
    and extract the `rowspan` value if present.

    A `|` inside a cell only separates attributes from content when the text
    before it contains `=` (an attribute assignment) and does not contain
    `[[` (to avoid misreading the pipe in a `[[Page|alias]]` wikilink as an
    attribute separator).
    """

    content = part.strip()
    rowspan = 1
    if "|" in content:
        before, after = content.split("|", 1)
        if "=" in before and "[[" not in before:
            match = re.search(r"\browspan\s*=\s*\"?(\d+)\"?", before, re.IGNORECASE)
            if match:
                rowspan = int(match.group(1))
            content = after.strip()

    return content, rowspan
