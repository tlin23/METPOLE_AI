"""
API routes for the application.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
from typing import List, Dict, Any
import traceback

from .models import AskRequest, ChunkResult, AskResponse
from ..retriever.ask import Retriever
from ..auth import validate_token, require_admin
from ..database import User, Session, Message, get_db_connection

# Create router
router = APIRouter()

# Initialize components
retriever = Retriever(production=os.getenv("PRODUCTION", "false").lower() == "true")


@router.get("/health")
async def health_check():
    """Health check endpoint to verify the server is running."""
    return JSONResponse(content={"status": "ok"})


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
        raise HTTPException(
            status_code=429,
            detail={"message": "Daily question quota exceeded", "quota_remaining": 0},
        )

    try:
        # Create session if needed
        session_id = Session.create(user_info["user_id"])

        # Log the question
        Message.create(
            session_id=session_id,
            user_id=user_info["user_id"],
            message_type="question",
            message_text=request.question,
        )

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

        # Log the answer
        Message.create(
            session_id=session_id,
            user_id=user_info["user_id"],
            message_type="answer",
            message_text=answer_result["answer"],
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
    email: str, user_info: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Add a new admin user."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "UPDATE users SET is_admin = 1 WHERE email = ? RETURNING user_id, email",
            (email,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
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
