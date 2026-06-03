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

"""Module implementing the cache functionality of WiCLIpedia.

This module provides functions to store and retrieve Wikipedia API responses
from a local cache, reducing the number of API calls made to Wikipedia.

Cache entries are stored in a SQLite database in the user's cache directory
and expire after 72 hours.

Errors during `load`, `save`, or `prune` operations are handled gracefully to
avoid blocking the user experience.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

_CACHE_DIR = Path.home() / ".cache" / "wiclipedia"
_DB_PATH = _CACHE_DIR / "cache.db"
_TTL = 60 * 60 * 24 * 3


def load(page: str, lang: str, resource: str) -> dict[str, Any] | None:
    conn = _connect()

    try:
        row = conn.execute(
            """
            SELECT data, cached_at FROM cache
            WHERE page = ? AND lang = ? AND resource = ?
            AND cached_at > ?
            """,
            (page, lang, resource, time.time() - _TTL),
        ).fetchone()

        if row is None:
            return None

        data_json, cached_at = row
        data = json.loads(data_json)

        # Inject cache metadata into the returned dict as a non-persistent key
        # as it is not part of the API response and is stripped before saving
        data["_cached_at"] = cached_at

        return data

    except Exception:
        return None

    finally:
        conn.close()


def save(page: str, lang: str, resource: str, data: dict[str, Any]) -> None:
    conn = _connect()

    try:
        conn.execute(
            """
            INSERT INTO cache (page, lang, resource, data, cached_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(page, lang, resource)
            DO UPDATE SET data=excluded.data, cached_at=excluded.cached_at
            """,
            (page, lang, resource, json.dumps(data, ensure_ascii=False), time.time()),
        )
        conn.commit()

    except Exception:
        pass

    finally:
        conn.close()


def prune() -> None:
    conn = _connect()

    try:
        conn.execute("DELETE FROM cache WHERE cached_at < ?", (time.time() - _TTL,))
        conn.commit()

    except Exception:
        pass

    finally:
        conn.close()


def purge() -> int:
    conn = _connect()

    try:
        cursor = conn.execute("DELETE FROM cache")
        conn.commit()

        return cursor.rowcount

    except Exception:
        return 0

    finally:
        conn.close()


def _connect() -> sqlite3.Connection:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                page TEXT NOT NULL,
                lang TEXT NOT NULL,
                resource TEXT NOT NULL,
                data TEXT NOT NULL,
                cached_at REAL NOT NULL,
                PRIMARY KEY (page, lang, resource)
            )
            """)
        conn.commit()

        return conn

    except Exception as e:
        # Connection errors are raised explicitly: if the database is unreachable,
        # callers' silent exception handlers will suppress it gracefully
        raise RuntimeError(f"Failed to connect to cache database: {e}") from e
