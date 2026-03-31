"""Validate and run read-only SELECT queries against SQLite."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple

from database import serialize_cell

_FORBIDDEN = re.compile(
    r"\b("
    r"ATTACH|DETACH|PRAGMA|VACUUM|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|"
    r"REPLACE|TRUNCATE|ANALYZE|REINDEX|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|"
    r"MERGE|GRANT|REVOKE"
    r")\b",
    re.IGNORECASE,
)

_META_LEAK = re.compile(
    r"\bsqlite_(master|temp_master|schema)\b",
    re.IGNORECASE,
)


class SqlValidationError(ValueError):
    """Raised when a query fails safety checks."""


def validate_select_sql(sql: str) -> str:
    """Return stripped SQL (trailing semicolon removed). Raises SqlValidationError if unsafe."""
    text = sql.strip()
    if not text:
        raise SqlValidationError("SQL is empty")
    if ";" in text:
        raise SqlValidationError("Multiple statements are not allowed")
    text = text.rstrip().rstrip(";")
    upper = text.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise SqlValidationError("Only SELECT queries (including WITH ... SELECT) are allowed")
    if _FORBIDDEN.search(text):
        raise SqlValidationError("Query contains forbidden keywords")
    if _META_LEAK.search(text):
        raise SqlValidationError("Queries may not reference SQLite system tables")
    return text


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri = db_path.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def execute_select(
    db_path: Path,
    sql: str,
    *,
    max_rows: int,
) -> Tuple[List[str], List[List[Any]], bool]:
    """
    Run validated SQL and return (column_names, rows, truncated).
    """
    safe_sql = validate_select_sql(sql)
    conn = connect_readonly(db_path)
    try:
        cur = conn.execute(safe_sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows: List[List[Any]] = []
        truncated = False
        for i, row in enumerate(cur):
            if i >= max_rows:
                truncated = True
                break
            rows.append([serialize_cell(row[j]) for j in range(len(columns))])
        return columns, rows, truncated
    finally:
        conn.close()
