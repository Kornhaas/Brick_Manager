# Stage 1: Build
FROM python:3.12-slim AS builder

# Set the working directory
WORKDIR /app

# Install build dependencies, combining steps to reduce layers and clean up after installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install --no-cache-dir poetry

# Copy dependency files first for layer caching optimization
COPY pyproject.toml poetry.lock ./

# Configure Poetry to avoid creating virtual environments and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy the application code
COPY . .

# Stage 2: Production (distroless approach with minimal Python runtime)
# Use Google's distroless image for improved security and reduced image size
FROM python:3.12-slim

# Copy only the necessary files from the builder stage
COPY --from=builder /app /app

# Switch to non-root user to enhance security
USER 1000

# Set the working directory and expose the necessary port
WORKDIR /app
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Use entrypoint to run the application, focusing on minimal executable setup
ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
