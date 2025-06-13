"""Integration tests for OAuth flow and authentication."""

import pytest


def test_oauth_callback_endpoint(nginx_server):
    """Test that OAuth callback endpoint is reachable through Nginx proxy."""
    response = nginx_server("http://localhost:3000/oauth2/callback")
    assert response.status_code in [200, 302]  # Either success or redirect


def test_protected_route_unauthorized(client):
    """Test that protected routes return 401 without auth."""
    response = client.post("/api/ask", json={"question": "test question", "top_k": 5})
    assert response.status_code == 401
    assert "Missing authentication credentials" in response.json()["detail"]


@pytest.mark.usefixtures("mock_google_auth")
def test_protected_route_authorized(client, mock_auth_headers):
    """Test that protected routes work with valid auth."""
    response = client.post(
        "/api/ask",
        json={"question": "test question", "top_k": 5},
        headers=mock_auth_headers,
    )
    assert response.status_code == 200


def test_nginx_proxy_routes(nginx_server):
    """Test that Nginx proxy routes are accessible."""
    # Test OAuth2 proxy route
    response = nginx_server("http://localhost:3000/oauth2/")
    assert response.status_code in [200, 302]  # Either success or redirect

    # Test admin route (should be protected)
    response = nginx_server("http://localhost:3000/admin/")
    assert response.status_code == 401


@pytest.mark.parametrize("mock_google_auth", ["admin"], indirect=True)
def test_admin_route_authorized(client, mock_auth_headers, mock_google_auth):
    """Test that admin routes work with valid auth."""
    response = client.get("/api/admin/health", headers=mock_auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["system"]["admin_access"] is True


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options(
        "/api/ask",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


def test_invalid_token(client):
    """Test that invalid tokens are rejected."""
    response = client.post(
        "/api/ask",
        json={"question": "test question", "top_k": 5},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]
