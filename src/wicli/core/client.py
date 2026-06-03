# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of WiCLIpedia.
#
# WiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with WiCLIpedia.  If not, see <https://www.gnu.org/licenses/>.

"""Module implementing the core API functionality of WiCLIpedia.

This module provides functions to interact with the Wikipedia API, including
fetching page properties, summaries, disambiguation pages, table of contents,
and specific sections of a page.

It uses the `MediaWiki web service API`, more information about those APIs can be
found at the following docs page:
    https://www.mediawiki.org/wiki/API:Main_page
    https://en.wikipedia.org/w/api.php
    https://en.wikipedia.org/wiki/Special:ApiSandbox
"""

import functools
import json
import time
from importlib.metadata import version
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import cache

_USER_AGENT = f"wiclipedia/{version('wiclipedia')} (https://pypi.org/project/wiclipedia/; wicli@adversum.net)"
_BASE_URL = "https://{lang}.wikipedia.org/w/api.php"
_USE_CACHE = True
_MAX_RETRIES = 3


def disable_cache():
    global _USE_CACHE
    _USE_CACHE = False


def _cached(resource: str):
    """Decorator that loads from cache before calling fn, and saves the result after."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(page: str, lang: str = "en", **kwargs):
            if not _USE_CACHE:
                return fn(page, lang=lang, **kwargs)

            res = resource.format(**kwargs)
            cached = cache.load(page, lang, res)

            if cached is not None:
                return cached

            data = fn(page, lang=lang, **kwargs)
            cache.save(page, lang, res, data)
            return data

        return wrapper

    return decorator


def fetch_props(page: str, lang: str = "en") -> dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "titles": page,
        "prop": "pageprops",
        "redirects": True,
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


@_cached("summary")
def fetch_summary(page: str, lang: str = "en") -> dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "titles": page,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


@_cached("disambiguation")
def fetch_disambiguation(page: str, lang: str = "en") -> dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": page,
        "prop": "wikitext",
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


@_cached("toc")
def fetch_toc(page: str, lang: str = "en") -> dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": page,
        "prop": "tocdata",
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


@_cached("section_{section}")
def fetch_section(page: str, section: int, lang: str = "en") -> dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": page,
        "prop": "wikitext",
        "section": section,
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def _get(url: str) -> dict[str, Any]:
    """Perform an HTTP GET request and return the parsed JSON response.

    Retries up to _MAX_RETRIES times on HTTP 429, honouring the Retry-After
    header when present, and falling back to exponential backoff otherwise.
    """

    req = Request(url, headers={"User-Agent": _USER_AGENT})

    for attempt in range(_MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=10) as response:
                try:
                    return json.loads(response.read().decode("utf-8"))

                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid JSON response: {e}") from e

        except HTTPError as e:
            if e.code == 429 and attempt < _MAX_RETRIES:
                retry_after = e.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else 3 ** (attempt + 1)
                except ValueError:
                    wait = 3 ** (attempt + 1)

                time.sleep(wait)
                continue

            if e.code == 429:
                raise RuntimeError("Too many requests. Please try again later.") from e

            raise RuntimeError(f"HTTP error: {e.code} {e.reason}") from e

        except URLError as e:
            raise RuntimeError(f"Network error: {e.reason}") from e

        except TimeoutError as e:
            raise RuntimeError("Request timed out.") from e
