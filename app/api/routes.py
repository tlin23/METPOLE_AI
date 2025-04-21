"""
API routes for the application.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.crawler.crawl import crawl
from app.embedder.embed import Embedder
from app.retriever.ask import Retriever


# Create router
router = APIRouter()

# Initialize components
embedder = Embedder()
retriever = Retriever()


# Define models
class CrawlRequest(BaseModel):
    url: str


class CrawlResponse(BaseModel):
    url: str
    content: Optional[str] = None
    doc_id: Optional[str] = None
    success: bool
    message: str


class QueryRequest(BaseModel):
    query: str
    n_results: Optional[int] = 5


class QueryResponse(BaseModel):
    query: str
    results: List
    success: bool
    message: str


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_url(request: CrawlRequest):
    """
    Crawl a URL and store its content.
    """
    try:
        # Crawl the URL
        content = crawl(request.url)
        
        if not content:
            return CrawlResponse(
                url=request.url,
                success=False,
                message="Failed to extract content from URL"
            )
        
        # Embed the content
        doc_id = embedder.embed_text(content)
        
        return CrawlResponse(
            url=request.url,
            content=content[:100] + "..." if len(content) > 100 else content,
            doc_id=doc_id,
            success=True,
            message="URL crawled and embedded successfully"
        )
    
    except Exception as e:
        return CrawlResponse(
            url=request.url,
            success=False,
            message=f"Error: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
    """
    Query the embedded data.
    """
    try:
        results = retriever.query(request.query, request.n_results)
        
        return QueryResponse(
            query=request.query,
            results=results,
            success=True,
            message="Query executed successfully"
        )
    
    except Exception as e:
        return QueryResponse(
            query=request.query,
            results=[],
            success=False,
            message=f"Error: {str(e)}"
        )
