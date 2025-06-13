"""Integration tests for main API routes."""

import pytest
from fastapi.testclient import TestClient
from backend.server.app import service
from unittest.mock import patch


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(service)


def test_health_check(client):
    """Test the health check endpoint returns system status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "system" in data
    assert data["system"]["status"] == "operational"


def test_ask_question_unauthorized(client):
    """Test asking a question without authentication fails."""
    response = client.post(
        "/api/ask",
        json={"question": "What is AI?", "top_k": 3},
    )
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_ask_question_success(client, mock_auth_headers, regular_user):
    """Test successfully asking a question returns answer and metadata."""
    response = client.post(
        "/api/ask",
        json={"question": "What is AI?", "top_k": 3},
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "answer" in data
    assert "chunks" in data
    assert "quota_remaining" in data
    assert data["question"] == "What is AI?"


@pytest.mark.usefixtures("mock_google_auth")
def test_ask_question_quota_exceeded(client, mock_google_auth):
    """Test the ask endpoint returns 429 when quota is exceeded."""
    with patch(
        "backend.server.database.models.User.increment_question_count"
    ) as mock_quota:
        mock_quota.return_value = 0  # No quota remaining
        response = client.post(
            "/api/ask",
            json={"question": "What is AI?"},
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 429
    data = response.json()
    # Updated to use our new structured error format
    assert data["success"] is False
    assert "daily question limit" in data["message"]
    assert data["error_code"] == 429
    assert "quota_remaining" in data
    assert "reset_time" in data


def test_create_feedback_unauthorized(client):
    """Test creating feedback without authentication fails."""
    response = client.post(
        "/api/feedback",
        json={"answer_id": "test-id", "like": True},
    )
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_create_feedback_success(
    client, mock_auth_headers, regular_user, answer_factory
):
    """Test successfully creating feedback returns feedback data."""
    answer_id = answer_factory()
    response = client.post(
        "/api/feedback",
        json={"answer_id": answer_id, "like": True, "suggestion": "Great answer!"},
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "feedback_id" in data
    assert data["answer_id"] == answer_id
    assert data["like"] is True
    assert data["suggestion"] == "Great answer!"
    assert "created_at" in data


def test_get_feedback_unauthorized(client):
    """Test getting feedback without authentication fails."""
    response = client.get("/api/feedback?answer_id=test-id")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_get_feedback_success(
    client, mock_auth_headers, regular_user, feedback_factory
):
    """Test successfully getting feedback returns feedback data."""
    feedback = feedback_factory(user_id=regular_user, return_full=True)
    response = client.get(
        f"/api/feedback?answer_id={feedback['answer_id']}",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "feedback_id" in data
    assert "like" in data
    assert "suggestion" in data


@pytest.mark.usefixtures("mock_google_auth")
def test_get_feedback_not_found(client, mock_auth_headers, regular_user):
    """Test getting non-existent feedback returns 404."""
    response = client.get(
        "/api/feedback?answer_id=non-existent",
        headers=mock_auth_headers,
    )
    assert response.status_code == 404


def test_delete_feedback_unauthorized(client):
    """Test deleting feedback without authentication fails."""
    response = client.delete("/api/feedback?answer_id=test-id")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_delete_feedback_success(
    client, mock_auth_headers, regular_user, feedback_factory
):
    """Test successfully deleting feedback returns success."""
    feedback = feedback_factory(user_id=regular_user, return_full=True)
    response = client.delete(
        f"/api/feedback?answer_id={feedback['answer_id']}",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.usefixtures("mock_google_auth")
def test_delete_feedback_not_found(client, mock_auth_headers, regular_user):
    """Test deleting non-existent feedback returns 404."""
    response = client.delete(
        "/api/feedback?answer_id=non-existent",
        headers=mock_auth_headers,
    )
    assert response.status_code == 404
