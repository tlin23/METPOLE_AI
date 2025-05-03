from dotenv import load_dotenv
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.routes import router as api_router
from backend.vector_store.init_chroma import init_chroma_db

# Load environment variables
load_dotenv()


# Define lifespan context manager
@asynccontextmanager
async def lifespan(service: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize services
    chroma_db_path = os.getenv("CHROMA_DB_PATH")
    print(f"Initializing Chroma DB at: {chroma_db_path}")

    # Ensure the directory exists
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)

    # Initialize the Chroma DB
    init_chroma_db()

    yield

    # Shutdown: Clean up resources if needed
    print("Shutting down application...")


# Create FastAPI app with lifespan
service = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Local development frontend
    "https://metpol-ai-frontend.onrender.com",  # Render frontend
    "https://metpol-ai-frontend.vercel.app",  # Optional Vercel frontend
    "*",  # Allow all origins during development (remove in production)
]

service.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
service.include_router(api_router, prefix="/api")

# Serve React static files
frontend_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)
service.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


# Serve index.html on root
@service.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    # Print some environment info
    print(f"CHROMA_DB_PATH: {os.getenv('CHROMA_DB_PATH')}")

    # Run the FastAPI server
    print(
        "Run the FastAPI server at http://127.0.0.1:8000 with: uvicorn backend.server:service --reload"
    )
    uvicorn.run("backend.server:service", host="127.0.0.1", port=8000, reload=True)
