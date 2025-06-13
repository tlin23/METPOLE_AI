"""
Authentication middleware and utilities for Google OAuth.
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import logging
from typing import Dict, Any
from ..database.models import User

# Set up logging
logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)

# Google OAuth client ID
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is required")

# Get admin emails from environment
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS").split(",")


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Validate Google ID token and return user info.

    Args:
        credentials: HTTP Authorization credentials containing the token

    Returns:
        Dict containing user info (sub, email, is_admin)

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        logger.warning("Missing authentication credentials in request")
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

        # Create or update user in database
        User.create_or_update(user_id, email)

        # Check if user is admin (load dynamically for testing)
        admin_emails = [
            e.strip() for e in os.getenv("ADMIN_EMAILS").split(",") if e.strip()
        ]
        is_admin = email in admin_emails

        logger.info(f"Successful authentication for user: {email}")
        return {"user_id": user_id, "email": email, "is_admin": is_admin}
    except ValueError as e:
        logger.error(f"Invalid authentication token: {str(e)}")
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def require_admin(
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """
    Dependency that requires admin access.

    Args:
        user_info: User info from validate_token

    Returns:
        Dict containing user info (only for admin users)

    Raises:
        HTTPException: If user is not an admin
    """
    if not user_info.get("is_admin", False):
        logger.warning(
            f"Non-admin user {user_info.get('email')} attempted to access admin endpoint"
        )
        raise HTTPException(status_code=403, detail="Admin access required")

    return user_info
