"""
API routes for the application.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
from typing import List, Dict, Any
import traceback
from datetime import datetime, timedelta, UTC
import time

from backend.server.api.models import AskRequest, AskResponse, FeedbackRequest
from backend.server.retriever.ask import Retriever
from backend.server.retriever.models import RetrievedChunk
from backend.server.api.auth import validate_token, require_admin
from backend.server.database.models import User, Session, Question, Answer, Feedback
from backend.server.database.connection import get_db_connection

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

        # Start timing
        start_time = time.time()

        # Query the vector store using cosine similarity
        results = retriever.query(request.question, request.top_k)

        # Format the results
        chunks = []
        for i in range(len(results["documents"][0])):
            chunk = RetrievedChunk(
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

        # Calculate response time
        response_time = time.time() - start_time

        # Create question and answer
        question_id = Question.create(
            session_id=session_id,
            user_id=user_info["user_id"],
            question_text=request.question,
        )

        Answer.create(
            question_id=question_id,
            answer_text=answer_result["answer"],
            prompt=answer_result.get("prompt", ""),
            retrieved_chunks=[chunk.model_dump() for chunk in chunks],
            response_time=response_time,
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


# Feedback endpoints
@router.post("/feedback")
async def create_feedback(
    feedback: FeedbackRequest,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Create or update feedback for an answer."""
    feedback_id = Feedback.create_or_update(
        user_id=user_info["user_id"],
        answer_id=feedback.answer_id,
        like=feedback.like,
        suggestion=feedback.suggestion,
    )
    return {"feedback_id": feedback_id}


@router.get("/feedback")
async def get_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Get feedback for an answer."""
    feedback = Feedback.get(answer_id, user_info["user_id"])
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.delete("/feedback")
async def delete_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> Dict[str, Any]:
    """Delete feedback for an answer."""
    success = Feedback.delete(answer_id, user_info["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"success": True}


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
