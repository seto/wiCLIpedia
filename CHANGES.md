# Changelog

> **Note:** entries from 0.1.0 (initial release) to 0.2.4 were reconstructed from the
> commit history and may not be 100% accurate.

## Version 0.2.4 - 2026-08-22

### Added

- Added `langx` to `TEMPLATES_KEEP_LAST`, so `{{langx|...}}` templates render their last
  parameter like the existing `{{lang}}`/`{{langue}}` templates instead of being
  stripped entirely.

### Changed

- Extracted every language-specific template table (`TEMPLATES_KEEP_LAST`,
  `TEMPLATES_KEEP_FIRST`, `BLOCKQUOTE_TEMPLATES`, `POEMQUOTE_TEMPLATES`,
  `TEMPLATES_STATIC`) out of the lexer and into a dedicated
  `parsing/languages/templates.py` module, so wikitext knowledge lives apart from the
  tokenizing logic that consumes it.

### Fixed

- Fixed section text rendering leaking raw HTML comments (`<!-- ... -->`) into the
  output; these are now stripped before tokenizing, matching how `<gallery>` blocks were
  already dropped.
- Fixed `<gallery>...</gallery>` markup (and its file-listing content) surfacing as
  garbled text instead of being removed outright.

## Version 0.2.3 - 2026-08-08

### Added

- Added support for `{{poem quote}}`/`{{poemquote}}` templates: poem text is now
  captured as its own `TokenType.POEM` token and rendered with preserved line breaks and
  indentation, the same way `BLOCKQUOTE` templates already were.

### Changed

- Improved exception handling in `cache.py`: `load`/`save`/`prune` now only swallow the
  specific `sqlite3.DatabaseError`/`json.JSONDecodeError` cases they expect, instead of
  catching broad exceptions that could mask real bugs.
- Enforced strict type annotations for `cached_at`, closing a gap where the cache
  timestamp could silently be treated as `Any`.

### Fixed

- Fixed blockquote text getting truncated whenever it contained a wikilink, since the
  lexer's blockquote extraction stopped at the first `]]` instead of the template's
  closing `}}`.
- Fixed template parameters leaking into rendered text when a template was stripped but
  its raw parameter markup wasn't fully consumed.

## Version 0.2.2 - 2026-07-26

### Added

- Added support for parsing definition list terms (`;term`) in wikitext sections,
  alongside the existing bullet and numbered list handling.
- Added the `portal inline` template to `TEMPLATES_KEEP_LAST`, so `{{portal inline}}`
  renders its label instead of being dropped.

### Changed

- Improved table parsing and rendering, refining how `parse_table` builds `ParsedTable`
  rows ahead of the `rowspan` support that landed here.

### Fixed

- Fixed empty bullets being left behind in list items whenever a template inside them
  was stripped down to nothing.

## Version 0.2.1 - 2026-07-20

### Fixed

- Fixed a relative-link regression that slipped back in right after the 0.2.0 fix; this
  time for good.

## Version 0.2.0 - 2026-07-20

### Features

- Implemented a wikitext table parser (`parsing/table.py`): raw `{|...|}` blocks are now
  converted into a structured `ParsedTable` of `TableCell` rows, with `rowspan` values
  inherited into subsequent rows at the correct column position. `colspan` is parsed but
  not merged; cells using it render as-is in their own column.
- Wired table parsing into `parse_section`, and added a dedicated renderer so tables
  show up as formatted output rather than raw wikitext.
- Added support for extracting the title/year out of `{{citation}}` templates instead of
  dropping the whole reference.

### Fixed

- Fixed unhandled external links (`[url text]`) leaking into section text unparsed.
- Fixed a broken relative link.

## Version 0.1.5 - 2026-07-08

### Changed

- Enhanced overall CLI UX around prompts and invalid-input handling.

## Version 0.1.4 - 2026-07-07

### Changed

- Enhanced prompts rendering.

## Version 0.1.3 - 2026-07-06

### Added

- Added logic to reprint the table of contents without re-fetching it, so users can
  review it again after viewing a section.

### Changed

- Enhanced prompt messages printing.

## Version 0.1.2 - 2026-06-13

### Fixed

- Fixed the disambiguation parser to correctly extract page titles and descriptions,
  which were previously mismatched in some cases.

## Version 0.1.1 - 2026-06-12

### Changed

- Refactored disambiguation rendering to wrap long content instead of overflowing the
  terminal width.
- Refactored table of contents logic to handle invalid input without crashing the
  session.

## Version 0.1.0 - 2026-06-03

Initial release. Enjoy exploring Wikipedia from your terminal!

### Features

- A stateless Wikipedia API transport layer (`core/client.py`) handles all calls to the
  MediaWiki API.
- Page summaries, disambiguation pages, and tables of contents can be fetched and parsed
  into structured data, each with its own parser.
- A page section parser extracts individual sections, with dedicated renderers for
  tables of contents and summaries.
- Parsing is built around a wikitext lexer and AST-based pipeline (`parsing/lexer.py`,
  `parsing/nodes.py`, `parsing/parser.py`).
- Redirects are followed automatically, and disambiguation pages let users pick the
  right target from the CLI.
- An interactive search navigation loop lets users jump between pages and sections
  without restarting `wicli`.
- A sqlite-backed local cache (`core/cache.py`) stores API responses for 72 hours, with
  `--no-cache` and `--purge` CLI flags and automatic pruning of stale entries.
- Colored output is automatically disabled when the `NO_COLOR` environment variable is
  set, following the [no-color.org](https://no-color.org) convention, or when stdout
  isn't a TTY.
