from typing import Optional
from pydantic import BaseModel


class ContentChunk(BaseModel):
    chunk_id: str
    file_name: str
    file_ext: str
    page_number: int
    text_content: str
    document_title: Optional[str] = None
