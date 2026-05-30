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

"""AST node definitions for the WiCLIpedia wikitext parser.

Defines `TokenType`, the enum of all recognized wikitext constructs,
and `Token`, the minimal unit produced by the lexer.
"""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    FILE = auto()
    HEADING = auto()
    LINK = auto()
    LIST_ITEM = auto()
    NEWLINE = auto()
    REF = auto()
    TABLE = auto()
    TEMPLATE = auto()
    TEXT = auto()


@dataclass
class Token:
    type: TokenType
    value: str
