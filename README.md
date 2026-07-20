<h1 align="center">WiCLIpedia</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0+-blue.svg" alt="License: AGPL-3.0-or-later"></a>
  <a href="https://pypi.org/project/wiclipedia/"><img src="https://img.shields.io/pypi/v/wiclipedia.svg?maxAge=86400&color=blue" alt="Version"></a>
  <a href="https://pypi.org/project/wiclipedia"><img src="https://img.shields.io/pypi/pyversions/wiclipedia.svg" alt="Supported Versions"></a>
  <a href="https://github.com/seto/wiCLIpedia/actions"><img src="https://img.shields.io/github/actions/workflow/status/seto/wiCLIpedia/tests.yml?label=tests&logo=github" alt="Tests"></a>
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code_style-black-000000.svg" alt="Code Style: Black"></a>
</p>

This is a minimalist command line interface (CLI) program to fetch and display data from
Wikipedia.

_In an era where Artificial Intelligence answers everything and large language models
shape our knowledge, this program is a small tribute to Wikipedia, the silent,
human-curated backbone that feeds those very models. Never forget the source._

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/51b51758-e340-4d1c-8255-5c784cd8f8c4" width="600" alt="Demo">
</p>

---

## Features

- Fetches and displays article summaries and table of contents
- Navigates article sections interactively
- Handles redirects and disambiguation pages automatically
- Supports multiple Wikipedia languages
- Caches responses locally to minimize API calls
- ANSI colors and styles for enhanced readability (can be disabled)

## Installation

```bash
pip install wiclipedia
```

## Usage

```bash
wicli "Blade Runner"
```

If no page title is provided, the program will prompt you to enter one interactively.

You will be interactively prompted to navigate through the article summary sections.  
To navigate, use the section numbers shown in the table of contents.

If the query matches a disambiguation page, you will be prompted to select the intended
article from a list of options.

By default, it fetches the English Wikipedia.  
To specify a different language, use the `-l` or `--lang` option:

```bash
wicli "La classe operaia va in paradiso" --lang it
```

Available commands during navigation:

- `:b` — Go back to the start prompt
- `:q` — Exit the program
- `:m` — Show the table of contents menu (only available when navigating sections)

## Options

| Option         | Description                                          |
| -------------- | ---------------------------------------------------- |
| `page`         | Wikipedia page title (optional, prompted if omitted) |
| `-l`, `--lang` | Language code (default: `en`)                        |
| `--no-cache`   | Disable local cache for the session                  |
| `--purge`      | Purge local cache and exit                           |

## Cache

Responses are cached locally for 72 hours to reduce API calls.  
The cache is stored in `~/.cache/wiclipedia/`.  
Use `--no-cache` to bypass it for a session, or `--purge` to clear it entirely.

## Display

ANSI colors and styles are enabled by default.  
Set the `NO_COLOR` environment variable to disable them (see
[no-color.org](https://no-color.org)).

## API Respect and Fair Use Disclaimer

WiCLIpedia interfaces directly with the official Wikipedia PHP/MediaWiki APIs without
using any third-party scraping libraries.  
Please use this program responsibly. If you need to perform massive automated data
extraction, use official database dumps instead of hammering the live API.

WiCLIpedia caches responses locally for 72 hours by default to minimize API load. Check
the [Cache](#cache) section for details.

More information about the MediaWiki API and usage guidelines:

- [API Documentation](https://www.mediawiki.org/wiki/API:Main_page)
- [API Etiquette](https://www.mediawiki.org/wiki/API:Etiquette)

## License

This program is licensed under the
[GNU Affero General Public License v3.0 or later](https://www.gnu.org/licenses/agpl-3.0.html)
(AGPL-3.0+).  
See the [LICENSE](https://github.com/seto/wiCLIpedia/blob/master/LICENSE) file for
details.
