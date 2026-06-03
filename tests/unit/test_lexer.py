from wicli.parsing.lexer import tokenize
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
    tokens = tokenize("{{cite web|url=http://example.com|title=Example}}")
    assert tokens == []


def test_template_keep_last():
    tokens = tokenize("{{lang|fr|Bonjour}}")
    assert len(tokens) == 1
    assert tokens[0].value == "Bonjour"


def test_template_keep_first():
    tokens = tokenize("{{citation needed|date=April 2025}}")
    assert len(tokens) == 1
    assert tokens[0].value == "date=April 2025"


def test_blockquote_template():
    tokens = tokenize("{{blockquote|That is not dead which can eternal lie.}}")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.BLOCKQUOTE
    assert "That is not dead which can eternal lie." in tokens[0].value


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
