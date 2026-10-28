import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-before-deployment")
    DATABASE = str(BASE_DIR / "db" / "career_connect.db")
    UPLOAD_FOLDER = str(BASE_DIR / "uploads" / "cvs")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
