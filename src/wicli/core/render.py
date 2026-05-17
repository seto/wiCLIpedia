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

"""Module implementing the rendering of Wikipedia content for the CLI.

This module provides functions to format and style the output of Wikipedia content
for display in the command line interface.

It includes rendering of page summaries, table of contents, sections,
disambiguation options, and user prompts and navigation.
"""

import os
import textwrap

# ANSI escape codes to style terminal output
_ITALIC = "\033[3m"
_BOLD = "\033[1m"
_INFO = "\033[34m"
_WARNING = "\033[33m"
_SUCCESS = "\033[32m"
_ERROR = "\033[31m"
_RESET = "\033[0m"


def render_summary(page_title: str, summary: str) -> str:
    wrapped = textwrap.fill(summary, width=_get_width())

    output = f"""
{_render_content_banner()}

{_BOLD}{page_title}{_RESET}

{_ITALIC}{wrapped}{_RESET}
"""

    return output


def render_toc(sections: list) -> str:
    toc = []
    for section in sections:
        indent = "  " * (section["tocLevel"] - 1)
        num = f"{section['number']}." if section["tocLevel"] == 1 else section["number"]
        num_padded = f"{num:<5}"
        line = f"{indent}{_BOLD}{num_padded}{_RESET} {section['line']}"
        toc.append(line)

    toc_str = "\n".join(toc)

    output = f"""
{_render_content_banner()}

{_BOLD}Available content for this page:{_RESET}

{toc_str}
"""

    return output


def render_toc_prompt() -> str:
    return f"{_INFO}Do you want to see the table of contents? (y/n): {_RESET}"


def render_toc_skip() -> str:
    return f"{_WARNING}Invalid choice. Skipping table of contents.{_RESET}"


def render_toc_navigation_prompt() -> str:
    return f"{_INFO}Enter the section number, or 'q' to exit: {_RESET}"


def render_section(title: str, section: str) -> str:
    wrapped = textwrap.fill(section, width=_get_width())

    output = f"""
{_render_content_banner()}

{_BOLD}{title}{_RESET}

{_ITALIC}{wrapped}{_RESET}
"""

    return output


def render_disambiguation(options: list) -> str:
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
{_render_content_banner()}

{_BOLD}This page is a disambiguation for the following options:{_RESET}

{links_str}
"""

    return output


def render_disambiguation_prompt() -> str:
    return f"{_INFO}Enter the page number, or 'q' to exit: {_RESET}"


def render_invalid_choice() -> str:
    return f"{_WARNING}Invalid choice. Enter a valid number or 'q' to exit: {_RESET}"


def render_redirect(page: str) -> str:
    return f"\n{_INFO}{_BOLD}Redirected to '{page}'.{_RESET}"


def render_not_found(page: str, lang: str) -> str:
    return f"{_ERROR}Page '{page}' not found in {lang} Wikipedia.{_RESET}"


def render_exit() -> str:
    return f"{_SUCCESS}{_BOLD}Goodbye!{_RESET}"


def _get_width() -> int:
    try:
        column = os.get_terminal_size().columns
    except OSError:
        column = 88

    width = min(column, 88)
    return width


def _render_content_banner() -> str:
    width = _get_width()
    separator = "─" * width

    banner = f"""{separator}\n© Wikipedia contributors | CC BY-SA 4.0\n{separator}"""

    return banner
