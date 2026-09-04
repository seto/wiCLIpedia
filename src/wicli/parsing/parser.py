# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of wiCLIpedia.
#
# wiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with wiCLIpedia.  If not, see <https://www.gnu.org/licenses/>.

"""Module implementing the parsing of Wikipedia API responses.

This module provides functions to parse the JSON responses from the Wikipedia API,
extracting relevant information such as page properties, summaries, sections, and
disambiguation options.

It includes the cleaning of wikitext to produce readable plain text for better
rendering in the command line interface.
"""

import re
from typing import Any

from .lexer import tokenize
from .nodes import TokenType
from .table import encode_table, parse_table


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

    if not extract:
        return {"status": "missing"}

    paragraphs = [
        " ".join(block.split()) for block in extract.splitlines() if block.strip()
    ]

    return {
        "status": "found",
        "paragraphs": paragraphs,
        "_cached_at": response.get("_cached_at"),
    }


def parse_section(response: dict[str, Any]) -> dict[str, Any]:
    wikitext = response.get("parse", {}).get("wikitext", "")
    if not wikitext:
        return {"status": "missing"}

    tokens = tokenize(wikitext)
    blocks, buffer = [], []
    for token in tokens:
        if token.type == TokenType.TABLE:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []

            parsed = parse_table(token.value)
            for row in parsed.rows:
                for cell in row:
                    cell.text = _clean_inline(cell.text)

            if parsed.caption:
                parsed.caption = _clean_inline(parsed.caption)

            if parsed.rows:
                blocks.append(f"\x00TABLE\x00{encode_table(parsed)}\x00")
            else:
                blocks.append("[Table not available in CLI]")

        elif token.type == TokenType.LIST_ITEM:
            cleaned = _clean_inline(token.value).lstrip("*#").strip()

            if cleaned:
                buffer.append("• " + cleaned)

        elif token.type == TokenType.TEXT:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []

            cleaned = _clean_inline(token.value)
            if cleaned:
                blocks.append(cleaned)

        elif token.type == TokenType.DEFINITION_TERM:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []

            cleaned = _clean_inline(token.value.lstrip(";").strip())
            if cleaned:
                blocks.append(f"\x00SUBHEADING\x00{cleaned}\x00")

        elif token.type == TokenType.SUBHEADING:
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []

            cleaned = _clean_inline(token.value.strip().strip("="))
            if cleaned:
                blocks.append(f"\x00SUBHEADING\x00{cleaned}\x00")

        elif token.type in (TokenType.BLOCKQUOTE, TokenType.POEM):
            if buffer:
                blocks.append("\n".join(buffer))
                buffer = []

            raw = token.value
            if raw.startswith("\x00POEM\x00"):
                inner = raw[len("\x00POEM\x00") :].rstrip("\x00")
                cleaned_lines = [
                    _clean_inline(line) for line in inner.split("\x00LINE\x00")
                ]
                cleaned_lines = [l for l in cleaned_lines if l]
                if cleaned_lines:
                    blocks.append(
                        "\x00POEM\x00" + "\x00LINE\x00".join(cleaned_lines) + "\x00"
                    )
            else:
                text = raw.replace("\x00BLOCKQUOTE\x00", "").replace("\x00", "")
                cleaned = _clean_inline(text)
                if cleaned:
                    blocks.append(f"\x00BLOCKQUOTE\x00{cleaned}\x00")

    if buffer:
        blocks.append("\n".join(buffer))

    return {
        "status": "found",
        "section": "\n\n".join(blocks),
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

    links = []
    for line in lines:
        stripped = re.sub(r"('{2,5}|\*|{{.*?}})", "", line).strip()

        # Prefer [[Page|alias]] over [[Page]] when extracting the page title,
        # so that links with display text don't show the alias as the title
        match = re.search(r"\[\[([^\]|]+)\|[^\]]*\]\]", stripped) or re.search(
            r"\[\[([^\]]+)\]\]", stripped
        )

        if match:
            title = match.group(1).split("#")[0].strip()
            before = _clean_inline(stripped[: match.start()]).strip(" –-,")
            after = _clean_inline(stripped[match.end() :]).strip(" –-,")

            # Reverse order: after comes first to preserve natural
            # reading flow when the link appears mid-line or at the end
            if before and after:
                desc = f"{after}, {before}"
            else:
                desc = after or before

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


def _clean_inline(text: str) -> str:
    """Clean residual wikitext inline markup from a single token value.

    Called after the lexer has already stripped multi-line refs and templates.
    Handles inline refs and links that survive on a single line of text.
    """

    # Match and remove <ref> tags that may be left in the token value,
    # which can occur if they open and close within the same line
    text = re.sub(r"<ref[^>]*(?<!/)>.*?</ref>", "", text)
    text = re.sub(r"<ref[^>]*/?>", "", text)

    # Match and remove external links, keeping the display text if present
    text = re.sub(r"\[(?:https?|ftp)://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[(?:https?|ftp)://\S+\]", "", text)

    # Match and remove internal links, keeping the display text if present
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    # Remove bold/italic markup, replace <br> with space, strip remaining HTML
    # tags, and normalize whitespaces to single spaces
    text = re.sub(r"'{2,5}", "", text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = " ".join(text.split())

    return text.strip()
