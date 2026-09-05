from wicli.core import render


class TestRenderCachePurged:
    def test_zero_rows(self):
        result = render.render_cache_purged(0)
        assert "already empty" in result

    def test_one_row(self):
        result = render.render_cache_purged(1)
        assert "1 entry" in result

    def test_many_rows(self):
        result = render.render_cache_purged(5)
        assert "5 entries" in result


class TestRenderTitleFallback:
    def test_contains_original_and_fallback(self):
        result = render.render_title_fallback("python", "Python")
        assert "python" in result
        assert "Python" in result


class TestRenderSummaryNotFound:
    def test_contains_title(self):
        result = render.render_summary_not_found("Foobar")
        assert "Foobar" in result


class TestRenderTocNotFound:
    def test_returns_string(self):
        result = render.render_toc_not_found()
        assert isinstance(result, str)
        assert len(result) > 0


class TestRenderSectionNotFound:
    def test_contains_title(self):
        result = render.render_section_not_found("History")
        assert "History" in result


class TestRenderDisambiguationNotFound:
    def test_contains_page(self):
        result = render.render_disambiguation_not_found("Blade Runner")
        assert "Blade Runner" in result


class TestRenderSectionBlocks:
    def test_subheading_different_from_title(self):
        section = "\x00SUBHEADING\x00Overview\x00"
        result = render.render_section("History", section, cached_at=None)
        assert "Overview" in result

    def test_subheading_equal_to_title_skipped(self):
        section = "\x00SUBHEADING\x00History\x00"
        result = render.render_section("History", section, cached_at=None)
        # The subheading matches the title so it should not appear as a block
        # (only the title line in the header is present)
        assert result.count("History") == 1

    def test_blockquote_block(self):
        section = "\x00BLOCKQUOTE\x00To be or not to be.\x00"
        result = render.render_section("Hamlet", section, cached_at=None)
        assert "To be or not to be." in result

    def test_poemquote_block(self):
        section = (
            "\x00POEM\x00FOLLOW\x00LINE\x00THE\x00LINE\x00WHITE\x00LINE\x00RABBIT\x00"
        )
        result = render.render_section("Poem", section, cached_at=None)
        assert "FOLLOW" in result
        assert "THE" in result
        assert "WHITE" in result
        assert "RABBIT" in result

    def test_list_block(self):
        section = "• First item\n• Second item"
        result = render.render_section("Items", section, cached_at=None)
        assert "First item" in result
        assert "Second item" in result


class TestRenderStyle:
    def test_style_with_no_color_returns_plain(self):
        # _NO_COLOR is True in test environments (no TTY), so _style returns plain text
        result = render._style("hello", render._BOLD)
        assert result == "hello"

    def test_style_with_color_enabled_adds_codes(self, monkeypatch):
        monkeypatch.setattr(render, "_NO_COLOR", False)
        result = render._style("hello", render._BOLD)
        assert render._BOLD in result
        assert render._RESET in result
        assert "hello" in result


class TestRenderContentBannerCached:
    def test_cached_at_shows_timestamp(self):
        result = render._render_content_banner(cached_at=1700000000.0)
        assert "cache" in result.lower()

    def test_no_cached_at_shows_live(self):
        result = render._render_content_banner(cached_at=None)
        assert "live" in result.lower() or "fetched" in result.lower()


class TestRenderInvalidChoice:
    def test_toc_invalid_choice(self):
        result = render.render_toc_invalid_choice("x")
        assert "'x'" in result
        assert "'y'" in result
        assert "'n'" in result

    def test_toc_navigation_invalid_choice(self):
        result = render.render_toc_navigation_invalid_choice("99")
        assert "'99'" in result
        assert "':m'" in result

    def test_toc_navigation_invalid_choice_with_links(self):
        result = render.render_toc_navigation_invalid_choice("99", has_links=True)
        assert "'99'" in result
        assert "'j1'" in result

    def test_disambiguation_invalid_choice(self):
        result = render.render_disambiguation_invalid_choice("99")
        assert "'99'" in result


class TestRenderTocNavigationPrompt:
    def test_without_links(self):
        result = render.render_toc_navigation_prompt()
        assert "related page" not in result

    def test_with_links(self):
        result = render.render_toc_navigation_prompt(has_links=True)
        assert "related page" in result


class TestRenderSectionLinks:
    def test_lists_all_pages(self):
        links = [
            {"page": "Neuromancer", "desc": "Neuromancer"},
            {"page": "Count Zero", "desc": "Count Zero"},
            {"page": "Mona Lisa Overdrive", "desc": "Mona Lisa Overdrive"},
        ]
        result = render.render_section_links(links)
        assert "j1" in result
        assert "j2" in result
        assert "Neuromancer" in result
        assert "Count Zero" in result
        assert "Mona Lisa Overdrive" in result


class TestShowNotices:
    def test_show_warranty_mentions_no_warranty(self):
        result = render.show_warranty()
        assert "NO WARRANTY" in result

    def test_show_conditions_mentions_license(self):
        result = render.show_conditions()
        assert "GNU Affero General Public License" in result


class TestRenderTableBlock:
    def test_table_block_rendered(self):
        from wicli.parsing.table import ParsedTable, TableCell, encode_table

        table = ParsedTable(
            rows=[
                [TableCell("A", True), TableCell("B", True)],
                [TableCell("1", False), TableCell("2", False)],
            ]
        )
        section = f"\x00TABLE\x00{encode_table(table)}\x00"
        result = render.render_section("Data", section, cached_at=None)
        assert "A" in result and "1" in result

    def test_table_caption_rendered(self):
        from wicli.parsing.table import ParsedTable, TableCell, encode_table

        table = ParsedTable(rows=[[TableCell("X", False)]], caption="My caption")
        section = f"\x00TABLE\x00{encode_table(table)}\x00"
        result = render.render_section("Data", section, cached_at=None)
        assert "My caption" in result

    def test_render_table_empty_returns_blank(self):
        from wicli.parsing.table import ParsedTable

        assert render._render_table(ParsedTable(rows=[])) == ""

    def test_table_multiple_header_rows(self):
        from wicli.parsing.table import ParsedTable, TableCell, encode_table

        table = ParsedTable(
            rows=[
                [TableCell("H1", True)],
                [TableCell("H2", True)],
                [TableCell("d", False)],
            ]
        )
        section = f"\x00TABLE\x00{encode_table(table)}\x00"
        result = render.render_section("Data", section, cached_at=None)
        assert "H1" in result and "H2" in result and "d" in result
