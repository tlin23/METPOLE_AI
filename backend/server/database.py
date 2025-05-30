"""
Database setup and models for the application.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Database path
DB_PATH = Path(__file__).parent / "data" / "app.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
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
                timestamp TIMESTAMP NOT NULL,
                message_type TEXT NOT NULL,
                message_text TEXT NOT NULL,
                retrieved_chunks TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        conn.commit()
    finally:
        conn.close()


# Initialize database on module import
init_db()


class User:
    @staticmethod
    def create_or_update(user_id: str, email: str, is_admin: bool = False) -> None:
        """Create or update a user."""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (user_id, email, is_admin, question_count, last_question_reset)
                VALUES (?, ?, ?, 0, date('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    email = excluded.email,
                    is_admin = excluded.is_admin
            """,
                (user_id, email, is_admin),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get(user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        conn = get_db_connection()
        try:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def increment_question_count(user_id: str) -> int:
        """Increment question count and return remaining quota."""
        conn = get_db_connection()
        try:
            # Start transaction
            conn.execute("BEGIN TRANSACTION")

            # Check if we need to reset the count (new day)
            conn.execute(
                """
                UPDATE users
                SET question_count = 0, last_question_reset = date('now')
                WHERE user_id = ? AND date(last_question_reset) < date('now')
            """,
                (user_id,),
            )

            # Get current count and quota limit
            cursor = conn.execute(
                """
                SELECT question_count, is_admin
                FROM users
                WHERE user_id = ?
            """,
                (user_id,),
            )
            row = cursor.fetchone()

            if not row:
                conn.rollback()
                return 0

            question_count = row["question_count"]
            max_quota = 20 if row["is_admin"] else 5

            # Only increment if under quota
            if question_count < max_quota:
                conn.execute(
                    """
                    UPDATE users
                    SET question_count = question_count + 1
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
                question_count += 1

            conn.commit()
            return max(0, max_quota - question_count)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class Session:
    @staticmethod
    def create(user_id: str) -> str:
        """Create a new session and return its ID."""
        import uuid

        session_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO sessions (session_id, user_id, start_time)
                VALUES (?, ?, ?)
            """,
                (session_id, user_id, datetime.utcnow()),
            )
            conn.commit()
            return session_id
        finally:
            conn.close()


class Message:
    @staticmethod
    def create(
        session_id: str,
        user_id: str,
        message_type: str,
        message_text: str,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Create a new message and return its ID."""
        import uuid

        message_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, session_id, user_id, timestamp,
                    message_type, message_text, retrieved_chunks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    session_id,
                    user_id,
                    datetime.utcnow(),
                    message_type,
                    message_text,
                    json.dumps(retrieved_chunks) if retrieved_chunks else None,
                ),
            )
            conn.commit()
            return message_id
        finally:
            conn.close()
