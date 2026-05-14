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

from typing import Any, Dict


def parse_page_props(response: Dict[str, Any]) -> Dict[str, Any]:
    pages = response.get("query", {}).get("pages", [])

    if not pages or "missing" in pages[0]:
        return {"status": "missing"}

    if "disambiguation" in pages[0].get("pageprops", {}):
        return {"status": "disambiguation"}

    if "pageprops" not in pages[0]:
        return {"status": "unknown"}

    return {"status": "found"}
