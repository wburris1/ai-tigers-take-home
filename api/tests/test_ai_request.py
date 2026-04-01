import sqlite3
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from config import VALID_EMAIL, VALID_PASSWORD
from main import app

client = TestClient(app)
VALID_LOGIN = {"email": VALID_EMAIL, "password": VALID_PASSWORD}
AI_URL = "/api/ai-request"


def _seed_items_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'alpha')")
    conn.commit()
    conn.close()


def _auth_headers(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    _seed_items_db(db_file)
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    login = client.post("/api/login", json=VALID_LOGIN)
    assert login.status_code == 200
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _mock_gemini_client(sql_json: str, answer: str):
    mock = MagicMock()
    sql_resp = MagicMock()
    sql_resp.text = sql_json
    ans_resp = MagicMock()
    ans_resp.text = answer
    mock.models.generate_content.side_effect = [sql_resp, ans_resp]
    return mock


def test_ai_request_requires_auth():
    response = client.post(AI_URL, json={"query": "how many rows?"})
    assert response.status_code == 401


def test_ai_request_rejects_invalid_token():
    response = client.post(
        AI_URL,
        json={"query": "x"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_ai_request_missing_gemini_key(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    _seed_items_db(db_file)
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    login = client.post("/api/login", json=VALID_LOGIN)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    response = client.post(AI_URL, json={"query": "count items"}, headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "GEMINI_API_KEY is not configured"


def test_ai_request_database_missing(tmp_path, monkeypatch):
    missing = tmp_path / "nope.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(missing))
    monkeypatch.setenv("GEMINI_API_KEY", "k")

    login = client.post("/api/login", json=VALID_LOGIN)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    response = client.post(AI_URL, json={"query": "x"}, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Database file not found"


def test_ai_request_no_user_tables(tmp_path, monkeypatch):
    db_file = tmp_path / "empty.db"
    sqlite3.connect(db_file).close()
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "k")

    login = client.post("/api/login", json=VALID_LOGIN)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    response = client.post(AI_URL, json={"query": "x"}, headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "No tables in database"


@patch("routes.ai_request.genai.Client")
def test_ai_request_client_init_failure(mock_client_cls, tmp_path, monkeypatch):
    mock_client_cls.side_effect = RuntimeError("init failed")
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "count"}, headers=headers)
    assert response.status_code == 500
    body = response.json()["detail"]
    assert body["message"] == "Failed to initialize Gemini client"
    assert "init failed" in body["error"]


@patch("routes.ai_request.genai.Client")
def test_ai_request_gemini_error_on_sql_generation(mock_client_cls, tmp_path, monkeypatch):
    mock = MagicMock()
    mock.models.generate_content.side_effect = genai_errors.APIError(
        503, {"message": "upstream unavailable"}
    )
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "how many?"}, headers=headers)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == 503
    assert detail["details"]["message"] == "upstream unavailable"
    assert "503" in detail["message"]


@patch("routes.ai_request.genai.Client")
def test_ai_request_gemini_error_on_answer(mock_client_cls, tmp_path, monkeypatch):
    sql_resp = MagicMock()
    sql_resp.text = '{"sql": "SELECT COUNT(*) AS n FROM items"}'
    mock = MagicMock()
    mock.models.generate_content.side_effect = [
        sql_resp,
        genai_errors.APIError(429, {"message": "quota"}),
    ]
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "count?"}, headers=headers)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == 429
    assert detail["details"]["message"] == "quota"


@patch("routes.ai_request.genai.Client")
def test_ai_request_empty_sql_response_text(mock_client_cls, tmp_path, monkeypatch):
    mock = MagicMock()
    sql_resp = MagicMock()
    sql_resp.text = None
    mock.models.generate_content.return_value = sql_resp
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "x"}, headers=headers)
    assert response.status_code == 502
    assert response.json()["detail"] == "Gemini returned no text for SQL generation"


@patch("routes.ai_request.genai.Client")
def test_ai_request_unparseable_sql(mock_client_cls, tmp_path, monkeypatch):
    mock = _mock_gemini_client("not json and no select", "n/a")
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "x"}, headers=headers)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["message"] == "Could not parse SQL from model response"
    assert "error" in detail


@patch("routes.ai_request.genai.Client")
def test_ai_request_sql_validation_error(mock_client_cls, tmp_path, monkeypatch):
    mock = _mock_gemini_client(
        '{"sql": "SELECT * FROM sqlite_master"}',
        "n/a",
    )
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "meta"}, headers=headers)
    assert response.status_code == 400
    assert "system tables" in response.json()["detail"].lower()


@patch("routes.ai_request.genai.Client")
def test_ai_request_sqlite_error(mock_client_cls, tmp_path, monkeypatch):
    mock = _mock_gemini_client(
        '{"sql": "SELECT missing_column FROM items"}',
        "n/a",
    )
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "bad col"}, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"].startswith("SQL error:")


@patch("routes.ai_request.genai.Client")
def test_ai_request_empty_answer_text(mock_client_cls, tmp_path, monkeypatch):
    sql_resp = MagicMock()
    sql_resp.text = '{"sql": "SELECT id, name FROM items"}'
    ans = MagicMock()
    ans.text = None
    mock = MagicMock()
    mock.models.generate_content.side_effect = [sql_resp, ans]
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "list items"}, headers=headers)
    assert response.status_code == 502
    assert response.json()["detail"] == "Gemini returned no text for the final answer"


@patch("routes.ai_request.genai.Client")
def test_ai_request_success(mock_client_cls, tmp_path, monkeypatch):
    mock = _mock_gemini_client(
        '{"sql": "SELECT id, name FROM items"}',
        "There is one row: id 1, name alpha.",
    )
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(
        AI_URL,
        json={"query": "What is in items?"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "There is one row: id 1, name alpha."
    assert data["sql"] == "SELECT id, name FROM items"
    assert data["model"] == "gemini-3-flash-preview"
    preview = data["result_preview"]
    assert preview["columns"] == ["id", "name"]
    assert preview["rows"] == [[1, "alpha"]]
    assert preview["truncated"] is False

    assert mock.models.generate_content.call_count == 2


@patch("routes.ai_request.genai.Client")
def test_ai_request_respects_gemini_model_env(mock_client_cls, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "custom-model")
    mock = _mock_gemini_client(
        '{"sql": "SELECT id FROM items"}',
        "One id.",
    )
    mock_client_cls.return_value = mock
    headers = _auth_headers(tmp_path, monkeypatch)

    response = client.post(AI_URL, json={"query": "ids?"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["model"] == "custom-model"
