"""
Vector store package for handling persistent vector embeddings.
"""

from app.vector_store.init_chroma import init_chroma_db

__all__ = ["init_chroma_db"]
