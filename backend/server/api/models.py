"""
API models for the application.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChunkResult(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    distance: Optional[float] = None


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class AskResponse(BaseModel):
    question: str
    chunks: List[ChunkResult]
    answer: Optional[str] = None
    is_general_knowledge: Optional[bool] = False
    contains_diy_advice: Optional[bool] = False
    source_info: Optional[str] = None
    success: bool
    message: str
    prompt: Optional[str] = None
    quota_remaining: int
    stacktrace: Optional[str] = None
