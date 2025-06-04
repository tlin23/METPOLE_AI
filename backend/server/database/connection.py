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
        # Create User table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                question_count INTEGER NOT NULL DEFAULT 0,
                last_question_reset DATE NOT NULL
            )
        """
        )

        # Create Session table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        # Create Message table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                prompt TEXT NOT NULL,
                question_timestamp DATETIME NOT NULL,
                answer_timestamp DATETIME NOT NULL,
                response_time FLOAT NOT NULL,
                retrieved_chunks TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        # Create Feedback table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                answer_id TEXT NOT NULL,
                like BOOLEAN NOT NULL,
                suggestion TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (answer_id) REFERENCES messages(message_id),
                UNIQUE(user_id, answer_id)
            )
        """
        )

        conn.commit()
    finally:
        conn.close()


# Initialize database on module import
init_db()
