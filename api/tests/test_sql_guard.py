import sqlite3

import pytest

from utils.sql_guard import SqlValidationError, execute_select, validate_select_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "SELECT * FROM t",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "  select id from items  ",
    ],
)
def test_validate_accepts_safe_select(sql: str):
    out = validate_select_sql(sql)
    assert out.upper().startswith("SELECT") or out.upper().startswith("WITH")


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "DELETE FROM t",
        "INSERT INTO t VALUES (1)",
        "DROP TABLE t",
        "SELECT 1; SELECT 2",
        "ATTACH DATABASE 'x' AS y",
        "PRAGMA user_version",
        "SELECT * FROM sqlite_master",
        "UPDATE t SET x=1",
    ],
)
def test_validate_rejects_unsafe(sql: str):
    with pytest.raises(SqlValidationError):
        validate_select_sql(sql)


def test_execute_select_respects_max_rows(tmp_path):
    db_file = tmp_path / "t.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE n (v INTEGER)")
    for i in range(5):
        conn.execute("INSERT INTO n VALUES (?)", (i,))
    conn.commit()
    conn.close()

    cols, rows, truncated = execute_select(
        db_file,
        "SELECT v FROM n ORDER BY v",
        max_rows=3,
    )
    assert cols == ["v"]
    assert rows == [[0], [1], [2]]
    assert truncated is True


def test_execute_select_not_truncated(tmp_path):
    db_file = tmp_path / "t.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE n (v INTEGER)")
    conn.execute("INSERT INTO n VALUES (1)")
    conn.commit()
    conn.close()

    cols, rows, truncated = execute_select(db_file, "SELECT v FROM n", max_rows=10)
    assert cols == ["v"]
    assert rows == [[1]]
    assert truncated is False
