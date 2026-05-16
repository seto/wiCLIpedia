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

import json
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "wiclipedia/0.0.1 (https://pypi.org/project/wiclipedia/; seto@adversum.net)"
BASE_URL = "https://{lang}.wikipedia.org/w/api.php"


def fetch_props(title: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "pageprops",
        "redirects": True,
        "formatversion": 2,
    }
    url = f"{BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_summary(title: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "formatversion": 2,
    }
    url = f"{BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_disambiguation(title: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "wikitext",
        "formatversion": 2,
    }
    url = f"{BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_toc(title: str, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "tocdata",
        "formatversion": 2,
    }
    url = f"{BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def fetch_section(title: str, section: int, lang: str = "en") -> Dict[str, Any]:
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "wikitext",
        "section": section,
        "formatversion": 2,
    }
    url = f"{BASE_URL.format(lang=lang)}?{urlencode(params)}"

    return _get(url)


def _get(url: str) -> Dict[str, Any]:
    req = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as e:
        raise RuntimeError(f"HTTP error: {e.code} {e.reason}") from e

    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}") from e
