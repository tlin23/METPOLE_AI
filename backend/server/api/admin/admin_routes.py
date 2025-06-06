"""
Admin API routes for the application.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import uuid

from backend.server.api.admin.auth import validate_token, require_admin
from backend.server.database.models import User
from backend.server.database.connection import get_db_connection

# Create admin router
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/list")
async def list_admins(
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """List all admin users."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT user_id, email FROM users WHERE is_admin = 1")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


@router.post("/add")
async def add_admin(
    email: str, user_info: Dict[str, Any] = Depends(validate_token)
) -> Dict[str, Any]:
    """Add a new admin user."""
    conn = get_db_connection()
    try:
        # Check if this is the first admin
        cursor = conn.execute(
            "SELECT COUNT(*) as admin_count FROM users WHERE is_admin = 1"
        )
        is_first_admin = cursor.fetchone()["admin_count"] == 0

        # If not first admin, require admin privileges
        if not is_first_admin:
            # Verify current user is admin
            current_user = User.get(user_info["user_id"])
            if not current_user or not current_user["is_admin"]:
                raise HTTPException(status_code=403, detail="Admin privileges required")

        # First check if user exists
        cursor = conn.execute(
            "SELECT user_id, email FROM users WHERE email = ?", (email,)
        )
        row = cursor.fetchone()

        if not row:
            # User doesn't exist, create them with a new user_id
            new_user_id = str(uuid.uuid4())
            cursor = conn.execute(
                """
                INSERT INTO users (user_id, email, is_admin, question_count, last_question_reset)
                VALUES (?, ?, 1, 0, date('now'))
                RETURNING user_id, email
                """,
                (new_user_id, email),
            )
            row = cursor.fetchone()
        else:
            # User exists, update their admin status
            cursor = conn.execute(
                "UPDATE users SET is_admin = 1 WHERE email = ? RETURNING user_id, email",
                (email,),
            )
            row = cursor.fetchone()

        conn.commit()
        return dict(row)
    finally:
        conn.close()


@router.post("/remove")
async def remove_admin(
    email: str, user_info: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Remove admin privileges from a user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "UPDATE users SET is_admin = 0 WHERE email = ? RETURNING user_id, email",
            (email,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return dict(row)
    finally:
        conn.close()


@router.post("/reset-quota")
async def reset_quota(
    email: str, user_info: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Reset question quota for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE users
            SET question_count = 0, last_question_reset = date('now')
            WHERE email = ?
            RETURNING user_id, email, question_count
        """,
            (email,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return dict(row)
    finally:
        conn.close()


@router.get("/check-quota")
async def check_quota(
    email: str, user_info: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Check question quota for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT user_id, email, question_count, last_question_reset
            FROM users
            WHERE email = ?
        """,
            (email,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)
    finally:
        conn.close()
