"""Shared database location for the Homework 5 backend."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DB_PATH = PROJECT_ROOT / "data" / "campus_customs.db"

