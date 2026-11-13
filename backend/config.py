import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    PROJECT_ROOT = str(BASE_DIR)
    FRONTEND_DIR = str(BASE_DIR / "frontend")
    TEMPLATE_FOLDER = str(BASE_DIR / "frontend" / "templates")
    STATIC_FOLDER = str(BASE_DIR / "frontend" / "static")
    DATABASE = str(BASE_DIR / "db" / "career_connect.db")
    UPLOAD_FOLDER = str(BASE_DIR / "uploads" / "cvs")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
        # External geocoding provider (can be replaced by self-hosted Photon)
    PHOTON_BASE_URL = os.environ.get(
        "PHOTON_BASE_URL",
        "https://photon.komoot.io"
    )
    PHOTON_TIMEOUT = 5
    PHOTON_CACHE_TTL = 300
    PHOTON_CACHE_MAX_SIZE = 256
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
