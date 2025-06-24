# Use Python 3.12 slim as base image (matching your pyproject.toml requirement)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies needed for Google ADK and Firebase
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy UV files for dependency installation
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies using UV (as root to avoid permission issues)
RUN uv sync --frozen --no-dev

# Copy application code - be explicit about directories
COPY main.py ./
COPY run.py ./
COPY job_matching_agent/ ./job_matching_agent/
COPY job_posting_agent/ ./job_posting_agent/
COPY assessment_agent/ ./assessment_agent/
COPY utils/ ./utils/
COPY templates/ ./templates/
COPY static/ ./static/
COPY config/ ./config/

# Create non-root user for security after installing dependencies
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p config && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Switch to non-root user
USER app

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Run the application using UV
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 