from dotenv import load_dotenv
import os
from fastapi import FastAPI
import uvicorn
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.vector_store.init_chroma import init_chroma_db

# Load environment variables
load_dotenv()

# Set default Chroma DB path if not in environment
if not os.getenv("CHROMA_DB_PATH"):
    os.environ["CHROMA_DB_PATH"] = "./data/index"

# Create FastAPI app
app = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Local development frontend
    "https://metpol-ai-frontend.onrender.com",  # Render frontend
    "https://metpol-ai-frontend.vercel.app",  # Optional Vercel frontend
    "*",  # Allow all origins during development (remove in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize the Chroma DB
    chroma_db_path = os.getenv("CHROMA_DB_PATH")
    print(f"Initializing Chroma DB at: {chroma_db_path}")

    # Ensure the directory exists
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)

    # Initialize the Chroma DB
    init_chroma_db()


if __name__ == "__main__":
    # Print some environment info
    print(f"CHROMA_DB_PATH: {os.getenv('CHROMA_DB_PATH')}")

    # Run the FastAPI server
    print(
        "Run the FastAPI server at http://127.0.0.1:8000 with: uvicorn main:app --reload"
    )
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
