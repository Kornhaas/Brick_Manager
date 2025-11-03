# Multi-stage build for optimal image size and security
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# Production stage
FROM python:3.12-slim

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Install runtime dependencies including gosu for user switching
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Ensure python3.12 is the default python
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.12 1

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY brick_manager/ ./brick_manager/
COPY docker-entrypoint.sh ./

# Create directories for mounted volumes with correct permissions
RUN mkdir -p /app/data/instance \
    /app/data/uploads \
    /app/data/output \
    /app/data/cache/images \
    /app/data/logs \
    /app/brick_manager/static/cache/images \
    && chown -R appuser:appuser /app

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Don't switch to non-root user here - entrypoint will handle it
# USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=brick_manager/app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Use docker-entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]

# Default command
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
