import os
import sqlite3

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from fastapi import APIRouter, Depends, HTTPException

from database import describe_schema, get_db_path, list_user_tables
from deps import get_current_user
from models.ai_query import AiQueryRequest
from utils.sql_chat import answer_user_text, parse_sql_from_model_text, sql_generation_user_text
from utils.sql_guard import SqlValidationError, execute_select

router = APIRouter(prefix="/api", tags=["ai"])

_SQL_SCHEMA = genai_types.Schema(
    type=genai_types.Type.OBJECT,
    properties={
        "sql": genai_types.Schema(
            type=genai_types.Type.STRING,
            description="A single SQLite SELECT or WITH ... SELECT statement.",
        ),
    },
    required=["sql"],
)

_SQL_GEN_INSTRUCTION = (
    "You translate natural language questions into exactly one SQLite SELECT query "
    "(WITH ... SELECT is allowed). Use only tables and columns from the provided schema. "
    "Prefer aggregates (COUNT, AVG, SUM, MIN, MAX) when summarizing. "
    "Return JSON with a single key 'sql'. Do not include SQL comments or multiple statements."
)


def _max_rows() -> int:
    raw = os.environ.get("AI_SQL_MAX_ROWS", "200")
    try:
        n = int(raw)
    except ValueError:
        return 200
    return max(1, min(n, 2000))


@router.post("/ai-request")
def ai_request(
    body: AiQueryRequest,
    _user: dict = Depends(get_current_user),
):
    """Natural language → Gemini-generated SQL → execute on SQLite → Gemini answer."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured",
        )
    model = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

    db_path = get_db_path()
    if not db_path.is_file():
        raise HTTPException(status_code=404, detail="Database file not found")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to initialize Gemini client",
                "error": str(exc),
            },
        ) from exc

    conn = sqlite3.connect(db_path)
    try:
        tables = list_user_tables(conn)
        if not tables:
            raise HTTPException(status_code=500, detail="No tables in database")
        schema_text = describe_schema(conn)
    finally:
        conn.close()

    sql_config = genai_types.GenerateContentConfig(
        system_instruction=_SQL_GEN_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=_SQL_SCHEMA,
    )

    gen_user = sql_generation_user_text(schema_text, body.query)

    try:
        sql_response = client.models.generate_content(
            model=model,
            contents=gen_user,
            config=sql_config,
        )
    except genai_errors.APIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "code": exc.code,
                "details": exc.details,
            },
        ) from exc

    sql_text = sql_response.text
    if sql_text is None:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned no text for SQL generation",
        )

    try:
        generated_sql = parse_sql_from_model_text(sql_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": "Could not parse SQL from model response", "error": str(exc)},
        ) from exc

    max_rows = _max_rows()
    try:
        columns, rows, truncated = execute_select(db_path, generated_sql, max_rows=max_rows)
    except SqlValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"SQL error: {exc}",
        ) from exc

    answer_prompt = answer_user_text(
        body.query,
        generated_sql,
        columns,
        rows,
        truncated,
    )

    try:
        answer_response = client.models.generate_content(
            model=model,
            contents=answer_prompt,
        )
    except genai_errors.APIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "code": exc.code,
                "details": exc.details,
            },
        ) from exc

    answer_text = answer_response.text
    if answer_text is None:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned no text for the final answer",
        )

    return {
        "text": answer_text,
        "model": model,
        "sql": generated_sql,
        "result_preview": {
            "columns": columns,
            "rows": rows,
            "truncated": truncated,
        },
    }
