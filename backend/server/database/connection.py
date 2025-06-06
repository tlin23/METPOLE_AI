"""
Database connection and initialization utilities.
"""

import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get a database connection."""
    db_path = os.environ.get("METROPOLE_DB_PATH")
    if not db_path:
        error_msg = "METROPOLE_DB_PATH not set. Please set the environment variable to the absolute path of your SQLite DB file."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Ensure the path is absolute
    db_path = Path(db_path).resolve()
    if not db_path.is_absolute():
        error_msg = f"METROPOLE_DB_PATH must be an absolute path, got: {db_path}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    try:
        # Read and execute schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()
            conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
