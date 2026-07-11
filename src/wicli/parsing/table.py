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

Known limitations: `colspan`/`rowspan` are not merged across cells; a cell
using either attribute is rendered as-is in its own row/column, and rows that
omit a spanned cell are padded with an empty one instead of inheriting the
value from the previous row.
"""

from dataclasses import dataclass

_ROW_SEP = "\x01"
_CELL_SEP = "\x02"
_HEADER_MARK = "\x03"
_CAPTION_SEP = "\x04"


@dataclass
class TableCell:
    text: str
    is_header: bool


@dataclass
class ParsedTable:
    rows: list[list[TableCell]]
    caption: str | None = None


def parse_table(raw: str) -> ParsedTable:
    """Parse a raw `{| ... |}` wikitext block into a `ParsedTable` object.

    The first line (table-level attributes, e.g., `{| class="wikitable"`) is
    always discarded. Rows with fewer cells than the widest row (due to rowspan/colspan)
    are padded with empty cells to ensure that every row has the same length.
    """

    lines = raw.splitlines()
    rows: list[list[TableCell]] = []
    current_row: list[TableCell] = []
    caption: str | None = None

    for line in lines[1:]:
        stripped = line.strip()

        if stripped.startswith("|}"):
            break

        if stripped.startswith("|-"):
            if current_row:
                rows.append(current_row)
                current_row = []
            continue

        # Handle caption lines (`|+`) before processing generic cell lines,
        # so that the caption is not included in the first row of cells.
        if stripped.startswith("|+"):
            caption = stripped[2:].strip()
            continue

        if stripped.startswith("!"):
            current_row.extend(_split_cells(stripped[1:], "!!", is_header=True))

        elif stripped.startswith("|"):
            current_row.extend(_split_cells(stripped[1:], "||", is_header=False))

    if current_row:
        rows.append(current_row)

    # Pad short rows (missing spanned cells, malformed wikitext) so every
    # row has the same number of columns for rendering.
    max_cols = max((len(r) for r in rows), default=0)
    for r in rows:
        r.extend(TableCell("", False) for _ in range(max_cols - len(r)))

    return ParsedTable(rows=rows, caption=caption)


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
    return [TableCell(*_strip_attrs(part), is_header) for part in text.split(separator)]


def _strip_attrs(part: str) -> tuple[str]:
    """Strip cell-level attributes (e.g., `style="..."`) from a cell's content.

    A `|` inside a cell only separates attributes from content when the text
    before it contains `=` (an attribute assignment) and does not contain
    `[[` (to avoid misreading the pipe in a `[[Page|alias]]` wikilink as an
    attribute separator).
    """

    content = part.strip()
    if "|" in content:
        before, after = content.split("|", 1)
        if "=" in before and "[[" not in before:
            content = after.strip()

    return (content,)
