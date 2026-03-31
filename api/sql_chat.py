"""Prompts and parsing for NL → SQL → answer (Gemini)."""

from __future__ import annotations

import json
import re
from typing import Any, List

_SQL_FENCE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)


def sql_generation_user_text(schema_text: str, user_question: str) -> str:
    return (
        "Database schema (SQLite, user tables only):\n"
        f"{schema_text}\n\n"
        "User question:\n"
        f"{user_question.strip()}\n\n"
        "Respond with JSON only (no markdown): "
        '{"sql": "<a single SQLite SELECT (or WITH ... SELECT) using only tables/columns above>"}'
    )


def answer_user_text(
    user_question: str,
    sql: str,
    columns: List[str],
    rows: List[List[Any]],
    truncated: bool,
) -> str:
    payload = {
        "executed_sql": sql,
        "columns": columns,
        "rows": rows,
        "truncated": truncated,
    }
    return (
        "The following JSON is the result of running the SQL query on the database. "
        "Answer the user's question in clear, concise plain language using ONLY this data. "
        "If the result is empty or insufficient, say so. Do not invent rows or values.\n\n"
        f"User question: {user_question.strip()}\n\n"
        f"Result JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def parse_sql_from_model_text(text: str) -> str:
    """Extract SQL from JSON response or ```sql fenced block."""
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "sql" in data:
            sql = data["sql"]
            if isinstance(sql, str) and sql.strip():
                return sql.strip()
    except json.JSONDecodeError:
        pass
    m = _SQL_FENCE.search(text)
    if m:
        return m.group(1).strip()
    if text.upper().startswith("SELECT") or text.upper().startswith("WITH"):
        return text.strip()
    raise ValueError("Could not parse SQL from model response")
