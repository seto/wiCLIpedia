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
        with patch("wicli.cli.client.fetch_props", return_value=_props_missing()):
            with patch("builtins.input", side_effect=["Unknown Page", ":q"]):
                result = main([])
        assert result == 0

    def test_page_not_found_via_argv(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_missing()):
            with patch("builtins.input", return_value=":q"):
                result = main(["Unknown Page"])
        assert result == 0


class TestRedirect:
    def test_redirect_followed(self):
        with patch(
            "wicli.cli.client.fetch_props",
            side_effect=[_props_redirect("Target Page"), _props_found()],
        ):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("builtins.input", side_effect=["n", ":q"]):
                    result = main(["Redirect Page"])
        assert result == 0


class TestFoundPage:
    def test_found_skip_toc(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("builtins.input", side_effect=["n", ":q"]):
                    result = main(["Python"])
        assert result == 0

    def test_found_page_argv(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("builtins.input", side_effect=["n", ":q"]):
                    result = main(["Python"])
        assert result == 0

    def test_found_with_toc_and_section(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("wicli.cli.client.fetch_toc", return_value=_toc()):
                    with patch(
                        "wicli.cli.client.fetch_section", return_value=_section()
                    ):
                        # y -> show TOC | 1 -> select section | :b -> back | :q -> quit
                        with patch(
                            "builtins.input", side_effect=["y", "1", ":b", ":q"]
                        ):
                            result = main(["Python"])
        assert result == 0

    def test_found_toc_invalid_section_then_back(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("wicli.cli.client.fetch_toc", return_value=_toc()):
                    # y -> show TOC | 99 -> invalid | :b -> back | :q -> quit
                    with patch("builtins.input", side_effect=["y", "99", ":b", ":q"]):
                        result = main(["Python"])
        assert result == 0

    def test_found_toc_quit_from_navigation(self):
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()):
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("wicli.cli.client.fetch_toc", return_value=_toc()):
                    # y -> show TOC | :q -> quit from section navigator
                    with patch("builtins.input", side_effect=["y", ":q"]):
                        result = main(["Python"])
        assert result == 0


class TestDisambiguation:
    def test_select_option_navigates_to_page(self):
        with patch(
            "wicli.cli.client.fetch_props",
            side_effect=[_props_disambiguation(), _props_found()],
        ):
            with patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ):
                with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                    # 1 -> select Page A | n -> skip TOC | :q -> quit
                    with patch("builtins.input", side_effect=["1", "n", ":q"]):
                        result = main(["Blade Runner"])
        assert result == 0

    def test_back_from_disambiguation(self):
        with patch(
            "wicli.cli.client.fetch_props", return_value=_props_disambiguation()
        ):
            with patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ):
                # :b -> back to prompt | :q -> quit
                with patch("builtins.input", side_effect=[":b", ":q"]):
                    result = main(["Blade Runner"])
        assert result == 0

    def test_invalid_choice_then_quit(self):
        with patch(
            "wicli.cli.client.fetch_props", return_value=_props_disambiguation()
        ):
            with patch(
                "wicli.cli.client.fetch_disambiguation", return_value=_disambiguation()
            ):
                # 99 -> invalid | :q -> quit
                with patch("builtins.input", side_effect=["99", ":q"]):
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
        with patch("wicli.cli.client.fetch_props", return_value=_props_found()) as mock:
            with patch("wicli.cli.client.fetch_summary", return_value=_summary()):
                with patch("builtins.input", side_effect=["n", ":q"]):
                    result = main(["Python", "--lang", "it"])
        assert result == 0
        mock.assert_called_with("Python", lang="it")


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
