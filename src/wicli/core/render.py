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

"""Module implementing the rendering of Wikipedia content for the CLI.

This module provides functions to format and style the output of Wikipedia content
for display in the command line interface.

It includes rendering of page summaries, table of contents, sections,
disambiguation options, and user prompts and navigation.
"""

import os
import sys
import textwrap
import time

from ..parsing.table import decode_table

_NO_COLOR = (
    os.environ.get("NO_COLOR") is not None
    or not hasattr(sys.stdout, "isatty")
    or not sys.stdout.isatty()
    or os.environ.get("TERM") == "dumb"
)

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_ITALIC = "\033[3m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_BLUE = "\033[34m"
_PURPLE = "\033[35m"
_CYAN = "\033[36m"


def render_welcome() -> str:
    width = _get_width()
    separator = "─" * width

    logo = (
        rf"""
               _ ________    ____               ___      
     _      __(_) ____/ /   /  _/___  ___  ____/ (_)___ _
    | | /| / / / /   / /    / // __ \/ _ \/ __  / / __ `/
    | |/ |/ / / /___/ /____/ // /_/ /  __/ /_/ / / /_/ / 
    |__/|__/_/\____/_____/___/ .___/\___/\__,_/_/\__,_/  
                            /_/                          
"""
        # Fallback to simple text if terminal is
        # narrower than the 58-char ASCII logo
        if width >= 58
        else "\nwiCLIpedia\n"
    )

    logo = "\n".join(
        line.center(width) if line.strip() else "" for line in logo.split("\n")
    )

    message = f"""
{_style(f"{separator}{logo}{separator}", _PURPLE, _BOLD)}

{_style("Welcome to WiCLIpedia! Your command-line gateway to Wikipedia content.", _BOLD)}

To get started, enter a Wikipedia page title when prompted.
You can specify the language at startup using -l or --lang (e.g., wicli --lang it).

User navigation:
    :b - Go back to the start prompt
    :q - Quit the application

{_style("Enjoy exploring Wikipedia from your terminal!", _ITALIC)}

{separator}
"""

    return message


def render_cache_purged(rows: int) -> str:
    if rows == 0:
        return _style("Cache is already empty. No entries to purge.", _BLUE, _BOLD)
    elif rows == 1:
        return _style("Cache purged successfully. 1 entry removed.", _GREEN, _BOLD)

    return _style(f"Cache purged successfully. {rows} entries removed.", _GREEN, _BOLD)


def render_start_prompt() -> str:
    return _style("Enter a page title:", _CYAN)


def render_redirect(page: str) -> str:
    return _style(f"Redirected to '{page}'.", _BLUE, _BOLD)


def render_title_fallback(original: str, fallback: str) -> str:
    return _style(f"Page '{original}' not found. Trying '{fallback}'.", _BLUE, _BOLD)


def render_not_found(page: str, lang: str) -> str:
    return _style(f"Page '{page}' not found in '{lang}' Wikipedia.", _YELLOW, _BOLD)


def render_user_cancelled() -> str:
    return _style("WiCLIpedia stopped by user.", _YELLOW, _BOLD)


def render_exit() -> str:
    return _style("Goodbye!", _GREEN, _BOLD)


def render_summary(title: str, paragraphs: list[str], cached_at: float = None) -> str:
    width = _get_width()

    summary = "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs)

    output = f"""
{_render_content_banner(cached_at)}

{_style(title, _BOLD)}

{summary}
"""

    return output


def render_summary_not_found(title: str) -> str:
    return _style(f"Summary not found for page '{title}'.", _YELLOW)


def render_toc_prompt() -> str:
    return _style("Do you want to see the table of contents (Y/n)?", _CYAN)


def render_toc_invalid_choice(choice: str) -> str:
    return _style(f"'{choice}' is not a valid choice. Enter 'y' or 'n'.", _YELLOW)


def render_toc(sections: list, cached_at: float = None) -> str:
    # Map each tocLevel to the maximum number width at that level,
    # used to align section numbers consistently within each level
    widths = {}
    for section in sections:
        lvl = section["tocLevel"]
        widths[lvl] = max(widths.get(lvl, 0), len(str(section["number"])))

    # Compute the cumulative indentation for each tocLevel by summing
    # the number widths (plus 2 separator spaces) of all preceding levels
    indents = {}
    offset = 0
    for lvl, width in sorted(widths.items()):
        indents[lvl] = offset
        offset += width + 2

    toc = []
    for section in sections:
        lvl = section["tocLevel"]
        indent = " " * indents[lvl]
        index = _style(f"{section['number']:<{widths[lvl]}}", _DIM)
        title = _style(section["line"], _BOLD) if lvl == 1 else section["line"]
        toc.append(f"{indent}{index}  {title}")

    toc_str = "\n".join(toc)

    output = f"""
{_render_content_banner(cached_at)}

{_style("Available content for this page:", _BOLD)}

{toc_str}
"""

    return output


def render_toc_navigation_prompt() -> str:
    return _style("Enter the section number:", _CYAN)


def render_toc_navigation_invalid_choice(choice: str) -> str:
    return _style(
        f"'{choice}' is not a valid choice. Enter a valid section number or ':m' to show the menu.",
        _YELLOW,
    )


def render_toc_not_found() -> str:
    return _style("Table of contents not found for this page.", _YELLOW)


def render_section(title: str, section: str, cached_at: float = None) -> str:
    width = _get_width()

    blocks = []
    for block in section.split("\n\n"):
        if block.startswith("\x00SUBHEADING\x00"):
            subheading = block.replace("\x00SUBHEADING\x00", "").replace("\x00", "")
            if subheading != title:
                blocks.append(_style(subheading, _DIM))

        elif block.startswith("\x00BLOCKQUOTE\x00"):
            quote = block.replace("\x00BLOCKQUOTE\x00", "").replace("\x00", "")
            quote = textwrap.fill(f"« {quote} »", width=width - 16)
            quote = textwrap.indent(quote, "      ")
            blocks.append(_style(quote, _ITALIC))

        elif block.startswith("•"):
            # For list blocks, each item is wrapped separately with
            # a hanging indent to align continuation lines under the text
            items = block.split("\n")
            blocks.append(
                "\n".join(
                    textwrap.fill(item, width=width, subsequent_indent="  ")
                    for item in items
                )
            )

        elif block.startswith("\x00TABLE\x00"):
            encoded = block.replace("\x00TABLE\x00", "").rstrip("\x00")
            blocks.append(_render_table(decode_table(encoded)))
        
        else:
            blocks.append(textwrap.fill(block, width=width))

    content = "\n\n".join(blocks)

    output = f"""
{_render_content_banner(cached_at)}

{_style(title, _BOLD)}

{content}
"""

    return output


def render_section_not_found(title: str) -> str:
    return _style(f"Content not found for section '{title}'.", _YELLOW)


def render_disambiguation(options: list, cached_at: float = None) -> str:
    width = _get_width()
    pad = len(str(len(options)))
    indent = " " * (pad + 2)

    links = []
    for i, option in enumerate(options, start=1):
        page = (
            f"{_style(option['page'], _BOLD)} - {option['desc']}"
            if option["desc"]
            else _style(option["page"], _BOLD)
        )
        wrapped = textwrap.fill(page, width=width, subsequent_indent=indent)
        num = _style(str(f"{i:<{pad}}"), _DIM)
        links.append(f"{num}  {wrapped}")

    links_str = "\n".join(links)

    output = f"""
{_render_content_banner(cached_at)}

{_style("This page is a disambiguation for the following options:", _BOLD)}

{links_str}
"""

    return output


def render_disambiguation_redirect(page: str) -> str:
    return _style(f"Redirected to '{page} (disambiguation page)'.", _BLUE, _BOLD)


def render_disambiguation_prompt() -> str:
    return _style("Enter the page number:", _CYAN)


def render_disambiguation_invalid_choice(choice: str) -> str:
    return _style(
        f"'{choice}' is not a valid choice. Enter a valid page number.",
        _YELLOW,
    )


def render_disambiguation_not_found(page: str) -> str:
    return _style(f"Disambiguation options not found for page '{page}'.", _YELLOW)


def _get_width() -> int:
    try:
        column = os.get_terminal_size().columns
    except OSError:
        column = 88

    width = min(column, 88)
    return width


def _style(text: str, *styles) -> str:
    """Apply ANSI style codes to text, unless NO_COLOR is set."""

    if not _NO_COLOR:
        prefix = "".join(styles)
        return f"{prefix}{text}{_RESET}"

    return text


def _render_content_banner(cached_at: float) -> str:
    width = _get_width()
    separator = _style("─" * width, _DIM)

    attribution = "© Wikipedia contributors ─ Content licensed under CC BY-SA 4.0"

    if cached_at:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cached_at))
        fetch = f"Loaded from cache (as of {ts})."
    else:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        fetch = f"Fetched from Wikipedia live (at {ts})."

    banner = f"""{separator}
{_style(attribution.center(width), _DIM, _BOLD)}
{_style(fetch.center(width), _DIM, _ITALIC)}
{separator}"""

    return banner


def _render_table(table) -> str:
    if not table.rows or not table.rows[0]:
        return ""

    width = _get_width()
    num_cols = len(table.rows[0])

    # 3 characters of overhead per column boundary (" │ "), plus the two
    # outer borders, subtracted from the terminal width before dividing
    # evenly across columns.
    col_width = max(6, (width - (num_cols + 1) * 3) // num_cols)
    separator = _style("─" * width, _BOLD)

    lines = []
    if table.caption:
        lines.append(_style(table.caption, _BOLD))
    lines.append(separator)

    for row in table.rows:
        wrapped = [textwrap.wrap(cell.text, width=col_width) or [""] for cell in row]
        height = max(len(w) for w in wrapped)
        for w in wrapped:
            w.extend([""] * (height - len(w)))

        for line_idx in range(height):
            cells = []
            for c, cell in enumerate(row):
                text = wrapped[c][line_idx].ljust(col_width)
                cells.append(_style(text, _BOLD) if cell.is_header else text)
            lines.append(" │ ".join(cells))

        if any(cell.is_header for cell in row):
            lines.append(separator)

    lines.append(separator)
    return "\n".join(lines)
