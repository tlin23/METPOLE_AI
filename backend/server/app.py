"""
FastAPI application server.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import traceback

from backend.server.api.main.main_routes import router as api_router
from backend.server.api.admin.admin_routes import router as admin_router
from backend.server.database.connection import init_db

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("/tmp/app.log", mode="a")],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Starting MetPol AI application")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    yield
    logger.info("Shutting down MetPol AI application")


# Create FastAPI app
service = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
    lifespan=lifespan,
)


# Global exception handler
@service.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception for {request.method} {request.url}: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred. Please try again later.",
            "error_type": type(exc).__name__,
        },
    )


# HTTP exception handler for better error responses
@service.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured responses."""
    logger.warning(f"HTTP {exc.status_code} for {request.method} {request.url}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": (
                exc.detail
                if isinstance(exc.detail, str)
                else exc.detail.get("message", "An error occurred")
            ),
            "error_code": exc.status_code,
            **(exc.detail if isinstance(exc.detail, dict) else {}),
        },
    )


# ✅ Environment-based CORS configuration for production readiness
def get_cors_origins():
    """Get CORS origins from environment variables."""
    # Get allowed origins from environment
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")

    if cors_origins_env:
        # Parse comma-separated origins from environment
        origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        logger.info(f"Using CORS origins from environment: {origins}")
        return origins

    # Default origins for development/fallback
    is_production = os.getenv("PRODUCTION", "false").lower() == "true"

    if is_production:
        # Strict production origins - only known production domains
        default_origins = [
            "https://metpole-ai.vercel.app",  # Production frontend
        ]
        logger.warning("Production mode: Using strict CORS origins")
    else:
        # Development origins
        default_origins = [
            "http://localhost:5173",  # Local dev (Vite)
            "http://localhost:3000",  # Local dev (Docker/Create React App)
            "http://127.0.0.1:5173",  # Alternative localhost
            "http://127.0.0.1:3000",  # Alternative localhost
            "https://metpole-ai.vercel.app",  # Production frontend for testing
        ]
        logger.info("Development mode: Using permissive CORS origins")

    return default_origins


cors_origins = get_cors_origins()

service.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
service.include_router(api_router, prefix="/api")
service.include_router(admin_router, prefix="/api/admin")

if __name__ == "__main__":
    uvicorn.run("backend.server.app:service", host="127.0.0.1", port=8000, reload=True)
