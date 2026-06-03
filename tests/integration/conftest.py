from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_cache_prune():
    """Prevent tests from touching the real on-disk cache."""

    with patch("wicli.core.cache.prune"):
        yield
