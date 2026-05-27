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

_NO_COLOR = (
    os.environ.get("NO_COLOR") is not None
    or not hasattr(sys.stdout, "isatty")
    or not sys.stdout.isatty()
    or os.environ.get("TERM") == "dumb"
)

_RESET = "" if _NO_COLOR else "\033[0m"
_BOLD = "" if _NO_COLOR else "\033[1m"
_DIM = "" if _NO_COLOR else "\033[2m"
_ITALIC = "" if _NO_COLOR else "\033[3m"
_RED = "" if _NO_COLOR else "\033[31m"
_YELLOW = "" if _NO_COLOR else "\033[33m"
_GREEN = "" if _NO_COLOR else "\033[32m"
_BLUE = "" if _NO_COLOR else "\033[34m"
_PURPLE = "" if _NO_COLOR else "\033[35m"
_CYAN = "" if _NO_COLOR else "\033[36m"


def render_welcome() -> str:
    width = _get_width()
    separator = "─" * width

    logo = rf"""{_PURPLE}{_BOLD}{separator}
                               _ ________    ____               ___      
                     _      __(_) ____/ /   /  _/___  ___  ____/ (_)___ _
                    | | /| / / / /   / /    / // __ \/ _ \/ __  / / __ `/
                    | |/ |/ / / /___/ /____/ // /_/ /  __/ /_/ / / /_/ / 
                    |__/|__/_/\____/_____/___/ .___/\___/\__,_/_/\__,_/  
                                            /_/                                               
{separator}{_RESET}"""

    message = f"""
{logo if width >= 72 else ""}

{_BOLD}Welcome to WiCLIpedia! Your command-line gateway to Wikipedia content.{_RESET}

To get started, enter a Wikipedia page title when prompted.
You can specify the language at startup using -l or --lang (e.g., wicli --lang it).

User navigation:
    :b - Go back to the start prompt
    :q - Quit the application

{_ITALIC}Enjoy exploring Wikipedia from your terminal!{_RESET}

{separator}
"""

    return message


def render_cache_purged(rows: int) -> str:
    if rows == 0:
        return f"{_BLUE}{_BOLD}Cache is already empty. No entries to purge.{_RESET}"
    elif rows == 1:
        return f"{_GREEN}{_BOLD}Cache purged successfully. 1 entry removed.{_RESET}"

    return f"{_GREEN}{_BOLD}Cache purged successfully. {rows} entries removed.{_RESET}"


def render_start_prompt() -> str:
    return f"{_CYAN}Enter a page title: {_RESET}"


def render_redirect(page: str) -> str:
    return f"{_BLUE}{_BOLD}Redirected to '{page}'.{_RESET}"


def render_title_fallback(original: str, fallback: str) -> str:
    return f"{_BLUE}{_BOLD}Page '{original}' not found. Trying '{fallback}'.{_RESET}"


def render_not_found(page: str, lang: str) -> str:
    return f"{_YELLOW}{_BOLD}Page '{page}' not found in {lang} Wikipedia.{_RESET}"


def render_invalid_choice() -> str:
    return f"{_YELLOW}Invalid choice. Enter a valid number.{_RESET}"


def render_user_cancelled() -> str:
    return f"{_YELLOW}WiCLIpedia stopped by user.{_RESET}"


def render_exit() -> str:
    return f"{_GREEN}{_BOLD}Goodbye!{_RESET}"


def render_summary(title: str, summary: str, cached_at: float = None) -> str:
    wrapped = textwrap.fill(summary, width=_get_width())

    output = f"""
{_render_content_banner(cached_at)}

{_BOLD}{title}{_RESET}

{_ITALIC}{wrapped}{_RESET}
"""

    return output


def render_summary_not_found(title: str) -> str:
    return f"{_YELLOW}Summary not found for page '{title}'.{_RESET}"


def render_toc(sections: list, cached_at: float = None) -> str:
    toc = []
    for section in sections:
        indent = "  " * (section["tocLevel"] - 1)
        num = f"{section['number']}." if section["tocLevel"] == 1 else section["number"]
        num_padded = f"{num:<5}"
        line = f"{indent}{_BOLD}{num_padded}{_RESET} {section['line']}"
        toc.append(line)

    toc_str = "\n".join(toc)

    output = f"""
{_render_content_banner(cached_at)}

{_BOLD}Available content for this page:{_RESET}

{toc_str}
"""

    return output


def render_toc_prompt() -> str:
    return f"{_CYAN}Do you want to see the table of contents? (y/n): {_RESET}"


def render_toc_skip() -> str:
    return f"{_YELLOW}Invalid choice. Skipping table of contents.{_RESET}"


def render_toc_navigation_prompt() -> str:
    return f"{_CYAN}Enter the section number: {_RESET}"


def render_toc_not_found() -> str:
    return f"{_YELLOW}Table of contents not found for this page.{_RESET}"


def render_section(title: str, section: str, cached_at: float = None) -> str:
    wrapped = textwrap.fill(section, width=_get_width())

    output = f"""
{_render_content_banner(cached_at)}

{_BOLD}{title}{_RESET}

{_ITALIC}{wrapped}{_RESET}
"""

    return output


def render_section_not_found(title: str) -> str:
    return f"{_YELLOW}Content not found for section '{title}'.{_RESET}"


def render_disambiguation(options: list, cached_at: float = None) -> str:
    links = []
    for i, option in enumerate(options, start=1):
        entry = (
            f"{_ITALIC}{option['page']}{_RESET} - {option['desc']}"
            if option["desc"]
            else f"{_ITALIC}{option['page']}{_RESET}"
        )
        links.append(f"{i}. {entry}")

    links_str = "\n".join(links)

    output = f"""
{_render_content_banner(cached_at)}

{_BOLD}This page is a disambiguation for the following options:{_RESET}

{links_str}
"""

    return output


def render_disambiguation_redirect(page: str) -> str:
    return f"{_BLUE}{_BOLD}Redirected to '{page} (disambiguation page)'.{_RESET}"


def render_disambiguation_prompt() -> str:
    return f"{_CYAN}Enter the page number: {_RESET}"


def render_disambiguation_not_found(page: str) -> str:
    return f"{_YELLOW}Disambiguation options not found for page '{page}'.{_RESET}"


def _get_width() -> int:
    try:
        column = os.get_terminal_size().columns
    except OSError:
        column = 88

    width = min(column, 88)
    return width


def _render_content_banner(cached_at: float) -> str:
    width = _get_width()
    separator = "─" * width

    attribution = "© Wikipedia contributors ─ Content licensed under CC BY-SA 4.0"

    if cached_at:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(cached_at)))
        fetch = f"Loaded from cache (as of {ts})."
    else:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        fetch = f"Fetched from Wikipedia live (at {ts})."

    banner = f"""{_DIM}{separator}
{_BOLD}{attribution.center(width)}{_RESET}
{_DIM}{_ITALIC}{fetch.center(width)}{_RESET}
{_DIM}{separator}{_RESET}"""

    return banner
