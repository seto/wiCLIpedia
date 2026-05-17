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

import os
import textwrap

ITALIC = "\033[3m"
BOLD = "\033[1m"
INFO = "\033[34m"
ERROR = "\033[31m"
RESET = "\033[0m"


def render_summary(page_title: str, summary: str) -> str:
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = 88

    width = min(columns, 88)
    wrapped = textwrap.fill(summary, width=width)

    output = f"""
─────────────────────────────────────────────
   © Wikipedia contributors | CC BY-SA 4.0
─────────────────────────────────────────────

{BOLD}{page_title}{RESET}

{ITALIC}{wrapped}{RESET}
"""

    return output


def render_toc(sections: list) -> str:
    toc = []
    for section in sections:
        indent = "  " * (section["tocLevel"] - 1)
        num = f"{section['number']}." if section["tocLevel"] == 1 else section["number"]
        num_padded = f"{num:<5}"
        line = f"{indent}{BOLD}{num_padded}{RESET} {section['line']}"
        toc.append(line)

    toc_str = "\n".join(toc)

    output = f"""
─────────────────────────────────────────────
   © Wikipedia contributors | CC BY-SA 4.0
─────────────────────────────────────────────

{BOLD}Available content for this page:{RESET}

{toc_str}
"""

    return output


def render_toc_prompt() -> str:
    return "Do you want to see the table of contents? (y/n): "


def render_toc_skip() -> str:
    return f"{ERROR}{BOLD}Invalid choice. Skipping table of contents.{RESET}"


def render_toc_navigation_prompt() -> str:
    return "Enter the section number that you want to view, or '0' to exit: "


def render_section(title: str, section: str) -> str:
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = 88

    width = min(columns, 88)
    wrapped = textwrap.fill(section, width=width)

    output = f"""
─────────────────────────────────────────────
   © Wikipedia contributors | CC BY-SA 4.0
─────────────────────────────────────────────

{BOLD}{title}{RESET}

{ITALIC}{wrapped}{RESET}
"""

    return output


def render_disambiguation(options: list) -> str:
    links = []
    for i, option in enumerate(options, start=1):
        entry = (
            f"{ITALIC}{option['page']}{RESET} - {option['desc']}"
            if option["desc"]
            else f"{ITALIC}{option['page']}{RESET}"
        )
        links.append(f"{i}. {entry}")

    links_str = "\n".join(links)

    output = f"""
─────────────────────────────────────────────
   © Wikipedia contributors | CC BY-SA 4.0
─────────────────────────────────────────────

{BOLD}This page is a disambiguation for the following options:{RESET}

{links_str}
"""

    return output


def render_disambiguation_prompt() -> str:
    return "Enter the number of the page you want to view: "


def render_invalid_choice() -> str:
    return f"{ERROR}{BOLD}Invalid choice. Enter a valid number or '0' to exit: {RESET}"


def render_redirect(page: str) -> str:
    return f"\n{INFO}{BOLD}Redirected to '{page}'.{RESET}"


def render_not_found(page: str, lang: str) -> str:
    return f"{ERROR}{BOLD}Page '{page}' not found in {lang} Wikipedia.{RESET}"
