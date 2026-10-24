from wicli.parsing.lexer import _classify_line, tokenize
from wicli.parsing.nodes import TokenType


def test_plain_text():
    tokens = tokenize("Simple text line.")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.TEXT
    assert tokens[0].value == "Simple text line."


def test_heading_discarded():
    tokens = tokenize("== Section ==")
    assert tokens == []


def test_subheading_kept():
    tokens = tokenize("=== Subsection ===")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.SUBHEADING


def test_list_item():
    tokens = tokenize("* Item one")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.LIST_ITEM


def test_numbered_list_item():
    tokens = tokenize("# Numbered item")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.LIST_ITEM


def test_file_link_discarded():
    tokens = tokenize("[[File:image.jpg|thumb|Caption]]")
    assert tokens == []


def test_empty_line_discarded():
    tokens = tokenize("")
    assert tokens == []


def test_ref_inline_stripped():
    tokens = tokenize("Text with <ref>citation</ref> inline.")
    assert len(tokens) == 1
    assert "ref" not in tokens[0].value
    assert "citation" not in tokens[0].value


def test_self_closing_ref_stripped():
    tokens = tokenize("Text <ref name='foo'/> continues.")
    assert len(tokens) == 1
    assert "ref" not in tokens[0].value


def test_generic_template_discarded():
    tokens = tokenize("{{some unknown template|foo=bar}}")
    assert tokens == []


def test_template_keep_last():
    tokens = tokenize("{{lang|fr|Bonjour}}")
    assert len(tokens) == 1
    assert tokens[0].value == "Bonjour"


def test_template_keep_first():
    tokens = tokenize("{{citation needed|date=April 2025}}")
    assert len(tokens) == 0


def test_template_keep_first_positional():
    tokens = tokenize("{{citation needed|some custom text}}")
    assert len(tokens) == 1
    assert tokens[0].value == "some custom text"


def test_blockquote_template():
    tokens = tokenize("{{blockquote|That is not dead which can eternal lie.}}")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.BLOCKQUOTE
    assert "That is not dead which can eternal lie." in tokens[0].value


def test_blockquote_with_wikilink_pipe():
    tokens = tokenize("{{blockquote|Text about [[Max Stirner|Stirner]] here.}}")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.BLOCKQUOTE
    assert "[[Max Stirner|Stirner]]" in tokens[0].value


def test_poem_quote_preserves_line_breaks():
    tokens = tokenize("{{poem quote|First line.\nSecond line.\nThird line.}}")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.POEM
    assert "\x00POEM\x00" in tokens[0].value
    assert tokens[0].value.count("\x00LINE\x00") == 2


def test_won_template_kept_as_text():
    tokens = tokenize("{{won}}")
    assert len(tokens) == 1
    assert tokens[0].value == "Won"


def test_nom_template_kept_as_text():
    tokens = tokenize("text with {{nom}} inline")
    assert len(tokens) == 1
    assert "Nominated" in tokens[0].value


def test_definition_term():
    tokens = tokenize(";Kerrang! Awards")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.DEFINITION_TERM
    assert tokens[0].value == ";Kerrang! Awards"


def test_citation_template_keeps_title():
    tokens = tokenize("{{cite web|url=http://example.com|title=Example}}")
    assert len(tokens) == 1
    assert tokens[0].value == "Example"


def test_citation_template_keeps_title_and_year():
    tokens = tokenize("{{cita libro|titolo=Il falso e l'osceno|anno=2009}}")
    assert len(tokens) == 1
    assert tokens[0].value == "Il falso e l'osceno - 2009."


def test_citation_template_without_title_discarded():
    # No title param at all -> nothing useful to show, falls back to silent removal
    tokens = tokenize("{{cite web|url=http://example.com}}")
    assert tokens == []


def test_album_template_keeps_title_year_and_track_list():
    wikitext = """{{Album|titre = The Soft Moon
|label = Captured Tracks
|année = 2010
|contenu =
#''Breathe The Fire''
#''Circles''
}}"""

    tokens = tokenize(wikitext)

    assert len(tokens) == 3
    assert tokens[0].type == TokenType.TEXT
    assert tokens[0].value == "'''The Soft Moon (2010)'''"
    assert tokens[1].type == TokenType.LIST_ITEM
    assert tokens[1].value == "#''Breathe The Fire''"
    assert tokens[2].type == TokenType.LIST_ITEM
    assert tokens[2].value == "#''Circles''"


def test_table_consumed_as_single_token():
    wikitext = "{|\n! Header\n|-\n| Cell\n|}"
    tokens = tokenize(wikitext)
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.TABLE


def test_html_entities_normalized():
    tokens = tokenize("A &amp; B &lt; C")
    assert tokens[0].value == "A & B < C"


def test_nbsp_normalized():
    tokens = tokenize("foo\xa0bar")
    assert tokens[0].value == "foo bar"


def test_multiline_ref_stripped():
    wikitext = "Before<ref>\nMultiline\nref\n</ref>After"
    tokens = tokenize(wikitext)
    assert len(tokens) == 1
    assert tokens[0].value == "BeforeAfter"


def test_html_comment_inline_stripped():
    tokens = tokenize("Text with <!-- comment --> inline.")
    assert len(tokens) == 1
    assert "<!--" not in tokens[0].value
    assert "comment" not in tokens[0].value
    assert "Text with" in tokens[0].value
    assert "inline." in tokens[0].value


def test_multiline_html_comment_stripped():
    wikitext = "Before<!-- Multi\nline\ncomment -->After"
    tokens = tokenize(wikitext)
    assert len(tokens) == 1
    assert tokens[0].value == "BeforeAfter"


def test_subheading_with_html_comment_cleaned():
    wikitext = "=== Notable members ===<!-- A comment -->"
    tokens = tokenize(wikitext)
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.SUBHEADING
    assert "<!--" not in tokens[0].value
    assert "A comment" not in tokens[0].value
    assert "Notable members" in tokens[0].value


def test_gallery_stripped():
    wikitext = "Text before\n<gallery>\nFile:Image1.jpg|Caption 1\nFile:Image2.jpg|Caption 2\n</gallery>\nText after"
    tokens = tokenize(wikitext)
    assert len(tokens) == 2
    assert all(t.type == TokenType.TEXT for t in tokens)
    assert tokens[0].value == "Text before"
    assert tokens[1].value == "Text after"
    assert not any("<gallery>" in t.value for t in tokens)


def test_gallery_inline_stripped():
    wikitext = "Text with <gallery>File:Image.jpg|Caption</gallery> inline."
    tokens = tokenize(wikitext)
    assert len(tokens) == 1
    assert "<gallery>" not in tokens[0].value
    assert "Caption" not in tokens[0].value
    assert "File:Image.jpg" not in tokens[0].value


def test_mixed_content():
    wikitext = "First line.\n== Heading ==\nSecond line."
    tokens = tokenize(wikitext)
    types = [t.type for t in tokens]
    assert TokenType.HEADING not in types
    assert types.count(TokenType.TEXT) == 2


def test_empty_line_in_middle_discarded():
    # An empty line between two content lines should be classified as NEWLINE
    # and silently discarded
    tokens = tokenize("First line.\n\nSecond line.")
    assert len(tokens) == 2
    assert all(t.type == TokenType.TEXT for t in tokens)


class TestClassifyLine:
    """Direct tests for _classify_line covering branches unreachable via tokenize.

    TEMPLATE and REF are pre-stripped by _strip_templates / _strip_refs before
    tokenize reaches _classify_line, so they can only be exercised by calling
    _classify_line directly.
    """

    def test_template_line(self):
        assert _classify_line("{{some template}}") == TokenType.TEMPLATE

    def test_ref_line(self):
        assert _classify_line("<ref name='x'>citation</ref>") == TokenType.REF

    def test_newline_empty_string(self):
        assert _classify_line("") == TokenType.NEWLINE

    def test_newline_whitespace_only(self):
        assert _classify_line("   ") == TokenType.NEWLINE


class TestMainArticleTemplate:
    def test_emits_main_article_token(self):
        tokens = tokenize("{{See also|Page#Sec|l1=Label}}\nText.")
        assert tokens[0].type == TokenType.MAIN_ARTICLE
        assert tokens[0].value == "\x00MAIN\x00Page\x00"
        assert tokens[1].type == TokenType.TEXT

    def test_without_positional_param_is_discarded(self):
        tokens = tokenize("{{Main|l1=Label}}\nText.")
        assert [t.type for t in tokens] == [TokenType.TEXT]

    def test_classify_line(self):
        assert _classify_line("\x00MAIN\x00Page\x00") == TokenType.MAIN_ARTICLE


class TestChartTable:
    WIKITEXT = (
        "{{Charttabelle\n|DE|AT\n| Art = Alben\n| INHALT =\n"
        "{{Charteintrag\n|DE|AT\n| Jahr = 2002\n| Titel = Live\n"
        "| POS_DE = 45 | WO_DE = 3\n"
        "| Anmerkung = Erstveröffentlichung: 2002<br />„Halo 17“\n}}\n"
        "{{Charteintrag\n|DE|AT\n| Jahr = 2026\n| Titel = [[Nine|Noize]]\n"
        "| POS_AT = 7 | WO_AT = 1\n}}\n}}"
    )

    def test_expanded_into_table_token(self):
        tokens = tokenize(self.WIKITEXT)
        assert [t.type for t in tokens] == [TokenType.TABLE]
        lines = tokens[0].value.splitlines()
        assert lines[0] == "{|"
        assert lines[-1] == "|}"
        assert "! Jahr !! Titel !! DE !! AT !! Anmerkungen" in lines
        assert (
            "| 2002 || Live || 45 (3) ||  || Erstveröffentlichung: 2002<br />„Halo 17“"
            in lines
        )
        assert "| 2026 || [[Nine|Noize]] ||  || 7 (1) || " in lines

    def test_countries_taken_from_entries_when_header_has_none(self):
        wikitext = (
            "{{Charttabelle\n| INHALT =\n"
            "{{Charteintrag\n|US\n| Jahr = 1999\n| Titel = X\n| POS_US = 3\n}}\n}}"
        )
        table = tokenize(wikitext)[0].value
        assert "! Jahr !! Titel !! US !! Anmerkungen" in table
        assert "| 1999 || X || 3 || " in table

    def test_text_around_table_is_kept(self):
        tokens = tokenize("Before.\n" + self.WIKITEXT + "\nAfter.")
        assert [t.type for t in tokens] == [
            TokenType.TEXT,
            TokenType.TABLE,
            TokenType.TEXT,
        ]

    def test_without_entries_is_discarded(self):
        assert tokenize("{{Charttabelle\n|DE\n| INHALT =\n}}") == []

    def test_unterminated_template_is_ignored(self):
        assert tokenize("{{Charttabelle\n|DE\n| INHALT = x") == []
