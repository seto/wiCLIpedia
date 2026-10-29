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

from ..parsing.table import ParsedTable, decode_table

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
        r"""
               _ ________    ____               ___      
     _      __(_) ____/ /   /  _/___  ___  ____/ (_)___ _
    | | /| / / / /   / /    / // __ \/ _ \/ __  / / __ `/
    | |/ |/ / / /___/ /____/ // /_/ /  __/ /_/ / / /_/ / 
    |__/|__/_/\____/_____/___/ .___/\___/\__,_/_/\__,_/  
                            /_/                          
"""  # noqa: W291
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

{_render_message("Welcome to wiCLIpedia! Your command-line gateway to Wikipedia content.", _BOLD)}

To get started, enter a Wikipedia page title when prompted.
You can specify the language at startup using -l or --lang (e.g., wicli --lang it).

User navigation:
    :b - Go back to the start prompt
    :q - Quit the application

{_render_message("Enjoy exploring Wikipedia from your terminal!", _ITALIC)}

{_render_message(_license_notice(), _DIM, _ITALIC)}

{separator}"""

    return message


def render_cache_purged(rows: int) -> str:
    if rows == 0:
        return _render_message(
            "wiCLIpedia cache is already empty. No entries to purge.",
            _BLUE,
            _BOLD,
            padding_lines=1,
        )
    elif rows == 1:
        return _render_message(
            "wiCLIpedia cache purged successfully. 1 entry removed.",
            _GREEN,
            _BOLD,
            padding_lines=1,
        )

    return _render_message(
        f"wiCLIpedia cache purged successfully. {rows} entries removed.",
        _GREEN,
        _BOLD,
        padding_lines=1,
    )


def render_start_prompt() -> str:
    return _render_message("Enter a page title:", _CYAN, padding_before=1)


def show_warranty() -> str:
    text = """
THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.
EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE
OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE
COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
"""

    return _render_message(text, _DIM, _ITALIC, padding_before=1)


def show_conditions() -> str:
    text = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

See https://www.gnu.org/licenses/agpl-3.0.html for the full text.
"""

    return _render_message(text, _DIM, _ITALIC, padding_before=1)


def render_redirect(page: str) -> str:
    return _render_message(f"Redirected to '{page}'.", _BLUE, _BOLD)


def render_title_fallback(original: str, fallback: str) -> str:
    return _render_message(
        f"Page '{original}' not found. Trying '{fallback}'.", _BLUE, _BOLD
    )


def render_language_switch(lang: str) -> str:
    return _render_message(f"Switching to '{lang}' Wikipedia.", _BLUE, _BOLD)


def render_not_found(page: str, lang: str) -> str:
    return _render_message(
        f"Page '{page}' not found in '{lang}' Wikipedia.", _YELLOW, _BOLD
    )


def render_user_cancelled() -> str:
    return _render_message(
        "wiCLIpedia stopped by user.", _YELLOW, _BOLD, padding_before=1
    )


def render_exit() -> str:
    return _render_message("Goodbye!", _GREEN, _BOLD, padding_lines=1)


def render_error(label: str, error: object) -> str:
    return _render_message(f"{label}: {error}", _RED, _BOLD, padding_lines=1)


def render_summary(title: str, paragraphs: list[str], cached_at: float | None) -> str:
    width = _get_width()

    summary = "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs)

    output = f"""
{_render_content_banner(cached_at)}

{_render_message(title, _BOLD)}

{summary}
"""

    return output


def render_summary_not_found(title: str) -> str:
    return _render_message(f"Summary not found for page '{title}'.", _YELLOW)


def render_toc_prompt() -> str:
    return _render_message("Do you want to see the table of contents (Y/n)?", _CYAN)


def render_toc_invalid_choice(choice: str) -> str:
    return _render_message(
        f"'{choice}' is not a valid choice. Enter 'y' or 'n'.", _YELLOW
    )


def render_toc(sections: list, cached_at: float | None) -> str:
    # Map each tocLevel to the maximum number width at that level,
    # used to align section numbers consistently within each level
    widths: dict[int, int] = {}
    for section in sections:
        lvl = section["tocLevel"]
        widths[lvl] = max(widths.get(lvl, 0), len(str(section["number"])))

    # Compute the cumulative indentation for each tocLevel by summing
    # the number widths (plus 2 separator spaces) of all preceding levels
    indents: dict[int, int] = {}
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

{_render_message("Available content for this page:", _BOLD)}

{toc_str}
"""

    return output


def render_toc_navigation_prompt(
    has_links: bool = False,
    links_shown: bool = False,
    main_pages_shown: bool = False,
) -> str:
    if not (has_links or main_pages_shown):
        return _render_message("Enter a section number:", _CYAN)

    options = ["Enter a section number"]
    if main_pages_shown:
        options.append("'0N' to open one of the section's pages")
    if links_shown:
        options.append("'jN' to open a related page")
    options.append("or ':m' to show the menu:")

    return _render_message(", ".join(options), _CYAN)


def render_toc_navigation_invalid_choice(
    choice: str,
    has_links: bool = False,
    links_shown: bool = False,
    main_pages: int = 0,
    main_pages_shown: bool = False,
) -> str:
    if not (has_links or main_pages):
        return _render_message(
            f"'{choice}' is not a valid choice. Enter a valid section number or ':m' to show the menu.",
            _YELLOW,
        )

    options = ["Enter a valid section number"]
    if main_pages == 1:
        options.append("'0' to open the section's page")
    elif main_pages_shown:
        options.append("'0N' to open one of the section's pages")
    elif main_pages > 1:
        options.append("'0' to show the section's pages")
    if links_shown:
        options.append("a related page number (e.g. 'j1')")
    elif has_links:
        options.append("'j' to show related pages")
    options.append("or ':m' to show the menu.")

    return _render_message(
        f"'{choice}' is not a valid choice. " + ", ".join(options), _YELLOW
    )


def render_toc_not_found() -> str:
    return _render_message("Table of contents not found for this page.", _YELLOW)


def render_section(title: str, section: str, cached_at: float | None) -> str:
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

        elif block.startswith("\x00POEM\x00"):
            inner = block[len("\x00POEM\x00") :].rstrip("\x00")
            lines = [line for line in inner.split("\x00LINE\x00") if line.strip()]
            poem = "\n".join(textwrap.indent(line, "      ") for line in lines)
            blocks.append(_style(poem, _ITALIC))

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

{_render_message(title, _BOLD)}

{content}
"""

    return output


def render_section_not_found(title: str) -> str:
    return _render_message(f"Content not found for section '{title}'.", _YELLOW)


def render_section_links(links: list[dict[str, str]]) -> str:
    pad = len(str(len(links)))

    entries = []
    for i, link in enumerate(links, start=1):
        num = _style(f"{f'j{i}':<{pad + 1}}", _DIM)
        entries.append(f"{num}  {_render_link_title(link)}")

    entries_str = "\n".join(entries)

    return f"""
{_render_message("Related pages you can jump to:", _BOLD)}

{entries_str}
"""


def render_section_hints(main_pages: list[str], has_links: bool) -> str:
    hints = []
    if main_pages:
        hints.append(render_main_article_prompt(main_pages))
    if has_links:
        hints.append(render_rabbit_hole_prompt())

    return "\n".join(hints) + "\n" if hints else ""


def render_main_article_prompt(pages: list[str]) -> str:
    if len(pages) == 1:
        return _render_message(
            f"This section has its own page: {pages[0]}. Enter '0' to open it.",
            _CYAN,
            _DIM,
        )

    return _render_message(
        "This section has its own pages. Enter '0' to show them.", _CYAN, _DIM
    )


def render_main_articles(pages: list[str]) -> str:
    pad = len(str(len(pages)))

    entries = []
    for i, page in enumerate(pages, start=1):
        num = _style(f"{f'0{i}':<{pad + 1}}", _DIM)
        entries.append(f"{num}  {_style(page, _BOLD)}")

    entries_str = "\n".join(entries)

    return f"""
{_render_message("Pages dedicated to this section you can open:", _BOLD)}

{entries_str}
"""


def render_rabbit_hole_prompt() -> str:
    return _render_message(
        "Down the rabbit hole? Enter 'j' to show related pages.", _CYAN, _DIM
    )


def render_disambiguation(options: list, cached_at: float | None) -> str:
    width = _get_width()
    pad = len(str(len(options)))
    indent = " " * (pad + 2)

    links = []
    for i, option in enumerate(options, start=1):
        title = _render_link_title(option)
        page = f"{title} - {option['desc']}" if option["desc"] else title
        wrapped = textwrap.fill(page, width=width, subsequent_indent=indent)
        num = _style(str(f"{i:<{pad}}"), _DIM)
        links.append(f"{num}  {wrapped}")

    links_str = "\n".join(links)

    output = f"""
{_render_content_banner(cached_at)}

{_render_message("This page is a disambiguation for the following options:", _BOLD)}

{links_str}
"""

    return output


def render_disambiguation_redirect(page: str) -> str:
    return _render_message(
        f"Redirected to '{page} (disambiguation page)'.", _BLUE, _BOLD
    )


def render_disambiguation_prompt() -> str:
    return _render_message("Enter the page number:", _CYAN)


def render_disambiguation_invalid_choice(choice: str) -> str:
    return _render_message(
        f"'{choice}' is not a valid choice. Enter a valid page number.",
        _YELLOW,
    )


def render_disambiguation_not_found(page: str) -> str:
    return _render_message(
        f"Disambiguation options not found for page '{page}'.", _YELLOW
    )


def _get_width() -> int:
    try:
        column = os.get_terminal_size().columns
    except OSError:
        column = 100

    width = min(column, 100)
    return width


def _style(text: str, *styles: str) -> str:
    if not _NO_COLOR:
        prefix = "".join(styles)
        return f"{prefix}{text}{_RESET}"

    return text


def _render_link_title(link: dict[str, str]) -> str:
    title = _style(link["page"], _BOLD)
    lang = link.get("lang")

    return f"{_style(f'[{lang}]', _DIM, _BOLD)} {title}" if lang else title


def _render_message(
    text: str,
    *styles: str,
    padding_lines: int = 0,
    padding_before: int | None = None,
    padding_after: int | None = None,
) -> str:
    """Wrap a standalone CLI message and optionally add vertical padding.

    `padding_lines` applies to both sides unless overridden by
    `padding_before` or `padding_after`.
    """

    message = "\n".join(
        textwrap.fill(line, width=_get_width()) if line else ""
        for line in text.strip("\n").splitlines()
    )
    before = "\n" * (padding_lines if padding_before is None else padding_before)
    after = "\n" * (padding_lines if padding_after is None else padding_after)

    return _style(f"{before}{message}{after}", *styles)


def _license_notice() -> str:
    return """This program comes with ABSOLUTELY NO WARRANTY; for details type ':show-w'.
This is free software, and you are welcome to redistribute it
under certain conditions; type ':show-c' for details."""


def _render_content_banner(cached_at: float | None) -> str:
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


def _render_table(table: ParsedTable) -> str:
    if not table.rows or not table.rows[0]:
        return ""

    num_cols = len(table.rows[0])

    # Each row is "│ " + cells joined by " │ " + " │": 3 * num_cols + 1 characters
    # of overhead on top of the column contents
    available = _get_width() - (3 * num_cols + 1)
    natural = [
        max(1, max(len(row[c].text) for row in table.rows)) for c in range(num_cols)
    ]
    col_widths = _fit_column_widths(natural, available)

    def rule(left: str, mid: str, right: str, fill: str) -> str:
        segments = [fill * (w + 2) for w in col_widths]
        return _style(f"{left}{mid.join(segments)}{right}", _DIM)

    top = rule("┌", "┬", "┐", "─")
    inner = rule("├", "┼", "┤", "─")
    header_rule = rule("╞", "╪", "╡", "═")
    bottom = rule("└", "┴", "┘", "─")
    edge = _style("│", _DIM)

    # A heavier rule separates the leading all-header rows from the body
    header_rows = 0
    for row in table.rows:
        if not all(cell.is_header for cell in row):
            break
        header_rows += 1

    lines = []
    if table.caption:
        lines.append(_render_message(table.caption, _BOLD))
    lines.append(top)

    for i, row in enumerate(table.rows):
        wrapped = [
            textwrap.wrap(cell.text, width=col_widths[c]) or [""]
            for c, cell in enumerate(row)
        ]
        height = max(len(w) for w in wrapped)

        for line_idx in range(height):
            cells = []
            for c, cell in enumerate(row):
                part = wrapped[c][line_idx] if line_idx < len(wrapped[c]) else ""
                text = part.ljust(col_widths[c])
                cells.append(_style(text, _BOLD) if cell.is_header else text)
            lines.append(f"{edge} {f' {edge} '.join(cells)} {edge}")

        if i < len(table.rows) - 1:
            lines.append(header_rule if i + 1 == header_rows else inner)

    lines.append(bottom)
    return "\n".join(lines)


def _fit_column_widths(
    natural: list[int], available: int, min_width: int = 6
) -> list[int]:
    """Shrink column widths to fit `available` characters.

    Columns that already fit within their fair share keep their natural width;
    the space they leave over is redistributed to the wider columns.
    """

    if sum(natural) <= available:
        return natural

    widths = [0] * len(natural)
    pending = list(range(len(natural)))
    remaining = available

    while pending:
        fair = remaining // len(pending)
        settled = [c for c in pending if natural[c] <= fair]
        if not settled:
            break
        for c in settled:
            widths[c] = natural[c]
            remaining -= natural[c]
            pending.remove(c)

    if pending:
        share, extra = divmod(remaining, len(pending))
        for n, c in enumerate(pending):
            widths[c] = share + (1 if n < extra else 0)

    return [max(min(min_width, n), w) for n, w in zip(natural, widths, strict=False)]
