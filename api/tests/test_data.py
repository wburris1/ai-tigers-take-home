import sqlite3

import jwt
import pytest
from fastapi.testclient import TestClient

from config import JWT_SECRET, VALID_EMAIL, VALID_PASSWORD, USER_NAME
from main import app

client = TestClient(app)

VALID_BODY = {"email": VALID_EMAIL, "password": VALID_PASSWORD}


def test_data_requires_auth():
    response = client.get("/api/data")
    assert response.status_code == 401


def test_data_rejects_invalid_token():
    response = client.get(
        "/api/data",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_data_returns_rows_for_temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'alpha')")
    conn.commit()
    conn.close()

    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))

    login = client.post("/api/login", json=VALID_BODY)
    assert login.status_code == 200
    token = login.json()["token"]

    response = client.get(
        "/api/data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["table"] == "items"
    assert data["columns"] == ["id", "name"]
    assert data["rows"] == [[1, "alpha"]]
    assert data["total"] == 1
    assert data["offset"] == 0
    assert data["limit"] == 50

    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert decoded["sub"] == VALID_EMAIL
    assert decoded["name"] == USER_NAME


def test_data_pagination(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    for i in range(5):
        conn.execute("INSERT INTO items VALUES (?, ?)", (i, f"row{i}"))
    conn.commit()
    conn.close()

    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))

    login = client.post("/api/login", json=VALID_BODY)
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    p1 = client.get("/api/data?limit=2&offset=0", headers=headers)
    assert p1.status_code == 200
    d1 = p1.json()
    assert d1["total"] == 5
    assert d1["offset"] == 0
    assert d1["limit"] == 2
    assert len(d1["rows"]) == 2

    p2 = client.get("/api/data?limit=2&offset=2", headers=headers)
    assert p2.status_code == 200
    d2 = p2.json()
    assert d2["total"] == 5
    assert len(d2["rows"]) == 2

    p3 = client.get("/api/data?limit=10&offset=4", headers=headers)
    assert p3.status_code == 200
    d3 = p3.json()
    assert len(d3["rows"]) == 1
