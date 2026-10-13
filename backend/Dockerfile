FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to avoid downloading ~3GB of CUDA wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy project specification and application source
COPY pyproject.toml .
COPY src/ /app/src/

# Install the project and dependencies
RUN pip install --no-cache-dir .

# Pre-download ML models to eliminate first-request cold start and timeout
RUN python -c "from sentence_transformers import CrossEncoder, SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "zaisaku.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
