"""
API models for the application.
"""

from pydantic import BaseModel
from typing import List, Optional
from ..retriever.models import RetrievedChunk


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
