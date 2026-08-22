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

"""Multilingual template and namespace constants for Wikipedia wikitext parsing."""

# Templates where the last parameter contains the content to keep
TEMPLATES_KEEP_LAST = {
    "abbr",
    "as of",
    "cast listing",
    "citation",
    "date",
    "lang",
    "langx",
    "langue",
    "nowrap",
    "portal inline",
    "transl",
    "unité",
}

# Templates where the first parameter contains the content to keep
TEMPLATES_KEEP_FIRST = {
    "citation nécessaire",
    "citation needed",
    "cn",
    "cr",
    "cita requerida",
    "référence nécessaire",
    "senza fonte",
}

# Templates for blockquotes with language-specific names
BLOCKQUOTE_TEMPLATES = {
    "blockquote",
    "cita",
    "citazione",
    "quote",
    "cquote",
    "zitat",
}

# Templates for poem/poetry blocks
POEMQUOTE_TEMPLATES = {
    "poem quote",
    "poemquote",
}

# Templates with static replacement text
TEMPLATES_STATIC = {
    "nom": "Nominated",
    "nominated": "Nominated",
    "win": "Won",
    "won": "Won",
}

# File namespace prefixes for various language Wikipedias
FILE_NAMESPACES = (
    "[[Archivo:",
    "[[Bild:",
    "[[Datei:",
    "[[Fichier:",
    "[[File:",
    "[[Image:",
    "[[Immagine:",
)

# Citation templates with parameter name mappings for each language
# Maps template name to a dict with parameter aliases for "title" and "year"
CITATION_TEMPLATES = {
    "cita libro": {"title": "titolo", "year": "anno"},
    "cita news": {"title": "titolo", "year": "anno"},
    "cita pubblicazione": {"title": "titolo", "year": "anno"},
    "cita web": {"title": "titolo", "year": "anno"},
    "cite book": {"title": "title", "year": "year"},
    "cite journal": {"title": "title", "year": "date"},
    "cite magazine": {"title": "title", "year": "date"},
    "cite news": {"title": "title", "year": "year"},
    "cite web": {"title": "title", "year": "date"},
    "internetquelle": {"title": "titel", "year": "datum"},
    "lien web": {"title": "titre", "year": "année"},
}
