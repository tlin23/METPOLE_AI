"""
End-to-end integration tests for the complete user journey.
Tests the requirements from Prompt 8: End-to-End Happy Path
"""

import pytest
from fastapi.testclient import TestClient
from backend.server.app import service


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(service)


@pytest.mark.usefixtures("mock_google_auth")
def test_end_to_end_happy_path_regular_user(
    client, mock_auth_headers, regular_user, answer_factory, clean_db
):
    """
    Test the complete end-to-end user journey:
    1. User logs in (simulated by headers)
    2. User asks a question via /api/ask
    3. User submits feedback and sees confirmation
    4. All interactions work correctly
    """

    # Step 1: User asks a question (simulates frontend login + ask)
    ask_response = client.post(
        "/api/ask",
        json={"question": "What is artificial intelligence?", "top_k": 3},
        headers=mock_auth_headers,
    )

    assert ask_response.status_code == 200
    ask_data = ask_response.json()
    assert ask_data["success"] is True
    assert "answer" in ask_data
    assert "chunks" in ask_data
    assert ask_data["question"] == "What is artificial intelligence?"

    # Step 2: Create a real answer for feedback testing
    answer_id = answer_factory(
        answer_text="AI is a field of computer science focused on creating intelligent machines.",
        prompt="User asked about artificial intelligence",
        retrieved_chunks=[{"text": "AI involves machine learning and neural networks"}],
    )

    # Step 3: User provides positive feedback
    feedback_response = client.post(
        "/api/feedback",
        json={"answer_id": answer_id, "like": True, "suggestion": "Great explanation!"},
        headers=mock_auth_headers,
    )

    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert "feedback_id" in feedback_data
    assert feedback_data["like"] is True
    assert feedback_data["suggestion"] == "Great explanation!"

    # Step 4: User retrieves their feedback (confirmation)
    get_feedback_response = client.get(
        f"/api/feedback?answer_id={answer_id}",
        headers=mock_auth_headers,
    )

    assert get_feedback_response.status_code == 200
    retrieved_feedback = get_feedback_response.json()
    assert retrieved_feedback["like"] is True
    assert retrieved_feedback["suggestion"] == "Great explanation!"


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_end_to_end_admin_access(client, admin_user, clean_db, mock_google_auth):
    """
    Test the complete admin journey:
    1. Admin logs in
    2. Admin fetches /api/admin/me and verifies admin access
    3. Admin can perform regular user actions too
    """
    admin_headers = {"Authorization": "Bearer admin-token"}

    # Step 1: Admin checks their status via /api/admin/me
    admin_me_response = client.get(
        "/api/admin/me",
        headers=admin_headers,
    )

    assert admin_me_response.status_code == 200
    admin_data = admin_me_response.json()
    assert admin_data["is_admin"] is True
    assert "email" in admin_data
    assert admin_data["email"] == "admin@example.com"

    # Step 2: Admin can also ask questions like regular users
    ask_response = client.post(
        "/api/ask",
        json={"question": "Admin testing the system", "top_k": 3},
        headers=admin_headers,
    )

    assert ask_response.status_code == 200
    ask_data = ask_response.json()
    assert ask_data["success"] is True
    assert "answer" in ask_data


@pytest.mark.usefixtures("mock_google_auth")
def test_end_to_end_regular_user_admin_check(
    client, mock_auth_headers, regular_user, clean_db
):
    """
    Test that regular users can check their admin status (should be False).
    This verifies the frontend can determine if admin UI should be shown.
    """
    # Regular user checks admin status
    admin_me_response = client.get(
        "/api/admin/me",
        headers=mock_auth_headers,
    )

    assert admin_me_response.status_code == 200
    admin_data = admin_me_response.json()
    assert admin_data["is_admin"] is False
    assert "email" in admin_data
    assert admin_data["email"] == "user@example.com"


@pytest.mark.usefixtures("mock_google_auth")
def test_end_to_end_auth_flow(client, regular_user, clean_db):
    """
    Test authentication flow - authorized vs unauthorized access.
    """
    # Step 1: Test unauthorized access fails
    unauth_response = client.post(
        "/api/ask",
        json={"question": "Unauthorized question"},
    )
    assert unauth_response.status_code == 401

    # Step 2: Test authorized access succeeds
    auth_headers = {"Authorization": "Bearer mock-token"}
    auth_response = client.post(
        "/api/ask",
        json={"question": "Authorized question", "top_k": 3},
        headers=auth_headers,
    )
    assert auth_response.status_code == 200
    assert auth_response.json()["success"] is True
