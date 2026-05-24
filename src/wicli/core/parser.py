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

"""Module implementing the parsing of Wikipedia API responses.

This module provides functions to parse the JSON responses from the Wikipedia API,
extracting relevant information such as page properties, summaries, sections, and
disambiguation options.

It includes the cleaning of wikitext to produce readable plain text for better
rendering in the command line interface.
"""

import re
from typing import Any

# File namespace aliases used to identify and remove file embeds,
# supports EN, IT, FR, ES, DE languages
_FILE_NAMESPACES = r"File|Image|Immagine|Fichier|Archivo|Datei"
_RE_FILE_EMBED = re.compile(rf"\[\[(?:{_FILE_NAMESPACES}):[^\]]*\]\]", re.IGNORECASE)


def parse_props(response: dict[str, Any]) -> dict[str, Any]:
    redirects = response.get("query", {}).get("redirects", [])

    if redirects and (target_page := redirects[0].get("to")):
        return {"status": "redirect", "target": target_page}

    pages = response.get("query", {}).get("pages", [])

    if not pages or "missing" in pages[0]:
        return {"status": "missing"}

    if "disambiguation" in pages[0].get("pageprops", {}):
        return {"status": "disambiguation"}

    if "pageprops" not in pages[0]:
        return {"status": "unknown"}

    return {"status": "found"}


def parse_summary(response: dict[str, Any]) -> dict[str, Any]:
    pages = response.get("query", {}).get("pages", [])

    if not pages or "missing" in pages[0]:
        return {"status": "missing"}

    extract = pages[0].get("extract", "")

    return {
        "status": "found",
        "summary": extract,
        "_cached_at": response.get("_cached_at"),
    }


def parse_section(response: dict[str, Any]) -> dict[str, Any]:
    wikitext = response.get("parse", {}).get("wikitext", "")

    if not wikitext:
        return {"status": "missing"}

    # Replace {{' }} with an apostrophe before any other processing,
    # as it's used in wikitext to avoid parsing issues with apostrophes
    clean = re.sub(r"\{\{'?\}\}", "'", wikitext)

    clean = _RE_FILE_EMBED.sub("", clean)
    clean = re.sub(r"^={2,6}\s*(.*?)\s*={2,6}$", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"<ref[^>]*>.*?</ref>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<ref[^>]*/>", "", clean)

    # Preserve block quotations, then remove remaining templates
    # iteratively to handle nesting (e.g., {{a|{{b}}}})
    clean = re.sub(r"\{\{[Cc]itazione\|([^}]+)\}\}", r"\1", clean)
    while re.search(r"\{\{[^{}]*\}\}", clean):
        clean = re.sub(r"\{\{[^{}]*\}\}", "", clean)

    clean = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", clean)
    clean = re.sub(r"\[\[([^\]]+)\]\]", r"\1", clean)
    clean = re.sub(r"'{2,5}", "", clean)

    lines = [line.strip() for line in clean.strip().split("\n")]
    cleaned_section = "\n".join([line for line in lines if line])

    return {
        "status": "found",
        "section": cleaned_section,
        "_cached_at": response.get("_cached_at"),
    }


def parse_disambiguation(response: dict[str, Any]) -> dict[str, Any]:
    wikitext = response.get("parse", {}).get("wikitext", "")

    if not wikitext:
        return {"status": "missing"}

    lines = [
        line
        for line in wikitext.strip().split("\n")
        if line.strip().startswith(("*", "'''"))
    ]

    # Match [[Page Title|optional alias]] and extract title and description,
    # two passes: first to extract the page title, then to clean the description
    links = []
    for line in lines:
        stripped = re.sub(r"('{2,5}|\*|{{.*?}})", "", line).strip()
        match = re.search(r"\[\[(.*?)(?:\|.*?)?\]\]", stripped)
        if match:
            title = match.group(1).strip()
            desc = re.sub(r"\[\[(?:.*?\|)?(.*?)\]\]", r"\1", stripped)
            desc = re.sub(r"\[\[(.*?)\]\]", r"\1", desc)
            desc = desc.replace(title, "").strip(" –-,")
            links.append({"page": title, "desc": desc})

    return {
        "status": "found",
        "options": links,
        "_cached_at": response.get("_cached_at"),
    }


def parse_toc(response: dict[str, Any]) -> dict[str, Any]:
    sections_data = response.get("parse", {}).get("tocdata", {}).get("sections", [])

    if not sections_data:
        return {"status": "missing"}

    sections = []
    for section in sections_data:
        sections.append(
            {
                "index": section.get("index", 0),
                "line": re.sub(r"<.*?>", "", section.get("line", "")),
                "number": section.get("number", ""),
                "tocLevel": section.get("tocLevel", ""),
            }
        )

    return {
        "status": "found",
        "sections": sections,
        "_cached_at": response.get("_cached_at"),
    }
