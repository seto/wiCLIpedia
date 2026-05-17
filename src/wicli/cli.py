#!/usr/bin/env python3

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

import argparse
import sys

from .core import client, parser, render


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    ap = argparse.ArgumentParser(prog="wicli", description="WiCLIpedia CLI")
    ap.add_argument("title", help="page title")
    ap.add_argument("-l", "--lang", default="en", help="language code (default: en)")

    args = ap.parse_args(argv)
    target_page = args.title

    try:
        while True:
            api_props = client.fetch_props(target_page, lang=args.lang)
            props = parser.parse_props(api_props)

            if props["status"] == "redirect":
                target_page = props.get("redirects")
                print(render.render_redirect(target_page))
                continue

            if props["status"] == "found":
                api_summary = client.fetch_summary(target_page, lang=args.lang)
                summary = parser.parse_summary(api_summary)

                if not summary.get("summary"):
                    raise RuntimeError("Summary not found for the given page.")

                print(render.render_summary(target_page, summary.get("summary")))
                print(render.render_toc_prompt(), end="")

                choice = input().strip().lower()
                if choice == "y":
                    raw_toc = client.fetch_toc(target_page, lang=args.lang)
                    parsed_tocdata = parser.parse_toc(raw_toc)

                    if not parsed_tocdata.get("sections"):
                        raise RuntimeError(
                            "Table of contents not found for the given page."
                        )

                    print(render.render_toc(parsed_tocdata.get("sections")))
                    print(render.render_toc_navigation_prompt(), end="")

                    toc_map = {
                        s["number"]: {"index": s["index"], "line": s["line"]}
                        for s in parsed_tocdata["sections"]
                    }
                    while True:
                        section_choice = input().strip()

                        if section_choice == "0":
                            print("Exiting.")
                            return 0

                        if section_choice in toc_map:
                            section_index = toc_map[section_choice]["index"]
                            section_title = toc_map[section_choice]["line"]
                            api_section = client.fetch_section(
                                target_page, section_index, lang=args.lang
                            )
                            section = parser.parse_section(api_section)

                            if not section.get("section"):
                                raise RuntimeError(
                                    "Content not found for the given section."
                                )

                            print(
                                render.render_section(
                                    title=section_title, section=section.get("section")
                                )
                            )
                            print(render.render_toc_navigation_prompt(), end="")
                            continue

                        print(render.render_invalid_choice(), end="")

                elif choice != "n":
                    print(render.render_toc_skip())

                break

            if props["status"] == "disambiguation":
                api_disambiguation = client.fetch_disambiguation(target_page, lang=args.lang)
                disambiguation = parser.parse_disambiguation(api_disambiguation)

                if not disambiguation.get("options"):
                    raise RuntimeError("Disambiguation options not found for the given page.")

                print(render.render_disambiguation(disambiguation.get("options")))
                print(render.render_disambiguation_prompt(), end="")

                while True:
                    choice = input().strip()

                    if choice == "0":
                        print("Exiting.")
                        return 0

                    if choice.isdigit() and (1 <= int(choice) <= len(disambiguation["options"])):
                        target_page = disambiguation["options"][int(choice) - 1]["page"]
                        break

                    print(render.render_invalid_choice(), end="")

                continue

            if props["status"] in ("missing", "unknown"):
                print(render.render_not_found(target_page, args.lang), file=sys.stderr)
                return 1

            else:
                raise RuntimeError(f"Unexpected page status: {props['status']}")

    except RuntimeError as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
