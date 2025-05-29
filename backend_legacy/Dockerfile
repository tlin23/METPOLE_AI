# Backend Dockerfile
FROM python:3.11-slim

# Set workdir to project root so `backend_legacy` is importable
WORKDIR /app

# Copy only backend_legacy code and root-level requirements
COPY backend_legacy backend_legacy
COPY backend_legacy/requirements.txt .

# Install backend_legacy dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend_legacy port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "backend_legacy.server:service", "--host", "0.0.0.0", "--port", "8000"]
