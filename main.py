from dotenv import load_dotenv
import os
from fastapi import FastAPI
import uvicorn
from app.api.routes import router as api_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="MetPol AI",
    description="A FastAPI application for crawling, embedding, and retrieving information",
    version="0.1.0"
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    # Print some environment info
    print(f"CHROMA_DB_PATH: {os.getenv('CHROMA_DB_PATH')}")
    
    # Run the FastAPI server
    print("Run the FastAPI server at http://127.0.0.1:8000 with: uvicorn main:app --reload")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
