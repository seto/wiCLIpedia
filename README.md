# WiCLIpedia

[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0+-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/wiclipedia.svg?maxAge=86400)](https://pypi.org/project/wiclipedia/)
[![Supported Versions](https://img.shields.io/pypi/pyversions/wiclipedia.svg)](https://pypi.org/project/wiclipedia)
[![Code Style: Black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)

This is a minimalistic command-line tool to fetch and display Wikipedia page properties.

_In an era where Artificial Intelligence answers everything and large language models shape our knowledge, this program is a small tribute to Wikipedia, the silent, human-curated backbone that feeds those very models. Never forget the source._

## Installation

```bash
pip install wiclipedia
```

## Usage

```bash
wicli "Page Title"
```

By default, it fetches the English Wikipedia.  
To specify a different language, use the `-l` or `--lang` option:

```bash
wicli "Titolo della pagina" -l it
```
