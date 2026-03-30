"""Ensure test env is set before `main` is imported (JWT_SECRET is read at import time)."""

import os

os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
