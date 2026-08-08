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
