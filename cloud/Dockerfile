FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for better caching)
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python packages
# Note: Using --no-cache-dir to reduce image size, but layer caching will speed up rebuilds
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Pre-download the embedding model to avoid rate limits at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy modules needed by backend (including bot files and scrapers)
COPY *.py system_prompts.json /app/

# Copy backend
COPY backend/ /app/backend/

# Copy frontend
COPY frontend/ /app/frontend/

# Copy scraped data
COPY scraped_data /app/scraped_data/

# Build ChromaDB index during Docker build (uses correct ChromaDB version!)
RUN python /app/build_complete_index.py

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables (will be set in Cloud Run)
ENV PORT=8080
ENV PYTHONPATH=/app
ENV TOKENIZERS_PARALLELISM=false
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Run the application
CMD uvicorn backend.api:app --host 0.0.0.0 --port $PORT

