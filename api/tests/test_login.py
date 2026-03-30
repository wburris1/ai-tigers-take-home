import jwt
import pytest
from fastapi.testclient import TestClient

from main import JWT_SECRET, VALID_EMAIL, VALID_PASSWORD, USER_NAME, app

client = TestClient(app)

VALID_BODY = {"email": VALID_EMAIL, "password": VALID_PASSWORD}


def test_login_success_returns_token_and_user():
    response = client.post("/api/login", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"] == {"name": USER_NAME, "email": VALID_EMAIL}

    decoded = jwt.decode(data["token"], JWT_SECRET, algorithms=["HS256"])
    assert decoded["sub"] == VALID_EMAIL
    assert decoded["name"] == USER_NAME
    assert "iat" in decoded and "exp" in decoded
    assert decoded["exp"] > decoded["iat"]


def test_login_strips_email_whitespace():
    response = client.post(
        "/api/login",
        json={"email": f"  {VALID_EMAIL}  ", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == VALID_EMAIL


@pytest.mark.parametrize(
    "email,password",
    [
        ("wrong@example.com", VALID_PASSWORD),
        (VALID_EMAIL, "wrong-password"),
        ("", ""),
    ],
)
def test_login_invalid_credentials_returns_401(email: str, password: str):
    response = client.post("/api/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid email or password"}
