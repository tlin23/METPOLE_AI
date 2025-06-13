"""
Admin routes for the application.
"""

from fastapi import APIRouter, Depends
from ..auth import validate_token, require_admin
from ..models.models import AdminMeResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def admin_health(user_info: dict = Depends(require_admin)):
    """
    Admin health check endpoint that verifies admin access and system status.
    Returns 200 if user is authorized and system is healthy.
    """
    return HealthResponse(
        status="ok",
        system={
            "status": "operational",
            "admin_access": True,
            "message": "Admin access verified",
            "user": {"email": user_info["email"], "is_admin": user_info["is_admin"]},
        },
    )


@router.get("/me", response_model=AdminMeResponse)
def get_me(user_info: dict = Depends(validate_token)):
    """
    Get current user information including admin status.
    Any authenticated user can check their own admin status.
    """
    return AdminMeResponse(email=user_info["email"], is_admin=user_info["is_admin"])
