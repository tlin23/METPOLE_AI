"""
Admin routes for the application.
"""

from fastapi import APIRouter, Depends, HTTPException
from ..auth import validate_token
import os

router = APIRouter()


@router.get("/health")
async def admin_health(user_info: dict = Depends(validate_token)):
    """
    Admin health check endpoint that verifies admin access and system status.
    Returns 200 if user is authorized and system is healthy.
    """
    # Check if user is admin (email is in allowed list)
    if not user_info.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access the admin interface",
        )
    return {
        "status": "ok",
        "message": "Admin access verified",
        "system": {"status": "operational", "admin_access": True},
    }


@router.get("/me")
def get_me(user_info: dict = Depends(validate_token)):
    admin_emails = [
        e.strip() for e in os.environ.get("ADMIN_EMAILS").split(",") if e.strip()
    ]
    email = user_info.get("email")
    is_admin = email in admin_emails
    return {"email": email, "is_admin": is_admin}
