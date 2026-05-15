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

    try:
        response = fetch_props(args.title, lang=args.lang)
        parsed_response = parse_props(response)

        if parsed_response["status"] == "found":
            raw_summary = fetch_summary(args.title, lang=args.lang)
            parsed_summary = parse_summary(raw_summary)

            if not parsed_summary.get("summary"):
                raise RuntimeError("Summary not found for the given page.")

            print(render_summary(args.title, parsed_summary.get("summary")))

        elif parsed_response["status"] == "disambiguation":
            raw_disambiguation = fetch_disambiguation(args.title, lang=args.lang)
            parsed_disambiguation = parse_disambiguation(raw_disambiguation)

            if not parsed_disambiguation.get("options"):
                raise RuntimeError("Disambiguation options not found for the given page.")

            print(render_disambiguation(parsed_disambiguation.get("options")))

        elif (
            parsed_response["status"] == "missing"
            or parsed_response["status"] == "unknown"
        ):
            print(
                f"Page '{args.title}' not found in {args.lang} Wikipedia.",
                file=sys.stderr,
            )
            return 1

    except RuntimeError as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
