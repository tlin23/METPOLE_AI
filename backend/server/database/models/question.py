"""
Question model for database operations.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.server.database.connection import get_db_connection


class Question:
    @staticmethod
    def create(
        session_id: str,
        user_id: Optional[str],
        question_text: str,
    ) -> str:
        """Create a new question and return its ID."""
        question_id = str(uuid.uuid4())
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO questions (
                    question_id, session_id, user_id, question_text, created_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    question_id,
                    session_id,
                    user_id,
                    question_text,
                ),
            )
            conn.commit()
            return question_id
        finally:
            conn.close()

    @staticmethod
    def get(question_id: str) -> Optional[Dict[str, Any]]:
        """Get a question by ID."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                SELECT q.*, u.email as user_email
                FROM questions q
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE q.question_id = ?
            """,
                (question_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def list_questions(
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List questions with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT q.*, u.email as user_email
                FROM questions q
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND q.user_id = ?"
                params.append(user_id)
            if session_id:
                query += " AND q.session_id = ?"
                params.append(session_id)
            if since:
                query += " AND q.created_at >= ?"
                params.append(since)
            if until:
                query += " AND q.created_at <= ?"
                params.append(until)

            query += " ORDER BY q.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def search_questions(
        text: str,
        fuzzy: bool = False,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search questions by text with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT q.*, u.email as user_email
                FROM questions q
                LEFT JOIN users u ON q.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if fuzzy:
                query += " AND q.question_text LIKE ?"
                search_term = f"%{text}%"
                params.append(search_term)
            else:
                query += " AND q.question_text LIKE ?"
                search_term = f"%{text}%"
                params.append(search_term)

            if user_id:
                query += " AND q.user_id = ?"
                params.append(user_id)
            if session_id:
                query += " AND q.session_id = ?"
                params.append(session_id)
            if since:
                query += " AND q.created_at >= ?"
                params.append(since)
            if until:
                query += " AND q.created_at <= ?"
                params.append(until)

            query += " ORDER BY q.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def delete(question_id: str) -> bool:
        """Delete a question and its associated answer."""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM questions
                WHERE question_id = ?
            """,
                (question_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
