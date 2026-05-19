# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of WiCLIpedia.
#
# WiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
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

import json
from importlib.metadata import version
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_USER_AGENT = f"wiclipedia/{version('wiclipedia')} (https://pypi.org/project/wiclipedia/; wicli@adversum.net)"
_BASE_URL = "https://{lang}.wikipedia.org/w/api.php"


def fetch_props(page: str, lang: str = "en") -> Dict[str, Any]:
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


def fetch_summary(page: str, lang: str = "en") -> Dict[str, Any]:
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


def fetch_disambiguation(page: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": page,
        "prop": "wikitext",
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_toc(page: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": page,
        "prop": "tocdata",
        "formatversion": 2,
    }
    url = f"{_BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_section(page: str, section: int, lang: str = "en") -> Dict[str, Any]:
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


def _get(url: str) -> Dict[str, Any]:
    """Perform an HTTP GET request and return the parsed JSON response."""

    req = Request(url, headers={"User-Agent": _USER_AGENT})

    try:
        with urlopen(req, timeout=5) as response:
            data = response.read().decode("utf-8")

    except HTTPError as e:
        raise RuntimeError(f"HTTP error: {e.code} {e.reason}") from e

    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e

    except TimeoutError as e:
        raise RuntimeError("Request timed out.") from e

    try:
        return json.loads(data)

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {e}") from e
