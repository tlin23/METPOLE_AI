# Backend Dockerfile
FROM python:3.11-slim

# Set workdir to project root so `backend` is importable
WORKDIR /app

# Copy only backend code and root-level requirements
COPY backend backend
COPY backend/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 8000 8080

# Create startup script
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]
