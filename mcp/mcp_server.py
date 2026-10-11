"""Homework 5 MCP entry point placeholder.

Problem 2 establishes the working database path. Domain tools will be added in
later problems; all of them must import DB_PATH from backend.db_config rather
than opening the untouched seed database.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"

if __name__ == "__main__":
    print(DB_PATH)
