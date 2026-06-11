#!/usr/bin/env python3

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

"""Module implementing the command line entry point of WiCLIpedia.

This module can be executed from the command line using the following command
from the `src` directory:

    python -m wicli [page] [-l LANG]

CLI arguments:
- `page`: The Wikipedia page title to retrieve (optional, prompted if not provided).
- `-l` or `--lang`: The language code of the Wikipedia to query (defaults to "en").
- `--no-cache`: Disable local cache storage for the session (force fresh API calls).

For more details, run with `-h` or `--help`.
"""

import argparse
import sys

from .core import cache, client, render
from .core.exceptions import WicliAPIError, WicliNetworkError
from .parsing import parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    ap = argparse.ArgumentParser(prog="wicli", description="WiCLIpedia CLI")
    ap.add_argument("page", nargs="?", default=None, help="page title")
    ap.add_argument("-l", "--lang", default="en", help="language code (default: en)")
    ap.add_argument("--no-cache", action="store_true", help="disable local cache")
    ap.add_argument("--purge", action="store_true", help="purge local cache and exit")

    args = ap.parse_args(argv)

    if args.purge:
        rows = cache.purge()
        print(render.render_cache_purged(rows))
        return 0

    if args.no_cache:
        client.disable_cache()
    else:
        cache.prune()

    target = args.page
    choice = None

    print(render.render_welcome())

    try:
        # Main command-line loop (REPL)
        # State driving:
        # - If `target` is None: prompt the user for a new search page
        # - If `target` is set: resolve the page title and dispatch to the
        #   corresponding handler based on its status (found, redirect, disambiguation)
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

            resolved = _resolve_page(target, args.lang)
            if resolved is None:
                print(render.render_not_found(target, args.lang))
                target = None
                continue
            target, props = resolved

            if props["status"] == "redirect":
                target = props.get("target")
                print(render.render_redirect(target))
                continue

            if props["status"] == "found":
                api_summary = client.fetch_summary(target, lang=args.lang)
                summary = parser.parse_summary(api_summary)

                if not summary.get("paragraphs"):
                    print(render.render_summary_not_found(target))
                    target = None
                    continue

                print(
                    render.render_summary(
                        target,
                        summary.get("paragraphs"),
                        cached_at=summary.get("_cached_at"),
                    )
                )

                # TOC prompt loop: Keeps asking until a valid choice (y/n)
                # or a navigation command (:b/:q) is entered
                while True:
                    print(render.render_toc_prompt(), end="")
                    choice = input().strip()

                    if choice.lower() in ("n", ":b", ":q"):
                        break

                    if choice.lower() == "y":
                        raw_toc = client.fetch_toc(target, lang=args.lang)
                        parsed_tocdata = parser.parse_toc(raw_toc)

                        if not parsed_tocdata.get("sections"):
                            print(render.render_toc_not_found())
                            target = None
                            continue

                        print(
                            render.render_toc(
                                parsed_tocdata.get("sections"),
                                cached_at=parsed_tocdata.get("_cached_at"),
                            )
                        )

                        toc_map = {
                            s["number"]: {"index": s["index"], "line": s["line"]}
                            for s in parsed_tocdata["sections"]
                        }

                        # Section navigation loop: Allows the user to repeatedly
                        # view different sections of the current page until exiting
                        while True:
                            print(render.render_toc_navigation_prompt(), end="")
                            choice = input().strip()

                            if choice.lower() in (":b", ":q"):
                                break

                            if choice in toc_map:
                                index = toc_map[choice]["index"]
                                title = toc_map[choice]["line"]
                                api_section = client.fetch_section(
                                    target, section=index, lang=args.lang
                                )
                                section = parser.parse_section(api_section)

                                if not section.get("section"):
                                    print(render.render_section_not_found(title))
                                    continue

                                print(
                                    render.render_section(
                                        title,
                                        section.get("section"),
                                        cached_at=section.get("_cached_at"),
                                    )
                                )
                                continue

                            print(render.render_invalid_choice())

                        break

                    print(render.render_invalid_choice())

                if choice.lower() == ":q":
                    break

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

                print(
                    render.render_disambiguation(
                        disambiguation.get("options"),
                        cached_at=disambiguation.get("_cached_at"),
                    )
                )

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

    except WicliAPIError as e:
        print(f"API error: {e}", file=sys.stderr)
        return 1

    except WicliNetworkError as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    except EOFError:
        print(render.render_user_cancelled())

    except KeyboardInterrupt:
        print(render.render_user_cancelled())

    print(render.render_exit())
    return 0


def _resolve_page(page: str, lang: str) -> tuple[str, dict] | None:
    for candidate in _candidates(page):
        api_props = client.fetch_props(candidate, lang=lang)
        props = parser.parse_props(api_props)

        if props["status"] not in ("missing", "unknown"):
            if page != candidate:
                print(render.render_title_fallback(page, candidate))
            return candidate, props

    return None


def _candidates(page: str) -> list[str]:
    # Normalizations to try when the page title is not found
    # to handle all-caps or mixed-case input
    seen = {page}
    result = [page]

    for normalized in (page.title(), page.capitalize()):
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


if __name__ == "__main__":
    sys.exit(main())
