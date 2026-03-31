import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

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


def table_column_info(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str]]:
    """Return (column_name, declared_type) for each column in table."""
    qtable = quote_ident(table)
    cur = conn.execute(f"PRAGMA table_info({qtable})")
    rows: List[Tuple[str, str]] = []
    for row in cur:
        # cid, name, type, notnull, dflt_value, pk
        rows.append((str(row[1]), str(row[2] or "")))
    return rows


def describe_schema(conn: sqlite3.Connection) -> str:
    """Compact schema text for LLM prompts (tables and columns only, no row data)."""
    tables = list_user_tables(conn)
    if not tables:
        return "(no user tables)"
    lines: List[str] = []
    for table in tables:
        cols = table_column_info(conn, table)
        col_desc = ", ".join(
            f"{quote_ident(name)} {typ.strip() or 'ANY'}" for name, typ in cols
        )
        lines.append(f"- Table {quote_ident(table)}: {col_desc}")
    return "\n".join(lines)
