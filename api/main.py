import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

VALID_EMAIL = "example@helloconstellation.com"
VALID_PASSWORD = "ConstellationInterview123!"
USER_NAME = "Example User"

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-in-production")

_REPO_ROOT = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    env = os.environ.get("SQLITE_DB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return _REPO_ROOT / "example.db"


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _serialize_cell(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _list_user_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cur.fetchall()]


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(body: LoginRequest):
    email = body.email.strip()
    if email != VALID_EMAIL or body.password != VALID_PASSWORD:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid email or password"},
        )
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=7)
    payload = {
        "sub": email,
        "name": USER_NAME,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token, "user": {"name": USER_NAME, "email": email}}


@app.get("/api/data")
def get_table_data(
    _user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return a page of rows from the first user table (alphabetically by name)."""
    db_path = get_db_path()
    if not db_path.is_file():
        raise HTTPException(status_code=404, detail="Database file not found")

    conn = sqlite3.connect(db_path)
    try:
        tables = _list_user_tables(conn)
        if not tables:
            raise HTTPException(status_code=500, detail="No tables in database")
        table = tables[0]
        qtable = _quote_ident(table)
        total = conn.execute(f"SELECT COUNT(*) FROM {qtable}").fetchone()[0]
        cur = conn.execute(
            f"SELECT * FROM {qtable} ORDER BY rowid LIMIT ? OFFSET ?",
            (limit, offset),
        )
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = []
        for row in cur:
            rows.append([_serialize_cell(row[i]) for i in range(len(columns))])
    finally:
        conn.close()

    return {
        "table": table,
        "columns": columns,
        "rows": rows,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
