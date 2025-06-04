"""
Answer model for database operations.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..connection import get_db_connection


class Answer:
    @staticmethod
    def create(
        question_id: str,
        session_id: str,
        answer_text: str,
        answer_timestamp: datetime,
    ) -> str:
        """Create a new answer and return its ID."""
        answer_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO answers (
                    answer_id, question_id, session_id, answer_text,
                    answer_timestamp, created_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    answer_id,
                    question_id,
                    session_id,
                    answer_text,
                    answer_timestamp,
                ),
            )
            conn.commit()
            return answer_id
        finally:
            conn.close()

    @staticmethod
    def get(answer_id: str) -> Optional[Dict[str, Any]]:
        """Get an answer by ID."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT a.*, q.question_text, q.user_id, u.email as user_email
                FROM answers a
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE a.answer_id = ?
            """,
                (answer_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_question(question_id: str) -> Optional[Dict[str, Any]]:
        """Get an answer by its question ID."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT a.*, q.question_text, q.user_id, u.email as user_email
                FROM answers a
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE a.question_id = ?
            """,
                (question_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def list_answers(
        limit: int = 100,
        offset: int = 0,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List answers with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT a.*, q.question_text, q.user_id, u.email as user_email
                FROM answers a
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if session_id:
                query += " AND a.session_id = ?"
                params.append(session_id)
            if since:
                query += " AND a.answer_timestamp >= ?"
                params.append(since)
            if until:
                query += " AND a.answer_timestamp <= ?"
                params.append(until)

            query += " ORDER BY a.answer_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def search_answers(
        text: str,
        fuzzy: bool = False,
        limit: int = 100,
        offset: int = 0,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search answers by text with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT a.*, q.question_text, q.user_id, u.email as user_email
                FROM answers a
                JOIN questions q ON a.question_id = q.question_id
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if fuzzy:
                query += " AND a.answer_text LIKE ?"
                search_term = f"%{text}%"
                params.append(search_term)
            else:
                query += " AND a.answer_text LIKE ?"
                search_term = f"%{text}%"
                params.append(search_term)

            if session_id:
                query += " AND a.session_id = ?"
                params.append(session_id)
            if since:
                query += " AND a.answer_timestamp >= ?"
                params.append(since)
            if until:
                query += " AND a.answer_timestamp <= ?"
                params.append(until)

            query += " ORDER BY a.answer_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def delete(answer_id: str) -> bool:
        """Delete an answer."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM answers
                WHERE answer_id = ?
            """,
                (answer_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
