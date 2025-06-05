from pydantic import BaseModel
from typing import Optional, Dict, Any


class RetrievedChunk(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    distance: Optional[float] = None
