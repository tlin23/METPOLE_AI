"""
FastAPI application server.
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.server.api.main.main_routes import router as api_router
from backend.server.api.admin.admin_routes import router as admin_router
from backend.server.database.connection import init_db

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


# Create FastAPI app
service = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
    lifespan=lifespan,
)

# ✅ Add CORS middleware
service.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local dev (Vite)
        "http://localhost:3000",  # Local dev (Docker)
        "https://metpole-ai.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
service.include_router(api_router, prefix="/api")
service.include_router(admin_router, prefix="/admin")

if __name__ == "__main__":
    uvicorn.run("backend.server.app:service", host="127.0.0.1", port=8000, reload=True)
