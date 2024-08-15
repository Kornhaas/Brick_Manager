# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (e.g., for building some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files to the container
COPY pyproject.toml poetry.lock ./

# Install Python dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy the entire project to the working directory
COPY . /app

# Change directory to lego_scanner
WORKDIR /app/lego_scanner

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# create the database and run the migrations
RUN poetry run flask db init || true
RUN poetry run flask db migrate -m "Initial migration." || true
RUN poetry run flask db upgrade || true

# Expose the port the app runs on
EXPOSE 5000

USER nonroot
# Command to run your application
CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0", "--port=5000"]