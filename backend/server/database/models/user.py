"""
User model for database operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.server.database.connection import get_db_connection
from backend.server.app_config import MAX_QUESTIONS_PER_DAY
from backend.server.database.models.question import Question

MAX_QUESTIONS_PER_DAY = int(MAX_QUESTIONS_PER_DAY)


class User:
    @staticmethod
    def create_or_update(user_id: str, email: str) -> None:
        """Create or update a user."""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (user_id, email, question_count, last_question_reset)
                VALUES (?, ?, 0, date('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    email = excluded.email
            """,
                (user_id, email),
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

            # Get current count
            cursor = conn.execute(
                """
                SELECT question_count
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

            # Only increment if under quota
            if question_count < MAX_QUESTIONS_PER_DAY:
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
            return max(0, MAX_QUESTIONS_PER_DAY - question_count)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def search_users(
        query: str,
        fuzzy: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search users by email or name."""
        conn = get_db_connection()
        try:
            if fuzzy:
                # SQLite doesn't have built-in fuzzy search, so we'll use LIKE for now
                search_query = f"%{query}%"
            else:
                search_query = query

            cursor = conn.execute(
                """
                SELECT u.*,
                       (SELECT COUNT(*) FROM questions q WHERE q.user_id = u.user_id) as question_count
                FROM users u
                WHERE u.email LIKE ?
                ORDER BY u.email
                LIMIT ? OFFSET ?
                """,
                (search_query, limit, offset),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_user_messages(
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get questions for a specific user."""
        return Question.list_questions(
            limit=limit,
            offset=offset,
            user_id=user_id,
            since=since,
            until=until,
        )
