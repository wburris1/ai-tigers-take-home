import os
import sqlite3
from pathlib import Path
from typing import List

from config import REPO_ROOT


def get_db_path() -> Path:
    env = os.environ.get("SQLITE_DB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return REPO_ROOT / "example.db"


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def serialize_cell(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def list_user_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cur.fetchall()]
