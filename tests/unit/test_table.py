from wicli.parsing.table import (
    ParsedTable,
    TableCell,
    decode_table,
    encode_table,
    parse_table,
)


class TestParseTable:
    def test_simple_row(self):
        raw = "{|\n! Year\n! Title\n|-\n| 1984\n| Dummy\n|}"
        result = parse_table(raw)
        assert result.rows[0][0].text == "Year"
        assert result.rows[0][0].is_header
        assert result.rows[1][0].text == "1984"
        assert not result.rows[1][0].is_header

    def test_multiple_cells_same_line_pipe(self):
        raw = "{|\n|-\n| Foo || Bar || Baz\n|}"
        result = parse_table(raw)
        assert [c.text for c in result.rows[0]] == ["Foo", "Bar", "Baz"]

    def test_multiple_cells_same_line_bang(self):
        raw = "{|\n! Foo !! Bar !! Baz\n|}"
        result = parse_table(raw)
        assert [c.text for c in result.rows[0]] == ["Foo", "Bar", "Baz"]

    def test_caption_extracted(self):
        raw = "{|\n|+Hello World\n! H\n|-\n| cell\n|}"
        result = parse_table(raw)
        assert result.caption == "Hello World"

    def test_no_caption_is_none(self):
        raw = "{|\n! H\n|-\n| cell\n|}"
        result = parse_table(raw)
        assert result.caption is None

    def test_style_attribute_stripped(self):
        raw = '{|\n|-\n|style="text-align:right"|1200\n|}'
        result = parse_table(raw)
        assert result.rows[0][0].text == "1200"

    def test_wikilink_pipe_not_mistaken_for_attribute(self):
        raw = "{|\n|-\n| [[Page|Alias]]\n|}"
        result = parse_table(raw)
        assert result.rows[0][0].text == "[[Page|Alias]]"

    def test_short_rows_padded(self):
        # Second row has fewer cells (e.g. rowspan in original wikitext)
        raw = "{|\n|-\n| X\n| Y\n|-\n| Z\n|}"
        result = parse_table(raw)
        assert len(result.rows[0]) == len(result.rows[1]) == 2
        assert result.rows[1][1].text == ""

    def test_empty_table_no_rows(self):
        raw = "{|\n|}"
        result = parse_table(raw)
        assert result.rows == []

    def test_rowspan_propagates_to_next_row(self):
        # rowspan="2" on "Song" should repeat it in the second row
        raw = '{|\n|-\n| rowspan="2" | Song\n| 1992\n|-\n| 1995\n|}'
        result = parse_table(raw)
        assert result.rows[0][0].text == "Song"
        assert result.rows[0][1].text == "1992"
        assert result.rows[1][0].text == "Song"  # inherited
        assert result.rows[1][1].text == "1995"

    def test_rowspan_mid_row_propagates(self):
        # rowspan in the middle column: [Year, Artist(rowspan=2), Song]
        raw = '{|\n|-\n| 1976\n| rowspan="2" | De Niro\n| Taxi Driver\n|-\n| 1980\n| Raging Bull\n|}'
        result = parse_table(raw)
        assert result.rows[0] == [
            TableCell("1976", False),
            TableCell("De Niro", False),
            TableCell("Taxi Driver", False),
        ]
        assert result.rows[1] == [
            TableCell("1980", False),
            TableCell("De Niro", False),  # inherited
            TableCell("Raging Bull", False),
        ]


class TestEncodeDecodeTable:
    def test_round_trip_preserves_cells(self):
        table = ParsedTable(
            rows=[
                [TableCell("X", True), TableCell("Y", True)],
                [TableCell("0", False), TableCell("1", False)],
            ]
        )
        decoded = decode_table(encode_table(table))
        assert decoded.rows[0][0].text == "X"
        assert decoded.rows[0][0].is_header
        assert decoded.rows[1][1].text == "1"
        assert not decoded.rows[1][1].is_header

    def test_round_trip_preserves_caption(self):
        table = ParsedTable(rows=[[TableCell("X", False)]], caption="Hello World")
        decoded = decode_table(encode_table(table))
        assert decoded.caption == "Hello World"

    def test_round_trip_no_caption_stays_none(self):
        table = ParsedTable(rows=[[TableCell("X", False)]], caption=None)
        decoded = decode_table(encode_table(table))
        assert decoded.caption is None
