import time
from unittest.mock import patch

import pytest

from wicli.core import cache


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache, "_DB_PATH", tmp_path / "cache.db")


def test_load_miss():
    result = cache.load("Python", "en", "summary")
    assert result is None


def test_save_and_load():
    cache.save("Python", "en", "summary", {"key": "value"})
    result = cache.load("Python", "en", "summary")
    assert result is not None
    assert result["key"] == "value"


def test_load_injects_cached_at():
    cache.save("Python", "en", "summary", {"key": "value"})
    result = cache.load("Python", "en", "summary")
    assert "_cached_at" in result
    assert isinstance(result["_cached_at"], float)


def test_load_miss_different_lang():
    cache.save("Python", "en", "summary", {"key": "value"})
    result = cache.load("Python", "it", "summary")
    assert result is None


def test_load_miss_different_resource():
    cache.save("Python", "en", "summary", {"key": "value"})
    result = cache.load("Python", "en", "toc")
    assert result is None


def test_load_expired_returns_none(monkeypatch):
    cache.save("Python", "en", "summary", {"key": "value"})
    monkeypatch.setattr(cache, "_TTL", 0)
    result = cache.load("Python", "en", "summary")
    assert result is None


def test_save_overwrites():
    cache.save("Python", "en", "summary", {"v": 1})
    cache.save("Python", "en", "summary", {"v": 2})
    result = cache.load("Python", "en", "summary")
    assert result["v"] == 2


def test_purge_returns_count():
    cache.save("Python", "en", "summary", {"key": "value"})
    cache.save("Python", "it", "summary", {"key": "value"})
    count = cache.purge()
    assert count == 2


def test_purge_empty_returns_zero():
    count = cache.purge()
    assert count == 0


def test_purge_clears_all():
    cache.save("Python", "en", "summary", {"key": "value"})
    cache.purge()
    result = cache.load("Python", "en", "summary")
    assert result is None


def test_prune_removes_expired():
    cache.save("Python", "en", "summary", {"key": "value"})
    future = time.time() + cache._TTL + 1
    with patch("wicli.core.cache.time") as mock_time:
        mock_time.time.return_value = future
        cache.prune()
    result = cache.load("Python", "en", "summary")
    assert result is None


def test_prune_keeps_fresh_entries():
    cache.save("Python", "en", "summary", {"key": "value"})
    cache.prune()
    result = cache.load("Python", "en", "summary")
    assert result is not None
