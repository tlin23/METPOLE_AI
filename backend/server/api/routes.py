"""
API routes for the application.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
from typing import List, Dict, Any, Optional
import traceback
from datetime import datetime, timedelta, UTC

from .models import AskRequest, ChunkResult, AskResponse, FeedbackRequest
from ..retriever.ask import Retriever
from ..auth import validate_token, require_admin
from ..database import User, Session, Message, Feedback, get_db_connection

# Create router
router = APIRouter()

# Initialize components
retriever = Retriever(production=os.getenv("PRODUCTION", "false").lower() == "true")


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the server is running and check system status.
    Returns information about the system state, including admin existence.
    """
    conn = get_db_connection()
    try:
        # Check if any admins exist
        cursor = conn.execute(
            "SELECT COUNT(*) as admin_count FROM users WHERE is_admin = 1"
        )
        admin_count = cursor.fetchone()["admin_count"]

        return JSONResponse(
            content={
                "status": "ok",
                "system": {"has_admins": admin_count > 0, "admin_count": admin_count},
            }
        )
    finally:
        conn.close()


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest, user_info: Dict[str, Any] = Depends(validate_token)
):
    """
    Ask a question to the chatbot.

    Args:
        request: The question request
        user_info: User info from authentication

    Returns:
        AskResponse with answer and metadata

    Raises:
        HTTPException: If user is over quota
    """
    # Check quota
    quota_remaining = User.increment_question_count(user_info["user_id"])
    if quota_remaining <= 0:
        # Calculate next reset time (midnight UTC)
        now = datetime.now(UTC)
        tomorrow = now + timedelta(days=1)
        reset_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        raise HTTPException(
            status_code=429,
            detail={
                "message": "You have reached your daily question limit. Your quota will reset tomorrow at midnight UTC. Please try again then.",
                "quota_remaining": 0,
                "reset_time": reset_time.isoformat(),
            },
        )

    try:
        # Create session if needed
        session_id = Session.create(user_info["user_id"])

        # Get current timestamp for question
        question_timestamp = datetime.now(UTC)

        # Query the vector store using cosine similarity
        results = retriever.query(request.question, request.top_k)

        # Format the results
        chunks = []
        for i in range(len(results["documents"][0])):
            chunk = ChunkResult(
                text=results["documents"][0][i],
                metadata=(
                    results["metadatas"][0][i]
                    if "metadatas" in results and results["metadatas"][0]
                    else None
                ),
                distance=(
                    results["distances"][0][i]
                    if "distances" in results and results["distances"][0]
                    else None
                ),
            )
            chunks.append(chunk)

        # Generate an answer using OpenAI's GPT model
        answer_result = retriever.generate_answer(request.question, chunks)

        # Log the Q&A pair
        Message.create(
            session_id=session_id,
            user_id=user_info["user_id"],
            question=request.question,
            answer=answer_result["answer"],
            prompt=answer_result.get("prompt", ""),
            question_timestamp=question_timestamp,
            answer_timestamp=datetime.now(UTC),
            retrieved_chunks=[chunk.model_dump() for chunk in chunks],
        )

        return AskResponse(
            question=request.question,
            chunks=chunks,
            answer=answer_result["answer"],
            is_general_knowledge=answer_result.get("is_general_knowledge"),
            contains_diy_advice=answer_result.get("contains_diy_advice"),
            source_info=answer_result.get("source_info"),
            prompt=answer_result.get("prompt"),
            success=True,
            message="Question answered successfully",
            quota_remaining=quota_remaining,
        )

    except Exception as e:
        return AskResponse(
            question=request.question,
            chunks=[],
            success=False,
            message=f"Error: {str(e)}",
            quota_remaining=quota_remaining,
            stacktrace=traceback.format_exc(),
        )


# Admin endpoints
@router.get("/admin/list")
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


@router.post("/admin/add")
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
            # User doesn't exist, create them
            # Use the actual user_id from the token
            cursor = conn.execute(
                """
                INSERT INTO users (user_id, email, is_admin, question_count, last_question_reset)
                VALUES (?, ?, 1, 0, date('now'))
                RETURNING user_id, email
                """,
                (user_info["user_id"], email),
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


@router.post("/admin/remove")
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


@router.post("/admin/reset-quota")
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


@router.get("/admin/check-quota")
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


# New admin query endpoints
@router.get("/admin/messages")
async def list_messages(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """List Q&A pairs with optional filtering."""
    return Message.list_messages(
        limit=limit,
        offset=offset,
        user_id=user_id,
        since=since,
        until=until,
    )


@router.get("/admin/messages/search")
async def search_messages(
    text: str,
    fuzzy: bool = False,
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Search Q&A pairs by text with optional filtering."""
    return Message.search_messages(
        text=text,
        fuzzy=fuzzy,
        limit=limit,
        offset=offset,
        user_id=user_id,
        since=since,
        until=until,
    )


@router.get("/admin/users/search")
async def search_users(
    query: str,
    fuzzy: bool = False,
    limit: int = 100,
    offset: int = 0,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Search users by email or name."""
    return User.search_users(
        query=query,
        fuzzy=fuzzy,
        limit=limit,
        offset=offset,
    )


@router.get("/admin/users/{user_id}/messages")
async def get_user_messages(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Get Q&A pairs for a specific user."""
    return User.get_user_messages(
        user_id=user_id,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
    )


@router.get("/admin/stats")
async def get_stats(
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 10,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """Get message statistics."""
    return Message.get_stats(
        since=since,
        until=until,
        limit=limit,
    )


@router.get("/admin/dump-db")
async def dump_db(user_info: dict = Depends(require_admin)):
    # Only allow if explicitly enabled via env var
    if os.getenv("ENABLE_DB_DUMP", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="DB dump not enabled")
    conn = get_db_connection()
    try:
        result = {}
        for table in ["users", "sessions", "messages"]:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            result[table] = [dict(r) for r in rows]
        return result
    finally:
        conn.close()


# Feedback endpoints
@router.post("/feedback")
async def create_feedback(
    feedback: FeedbackRequest,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Create or update feedback for an answer."""
    try:
        feedback_id = Feedback.create_or_update(
            user_id=user_info["user_id"],
            answer_id=feedback.answer_id,
            like=feedback.like,
            suggestion=feedback.suggestion,
        )
        return {
            "success": True,
            "message": "Feedback saved successfully",
            "feedback_id": feedback_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}",
        )


@router.get("/feedback")
async def get_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Get feedback for an answer."""
    feedback = Feedback.get(user_id=user_info["user_id"], answer_id=answer_id)
    if not feedback:
        return {"success": True, "feedback": None}
    return {"success": True, "feedback": feedback}


@router.delete("/feedback")
async def delete_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Delete feedback for an answer."""
    success = Feedback.delete(user_id=user_info["user_id"], answer_id=answer_id)
    return {
        "success": success,
        "message": "Feedback deleted successfully" if success else "No feedback found",
    }


# Admin feedback endpoints
@router.get("/admin/feedback")
async def list_feedback(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_info: Dict[str, Any] = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """List all feedback entries, optionally filtered by user_id."""
    return Feedback.list_feedback(user_id=user_id, limit=limit, offset=offset)
