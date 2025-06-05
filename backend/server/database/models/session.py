"""
Session model for database operations.
"""

import uuid
from datetime import UTC, datetime
from backend.server.database.connection import get_db_connection


class Session:
    @staticmethod
    def create(user_id: str) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO sessions (session_id, user_id, start_time)
                VALUES (?, ?, ?)
            """,
                (session_id, user_id, datetime.now(UTC)),
            )
            conn.commit()
            return session_id
        finally:
            conn.close()
