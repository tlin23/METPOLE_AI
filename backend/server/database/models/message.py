"""
Message model for database operations.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from ..connection import get_db_connection


class Message:
    @staticmethod
    def create(
        session_id: str,
        user_id: str,
        question: str,
        answer: str,
        prompt: str,
        question_timestamp: datetime,
        answer_timestamp: datetime,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Create a new Q&A pair and return its ID."""
        message_id = str(uuid.uuid4())
        response_time = (answer_timestamp - question_timestamp).total_seconds()

        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO messages (
                    message_id, session_id, user_id, question, answer, prompt,
                    question_timestamp, answer_timestamp, response_time, retrieved_chunks
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    session_id,
                    user_id,
                    question,
                    answer,
                    prompt,
                    question_timestamp,
                    answer_timestamp,
                    response_time,
                    json.dumps(retrieved_chunks) if retrieved_chunks else None,
                ),
            )
            conn.commit()
            return message_id
        finally:
            conn.close()

    @staticmethod
    def list_messages(
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List Q&A pairs with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT m.*, u.email as user_email
                FROM messages m
                JOIN users u ON m.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND m.user_id = ?"
                params.append(user_id)
            if since:
                query += " AND m.question_timestamp >= ?"
                params.append(since)
            if until:
                query += " AND m.question_timestamp <= ?"
                params.append(until)

            query += " ORDER BY m.question_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def search_messages(
        text: str,
        fuzzy: bool = False,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search Q&A pairs by text with optional filtering."""
        conn = get_db_connection()
        try:
            query = """
                SELECT m.*, u.email as user_email
                FROM messages m
                JOIN users u ON m.user_id = u.user_id
                WHERE 1=1
            """
            params = []

            if fuzzy:
                # SQLite doesn't have built-in fuzzy search, so we'll use LIKE for now
                query += " AND (m.question LIKE ? OR m.answer LIKE ?)"
                search_term = f"%{text}%"
                params.extend([search_term, search_term])
            else:
                query += " AND (m.question LIKE ? OR m.answer LIKE ?)"
                search_term = f"%{text}%"
                params.extend([search_term, search_term])

            if user_id:
                query += " AND m.user_id = ?"
                params.append(user_id)
            if since:
                query += " AND m.question_timestamp >= ?"
                params.append(since)
            if until:
                query += " AND m.question_timestamp <= ?"
                params.append(until)

            query += " ORDER BY m.question_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_stats(
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get Q&A statistics."""
        conn = get_db_connection()
        try:
            where_clause = "WHERE 1=1"
            params = []

            if since:
                where_clause += " AND question_timestamp >= ?"
                params.append(since)
            if until:
                where_clause += " AND question_timestamp <= ?"
                params.append(until)

            # Most common questions
            cursor = conn.execute(
                f"""
                SELECT question, COUNT(*) as count
                FROM messages
                {where_clause}
                GROUP BY question
                ORDER BY count DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_questions = [dict(row) for row in cursor.fetchall()]

            # Most common answers
            cursor = conn.execute(
                f"""
                SELECT answer, COUNT(*) as count
                FROM messages
                {where_clause}
                GROUP BY answer
                ORDER BY count DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_answers = [dict(row) for row in cursor.fetchall()]

            # Most common retrieved chunks
            cursor = conn.execute(
                f"""
                SELECT json_extract(retrieved_chunks, '$[0].text') as chunk_text,
                       COUNT(*) as count
                FROM messages
                {where_clause}
                AND retrieved_chunks IS NOT NULL
                GROUP BY chunk_text
                ORDER BY count DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_chunks = [dict(row) for row in cursor.fetchall()]

            # Top users by question count
            cursor = conn.execute(
                f"""
                SELECT u.email, COUNT(*) as question_count
                FROM messages m
                JOIN users u ON m.user_id = u.user_id
                {where_clause}
                GROUP BY m.user_id
                ORDER BY question_count DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_users = [dict(row) for row in cursor.fetchall()]

            return {
                "top_questions": top_questions,
                "top_answers": top_answers,
                "top_chunks": top_chunks,
                "top_users": top_users,
            }
        finally:
            conn.close()
