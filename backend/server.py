from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from backend.api.routes import router as api_router

# Load environment variables
load_dotenv()

# Create FastAPI app with lifespan
service = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0",
)

# Include API routes
service.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run("backend.server:service", host="127.0.0.1", port=8000, reload=True)
