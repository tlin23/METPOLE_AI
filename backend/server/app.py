"""
FastAPI application server.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api.routes import router as api_router

# Load environment variables
load_dotenv()

# Create FastAPI app
service = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
)

# ✅ Add CORS middleware
service.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local dev (Vite)
        "http://localhost:3000",  # Docker
        "https://metpole-ai.vercel.app",  # Your Vercel frontend
        "http://localhost:8080",  # OAuth CLI redirect
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
service.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("backend.server.app:service", host="127.0.0.1", port=8000, reload=True)
