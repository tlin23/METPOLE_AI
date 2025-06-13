"""
API models for the application.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.server.retriever.models import RetrievedChunk


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class AskResponse(BaseModel):
    question: str
    chunks: List[RetrievedChunk]
    answer: Optional[str] = None
    is_general_knowledge: Optional[bool] = False
    contains_diy_advice: Optional[bool] = False
    source_info: Optional[str] = None
    success: bool
    message: str
    prompt: Optional[str] = None
    quota_remaining: int
    stacktrace: Optional[str] = None


class FeedbackRequest(BaseModel):
    answer_id: str
    like: bool
    suggestion: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    answer_id: str
    like: bool
    suggestion: Optional[str] = None
    created_at: str


class HealthResponse(BaseModel):
    status: str
    system: Dict[str, Any]


class AdminMeResponse(BaseModel):
    email: str
    is_admin: bool


class StandardResponse(BaseModel):
    success: bool
    message: str
