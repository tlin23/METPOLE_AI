import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from backend.server.auth import validate_token, require_admin

pytestmark = pytest.mark.asyncio  # Mark all tests in this module as async


@pytest.fixture
def mock_token():
    """Create a mock token for testing."""
    return MagicMock(credentials="mock_token")


@pytest.fixture
def mock_user_info():
    """Create mock user info for testing."""
    return {"user_id": "test_user_id", "email": "test@example.com"}


@pytest.mark.auth
@patch("backend.server.auth.id_token.verify_oauth2_token")
@patch("backend.server.auth.User.get")
@patch("backend.server.auth.User.create_or_update")
async def test_validate_token_success(
    mock_create_or_update,
    mock_get,
    mock_verify_token,
    mock_token,
):
    """Test successful token validation."""
    # Mock the token verification
    mock_verify_token.return_value = {
        "sub": "test_user_id",
        "email": "test@example.com",
    }

    # Mock existing user
    mock_get.return_value = {"is_admin": False}

    # Test the function
    result = await validate_token(mock_token)

    assert result["user_id"] == "test_user_id"
    assert result["email"] == "test@example.com"
    mock_create_or_update.assert_called_once()


@pytest.mark.auth
async def test_validate_token_missing_credentials():
    """Test token validation with missing credentials."""
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(None)
    assert exc_info.value.status_code == 401
    assert "Missing authentication credentials" in str(exc_info.value.detail)


@pytest.mark.auth
@patch("backend.server.auth.id_token.verify_oauth2_token")
async def test_validate_token_invalid(mock_verify_token, mock_token):
    """Test token validation with invalid token."""
    mock_verify_token.side_effect = ValueError("Invalid token")

    with pytest.raises(HTTPException) as exc_info:
        await validate_token(mock_token)
    assert exc_info.value.status_code == 401
    assert "Invalid authentication credentials" in str(exc_info.value.detail)


@pytest.mark.auth
@patch("backend.server.auth.User.get")
async def test_require_admin_success(mock_get, mock_user_info):
    """Test successful admin requirement check."""
    mock_get.return_value = {"is_admin": True}

    result = await require_admin(mock_user_info)
    assert result == mock_user_info


@pytest.mark.auth
@patch("backend.server.auth.User.get")
async def test_require_admin_failure(mock_get, mock_user_info):
    """Test admin requirement check failure."""
    # Mock the user lookup to return a non-admin user
    mock_get.return_value = {"is_admin": False}

    # The function should raise HTTPException for non-admin users
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_user_info)
    assert exc_info.value.status_code == 403
    assert "Admin privileges required" in str(exc_info.value.detail)


@pytest.mark.auth
@patch("backend.server.auth.User.get")
async def test_require_admin_user_not_found(mock_get, mock_user_info):
    """Test admin requirement check when user is not found."""
    # Mock the user lookup to return None (user not found)
    mock_get.return_value = None

    # The function should raise HTTPException when user is not found
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(mock_user_info)
    assert exc_info.value.status_code == 403
    assert "Admin privileges required" in str(exc_info.value.detail)
