#!/bin/bash
# Code quality maintenance script

echo "🔧 Running code quality tools..."

# Format code with black
echo "📝 Formatting code with black..."
poetry run black brick_manager/

# Sort imports with isort
echo "📦 Organizing imports with isort..."
poetry run isort --profile black brick_manager/

# Run flake8 with configuration
echo "🔍 Checking code quality with flake8..."
poetry run flake8 brick_manager/

# Run tests
echo "🧪 Running tests..."
poetry run pytest

echo "✅ Code quality check completed!"
