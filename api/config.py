import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret")

VALID_EMAIL = "example@helloconstellation.com"
VALID_PASSWORD = "ConstellationInterview123!"
USER_NAME = "Example User"
