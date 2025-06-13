"""
Admin routes for the application.
"""

from fastapi import APIRouter, Depends
from ..auth import validate_token, require_admin

router = APIRouter()


@router.get("/health")
async def admin_health(user_info: dict = Depends(require_admin)):
    """
    Admin health check endpoint that verifies admin access and system status.
    Returns 200 if user is authorized and system is healthy.
    """
    return {
        "status": "ok",
        "message": "Admin access verified",
        "system": {"status": "operational", "admin_access": True},
        "user": {"email": user_info["email"], "is_admin": user_info["is_admin"]},
    }


@router.get("/me")
def get_me(user_info: dict = Depends(validate_token)):
    """
    Get current user information including admin status.
    This endpoint doesn't require admin access - any authenticated user can check their status.
    """
    return {"email": user_info["email"], "is_admin": user_info["is_admin"]}
