import pytest
from fastapi.testclient import TestClient
from backend.server.app import service


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(service)


@pytest.mark.api
def test_app_title(client):
    """Test that the application has the correct title."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "MetPol AI" in response.text


@pytest.mark.api
def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options(
        "/api/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "http://localhost:5173" in response.headers["access-control-allow-origin"]


@pytest.mark.api
def test_api_router_included(client):
    """Test that the API router is included in the application."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
