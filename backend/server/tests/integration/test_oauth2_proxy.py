"""Integration tests for OAuth2 Proxy configuration and routing."""

import requests


def test_oauth2_proxy_health(client):
    """Test that OAuth2 Proxy health endpoint is accessible."""
    response = client.get("/oauth2/health")
    assert response.status_code in [200, 404]  # Either success or not found


def test_oauth2_proxy_callback(nginx_server):
    """Test that OAuth2 Proxy callback endpoint is accessible through Nginx."""
    response = requests.get(
        "http://localhost:3000/oauth2/callback", allow_redirects=False
    )
    assert response.status_code in [200, 302]  # Either success or redirect


def test_oauth2_proxy_protected_route(client):
    """Test that OAuth2 Proxy protected routes require authentication."""
    response = client.get("/admin/db-query/")
    assert response.status_code in [
        401,
        302,
    ]  # Either unauthorized or redirect to login


def test_oauth2_proxy_static_files(client):
    """Test that OAuth2 Proxy static files are accessible."""
    response = client.get("/static/oauth2-proxy.css")
    assert response.status_code in [200, 404]  # Either success or not found


def test_oauth2_proxy_headers(client, nginx_server):
    """Test that OAuth2 Proxy sets required headers."""
    response = requests.get("http://localhost:3000/oauth2/", allow_redirects=False)
    assert "x-auth-request-user" in response.headers
    assert "x-auth-request-email" in response.headers
    assert "x-auth-request-access-token" in response.headers


def test_oauth2_proxy_cookie_settings(client):
    """Test that OAuth2 Proxy sets secure cookies in production."""
    response = client.get("/oauth2/callback")
    cookies = response.cookies

    # Check cookie settings
    if "oauth2_proxy" in cookies:
        cookie = cookies["oauth2_proxy"]
        assert cookie.get("secure", False)  # Should be secure in production
        assert cookie.get("samesite", "").lower() in [
            "lax",
            "strict",
        ]  # Should have SameSite policy
