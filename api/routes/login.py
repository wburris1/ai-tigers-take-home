from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import JWT_SECRET, USER_NAME, VALID_EMAIL, VALID_PASSWORD
from models.login import LoginRequest

router = APIRouter(prefix="/api", tags=["login"])


@router.post("/login")
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
