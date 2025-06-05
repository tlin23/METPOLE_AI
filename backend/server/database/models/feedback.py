"""
Feedback model for database operations.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.server.database.connection import get_db_connection


class Feedback:
    @staticmethod
    def create_or_update(
        user_id: str,
        answer_id: str,
        like: bool,
        suggestion: Optional[str] = None,
    ) -> str:
        """Create or update feedback for an answer."""
        feedback_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO feedback (feedback_id, user_id, answer_id, like, suggestion, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
    def get(answer_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback for an answer from a specific user."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT f.*, a.answer_text, q.question_text, q.user_id, u.email as user_email
                FROM feedback f
                JOIN answers a ON f.answer_id = a.answer_id
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE f.answer_id = ? AND f.user_id = ?
            """,
                (answer_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def delete(answer_id: str, user_id: str) -> bool:
        """Delete feedback for an answer from a specific user."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM feedback
                WHERE answer_id = ? AND user_id = ?
            """,
                (answer_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def list_feedback(
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List feedback entries with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT f.*, a.answer_text, q.question_text, q.user_id, u.email as user_email
                FROM feedback f
                JOIN answers a ON f.answer_id = a.answer_id
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND f.user_id = ?"
                params.append(user_id)
            if session_id:
                query += " AND a.session_id = ?"
                params.append(session_id)
            if since:
                query += " AND f.created_at >= ?"
                params.append(since)
            if until:
                query += " AND f.created_at <= ?"
                params.append(until)

            query += " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
