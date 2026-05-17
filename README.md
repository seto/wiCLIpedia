# WiCLIpedia

[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0+-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/wiclipedia.svg?maxAge=86400)](https://pypi.org/project/wiclipedia/)
[![Supported Versions](https://img.shields.io/pypi/pyversions/wiclipedia.svg)](https://pypi.org/project/wiclipedia)
[![Code Style: Black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)

This is a minimalistic command line interface (CLI) tool to fetch and display data from Wikipedia.

_In an era where Artificial Intelligence answers everything and large language models shape our knowledge, this program is a small tribute to Wikipedia, the silent, human-curated backbone that feeds those very models. Never forget the source._

## Installation

```bash
pip install wiclipedia
```

## Usage

```bash
wicli "Blade Runner"
```

User will be interactively prompted to navigate through the article's sections and subsections, or select a different page if the query is ambiguous.

By default, it fetches the English Wikipedia.  
To specify a different language, use the `-l` or `--lang` option:

```bash
wicli "La classe operaia va in paradiso" --lang it
```

## API Respect & Fair Use Disclaimer

WiCLIpedia interfaces directly with the official Wikipedia PHP/MediaWiki APIs without using any third-party scraping libraries.
Please use this tool responsibly. If you need to perform massive automated data extraction, use official database dumps instead of hammering the live API.

## License

This program is licensed under the [GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html) (GPL-3.0). See the [LICENSE](LICENSE) file for details.
