# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of wiCLIpedia.
#
# wiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with wiCLIpedia.  If not, see <https://www.gnu.org/licenses/>.

"""Language-specific constants for Wikipedia wikitext parsing.

This package contains multilingual data structures used by the lexer,
including template names and namespace prefixes for various languages.
"""

from .templates import (
    BLOCKQUOTE_TEMPLATES,
    CITATION_TEMPLATES,
    FILE_NAMESPACES,
    POEMQUOTE_TEMPLATES,
    TEMPLATES_KEEP_FIRST,
    TEMPLATES_KEEP_LAST,
    TEMPLATES_STATIC,
)

__all__ = [
    "BLOCKQUOTE_TEMPLATES",
    "CITATION_TEMPLATES",
    "FILE_NAMESPACES",
    "POEMQUOTE_TEMPLATES",
    "TEMPLATES_KEEP_FIRST",
    "TEMPLATES_KEEP_LAST",
    "TEMPLATES_STATIC",
]
