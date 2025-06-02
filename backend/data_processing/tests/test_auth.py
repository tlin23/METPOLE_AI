"""
Tests for authentication and database functionality.
"""

import pytest
from unittest.mock import patch, Mock
import json
from backend.server.auth import validate_token, require_admin
from backend.server.database import User, Session, Message, get_db_connection
import os
from pathlib import Path
import tempfile
from datetime import datetime


# Mock Google token verification
@pytest.fixture
def mock_token_verification():
    with patch("google.oauth2.id_token.verify_oauth2_token") as mock:
        mock.return_value = {"sub": "test_user_id", "email": "test@example.com"}
        yield mock


# Test database setup
@pytest.fixture
def test_db():
    """Create a test database in memory."""
    # Create a temporary directory for the test database
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set the environment variable for the test database
        test_db_path = Path(temp_dir) / "test.db"
        os.environ["METROPOLE_DB_PATH"] = str(test_db_path)

        conn = get_db_connection()
        try:
            # Drop existing tables to ensure clean state
            conn.execute("DROP TABLE IF EXISTS messages")
            conn.execute("DROP TABLE IF EXISTS sessions")
            conn.execute("DROP TABLE IF EXISTS users")

            # Create tables
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

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    question_timestamp DATETIME NOT NULL,
                    answer_timestamp DATETIME NOT NULL,
                    response_time FLOAT NOT NULL,
                    retrieved_chunks TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """
            )

            conn.commit()
            yield conn

            # Clean up after test
            conn.execute("DROP TABLE IF EXISTS messages")
            conn.execute("DROP TABLE IF EXISTS sessions")
            conn.execute("DROP TABLE IF EXISTS users")
            conn.commit()
        finally:
            conn.close()
            # Clean up environment variable
            os.environ.pop("METROPOLE_DB_PATH", None)


def test_user_creation(test_db):
    """Test user creation and retrieval."""
    # Create user
    User.create_or_update("test_user_id", "test@example.com")

    # Get user
    user = User.get("test_user_id")
    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["is_admin"] == 0  # SQLite stores booleans as 0/1
    assert user["question_count"] == 0


def test_user_admin(test_db):
    """Test admin user creation and privileges."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    # Get user
    user = User.get("admin_user_id")
    assert user is not None
    assert user["email"] == "admin@example.com"
    assert user["is_admin"] == 1  # SQLite stores booleans as 0/1


def test_question_quota(test_db):
    """Test question quota enforcement."""
    # Create regular user
    User.create_or_update("test_user_id", "test@example.com")

    # Test quota for regular user
    for i in range(5):
        remaining = User.increment_question_count("test_user_id")
        assert remaining == 4 - i

    # Should return 0 when quota exceeded
    remaining = User.increment_question_count("test_user_id")
    assert remaining == 0


def test_admin_quota(test_db):
    """Test admin user quota."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    # Test quota for admin user
    for i in range(20):
        remaining = User.increment_question_count("admin_user_id")
        assert remaining == 19 - i

    # Should return 0 when quota exceeded
    remaining = User.increment_question_count("admin_user_id")
    assert remaining == 0


def test_quota_reset(test_db):
    """Test daily quota reset."""
    # Create user
    User.create_or_update("test_user_id", "test@example.com")

    # Use up quota
    for _ in range(5):
        User.increment_question_count("test_user_id")

    # Set last reset to yesterday
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE users
            SET last_question_reset = date('now', '-1 day')
            WHERE user_id = ?
        """,
            ("test_user_id",),
        )
        conn.commit()
    finally:
        conn.close()

    # Should reset quota
    remaining = User.increment_question_count("test_user_id")
    assert remaining == 4  # 5 - 1


def test_session_creation(test_db):
    """Test session creation."""
    # Create user
    User.create_or_update("test_user_id", "test@example.com")

    # Create session
    session_id = Session.create("test_user_id")
    assert session_id is not None

    # Verify session exists
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        session = cursor.fetchone()
        assert session is not None
        assert session["user_id"] == "test_user_id"
    finally:
        conn.close()


def test_message_logging(test_db):
    """Test message logging."""
    # Create user and session
    User.create_or_update("test_user_id", "test@example.com")
    session_id = Session.create("test_user_id")

    # Get timestamps
    question_timestamp = datetime.utcnow()
    answer_timestamp = datetime.utcnow()

    # Log Q&A pair
    message_id = Message.create(
        session_id=session_id,
        user_id="test_user_id",
        question="Test question",
        answer="Test answer",
        prompt="Test prompt",
        question_timestamp=question_timestamp,
        answer_timestamp=answer_timestamp,
        retrieved_chunks=[{"text": "Test chunk", "metadata": {"source": "test"}}],
    )

    # Verify message
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM messages WHERE message_id = ?", (message_id,)
        )
        message = cursor.fetchone()
        assert message is not None
        assert message["question"] == "Test question"
        assert message["answer"] == "Test answer"
        assert message["prompt"] == "Test prompt"
        assert json.loads(message["retrieved_chunks"]) == [
            {"text": "Test chunk", "metadata": {"source": "test"}}
        ]
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_token_validation(mock_token_verification, test_db):
    """Test Google token validation."""
    # Mock credentials
    credentials = Mock()
    credentials.credentials = "test_token"

    # Validate token
    user_info = await validate_token(credentials)
    assert user_info["user_id"] == "test_user_id"
    assert user_info["email"] == "test@example.com"

    # Verify token was validated
    mock_token_verification.assert_called_once()
    args, kwargs = mock_token_verification.call_args
    assert args[0] == "test_token"


@pytest.mark.asyncio
async def test_admin_requirement(test_db):
    """Test admin requirement check."""
    # Create regular user
    User.create_or_update("test_user_id", "test@example.com")

    # Should raise 403 for non-admin
    with pytest.raises(Exception) as exc_info:
        await require_admin({"user_id": "test_user_id"})
    assert exc_info.value.status_code == 403

    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    # Should pass for admin
    user_info = await require_admin({"user_id": "admin_user_id"})
    assert user_info["user_id"] == "admin_user_id"
