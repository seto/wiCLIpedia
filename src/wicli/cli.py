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

"""Module implementing the command line entry point of WiCLIpedia.

This module can be executed from the command line using the following command
from the `src` directory:

    python -m wicli [page] [-l LANG]

CLI arguments:
- `page`: The Wikipedia page title to retrieve (optional, prompted if not provided).
- `-l` or `--lang`: The language code of the Wikipedia to query (defaults to "en").

For more details, run with `-h` or `--help`.
"""

import argparse
import sys

from .core import client, parser, render


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    ap = argparse.ArgumentParser(prog="wicli", description="WiCLIpedia CLI")
    ap.add_argument("page", nargs="?", default=None, help="page title")
    ap.add_argument("-l", "--lang", default="en", help="language code (default: en)")

    args = ap.parse_args(argv)
    target = args.page
    choice = None

    print(render.render_welcome())

    try:
        # Main loop to handle redirects, section navigation, and disambiguation choices,
        # until a page and its content is successfully retrieved or the user exits
        while True:
            if choice and choice.lower() == ":q":
                break

            if not target:
                print(render.render_start_prompt(), end="")
                choice = input().strip()

                if choice.lower() == ":q":
                    break

                if not choice or choice.lower() == ":b":
                    continue

                target = choice
                continue

            api_props = client.fetch_props(target, lang=args.lang)
            props = parser.parse_props(api_props)

            if props["status"] in ("missing", "unknown"):
                # Fallback: retry with title case to handle all-caps or mixed-case input
                # e.g. "NINE INCH NAILS" -> "Nine Inch Nails"
                if target != target.title():
                    api_props = client.fetch_props(target.title(), lang=args.lang)
                    props = parser.parse_props(api_props)

                    if props["status"] in ("missing", "unknown"):
                        print(render.render_not_found(target, args.lang))
                        target = None
                        continue

                    print(render.render_title_fallback(target, target.title()))
                    target = target.title()

                else:
                    print(render.render_not_found(target, args.lang))
                    target = None
                    continue

            if props["status"] == "redirect":
                target = props.get("target")
                print(render.render_redirect(target))
                continue

            if props["status"] == "found":
                api_summary = client.fetch_summary(target, lang=args.lang)
                summary = parser.parse_summary(api_summary)

                if not summary.get("summary"):
                    print(render.render_summary_not_found(target))
                    target = None
                    continue

                print(render.render_summary(target, summary.get("summary")))
                print(render.render_toc_prompt(), end="")

                choice = input().strip()
                if choice.lower() == "y":
                    raw_toc = client.fetch_toc(target, lang=args.lang)
                    parsed_tocdata = parser.parse_toc(raw_toc)

                    if not parsed_tocdata.get("sections"):
                        print(render.render_toc_not_found())
                        target = None
                        continue

                    print(render.render_toc(parsed_tocdata.get("sections")))

                    toc_map = {
                        s["number"]: {"index": s["index"], "line": s["line"]}
                        for s in parsed_tocdata["sections"]
                    }
                    while True:
                        print(render.render_toc_navigation_prompt(), end="")
                        choice = input().strip()

                        if choice.lower() == ":q":
                            break

                        if choice.lower() == ":b":
                            target = None
                            break

                        if choice in toc_map:
                            index = toc_map[choice]["index"]
                            title = toc_map[choice]["line"]
                            api_section = client.fetch_section(
                                target, index, lang=args.lang
                            )
                            section = parser.parse_section(api_section)

                            if not section.get("section"):
                                print(render.render_section_not_found(title))
                                continue

                            print(render.render_section(title, section.get("section")))
                            continue

                        print(render.render_invalid_choice())

                elif choice.lower() not in (":b", ":q", "n"):
                    print(render.render_toc_skip())

                target = None
                continue

            if props["status"] == "disambiguation":
                api_disambiguation = client.fetch_disambiguation(target, lang=args.lang)
                disambiguation = parser.parse_disambiguation(api_disambiguation)

                print(render.render_disambiguation_redirect(target))

                if not disambiguation.get("options"):
                    print(render.render_disambiguation_not_found(target))
                    target = None
                    continue

                print(render.render_disambiguation(disambiguation.get("options")))

                disambiguation_map = {
                    str(i + 1): option["page"]
                    for i, option in enumerate(disambiguation["options"])
                }
                while True:
                    print(render.render_disambiguation_prompt(), end="")
                    choice = input().strip()

                    if choice.lower() == ":q":
                        break

                    if choice.lower() == ":b":
                        target = None
                        break

                    if choice in disambiguation_map:
                        target = disambiguation_map[choice]
                        break

                    print(render.render_invalid_choice())

                continue

            else:
                raise RuntimeError(f"Unexpected page status: {props['status']}")

    except RuntimeError as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    except KeyboardInterrupt:
        print(render.render_user_cancelled())

    print(render.render_exit())
    return 0


if __name__ == "__main__":
    sys.exit(main())
