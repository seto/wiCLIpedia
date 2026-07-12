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

"""Module implementing the lexer for Wikipedia wikitext.

This module provides a function to tokenize raw wikitext into a flat list of tokens,
classifying lines by their leading characters. It handles the normalization of HTML
entities and the greedy consumption of multi-line constructs such as tables.

The resulting tokens are used by the parser to extract relevant content for rendering in
the command line interface.
"""

import html
import re

from .nodes import Token, TokenType

_TEMPLATES_KEEP_LAST = {
    "abbr",
    "as of",
    "cast listing",
    "citation",
    "date",
    "lang",
    "langue",
    "nowrap",
    "transl",
    "unité",
}
_TEMPLATES_KEEP_FIRST = {
    "citation nécessaire",
    "citation needed",
    "cn",
    "cr",
    "cita requerida",
    "référence nécessaire",
    "senza fonte",
}
_BLOCKQUOTE_TEMPLATES = {
    "blockquote",
    "cita",
    "citazione",
    "quote",
    "cquote",
    "zitat",
}
_FILE_NAMESPACES = (
    "[[Archivo:",
    "[[Bild:",
    "[[Datei:",
    "[[Fichier:",
    "[[File:",
    "[[Image:",
    "[[Immagine:",
)
_CITATION_TEMPLATES = {
    "cita libro": {"title": "titolo", "year": "anno"},
    "cita news": {"title": "titolo", "year": "anno"},
    "cita pubblicazione": {"title": "titolo", "year": "anno"},
    "cita web": {"title": "titolo", "year": "anno"},
    "cite book": {"title": "title", "year": "year"},
    "cite journal": {"title": "title", "year": "date"},
    "cite magazine": {"title": "title", "year": "date"},
    "cite news": {"title": "title", "year": "year"},
    "cite web": {"title": "title", "year": "date"},
    "internetquelle": {"title": "titel", "year": "datum"},
    "lien web": {"title": "titre", "year": "année"},
}


def tokenize(wikitext: str) -> list[Token]:
    """Tokenize a wikitext string into a flat list of tokens.

    Before line-by-line classification, the full wikitext is pre-processed
    to remove refs and templates that may span multiple lines. Tables are then
    consumed greedily from `{|` to `|}` as the only remaining multi-line construct.

    Lines classified as HEADING, FILE, NEWLINE, or REF are discarded silently as
    they carry no content relevant to CLI rendering.
    """

    normalized = _normalize_entities(wikitext)
    normalized = _strip_refs(normalized)
    normalized = _strip_templates(normalized)

    lines = normalized.splitlines()

    i = 0
    tokens = []
    while i < len(lines):
        line = lines[i]
        token_type = _classify_line(line)

        if token_type == TokenType.TABLE:
            table_lines = [line]
            i += 1

            while i < len(lines):
                table_lines.append(lines[i])
                if lines[i].strip().startswith("|}"):
                    break
                i += 1

            tokens.append(Token(TokenType.TABLE, "\n".join(table_lines)))

        elif token_type in (
            TokenType.HEADING,
            TokenType.FILE,
            TokenType.NEWLINE,
            TokenType.REF,
        ):
            pass

        else:
            tokens.append(Token(token_type, line))

        i += 1

    return tokens


def _normalize_entities(text: str) -> str:
    """Normalize HTML entities and non-breaking spaces to plain text."""

    return html.unescape(text).replace("\xa0", " ")


def _strip_refs(text: str) -> str:
    """Remove all ref tags and their content from the full wikitext string.

    Done on the full string before line splitting because refs can open
    inline mid-sentence and close several lines later.
    """

    text = re.sub(r"<ref[^>]*(?<!/)>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/?>", "", text)

    return text


def _parse_named_params(parts: list[str]) -> dict[str, str]:
    params = {}
    for p in parts:
        if "=" in p:
            key, value = p.split("=", 1)
            params[key.strip().lower()] = value.strip()

    return params


def _strip_templates(text: str) -> str:
    """Remove all templates from the full wikitext string.

    Done on the full string before line splitting because templates can open
    inline mid-sentence and close several lines later.

    For templates in `_TEMPLATES_KEEP_LAST`, the last parameter is kept as visible text.
    For templates in `_TEMPLATES_KEEP_FIRST`, the first parameter is kept instead.

    Only the outermost template name is checked against either set;
    nested templates are always discarded regardless of their name.
    """

    i, depth = 0, 0
    result, current = [], []
    while i < len(text):
        if text[i : i + 2] == "{{":
            depth += 1
            current = []
            i += 2

        elif text[i : i + 2] == "}}":
            if depth == 1:
                inner = "".join(current)
                parts = inner.split("|")
                name = parts[0].strip().lower()

                if name in _BLOCKQUOTE_TEMPLATES and len(parts) > 1:
                    # Extract quote text handling language-specific variations
                    # where blockquotes might use an explicit 'text=' parameter
                    quote = next(
                        (
                            p.split("=", 1)[1].strip()
                            for p in parts[1:]
                            if p.strip().lower().startswith("text=")
                        ),
                        parts[1].strip() if len(parts) > 1 else "",
                    )
                    if quote:
                        result.append(f"\x00BLOCKQUOTE\x00{quote}\x00")

                elif name in _TEMPLATES_KEEP_LAST and len(parts) > 1:
                    result.append(parts[-1].strip())

                elif name in _TEMPLATES_KEEP_FIRST and len(parts) > 1:
                    result.append(parts[1].strip())

                elif name in _CITATION_TEMPLATES:
                    params = _parse_named_params(parts[1:])
                    title = params.get(_CITATION_TEMPLATES[name]["title"], "").strip()
                    year = params.get(_CITATION_TEMPLATES[name]["year"], "").strip()
                    if title:
                        result.append(f"{title} - {year}." if year else title)

            depth = max(0, depth - 1)
            current = []
            i += 2

        elif depth > 0:
            current.append(text[i])
            i += 1

        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def _classify_line(line: str) -> TokenType:
    """Classify a single wikitext line by its leading characters.

    Branch order matters:
    - SUBHEADING (`===`) is checked before HEADING (`==`) to avoid
      misclassifying deeper nesting levels.
    - HEADING (`==`) is checked before TEMPLATE (`{{`) because
      some section titles may contain template-like syntax.
    - TABLE (`{|`, `|-`) is checked before TEMPLATE (`{{`) for the same reason.
    - FILE is checked explicitly because `[[File:...]]` would otherwise be
      classified as TEXT.
    """

    stripped = line.strip()

    if stripped.startswith("==="):
        return TokenType.SUBHEADING

    if stripped.startswith("=="):
        return TokenType.HEADING

    if stripped.startswith(("{|", "|-")):
        return TokenType.TABLE

    if stripped.startswith("{{"):
        return TokenType.TEMPLATE

    if stripped.startswith(("*", "#")):
        return TokenType.LIST_ITEM

    if stripped.startswith("<ref"):
        return TokenType.REF

    if stripped.startswith(_FILE_NAMESPACES):
        return TokenType.FILE

    if stripped.startswith("\x00BLOCKQUOTE\x00"):
        return TokenType.BLOCKQUOTE

    if not stripped:
        return TokenType.NEWLINE

    return TokenType.TEXT
