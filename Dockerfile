# Multi-stage build for optimal image size and security
FROM python:3.12-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies (only needed if a dependency has no musllinux wheel)
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev

# Install Poetry into an isolated venv so it is not part of the runtime site-packages
RUN pip install --no-cache-dir --upgrade pip \
    && python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install --no-cache-dir poetry poetry-plugin-export

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Resolve dependencies from the lock file and install them into the system environment
RUN /opt/poetry/bin/poetry export --only main --without-hashes --format requirements.txt --output requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-alpine

# Create app user for security
RUN addgroup -S appuser && adduser -S -G appuser -h /app -s /bin/sh appuser

# Install runtime dependencies including su-exec for user switching
RUN apk add --no-cache \
    bash \
    curl \
    su-exec

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Patch base image packages, then drop pip: it is not needed at runtime and its
# vendored dependency manifest keeps getting flagged by image scanners
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && rm -rf /usr/local/lib/python3.12/site-packages/pip \
    /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
    /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.12

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
