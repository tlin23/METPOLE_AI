"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
from pathlib import Path
import tempfile
from backend.server.app import service
from backend.server.database import User, get_db_connection

# Test client
client = TestClient(service)


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


# Mock Google token verification
@pytest.fixture
def mock_token_verification():
    with patch("google.oauth2.id_token.verify_oauth2_token") as mock:
        # Use consistent user ID across all tests
        mock.return_value = {"sub": "admin_user_id", "email": "admin@example.com"}
        yield mock


# Mock retriever
@pytest.fixture
def mock_retriever():
    with patch("backend.server.api.routes.retriever") as mock:
        mock.query.return_value = {
            "documents": [["Test chunk"]],
            "metadatas": [[{"source": "test"}]],
            "distances": [[0.1]],
        }
        mock.generate_answer.return_value = {
            "answer": "Test answer",
            "is_general_knowledge": False,
            "contains_diy_advice": False,
            "source_info": "Test source",
            "prompt": "Test prompt",
        }
        yield mock


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "system" in data
    assert "has_admins" in data["system"]
    assert "admin_count" in data["system"]
    assert isinstance(data["system"]["admin_count"], int)


def test_ask_question_unauthorized():
    """Test asking question without authentication."""
    response = client.post("/api/ask", json={"question": "Test question"})
    assert response.status_code == 401


def test_ask_question(mock_token_verification, mock_retriever, test_db):
    """Test asking question with authentication."""
    # Create regular user
    User.create_or_update("admin_user_id", "admin@example.com")

    response = client.post(
        "/api/ask",
        json={"question": "Test question"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Test question"
    assert data["answer"] == "Test answer"
    assert data["success"] is True
    assert data["quota_remaining"] == 4  # 5 - 1


def test_ask_question_quota_exceeded(mock_token_verification, mock_retriever, test_db):
    """Test asking question when quota is exceeded."""
    # Create regular user
    User.create_or_update("admin_user_id", "admin@example.com")

    # Use up quota
    for _ in range(5):
        User.increment_question_count("admin_user_id")

    response = client.post(
        "/api/ask",
        json={"question": "Test question"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert response.status_code == 429
    data = response.json()
    assert (
        data["detail"]["message"]
        == "You have reached your daily question limit. Your quota will reset tomorrow at midnight UTC. Please try again then."
    )
    assert data["detail"]["quota_remaining"] == 0


def test_admin_list_unauthorized():
    """Test listing admins without authentication."""
    response = client.get("/api/admin/list")
    assert response.status_code == 401


def test_admin_list_not_admin(mock_token_verification, test_db):
    """Test listing admins as non-admin user."""
    # Create regular user
    User.create_or_update("admin_user_id", "admin@example.com")

    response = client.get(
        "/api/admin/list", headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 403


def test_admin_list(mock_token_verification, test_db):
    """Test listing admins as admin user."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    response = client.get(
        "/api/admin/list", headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "admin@example.com"


def test_admin_add(mock_token_verification, test_db):
    """Test adding admin user."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    # Create the user that will be promoted to admin
    User.create_or_update("new_admin_id", "new_admin@example.com")

    response = client.post(
        "/api/admin/add",
        params={"email": "new_admin@example.com"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_admin@example.com"

    # Verify user is now admin
    user = User.get(data["user_id"])
    assert user["is_admin"] == 1  # SQLite stores booleans as 0/1


def test_admin_remove(mock_token_verification, test_db):
    """Test removing admin user."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    response = client.post(
        "/api/admin/remove",
        params={"email": "admin@example.com"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@example.com"

    # Verify user is no longer admin
    user = User.get(data["user_id"])
    assert user["is_admin"] == 0  # SQLite stores booleans as 0/1


def test_admin_reset_quota(mock_token_verification, test_db):
    """Test resetting user quota."""
    # Create admin user
    User.create_or_update("admin_user_id", "admin@example.com", is_admin=True)

    # Create regular user and use up quota
    User.create_or_update("regular_user_id", "regular@example.com")
    for _ in range(5):
        User.increment_question_count("regular_user_id")

    response = client.post(
        "/api/admin/reset-quota",
        params={"email": "regular@example.com"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "regular@example.com"
    assert data["question_count"] == 0
