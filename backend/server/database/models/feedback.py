"""
Feedback model for database operations.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from ..connection import get_db_connection


class Feedback:
    @staticmethod
    def create_or_update(
        answer_id: str,
        feedback_text: str,
    ) -> str:
        """Create or update feedback for an answer."""
        feedback_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO feedback (feedback_id, answer_id, feedback_text, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(answer_id) DO UPDATE SET
                    feedback_text = excluded.feedback_text,
                    created_at = CURRENT_TIMESTAMP
            """,
                (feedback_id, answer_id, feedback_text),
            )
            conn.commit()
            return feedback_id
        finally:
            conn.close()

    @staticmethod
    def get(answer_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback for an answer."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT f.*, a.answer_text, q.question_text, q.user_id, u.email as user_email
                FROM feedback f
                JOIN answers a ON f.answer_id = a.answer_id
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE f.answer_id = ?
            """,
                (answer_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def delete(answer_id: str) -> bool:
        """Delete feedback for an answer."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM feedback
                WHERE answer_id = ?
            """,
                (answer_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def list_feedback(
        limit: int = 100,
        offset: int = 0,
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
