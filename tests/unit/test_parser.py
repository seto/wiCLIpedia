from wicli.parsing.parser import (
    parse_disambiguation,
    parse_props,
    parse_section,
    parse_summary,
    parse_toc,
)


class TestParseProps:
    def test_redirect(self):
        response = {"query": {"redirects": [{"to": "Target Page"}], "pages": []}}
        result = parse_props(response)
        assert result["status"] == "redirect"
        assert result["target"] == "Target Page"

    def test_missing(self):
        response = {"query": {"pages": [{"missing": True}]}}
        result = parse_props(response)
        assert result["status"] == "missing"

    def test_empty_pages(self):
        response = {"query": {"pages": []}}
        result = parse_props(response)
        assert result["status"] == "missing"

    def test_disambiguation(self):
        response = {"query": {"pages": [{"pageprops": {"disambiguation": ""}}]}}
        result = parse_props(response)
        assert result["status"] == "disambiguation"

    def test_found(self):
        response = {"query": {"pages": [{"pageprops": {"wikibase_item": "Q1234"}}]}}
        result = parse_props(response)
        assert result["status"] == "found"

    def test_unknown_no_pageprops(self):
        response = {"query": {"pages": [{"title": "Something", "ns": 0}]}}
        result = parse_props(response)
        assert result["status"] == "unknown"


class TestParseSummary:
    def test_found_single_paragraph(self):
        response = {"query": {"pages": [{"extract": "A short summary."}]}}
        result = parse_summary(response)
        assert result["status"] == "found"
        assert result["paragraphs"] == ["A short summary."]

    def test_found_multiple_paragraphs(self):
        response = {
            "query": {"pages": [{"extract": "First paragraph.\n\nSecond paragraph."}]}
        }
        result = parse_summary(response)
        assert result["paragraphs"] == ["First paragraph.", "Second paragraph."]

    def test_whitespace_normalized(self):
        response = {"query": {"pages": [{"extract": "  Hello   World  "}]}}
        result = parse_summary(response)
        assert result["paragraphs"] == ["Hello World"]

    def test_missing_page(self):
        response = {"query": {"pages": [{"missing": True}]}}
        result = parse_summary(response)
        assert result["status"] == "missing"

    def test_empty_extract(self):
        response = {"query": {"pages": [{"extract": ""}]}}
        result = parse_summary(response)
        assert result["status"] == "missing"

    def test_cached_at_propagated(self):
        response = {
            "query": {"pages": [{"extract": "Text."}]},
            "_cached_at": 1234567890.0,
        }
        result = parse_summary(response)
        assert result["_cached_at"] == 1234567890.0

    def test_no_cached_at_when_absent(self):
        response = {"query": {"pages": [{"extract": "Text."}]}}
        result = parse_summary(response)
        assert result.get("_cached_at") is None


class TestParseToc:
    def test_found_single_section(self):
        response = {
            "parse": {
                "tocdata": {
                    "sections": [
                        {"index": 1, "line": "History", "number": "1", "tocLevel": 1}
                    ]
                }
            }
        }
        result = parse_toc(response)
        assert result["status"] == "found"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["line"] == "History"
        assert result["sections"][0]["index"] == 1
        assert result["sections"][0]["number"] == "1"

    def test_missing_empty_sections(self):
        response = {"parse": {"tocdata": {"sections": []}}}
        result = parse_toc(response)
        assert result["status"] == "missing"

    def test_html_stripped_from_line(self):
        response = {
            "parse": {
                "tocdata": {
                    "sections": [
                        {
                            "index": 1,
                            "line": "History <span class='note'>note</span>",
                            "number": "1",
                            "tocLevel": 1,
                        }
                    ]
                }
            }
        }
        result = parse_toc(response)
        assert "<span" not in result["sections"][0]["line"]
        assert "History" in result["sections"][0]["line"]

    def test_multiple_sections(self):
        response = {
            "parse": {
                "tocdata": {
                    "sections": [
                        {"index": 1, "line": "History", "number": "1", "tocLevel": 1},
                        {
                            "index": 2,
                            "line": "Pretty Hate Machine",
                            "number": "1.1",
                            "tocLevel": 2,
                        },
                        {"index": 3, "line": "Legacy", "number": "2", "tocLevel": 1},
                    ]
                }
            }
        }
        result = parse_toc(response)
        assert len(result["sections"]) == 3
        assert result["sections"][1]["number"] == "1.1"


class TestParseSection:
    def test_found_plain_text(self):
        response = {"parse": {"wikitext": "Some plain text content."}}
        result = parse_section(response)
        assert result["status"] == "found"
        assert "Some plain text content." in result["section"]

    def test_table_rendered(self):
        response = {"parse": {"wikitext": "{|\n! H\n|-\n| cell\n|}"}}
        result = parse_section(response)
        assert result["status"] == "found"
        assert "\x00TABLE\x00" in result["section"]

    def test_table_replaced_when_empty(self):
        # A table block with no data rows at all falls back to the placeholder
        response = {"parse": {"wikitext": "{|\n|}"}}
        result = parse_section(response)
        assert "[Table not available in CLI]" in result["section"]

    def test_table_caption_cleaned(self):
        wikitext = "{|\n|+ ''Directed'' films\n! H\n|-\n| cell\n|}"
        response = {"parse": {"wikitext": wikitext}}
        result = parse_section(response)
        assert "''" not in result["section"]
        assert "Directed" in result["section"]

    def test_subheading_preserved(self):
        response = {"parse": {"wikitext": "=== Early life ===\nSome text."}}
        result = parse_section(response)
        assert result["status"] == "found"
        assert "Early life" in result["section"]

    def test_inline_links_cleaned(self):
        response = {"parse": {"wikitext": "Born in the [[Sprawl trilogy|Sprawl]]."}}
        result = parse_section(response)
        assert "[[" not in result["section"]
        assert "Sprawl" in result["section"]

    def test_external_link_cleaned(self):
        response = {
            "parse": {"wikitext": "Published as [http://example.com/book The Book]."}
        }
        result = parse_section(response)
        assert "[http" not in result["section"]
        assert "The Book" in result["section"]

    def test_bold_markup_cleaned(self):
        response = {"parse": {"wikitext": "'''Bold text''' and normal."}}
        result = parse_section(response)
        assert "'''" not in result["section"]
        assert "Bold text" in result["section"]


class TestParseDisambiguation:
    def test_found_with_descriptions(self):
        response = {
            "parse": {
                "wikitext": (
                    "* [[Blade Runner]] – 1982 science fiction film\n"
                    "* [[Blade Runner 2049]] – 2017 sequel"
                )
            }
        }
        result = parse_disambiguation(response)
        assert result["status"] == "found"
        assert len(result["options"]) == 2
        assert result["options"][0]["page"] == "Blade Runner"
        assert result["options"][1]["page"] == "Blade Runner 2049"

    def test_found_without_description(self):
        response = {"parse": {"wikitext": "* [[Python (programming language)]]"}}
        result = parse_disambiguation(response)
        assert result["status"] == "found"
        assert result["options"][0]["page"] == "Python (programming language)"

    def test_missing_empty_wikitext(self):
        response = {"parse": {"wikitext": ""}}
        result = parse_disambiguation(response)
        assert result["status"] == "missing"

    def test_piped_link_uses_page_title(self):
        response = {
            "parse": {"wikitext": "* [[Python (language)|Python]] – a language"}
        }
        result = parse_disambiguation(response)
        assert result["options"][0]["page"] == "Python (language)"

    def test_desc_combines_before_and_after(self):
        # Text both before and after the link — desc should merge both parts
        response = {"parse": {"wikitext": "* Foo, a [[Bar]] in Baz"}}
        result = parse_disambiguation(response)
        assert result["options"][0]["page"] == "Bar"
        assert "Foo" in result["options"][0]["desc"]
        assert "in Baz" in result["options"][0]["desc"]


class TestParseSectionTokenTypes:
    def test_list_items_prefixed_with_bullet(self):
        response = {"parse": {"wikitext": "* First item\n* Second item"}}
        result = parse_section(response)
        assert result["status"] == "found"
        assert "• First item" in result["section"]
        assert "• Second item" in result["section"]

    def test_blockquote_template_preserved(self):
        # The lexer converts {{quote|text}} into a BLOCKQUOTE token
        response = {"parse": {"wikitext": "{{quote|To be or not to be.}}"}}
        result = parse_section(response)
        assert result["status"] == "found"
        assert "To be or not to be." in result["section"]

    def test_list_buffer_flushed_before_text(self):
        # List items followed by a text block — buffer must be flushed first
        wikitext = "* Item one\n* Item two\n\nFollowing paragraph."
        response = {"parse": {"wikitext": wikitext}}
        result = parse_section(response)
        assert "• Item one" in result["section"]
        assert "Following paragraph." in result["section"]

    def test_list_buffer_flushed_at_end(self):
        # List items at the very end of the wikitext — flushed after the loop
        response = {"parse": {"wikitext": "* Only item"}}
        result = parse_section(response)
        assert "• Only item" in result["section"]

    def test_subheading_flushes_preceding_list(self):
        wikitext = "* List item\n=== Sub ==="
        response = {"parse": {"wikitext": wikitext}}
        result = parse_section(response)
        assert "• List item" in result["section"]
        assert "Sub" in result["section"]

    def test_blockquote_flushes_preceding_list(self):
        wikitext = "* List item\n{{quote|A quote.}}"
        response = {"parse": {"wikitext": wikitext}}
        result = parse_section(response)
        assert "• List item" in result["section"]
        assert "A quote." in result["section"]

    def test_table_flushes_preceding_list(self):
        wikitext = "* List item\n{|\n| cell\n|}"
        response = {"parse": {"wikitext": wikitext}}
        result = parse_section(response)
        assert "• List item" in result["section"]
        assert "\x00TABLE\x00" in result["section"]
