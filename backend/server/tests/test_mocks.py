"""Tests for mock implementations of external services."""

from unittest.mock import MagicMock, patch
import pytest
from google.oauth2 import id_token
from backend.server.retriever.ask import Retriever
from backend.server.retriever.models import RetrievedChunk
from backend.server.api.admin.auth import validate_token
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def test_openai_mock():
    with patch("openai.OpenAI") as mock_client:
        mock_message = MagicMock()
        mock_message.content = "This is a mock response from the AI assistant."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-3.5-turbo"
        mock_client.return_value.chat.completions.create.return_value = mock_response

        from openai import OpenAI  # <-- Import inside the patch context!

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is AI?"},
            ],
        )
        assert (
            response.choices[0].message.content
            == "This is a mock response from the AI assistant."
        )
    assert response.model == "gpt-3.5-turbo"
    assert response.choices[0].finish_reason == "stop"


def test_retriever_with_mock_openai():
    """Test that Retriever works with mocked OpenAI."""
    retriever = Retriever()

    # Create mock chunks with metadata
    chunks = [
        RetrievedChunk(
            text="Some mock text",
            metadata={
                "chunk_id": "1",
                "document_title": "Mock Document",
                "section": "Introduction",
            },
        )
    ]
    result = retriever.generate_answer("What is AI?", chunks)
    assert result["answer"] == "This is a mock response from the AI assistant."
    assert not result["is_general_knowledge"]
    assert not result["contains_diy_advice"]
    assert result["source_info"] == "Chunk 1 (Introduction) from Mock Document"


def test_google_auth_mock(mock_google_auth):
    """Test that Google OAuth token verification is properly mocked."""
    # Create mock credentials
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="mock-token"
    )
    # Verify token
    user_info = id_token.verify_oauth2_token(
        credentials.credentials,
        None,  # Request object not needed for mock
        "mock-client-id",
    )
    assert user_info["sub"] == "mock-user-id"
    assert user_info["email"] == "user@example.com"
    assert user_info["name"] == "Regular User"


@pytest.mark.asyncio
async def test_auth_middleware_with_mock(mock_google_auth):
    """Test that auth middleware works with mocked Google OAuth."""
    # Create mock credentials
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="mock-token"
    )
    # Test successful auth
    user_info = await validate_token(credentials)
    assert user_info["user_id"] == "mock-user-id"
    assert user_info["email"] == "user@example.com"
    # Test missing credentials
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(None)
    assert exc_info.value.status_code == 401
    assert "Missing authentication credentials" in str(exc_info.value.detail)


def test_mock_users(mock_admin_user, mock_regular_user):
    """Test that mock user creation works correctly."""
    from backend.server.database.models import User

    # Check admin user
    admin = User.get(mock_admin_user)
    assert admin is not None
    assert admin["email"] == "admin@example.com"
    assert admin["is_admin"] == 1
    # Check regular user
    regular = User.get(mock_regular_user)
    assert regular is not None
    assert regular["email"] == "user@example.com"
    assert regular["is_admin"] == 0
