# Dexter Workspace - Production Container
# Multi-stage build for minimal image size

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements first for layer caching
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy schema and helper files
COPY schema.sql ./
COPY helpers/ ./helpers/
COPY domains/ ./domains/

# Initialize database
RUN sqlite3 dexter.db < schema.sql

# Set environment variables
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 dexter && \
    chown -R dexter:dexter /workspace

USER dexter

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD sqlite3 dexter.db "SELECT 1;" || exit 1

# Default command (override for specific tasks)
CMD ["python3", "-m", "helpers.db_helper"]
