"""Shared fixtures for all tests."""

import os
import sqlite3
from pathlib import Path
import pytest

from backend.server.tests.factories.factories import (
    user_factory,  # noqa: F401
    session_factory,  # noqa: F401
    question_factory,  # noqa: F401
    answer_factory,  # noqa: F401
    feedback_factory,  # noqa: F401
)

TEST_DB_PATH = Path(__file__).parent / "test.db"


def get_test_db_connection():
    """Get a connection to the test database."""
    return sqlite3.connect(TEST_DB_PATH)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a fresh test database before the test session and clean up after."""
    # Set test database path in environment
    os.environ["METROPOLE_DB_PATH"] = str(TEST_DB_PATH)

    # Ensure we're not using the production database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Create test database and initialize schema
    conn = get_test_db_connection()
    try:
        with open(Path(__file__).parent.parent / "database" / "schema.sql") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

    yield

    # Clean up after tests
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    # Remove environment variable
    os.environ.pop("METROPOLE_DB_PATH", None)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean all tables before each test."""
    conn = get_test_db_connection()
    try:
        # Disable foreign key checks temporarily
        conn.execute("PRAGMA foreign_keys = OFF")

        # Get all tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Truncate each table
        for table in tables:
            conn.execute(f"DELETE FROM {table}")

        conn.commit()
    finally:
        # Re-enable foreign key checks
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()
