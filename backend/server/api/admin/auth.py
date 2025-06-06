"""
Authentication middleware and utilities for Google OAuth.
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from typing import Dict, Any
from ...database.models import User

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)

# Google OAuth client ID
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is required")


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Validate Google ID token and return user info.

    Args:
        credentials: HTTP Authorization credentials containing the token

    Returns:
        Dict containing user info (sub, email)

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=401, detail="Missing authentication credentials"
        )

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            credentials.credentials, requests.Request(), GOOGLE_CLIENT_ID
        )

        # Get user info
        user_id = idinfo["sub"]
        email = idinfo["email"]

        # Get existing user to preserve admin status
        existing_user = User.get(user_id)
        is_admin = existing_user["is_admin"] if existing_user else False

        # Create or update user in database
        User.create_or_update(user_id, email, is_admin=is_admin)

        return {"user_id": user_id, "email": email}
    except ValueError as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid authentication credentials: {str(e)}"
        )


async def require_admin(
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """
    Check if user has admin privileges.

    Args:
        user_info: User info from validate_token

    Returns:
        User info if admin

    Raises:
        HTTPException: If user is not an admin
    """
    user = User.get(user_info["user_id"])
    if not user or not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user_info
