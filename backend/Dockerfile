# Backend Dockerfile
FROM python:3.11-slim

# Set workdir to project root so `backend` is importable
WORKDIR /app

# Copy only backend code and root-level requirements
COPY backend backend
COPY backend/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "backend.server:service", "--host", "0.0.0.0", "--port", "8000"]
