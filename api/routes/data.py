import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_db_path, list_user_tables, quote_ident, serialize_cell
from deps import get_current_user

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/data")
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
        tables = list_user_tables(conn)
        if not tables:
            raise HTTPException(status_code=500, detail="No tables in database")
        table = tables[0]
        qtable = quote_ident(table)
        total = conn.execute(f"SELECT COUNT(*) FROM {qtable}").fetchone()[0]
        cur = conn.execute(
            f"SELECT * FROM {qtable} ORDER BY rowid LIMIT ? OFFSET ?",
            (limit, offset),
        )
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = []
        for row in cur:
            rows.append([serialize_cell(row[i]) for i in range(len(columns))])
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
