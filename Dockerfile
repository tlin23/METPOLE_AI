FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/html data/processed data/logs data/index

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_DB_PATH=/data/index

# Expose port
EXPOSE 8000

# Include pregenerated ChromaDB index
COPY data/index /app/data/index

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
