FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy parent directory files (needed by backend)
COPY ../conversation_manager.py /app/
COPY ../conversation_storage.py /app/
COPY ../rag_agent_complete.py /app/
COPY ../rag_agent_openai.py /app/
COPY ../system_prompts.json /app/

# Copy scraped data (if it exists)
COPY ../scraped_data/ /app/scraped_data/ 2>/dev/null || mkdir -p /app/scraped_data/

# Copy backend
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/

# Copy frontend
COPY frontend/ /app/frontend/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables (will be set in Cloud Run)
ENV PORT=8080

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Run the application
CMD uvicorn backend.api:app --host 0.0.0.0 --port $PORT

