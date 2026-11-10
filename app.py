"""Compatibility import for the Flask package now located in ``backend/app``."""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent / "backend" / "app")]

from backend.app import create_app  # noqa: E402

__all__ = ["create_app"]
