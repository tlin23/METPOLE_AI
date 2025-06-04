"""
Feedback model for database operations.
"""

from typing import Optional, List, Dict, Any
from ..connection import get_db_connection


class Feedback:
    @staticmethod
    def create_or_update(
        user_id: str,
        answer_id: str,
        like: bool,
        suggestion: Optional[str] = None,
    ) -> str:
        """Create or update feedback for a user/answer pair."""
        conn = get_db_connection()
        try:
            feedback_id = f"fb_{user_id}_{answer_id}"
            conn.execute(
                """
                INSERT INTO feedback (feedback_id, user_id, answer_id, like, suggestion, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, answer_id) DO UPDATE SET
                    like = excluded.like,
                    suggestion = excluded.suggestion,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (feedback_id, user_id, answer_id, like, suggestion),
            )
            conn.commit()
            return feedback_id
        finally:
            conn.close()

    @staticmethod
    def get(user_id: str, answer_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback for a user/answer pair."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM feedback
                WHERE user_id = ? AND answer_id = ?
            """,
                (user_id, answer_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def delete(user_id: str, answer_id: str) -> bool:
        """Delete feedback for a user/answer pair."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM feedback
                WHERE user_id = ? AND answer_id = ?
            """,
                (user_id, answer_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def list_feedback(
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List feedback entries, optionally filtered by user_id."""
        conn = get_db_connection()
        try:
            query = "SELECT * FROM feedback"
            params = []
            if user_id:
                query += " WHERE user_id = ?"
                params.append(user_id)
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
