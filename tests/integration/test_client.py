import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from wicli.core.client import _get
from wicli.core.exceptions import WicliAPIError, WicliNetworkError


class TestGetSuccess:
    def test_returns_parsed_json(self):
        with patch(
            "wicli.core.client.urlopen", return_value=_mock_response({"ok": True})
        ):
            result = _get("http://example.com")
        assert result == {"ok": True}


class TestGetAPIErrors:
    def test_invalid_json_raises_api_error(self):
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = b"not valid json {"
        with patch("wicli.core.client.urlopen", return_value=mock):
            with pytest.raises(WicliAPIError, match="Invalid JSON"):
                _get("http://example.com")

    def test_http_404_raises_api_error(self):
        err = _mock_http_error(404, "Not Found")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with pytest.raises(WicliAPIError, match="HTTP error: 404"):
                _get("http://example.com")

    def test_http_500_raises_api_error(self):
        err = _mock_http_error(500, "Internal Server Error")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with pytest.raises(WicliAPIError, match="HTTP error: 500"):
                _get("http://example.com")

    def test_http_429_exhausted_raises_api_error(self):
        err = _mock_http_error(429, "Too Many Requests", retry_after="0")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with patch("wicli.core.client.time.sleep"):
                with pytest.raises(WicliAPIError, match="Too many requests"):
                    _get("http://example.com")


class TestGetNetworkErrors:
    def test_url_error_raises_network_error(self):
        with patch(
            "wicli.core.client.urlopen", side_effect=URLError("connection refused")
        ):
            with pytest.raises(WicliNetworkError, match="Network error"):
                _get("http://example.com")

    def test_timeout_raises_network_error(self):
        with patch("wicli.core.client.urlopen", side_effect=TimeoutError()):
            with pytest.raises(WicliNetworkError, match="timed out"):
                _get("http://example.com")


class TestRetryLogic:
    def test_429_retries_max_retries_times(self):
        err = _mock_http_error(429, "Too Many Requests", retry_after="0")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with patch("wicli.core.client.time.sleep") as mock_sleep:
                with pytest.raises(WicliAPIError):
                    _get("http://example.com")
                # _MAX_RETRIES = 3, so sleep is called 3 times before giving up
                assert mock_sleep.call_count == 3

    def test_429_honours_retry_after_header(self):
        err = _mock_http_error(429, "Too Many Requests", retry_after="5")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with patch("wicli.core.client.time.sleep") as mock_sleep:
                with pytest.raises(WicliAPIError):
                    _get("http://example.com")
                # Each sleep call should use the Retry-After value
                for call in mock_sleep.call_args_list:
                    assert call[0][0] == 5.0

    def test_429_malformed_retry_after_uses_backoff(self):
        err = _mock_http_error(429, "Too Many Requests", retry_after="not-a-number")
        with patch("wicli.core.client.urlopen", side_effect=err):
            with patch("wicli.core.client.time.sleep") as mock_sleep:
                with pytest.raises(WicliAPIError):
                    _get("http://example.com")
                waits = [call[0][0] for call in mock_sleep.call_args_list]
                assert waits == [3**1, 3**2, 3**3]

    def test_succeeds_after_retry(self):
        err = _mock_http_error(429, "Too Many Requests", retry_after="0")
        success = _mock_response({"ok": True})
        with patch("wicli.core.client.urlopen", side_effect=[err, success]):
            with patch("wicli.core.client.time.sleep"):
                result = _get("http://example.com")
        assert result == {"ok": True}


def _mock_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = json.dumps(data).encode("utf-8")
    return mock


def _mock_http_error(code: int, reason: str, retry_after: str | None = None):
    headers = MagicMock()
    headers.get.return_value = retry_after
    return HTTPError("http://example.com", code, reason, headers, None)
