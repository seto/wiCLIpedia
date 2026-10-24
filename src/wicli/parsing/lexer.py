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

"""Module implementing the lexer for Wikipedia wikitext.

This module provides a function to tokenize raw wikitext into a flat list of tokens,
classifying lines by their leading characters. It handles the normalization of HTML
entities and the greedy consumption of multi-line constructs such as tables.

The resulting tokens are used by the parser to extract relevant content for rendering in
the command line interface.
"""

import html
import re

from .languages.templates import (
    ALBUM_TEMPLATES,
    BLOCKQUOTE_TEMPLATES,
    CHART_CAPTION,
    CHART_ENTRY_TEMPLATE,
    CHART_TABLE_HEADERS,
    CHART_TABLE_TEMPLATE,
    CITATION_TEMPLATES,
    FILE_NAMESPACES,
    MAIN_ARTICLE_TEMPLATES,
    POEMQUOTE_TEMPLATES,
    TEMPLATES_KEEP_FIRST,
    TEMPLATES_KEEP_LAST,
    TEMPLATES_STATIC,
)
from .nodes import Token, TokenType


def tokenize(wikitext: str) -> list[Token]:
    """Tokenize a wikitext string into a flat list of tokens.

    Before line-by-line classification, the full wikitext is pre-processed
    to remove refs and templates that may span multiple lines. Tables are then
    consumed greedily from `{|` to `|}` as the only remaining multi-line construct.

    Lines classified as HEADING, FILE, NEWLINE, or REF are discarded silently as
    they carry no content relevant to CLI rendering.
    """

    normalized = _normalize_entities(wikitext)
    normalized = _strip_html_comments(normalized)
    normalized = _strip_galleries(normalized)
    normalized = _strip_refs(normalized)
    normalized = _expand_chart_tables(normalized)
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


def _strip_html_comments(text: str) -> str:
    """Remove all HTML comments from the wikitext string.

    HTML comments can span multiple lines and are not relevant to CLI rendering.
    """

    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text


def _strip_galleries(text: str) -> str:
    """Remove all gallery HTML tags and their content from the wikitext."""

    text = re.sub(
        r"<gallery[^>]*>.*?</gallery>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    return text


def _parse_named_params(parts: list[str]) -> dict[str, str]:
    params = {}
    for p in parts:
        if "=" in p:
            key, value = p.split("=", 1)
            params[key.strip().lower()] = value.strip()

    return params


def _split_pipe(text: str) -> list[str]:
    """Split on | while ignoring pipes inside [[ ]] wikilinks and {{ }} templates."""

    parts, current, depth = [], [], 0
    i = 0
    while i < len(text):
        if text[i : i + 2] in ("[[", "{{"):
            depth += 1
            current.append(text[i : i + 2])
            i += 2
        elif text[i : i + 2] in ("]]", "}}"):
            depth = max(0, depth - 1)
            current.append(text[i : i + 2])
            i += 2
        elif text[i] == "|" and depth == 0:
            parts.append("".join(current))
            current = []
            i += 1
        else:
            current.append(text[i])
            i += 1

    parts.append("".join(current))
    return parts


def _find_templates(text: str, name: str) -> list[tuple[int, int]]:
    """Return the (start, end) spans of the outermost `{{name ...}}` templates.

    Nested braces are balanced, so templates containing other templates are
    returned whole. An unterminated template is ignored.
    """

    opener = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*(?=[|}])", re.IGNORECASE)

    spans = []
    pos = 0
    while match := opener.search(text, pos):
        depth, i = 0, match.start()
        while i < len(text):
            if text[i : i + 2] == "{{":
                depth += 1
                i += 2
            elif text[i : i + 2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1

        if depth != 0:
            break

        spans.append((match.start(), i))
        pos = i

    return spans


def _split_params(inner: str) -> tuple[list[str], dict[str, str]]:
    """Split template content into positional values and lowercased named params."""

    positional, named = [], {}
    for part in _split_pipe(inner)[1:]:
        key, sep, value = part.partition("=")
        if sep and re.fullmatch(r"\s*\w+\s*", key):
            named[key.strip().lower()] = value.strip()
        elif part.strip():
            positional.append(part.strip())

    return positional, named


def _expand_chart_tables(text: str) -> str:
    """Replace German `{{Charttabelle}}` templates with an equivalent wikitable.

    The template has no table markup in the wikitext: its rows are nested
    `{{Charteintrag}}` templates, which would otherwise be discarded as unknown.
    Each country listed in the header becomes a column showing the peak
    position and, when available, the weeks in the chart.
    """

    result = []
    pos = 0
    for start, end in _find_templates(text, CHART_TABLE_TEMPLATE):
        result.append(text[pos:start])
        result.append(_chart_table_to_wikitable(text[start + 2 : end - 2]))
        pos = end

    result.append(text[pos:])
    return "".join(result)


def _chart_table_to_wikitable(inner: str) -> str:
    codes, named = _split_params(inner)
    content = named.get("inhalt", "")

    entries = []
    for start, end in _find_templates(content, CHART_ENTRY_TEMPLATE):
        entry_codes, entry = _split_params(content[start + 2 : end - 2])
        entries.append((entry_codes, entry))

    if not entries:
        return ""

    if not codes:
        for entry_codes, _ in entries:
            codes.extend(c for c in entry_codes if c not in codes)

    headers = [CHART_TABLE_HEADERS["year"], CHART_TABLE_HEADERS["title"]]
    headers += codes + [CHART_TABLE_HEADERS["notes"]]

    lines = ["", "{|", f"|+ {CHART_CAPTION}", "! " + " !! ".join(headers)]
    for _, entry in entries:
        cells = [entry.get("jahr", ""), entry.get("titel", "")]
        for code in codes:
            position = entry.get(f"pos_{code.lower()}", "")
            weeks = entry.get(f"wo_{code.lower()}", "")
            if position and weeks:
                position = f"{position} ({weeks})"
            cells.append(position)
        cells.append(entry.get("anmerkung", ""))

        lines.append("|-")
        lines.append("| " + " || ".join(" ".join(c.split()) for c in cells))

    lines += ["|}", ""]
    return "\n".join(lines)


def _main_article_page(params: list[str]) -> str | None:
    for param in params:
        param = param.strip().removeprefix("[[").removesuffix("]]")
        if param and "=" not in param:
            title = param.split("|")[0].split("#")[0].strip()
            if title:
                return title

    return None


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
    result: list[str] = []
    current: list[str] = []
    while i < len(text):
        if text[i : i + 2] == "{{":
            depth += 1
            current = []
            i += 2

        elif text[i : i + 2] == "}}":
            if depth == 1:
                inner = "".join(current)
                parts = _split_pipe(inner)
                name = parts[0].strip().lower()

                if name in BLOCKQUOTE_TEMPLATES and len(parts) > 1:
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

                elif name in TEMPLATES_KEEP_LAST and len(parts) > 1:
                    result.append(parts[-1].strip())

                elif name in POEMQUOTE_TEMPLATES and len(parts) > 1:
                    poem = parts[1].strip().replace("\n", "\x00LINE\x00")
                    if poem:
                        result.append(f"\x00POEM\x00{poem}\x00")

                elif name in TEMPLATES_KEEP_FIRST and len(parts) > 1:
                    # Skip named params (e.g. date=) as they are meta-data and
                    # not relevant to the visible text content
                    first = parts[1].strip()
                    if "=" not in first:
                        result.append(first)

                elif name in CITATION_TEMPLATES:
                    params = _parse_named_params(parts[1:])
                    title = params.get(CITATION_TEMPLATES[name]["title"], "").strip()
                    year = params.get(CITATION_TEMPLATES[name]["year"], "").strip()
                    if title:
                        result.append(f"{title} - {year}." if year else title)

                elif name in ALBUM_TEMPLATES:
                    params = _parse_named_params(parts[1:])
                    title = params.get("titre", "").strip()
                    year = params.get("année", "").strip()
                    content = params.get("contenu", "").strip()

                    header_parts = [title] if title else []
                    if year:
                        header_parts.append(f"({year})")

                    album_text = []
                    if header_parts:
                        album_text.append(f"'''{' '.join(header_parts)}'''")
                    if content:
                        album_text.append(content)
                    if album_text:
                        result.append("\n" + "\n".join(album_text) + "\n")

                elif name in MAIN_ARTICLE_TEMPLATES:
                    # Kept as a marker on its own line: the parser decides whether
                    # it is a hatnote (before the text) or must be ignored
                    page = _main_article_page(parts[1:])
                    if page:
                        result.append(f"\n\x00MAIN\x00{page}\x00\n")

                elif name in TEMPLATES_STATIC:
                    result.append(TEMPLATES_STATIC[name])

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

    if stripped.startswith(";"):
        return TokenType.DEFINITION_TERM

    if stripped.startswith("<ref"):
        return TokenType.REF

    if stripped.startswith(FILE_NAMESPACES):
        return TokenType.FILE

    if stripped.startswith("\x00BLOCKQUOTE\x00"):
        return TokenType.BLOCKQUOTE

    if stripped.startswith("\x00POEM\x00"):
        return TokenType.POEM

    if stripped.startswith("\x00MAIN\x00"):
        return TokenType.MAIN_ARTICLE

    if not stripped:
        return TokenType.NEWLINE

    return TokenType.TEXT
