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
                       (SELECT COUNT(*) FROM messages m WHERE m.user_id = u.user_id) as message_count
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
        message_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific user."""
        return Message.list_messages(
            limit=limit,
            offset=offset,
            user_id=user_id,
            message_type=message_type,
            since=since,
            until=until,
        )


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

    @staticmethod
    def list_messages(
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        message_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List messages with optional filtering."""
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
            if message_type:
                query += " AND m.message_type = ?"
                params.append(message_type)
            if since:
                query += " AND m.timestamp >= ?"
                params.append(since)
            if until:
                query += " AND m.timestamp <= ?"
                params.append(until)

            query += " ORDER BY m.timestamp DESC LIMIT ? OFFSET ?"
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
        message_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search messages by text with optional filtering."""
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
                query += " AND m.message_text LIKE ?"
                params.append(f"%{text}%")
            else:
                query += " AND m.message_text LIKE ?"
                params.append(f"%{text}%")

            if user_id:
                query += " AND m.user_id = ?"
                params.append(user_id)
            if message_type:
                query += " AND m.message_type = ?"
                params.append(message_type)
            if since:
                query += " AND m.timestamp >= ?"
                params.append(since)
            if until:
                query += " AND m.timestamp <= ?"
                params.append(until)

            query += " ORDER BY m.timestamp DESC LIMIT ? OFFSET ?"
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
        """Get message statistics."""
        conn = get_db_connection()
        try:
            where_clause = "WHERE 1=1"
            params = []

            if since:
                where_clause += " AND timestamp >= ?"
                params.append(since)
            if until:
                where_clause += " AND timestamp <= ?"
                params.append(until)

            # Most common questions
            cursor = conn.execute(
                f"""
                SELECT message_text, COUNT(*) as count
                FROM messages
                {where_clause}
                AND message_type = 'question'
                GROUP BY message_text
                ORDER BY count DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_questions = [dict(row) for row in cursor.fetchall()]

            # Most common answers
            cursor = conn.execute(
                f"""
                SELECT message_text, COUNT(*) as count
                FROM messages
                {where_clause}
                AND message_type = 'answer'
                GROUP BY message_text
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
                AND m.message_type = 'question'
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
