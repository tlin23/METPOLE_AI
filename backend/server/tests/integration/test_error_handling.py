"""
Tests for error handling and logging functionality.
"""

import pytest

from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.server.app import service


class TestErrorHandling:
    """Test error handling across the application."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(service)

    def test_http_exception_handler_401(self, client):
        """Test HTTP exception handler for 401 errors."""
        response = client.post(
            "/api/ask",
            json={"question": "test question"},
            # No authorization header
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "authentication" in data["message"].lower()
        assert data["error_code"] == 401

    def test_http_exception_handler_429_quota(self, client, mock_google_auth):
        """Test HTTP exception handler for 429 rate limit errors."""
        # Mock user with exceeded quota
        with patch(
            "backend.server.database.models.User.increment_question_count"
        ) as mock_quota:
            mock_quota.return_value = 0  # No quota remaining

            response = client.post(
                "/api/ask",
                json={"question": "test question"},
                headers={"Authorization": "Bearer mock_token"},
            )

        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert "daily question limit" in data["message"].lower()
        assert data["error_code"] == 429
        assert "quota_remaining" in data
        assert "reset_time" in data

    def test_ask_endpoint_exception_handling(self, client, mock_google_auth):
        """Test exception handling in ask endpoint specifically."""
        with patch("backend.server.api.main.main_routes.retriever.query") as mock_query:
            mock_query.side_effect = Exception("Vector store error")

            response = client.post(
                "/api/ask",
                json={"question": "test question"},
                headers={"Authorization": "Bearer mock_token"},
            )

        # Ask endpoint catches exceptions and returns 200 with error in body
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Error:" in data["message"]
        assert "stacktrace" in data

    def test_feedback_endpoint_error_handling(self, client, mock_google_auth):
        """Test error handling in feedback endpoints."""
        with patch(
            "backend.server.database.models.Feedback.create_or_update"
        ) as mock_feedback:
            mock_feedback.side_effect = Exception("Database error")

            response = client.post(
                "/api/feedback",
                json={"answer_id": "123", "like": True},
                headers={"Authorization": "Bearer mock_token"},
            )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "failed to store feedback" in data["message"].lower()

    def test_invalid_json_request(self, client, mock_google_auth):
        """Test handling of invalid JSON requests."""
        response = client.post(
            "/api/ask",
            content="invalid json",  # Use content instead of data
            headers={
                "Authorization": "Bearer mock_token",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 422
        data = response.json()
        # FastAPI 422 responses have different structure
        assert "detail" in data

    def test_missing_required_fields(self, client, mock_google_auth):
        """Test handling of requests with missing required fields."""
        response = client.post(
            "/api/ask",
            json={},  # Missing question field
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 422
        data = response.json()
        # FastAPI 422 responses have different structure
        assert "detail" in data


class TestLogging:
    """Test logging functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(service)

    def test_auth_logging(self, client, mock_google_auth, caplog):
        """Test authentication logging."""
        # Test successful auth - use a protected endpoint
        client.post(
            "/api/ask",
            json={"question": "test question"},
            headers={"Authorization": "Bearer mock_token"},
        )

        # Check for successful auth log
        assert any(
            "Successful authentication" in record.message for record in caplog.records
        )

    def test_failed_auth_logging(self, client, caplog):
        """Test failed authentication logging."""
        with patch(
            "backend.server.api.auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")

            client.post(
                "/api/ask",
                json={"question": "test"},
                headers={"Authorization": "Bearer invalid_token"},
            )

        # Check for failed auth log
        assert any(
            "Invalid authentication token" in record.message
            for record in caplog.records
        )

    def test_question_processing_logging(self, client, mock_google_auth, caplog):
        """Test logging during question processing."""
        with patch(
            "backend.server.api.main.main_routes.retriever.query"
        ) as mock_query, patch(
            "backend.server.api.main.main_routes.retriever.generate_answer"
        ) as mock_answer:

            mock_query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }
            mock_answer.return_value = {"answer": "Test answer"}

            client.post(
                "/api/ask",
                json={"question": "test question"},
                headers={"Authorization": "Bearer mock_token"},
            )

        # Check for question processing logs
        assert any(
            "Question asked by user" in record.message for record in caplog.records
        )
        assert any(
            "Question processed for" in record.message for record in caplog.records
        )

    def test_quota_exceeded_logging(self, client, mock_google_auth, caplog):
        """Test logging when user exceeds quota."""
        with patch(
            "backend.server.database.models.User.increment_question_count"
        ) as mock_quota:
            mock_quota.return_value = 0

            client.post(
                "/api/ask",
                json={"question": "test question"},
                headers={"Authorization": "Bearer mock_token"},
            )

        # Check for quota exceeded log
        assert any(
            "exceeded daily quota" in record.message for record in caplog.records
        )

    def test_feedback_logging(self, client, mock_google_auth, caplog):
        """Test feedback submission logging."""
        with patch("backend.server.database.models.Feedback.create_or_update"), patch(
            "backend.server.database.models.Feedback.get"
        ) as mock_get:

            mock_get.return_value = {
                "answer_id": "123",
                "like": True,
                "suggestion": None,
            }

            client.post(
                "/api/feedback",
                json={"answer_id": "123", "like": True},
                headers={"Authorization": "Bearer mock_token"},
            )

        # Check for feedback log
        assert any("Feedback submitted" in record.message for record in caplog.records)

    def test_error_logging(self, client, mock_google_auth, caplog):
        """Test error logging."""
        with patch("backend.server.api.main.main_routes.retriever.query") as mock_query:
            mock_query.side_effect = Exception("Test error")

            client.post(
                "/api/ask",
                json={"question": "test question"},
                headers={"Authorization": "Bearer mock_token"},
            )

        # Check for error logs
        assert any(
            "Error processing question" in record.message for record in caplog.records
        )
        assert any("Traceback:" in record.message for record in caplog.records)


class TestNginxErrorHandling:
    """Test nginx error handling scenarios."""

    def test_api_error_response_format(self, client):
        """Test that API errors return proper JSON format expected by nginx."""
        response = client.post("/api/ask", json={"question": "test"})

        assert response.status_code == 401
        data = response.json()

        # Verify structure matches nginx @api_error expectations
        assert "success" in data
        assert "message" in data
        assert data["success"] is False
        assert isinstance(data["message"], str)

    def test_health_endpoint_for_nginx(self, client):
        """Test health endpoint that nginx can use for upstream checks."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
