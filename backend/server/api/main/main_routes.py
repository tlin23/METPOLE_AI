"""
API routes for the application.
"""

from fastapi import APIRouter, HTTPException, Depends
import os
from typing import Dict, Any
import traceback
from datetime import datetime, timedelta, UTC
import time
import logging

from backend.server.api.models.models import (
    AskRequest,
    AskResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    StandardResponse,
)
from backend.server.retriever.ask import Retriever
from backend.server.retriever.models import RetrievedChunk
from backend.server.api.auth import validate_token
from backend.server.database.models import User, Session, Question, Answer, Feedback

# Create router
router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize components
retriever = Retriever(production=os.getenv("PRODUCTION", "false").lower() == "true")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the server is running.
    Returns basic system status.
    """
    logger.debug("Health check requested")
    return HealthResponse(status="ok", system={"status": "operational"})


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
    user_email = user_info.get("email", "unknown")
    logger.info(f"Question asked by user {user_email}: {request.question[:100]}...")

    # Check quota
    quota_remaining = User.increment_question_count(user_info["user_id"])
    if quota_remaining <= 0:
        logger.warning(f"User {user_email} exceeded daily quota")
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
        logger.debug(f"Created session {session_id} for user {user_email}")

        # Start timing
        start_time = time.time()

        # Query the vector store using cosine similarity
        logger.debug(f"Querying vector store with top_k={request.top_k}")
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

        logger.debug(f"Retrieved {len(chunks)} chunks from vector store")

        # Generate an answer using OpenAI's GPT model
        logger.debug("Generating answer using OpenAI")
        answer_result = retriever.generate_answer(request.question, chunks)

        # Calculate response time
        response_time = time.time() - start_time
        logger.info(f"Question processed for {user_email} in {response_time:.2f}s")

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

        logger.debug(f"Stored question and answer in database for user {user_email}")

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
        logger.error(f"Error processing question for user {user_email}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return AskResponse(
            question=request.question,
            chunks=[],
            success=False,
            message=f"Error: {str(e)}",
            quota_remaining=quota_remaining,
            stacktrace=traceback.format_exc(),
        )


# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackRequest,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> FeedbackResponse:
    """Create or update feedback for an answer."""
    user_email = user_info.get("email", "unknown")
    logger.info(
        f"Feedback submitted by {user_email} for answer {feedback.answer_id}: {'like' if feedback.like else 'dislike'}"
    )

    try:
        Feedback.create_or_update(
            user_id=user_info["user_id"],
            answer_id=feedback.answer_id,
            like=feedback.like,
            suggestion=feedback.suggestion,
        )
        # Get the created feedback back from DB
        feedback_data = Feedback.get(feedback.answer_id, user_info["user_id"])
        logger.debug(f"Feedback stored successfully for user {user_email}")
        return FeedbackResponse(**feedback_data)
    except Exception as e:
        logger.error(f"Error storing feedback for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")


@router.get("/feedback", response_model=FeedbackResponse)
async def get_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> FeedbackResponse:
    """Get feedback for an answer."""
    user_email = user_info.get("email", "unknown")
    logger.debug(f"Feedback requested by {user_email} for answer {answer_id}")

    try:
        feedback = Feedback.get(answer_id, user_info["user_id"])
        if not feedback:
            logger.debug(
                f"No feedback found for answer {answer_id} by user {user_email}"
            )
            raise HTTPException(status_code=404, detail="Feedback not found")
        return FeedbackResponse(**feedback)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


@router.delete("/feedback", response_model=StandardResponse)
async def delete_feedback(
    answer_id: str,
    user_info: Dict[str, Any] = Depends(validate_token),
) -> StandardResponse:
    """Delete feedback for an answer."""
    user_email = user_info.get("email", "unknown")
    logger.info(f"Feedback deletion requested by {user_email} for answer {answer_id}")

    try:
        success = Feedback.delete(answer_id, user_info["user_id"])
        if not success:
            logger.debug(
                f"No feedback to delete for answer {answer_id} by user {user_email}"
            )
            raise HTTPException(status_code=404, detail="Feedback not found")
        logger.debug(f"Feedback deleted successfully for user {user_email}")
        return StandardResponse(success=True, message="Feedback deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete feedback")
