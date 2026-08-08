from unittest.mock import patch

from wicli.cli import main
from wicli.core.exceptions import WicliAPIError, WicliNetworkError


class TestPurge:
    def test_purge_flag_calls_cache_purge(self):
        with patch("wicli.cli.cache.purge", return_value=3) as mock_purge:
            result = main(["--purge"])
        assert result == 0
        mock_purge.assert_called_once()

    def test_purge_empty_cache(self):
        with patch("wicli.cli.cache.purge", return_value=0):
            result = main(["--purge"])
        assert result == 0


class TestQuitImmediately:
    def test_quit_at_prompt(self):
        with patch("builtins.input", return_value=":q"):
            result = main([])
        assert result == 0

    def test_back_loops(self):
        with patch("builtins.input", side_effect=[":b", ":q"]):
            result = main([])
        assert result == 0

    def test_empty_input_loops(self):
        with patch("builtins.input", side_effect=["", ":q"]):
            result = main([])
        assert result == 0


class TestPageNotFound:
    def test_page_not_found_prompts_again(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_missing()),
            patch("builtins.input", side_effect=["Unknown Page", ":q"]),
        ):
            result = main([])
        assert result == 0

    def test_page_not_found_via_argv(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_missing()),
            patch("builtins.input", return_value=":q"),
        ):
            result = main(["Unknown Page"])
        assert result == 0


class TestRedirect:
    def test_redirect_followed(self):
        with (
            patch(
                "wicli.cli.client.fetch_props",
                side_effect=[_props_redirect("Target Page"), _props_found()],
            ),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["Redirect Page"])
        assert result == 0


class TestFoundPage:
    def test_found_skip_toc(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_found_page_argv(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_found_with_toc_and_section(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("wicli.cli.client.fetch_toc", return_value=_toc()),
            patch("wicli.cli.client.fetch_section", return_value=_section()),
            # y -> show TOC | 1 -> select section | :b -> back | :q -> quit
            patch("builtins.input", side_effect=["y", "1", ":b", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_found_toc_invalid_section_then_back(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("wicli.cli.client.fetch_toc", return_value=_toc()),
            # y -> show TOC | 99 -> invalid | :b -> back | :q -> quit
            patch("builtins.input", side_effect=["y", "99", ":b", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_found_toc_quit_from_navigation(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("wicli.cli.client.fetch_toc", return_value=_toc()),
            # y -> show TOC | :q -> quit from section navigator
            patch("builtins.input", side_effect=["y", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_reprint_toc(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("wicli.cli.client.fetch_toc", return_value=_toc()) as mock_fetch_toc,
            # y -> show TOC | :m -> reprint TOC menu | :q -> quit
            patch("builtins.input", side_effect=["y", ":m", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0
        mock_fetch_toc.assert_called_once()


class TestDisambiguation:
    def test_select_option_navigates_to_page(self):
        with (
            patch(
                "wicli.cli.client.fetch_props",
                side_effect=[_props_disambiguation(), _props_found()],
            ),
            patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            # 1 -> select Page A | n -> skip TOC | :q -> quit
            patch("builtins.input", side_effect=["1", "n", ":q"]),
        ):
            result = main(["Blade Runner"])
        assert result == 0

    def test_back_from_disambiguation(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_disambiguation()),
            patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ),
            # :b -> back to prompt | :q -> quit
            patch("builtins.input", side_effect=[":b", ":q"]),
        ):
            result = main(["Blade Runner"])
        assert result == 0

    def test_invalid_choice_then_quit(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_disambiguation()),
            patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ),
            # 99 -> invalid | :q -> quit
            patch("builtins.input", side_effect=["99", ":q"]),
        ):
            result = main(["Blade Runner"])
        assert result == 0


class TestErrorHandling:
    def test_network_error_exits_1(self):
        with patch(
            "wicli.cli.client.fetch_props",
            side_effect=WicliNetworkError("connection refused"),
        ):
            result = main(["Python"])
        assert result == 1

    def test_api_error_exits_1(self):
        with patch(
            "wicli.cli.client.fetch_props",
            side_effect=WicliAPIError("HTTP error: 503"),
        ):
            result = main(["Python"])
        assert result == 1

    def test_eof_exits_0(self):
        with patch("builtins.input", side_effect=EOFError()):
            result = main([])
        assert result == 0

    def test_keyboard_interrupt_exits_0(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            result = main([])
        assert result == 0

    def test_lang_option_forwarded(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()) as mock,
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["Python", "--lang", "it"])
        assert result == 0
        mock.assert_called_with("Python", lang="it")

    def test_runtime_error_exits_2(self):
        with patch(
            "wicli.cli.client.fetch_props",
            side_effect=RuntimeError("unexpected"),
        ):
            result = main(["Python"])
        assert result == 2


class TestNoCache:
    def test_no_cache_flag_calls_disable_cache(self):
        with (
            patch("wicli.cli.client.disable_cache") as mock_disable,
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["Python", "--no-cache"])
        assert result == 0
        mock_disable.assert_called_once()


class TestTitleFallback:
    def test_fallback_to_title_case(self):
        # First call (raw input) → missing, second call (title-cased) → found
        with (
            patch(
                "wicli.cli.client.fetch_props",
                side_effect=[_props_missing(), _props_found()],
            ),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("builtins.input", side_effect=["n", ":q"]),
        ):
            result = main(["python"])
        assert result == 0


class TestEdgeCases:
    def test_empty_summary_prompts_again(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch(
                "wicli.cli.client.fetch_summary",
                return_value={"query": {"pages": [{"extract": ""}]}},
            ),
            patch("builtins.input", side_effect=[":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_toc_not_found_goes_back(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch(
                "wicli.cli.client.fetch_toc",
                return_value={"parse": {"tocdata": {"sections": []}}},
            ),
            # y → fetch TOC (empty) → back to prompt → :q
            patch("builtins.input", side_effect=["y", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_section_not_found_continues(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            patch("wicli.cli.client.fetch_toc", return_value=_toc()),
            patch(
                "wicli.cli.client.fetch_section",
                return_value={"parse": {"wikitext": ""}},
            ),
            # y → TOC | 1 → empty section | :b → back | :q
            patch("builtins.input", side_effect=["y", "1", ":b", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_invalid_toc_prompt_choice_then_quit(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_found()),
            patch("wicli.cli.client.fetch_summary", return_value=_summary()),
            # x → invalid choice in y/n prompt | :q
            patch("builtins.input", side_effect=["x", ":q"]),
        ):
            result = main(["Python"])
        assert result == 0

    def test_disambiguation_no_options_goes_back(self):
        with (
            patch("wicli.cli.client.fetch_props", return_value=_props_disambiguation()),
            patch(
                "wicli.cli.client.fetch_disambiguation",
                return_value={"parse": {"wikitext": "no links here"}},
            ),
            patch("builtins.input", side_effect=[":q"]),
        ):
            result = main(["Blade Runner"])
        assert result == 0

    def test_unknown_status_raises_runtime_error(self):
        with (
            patch(
                "wicli.cli.client.fetch_props",
                return_value={
                    "query": {"pages": [{"pageprops": {"wikibase_item": "Q1"}}]}
                },
            ),
            patch(
                "wicli.cli.parser.parse_props",
                return_value={"status": "spam and eggs"},
            ),
        ):
            result = main(["Python"])
        assert result == 2


def _props_found():
    return {"query": {"pages": [{"pageprops": {"wikibase_item": "Q1"}}]}}


def _props_missing():
    return {"query": {"pages": [{"missing": True}]}}


def _props_redirect(target: str):
    return {"query": {"redirects": [{"to": target}], "pages": []}}


def _props_disambiguation():
    return {"query": {"pages": [{"pageprops": {"disambiguation": ""}}]}}


def _summary():
    return {"query": {"pages": [{"extract": "A short summary."}]}}


def _toc():
    return {
        "parse": {
            "tocdata": {
                "sections": [
                    {"index": 1, "line": "History", "number": "1", "tocLevel": 1}
                ]
            }
        }
    }


def _section():
    return {"parse": {"wikitext": "Section content here."}}


def _disambiguation():
    return {
        "parse": {
            "wikitext": (
                "* [[Page A]] – description A\n" "* [[Page B]] – description B"
            )
        }
    }
