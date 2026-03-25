FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies
COPY pyproject.toml .
# We use pip to install the project and its dependencies natively
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir -e .

# Copy application source
COPY src/ /app/src/

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "zaisaku.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
