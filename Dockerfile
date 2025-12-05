# Use official Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager itself
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and uv.lock first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync

# Copy application code
COPY ./app ./app

# Prompts
COPY ./docs ./docs

RUN --mount=type=secret,id=env \
    export $(cat /run/secrets/env | xargs)

# Run the service
CMD ["uv", "run", "-m", "app"]
