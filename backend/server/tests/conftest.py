"""Shared fixtures for all tests."""

import os
import sqlite3
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from backend.server.app import service

from backend.server.tests.factories.factories import (
    user_factory,  # noqa: F401
    session_factory,  # noqa: F401
    question_factory,  # noqa: F401
    answer_factory,  # noqa: F401
    feedback_factory,  # noqa: F401
)

TEST_DB_PATH = Path(__file__).parent / "test.db"

# Mock OpenAI response
MOCK_OPENAI_RESPONSE = {
    "answer": "This is a mock response from the AI assistant.",
    "is_general_knowledge": False,
    "contains_diy_advice": False,
    "source_info": "Mock source information",
    "prompt": "Mock prompt used for generation",
}

# Mock Google OAuth
MOCK_ADMIN_USER_INFO = {
    "sub": "mock-admin-id",
    "email": "admin@example.com",
    "name": "Admin User",
    "picture": "https://example.com/photo.jpg",
}
MOCK_REGULAR_USER_INFO = {
    "sub": "mock-user-id",
    "email": "user@example.com",
    "name": "Regular User",
    "picture": "https://example.com/photo.jpg",
}


def get_test_db_connection():
    """Get a connection to the test database."""
    return sqlite3.connect(TEST_DB_PATH)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a fresh test database before the test session and clean up after."""
    # Set test database path in environment
    os.environ["METROPOLE_DB_PATH"] = str(TEST_DB_PATH)

    # Ensure we're not using the production database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Create test database and initialize schema
    conn = get_test_db_connection()
    try:
        with open(Path(__file__).parent.parent / "database" / "schema.sql") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

    yield

    # Clean up after tests
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    # Remove environment variable
    os.environ.pop("METROPOLE_DB_PATH", None)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean all tables before each test."""
    conn = get_test_db_connection()
    try:
        # Disable foreign key checks temporarily
        conn.execute("PRAGMA foreign_keys = OFF")

        # Get all tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Truncate each table
        for table in tables:
            conn.execute(f"DELETE FROM {table}")

        conn.commit()
    finally:
        # Re-enable foreign key checks
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Set admin emails for testing
    os.environ["ADMIN_EMAILS"] = "admin@example.com"
    # Set Google client ID for testing
    os.environ["GOOGLE_CLIENT_ID"] = "mock-client-id"
    yield
    # Clean up
    os.environ.pop("ADMIN_EMAILS", None)
    os.environ.pop("GOOGLE_CLIENT_ID", None)


@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI API calls to return predefined responses."""
    with patch("openai.OpenAI") as mock_client_global, patch(
        "backend.server.retriever.ask.OpenAI"
    ) as mock_client_local:
        # Create mock chat completion
        mock_message = ChatCompletionMessage(
            role="assistant", content=MOCK_OPENAI_RESPONSE["answer"]
        )
        mock_choice = Choice(message=mock_message, finish_reason="stop", index=0)
        mock_completion = ChatCompletion(
            id="mock-id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion",
        )
        # Set up the mock client for both global and local
        for mock_client in (mock_client_global, mock_client_local):
            mock_instance = mock_client.return_value
            mock_instance.chat.completions.create.return_value = mock_completion
        yield


@pytest.fixture
def mock_google_auth(request):
    """Mock Google OAuth token verification for admin or regular user."""
    user_type = getattr(request, "param", "regular")
    user_info = MOCK_ADMIN_USER_INFO if user_type == "admin" else MOCK_REGULAR_USER_INFO
    with patch("google.oauth2.id_token.verify_oauth2_token") as mock_verify:
        mock_verify.return_value = user_info
        yield mock_verify


@pytest.fixture
def mock_auth_headers():
    """Generate mock authorization headers for testing."""
    return {"Authorization": "Bearer mock-token"}


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    from backend.server.database.models import User

    user_id = MOCK_ADMIN_USER_INFO["sub"]
    User.create_or_update(user_id, MOCK_ADMIN_USER_INFO["email"])
    return user_id


@pytest.fixture
def regular_user():
    """Create a regular user for testing."""
    from backend.server.database.models import User

    user_id = MOCK_REGULAR_USER_INFO["sub"]
    User.create_or_update(user_id, MOCK_REGULAR_USER_INFO["email"])
    return user_id


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(service)


@pytest.fixture(scope="session")
def nginx_server():
    """Mock Nginx server that proxies to OAuth2 Proxy."""
    # Create a mock response that simulates OAuth2 Proxy behavior
    mock_oauth_response = MagicMock()
    mock_oauth_response.status_code = 302
    mock_oauth_response.headers = {
        "Location": "http://localhost:3000/",
        "x-auth-request-user": "test@example.com",
        "x-auth-request-email": "test@example.com",
        "x-auth-request-access-token": "mock-token",
    }
    mock_oauth_response.cookies = {"oauth2_proxy": {"secure": True, "samesite": "lax"}}

    # Create a mock response for admin routes
    mock_admin_response = MagicMock()
    mock_admin_response.status_code = 401
    mock_admin_response.headers = {}
    mock_admin_response.cookies = {}

    def mock_get(url, *args, **kwargs):
        if url.startswith("http://localhost:3000/oauth2/"):
            return mock_oauth_response
        elif url.startswith("http://localhost:3000/admin/"):
            return mock_admin_response
        # For any other routes, return a 404
        mock_404_response = MagicMock()
        mock_404_response.status_code = 404
        mock_404_response.headers = {}
        mock_404_response.cookies = {}
        return mock_404_response

    with patch("requests.get", side_effect=mock_get) as mock:
        yield mock
