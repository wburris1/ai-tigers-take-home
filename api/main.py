import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

VALID_EMAIL = "example@helloconstellation.com"
VALID_PASSWORD = "ConstellationInterview123!"
USER_NAME = "Example User"

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-in-production")

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
