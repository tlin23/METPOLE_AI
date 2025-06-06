"""Integration tests for admin API routes."""

import pytest
from fastapi.testclient import TestClient
from backend.server.app import service
from backend.server.tests.conftest import get_test_db_connection


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(service)


def test_list_admins_unauthorized(client):
    """Test listing admins without authentication fails."""
    response = client.get("/api/admin/list")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_list_admins_not_admin(client, mock_auth_headers, mock_regular_user):
    """Test listing admins as non-admin user fails."""
    response = client.get("/api/admin/list", headers=mock_auth_headers)
    assert response.status_code == 403


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_list_admins_success(
    client, mock_auth_headers, mock_admin_user, mock_google_auth
):
    """Test successfully listing admins returns admin list."""
    response = client.get("/api/admin/list", headers=mock_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "user_id" in data[0]
    assert "email" in data[0]


def test_add_admin_unauthorized(client):
    """Test adding admin without authentication fails."""
    response = client.post("/api/admin/add?email=newadmin@example.com")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_add_admin_not_admin(
    client, mock_auth_headers, mock_regular_user, user_factory
):
    """Test adding admin as non-admin user fails."""
    # Ensure there is already an admin in the system
    user_factory(email="existingadmin@example.com", is_admin=True)
    response = client.post(
        "/api/admin/add?email=newadmin@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_add_admin_success(
    client, mock_auth_headers, mock_admin_user, mock_google_auth
):
    """Test successfully adding an admin returns user data."""
    response = client.post(
        "/api/admin/add?email=newadmin@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert data["email"] == "newadmin@example.com"


def test_remove_admin_unauthorized(client):
    """Test removing admin without authentication fails."""
    response = client.post("/api/admin/remove?email=admin@example.com")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_remove_admin_not_admin(client, mock_auth_headers, mock_regular_user):
    """Test removing admin as non-admin user fails."""
    response = client.post(
        "/api/admin/remove?email=admin@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_remove_admin_success(
    client, mock_auth_headers, mock_admin_user, user_factory, mock_google_auth
):
    """Test successfully removing an admin returns user data."""
    # First create an admin user
    admin_email = "admin_to_remove@example.com"
    user_factory(email=admin_email, is_admin=True)

    response = client.post(
        f"/api/admin/remove?email={admin_email}",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert data["email"] == admin_email


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_remove_admin_not_found(
    client, mock_auth_headers, mock_admin_user, mock_google_auth
):
    """Test removing non-existent admin returns 404."""
    response = client.post(
        "/api/admin/remove?email=nonexistent@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 404


def test_reset_quota_unauthorized(client):
    """Test resetting quota without authentication fails."""
    response = client.post("/api/admin/reset-quota?email=user@example.com")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_reset_quota_not_admin(client, mock_auth_headers, mock_regular_user):
    """Test resetting quota as non-admin user fails."""
    response = client.post(
        "/api/admin/reset-quota?email=user@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_reset_quota_success(
    client, mock_auth_headers, mock_admin_user, user_factory, mock_google_auth
):
    """Test successfully resetting a user's quota returns user data."""
    # Create a user with some question count
    user_email = "user_to_reset@example.com"
    user_id = user_factory(email=user_email)

    conn = get_test_db_connection()
    try:
        conn.execute(
            "UPDATE users SET question_count = 5 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.post(
        f"/api/admin/reset-quota?email={user_email}",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "question_count" in data
    assert data["question_count"] == 0


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_reset_quota_not_found(
    client, mock_auth_headers, mock_admin_user, mock_google_auth
):
    """Test resetting quota for non-existent user returns 404."""
    response = client.post(
        "/api/admin/reset-quota?email=nonexistent@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 404


def test_check_quota_unauthorized(client):
    """Test checking quota without authentication fails."""
    response = client.get("/api/admin/check-quota?email=user@example.com")
    assert response.status_code == 401


@pytest.mark.usefixtures("mock_google_auth")
def test_check_quota_not_admin(client, mock_auth_headers, mock_regular_user):
    """Test checking quota as non-admin user fails."""
    response = client.get(
        "/api/admin/check-quota?email=user@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_check_quota_success(
    client, mock_auth_headers, mock_admin_user, user_factory, mock_google_auth
):
    """Test successfully checking a user's quota returns quota data."""
    # Create a user with some question count
    user_email = "user_to_check@example.com"
    user_id = user_factory(email=user_email)

    conn = get_test_db_connection()
    try:
        conn.execute(
            "UPDATE users SET question_count = 5 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.get(
        f"/api/admin/check-quota?email={user_email}",
        headers=mock_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "question_count" in data
    assert "last_question_reset" in data
    assert data["question_count"] == 5


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_check_quota_not_found(
    client, mock_auth_headers, mock_admin_user, mock_google_auth
):
    """Test checking quota for non-existent user returns 404."""
    response = client.get(
        "/api/admin/check-quota?email=nonexistent@example.com",
        headers=mock_auth_headers,
    )
    assert response.status_code == 404
