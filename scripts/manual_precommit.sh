#!/bin/bash
"""
Manual pre-commit script that can be run independently.
This is useful for running checks manually before committing.
"""

set -e

echo "🚀 Running manual pre-commit checks..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    print_status "Installing dependencies with Poetry..."
    poetry install
fi

# Run the main pre-commit analysis script
print_status "Running comprehensive pre-commit analysis..."
poetry run python scripts/pre_commit_analysis.py

# Check exit code
if [ $? -eq 0 ]; then
    print_success "All pre-commit checks passed!"
    echo ""
    echo "🎉 Your code is ready for commit!"
else
    print_error "Some pre-commit checks failed!"
    echo ""
    echo "Please fix the issues above before committing."
    exit 1
fi