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

from .core.client import fetch_disambiguation, fetch_props, fetch_summary
from .core.parser import parse_disambiguation, parse_props, parse_summary
from .core.render import render_disambiguation, render_summary


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(prog="wcli", description="WiCLIpedia CLI")
    parser.add_argument("title", help="page title")
    parser.add_argument("-l", "--lang", default="en", help="language code (default: en)")

    args = parser.parse_args(argv)
    target_page = args.title

    try:
        while True:
            api_props = fetch_props(target_page, lang=args.lang)
            props = parse_props(api_props)

            if props.get("redirects"):
                target_page = props.get("redirects")
                print(f"\nRedirected to '{target_page}'.")

            if props["status"] == "found":
                api_summary = fetch_summary(target_page, lang=args.lang)
                summary = parse_summary(api_summary)

                if not summary.get("summary"):
                    raise RuntimeError("Summary not found for the given page.")

                print(render_summary(target_page, summary.get("summary")))
                break

            elif props["status"] == "disambiguation":
                api_disambiguation = fetch_disambiguation(target_page, lang=args.lang)
                disambiguation = parse_disambiguation(api_disambiguation)

                if not disambiguation.get("options"):
                    raise RuntimeError("Disambiguation options not found for the given page.")

                print(render_disambiguation(disambiguation.get("options")))
                print("Enter the number of the page you want to view: ", end="")

                while True:
                    choice = input().strip()

                    if int(choice) == 0:
                        print("Exiting.")
                        return 0

                    if choice.isdigit() and (1 <= int(choice) <= len(disambiguation["options"])):
                        target_page = disambiguation["options"][int(choice) - 1]["page"]
                        break

                    print("Invalid choice. Enter a valid number or '0' to exit: ", end="")
                    continue

            elif props["status"] == "missing" or props["status"] == "unknown":
                print(
                    f"Page '{target_page}' not found in {args.lang} Wikipedia.",
                    file=sys.stderr,
                )
                return 1

    except RuntimeError as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
