FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ /app/backend/
COPY ../scraped_data/ /app/scraped_data/
COPY ../conversation_manager.py /app/
COPY ../conversation_storage.py /app/
COPY ../rag_agent_complete.py /app/
COPY ../rag_agent_openai.py /app/
COPY ../system_prompts.json /app/

# Copy frontend
COPY frontend/ /app/frontend/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]

