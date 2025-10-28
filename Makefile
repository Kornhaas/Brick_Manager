# Bricks Manager - Docker Management Makefile

.PHONY: help build up down logs restart clean backup restore health

# Default target
help:
	@echo "🔧 Bricks Manager Docker Commands"
	@echo ""
	@echo "🚀 Basic Operations:"
	@echo "  make up          - Start the application (build if needed)"
	@echo "  make down        - Stop the application"
	@echo "  make restart     - Restart the application"
	@echo "  make logs        - Show application logs"
	@echo "  make logs-f      - Follow application logs"
	@echo ""
	@echo "🔨 Build & Development:"
	@echo "  make build       - Build Docker image"
	@echo "  make rebuild     - Rebuild Docker image (no cache)"
	@echo "  make dev         - Start in development mode"
	@echo "  make shell       - Access container shell"
	@echo ""
	@echo "🎯 Code Quality & Testing:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make hooks       - Install Git hooks"
	@echo "  make pre-commit  - Run full pre-commit analysis with auto-fixes"
	@echo "  make check       - Run all checks without auto-fixes"
	@echo "  make format      - Format code (Black + isort)"
	@echo "  make lint        - Run linters (flake8 + pylint)"
	@echo "  make security    - Run security analysis"
	@echo "  make test        - Run test suite"
	@echo "  make test-cov    - Run tests with coverage report"
	@echo ""
	@echo "🗄️ Database & Data:"
	@echo "  make backup      - Backup all data"
	@echo "  make restore     - Restore from latest backup"
	@echo "  make db-shell    - Access database shell"
	@echo "  make reset-db    - Reset database (⚠️  destroys data)"
	@echo ""
	@echo "🔍 Monitoring & Maintenance:"
	@echo "  make health      - Check application health"
	@echo "  make stats       - Show container resource usage"
	@echo "  make clean       - Clean up Docker resources"
	@echo "  make update      - Update and restart application"

# Basic operations
up:
	@echo "🚀 Starting Bricks Manager..."
	docker-compose up -d
	@echo "✅ Application started! Visit http://localhost:5000"

down:
	@echo "🛑 Stopping Bricks Manager..."
	docker-compose down

restart:
	@echo "🔄 Restarting Bricks Manager..."
	docker-compose restart
	@echo "✅ Application restarted!"

logs:
	docker-compose logs bricks-manager

logs-f:
	docker-compose logs -f bricks-manager

# Build operations
build:
	@echo "🔨 Building Bricks Manager Docker image..."
	docker-compose build

rebuild:
	@echo "🔨 Rebuilding Bricks Manager Docker image (no cache)..."
	docker-compose build --no-cache

dev:
	@echo "🚀 Starting Bricks Manager in development mode..."
	@if [ ! -f docker-compose.dev.yml ]; then \
		echo "⚠️  docker-compose.dev.yml not found. Creating basic dev override..."; \
		echo "version: '3.8'" > docker-compose.dev.yml; \
		echo "services:" >> docker-compose.dev.yml; \
		echo "  bricks-manager:" >> docker-compose.dev.yml; \
		echo "    environment:" >> docker-compose.dev.yml; \
		echo "      - FLASK_ENV=development" >> docker-compose.dev.yml; \
		echo "      - FLASK_DEBUG=1" >> docker-compose.dev.yml; \
	fi
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

shell:
	@echo "🐚 Accessing container shell..."
	docker-compose exec bricks-manager bash

# Database operations
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	tar -czf backups/bricks-manager-backup-$$(date +%Y%m%d-%H%M%S).tar.gz data/
	@echo "✅ Backup created in backups/ directory"

restore:
	@echo "📥 Restoring from latest backup..."
	@LATEST=$$(ls -t backups/bricks-manager-backup-*.tar.gz 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "❌ No backup files found in backups/ directory"; \
		exit 1; \
	fi; \
	echo "Restoring from: $$LATEST"; \
	docker-compose down; \
	tar -xzf "$$LATEST"; \
	docker-compose up -d; \
	echo "✅ Restore completed!"

db-shell:
	@echo "🗄️ Accessing database shell..."
	docker-compose exec bricks-manager sqlite3 /app/data/instance/brick_manager.db

reset-db:
	@echo "⚠️  This will DESTROY all database data!"
	@echo "Are you sure? Press Ctrl+C to cancel, Enter to continue..."
	@read confirm
	docker-compose down
	rm -f data/instance/brick_manager.db
	docker-compose up -d
	@echo "✅ Database reset completed!"

# Monitoring
health:
	@echo "🏥 Checking application health..."
	@curl -s http://localhost:5000/health | python3 -m json.tool || echo "❌ Health check failed"

stats:
	@echo "📊 Container resource usage:"
	docker stats bricks-manager-app --no-stream

# Maintenance
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed!"

update:
	@echo "🔄 Updating Bricks Manager..."
	git pull
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Update completed!"

# Setup for first time users
setup:
	@echo "⚙️ Setting up Bricks Manager for first time..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✅ Please edit .env file with your settings (especially REBRICKABLE_TOKEN)"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi
	@mkdir -p data/{instance,uploads,output,cache,logs}
	@echo "📁 Created data directories"
	make up
	@echo "🎉 Setup completed! Please edit .env file and restart with 'make restart'"

# Code Quality & Development Commands
.PHONY: install test lint format check security clean-code hooks pre-commit

install:
	@echo "📦 Installing dependencies with Poetry..."
	poetry install

hooks:
	@echo "🔗 Installing Git hooks..."
	./scripts/install_hooks.sh

pre-commit:
	@echo "🔍 Running full pre-commit analysis with auto-fixes..."
	poetry run python scripts/pre_commit_analysis.py

check:
	@echo "🔍 Running all checks without auto-fixes..."
	poetry run python scripts/pre_commit_analysis.py --no-fix

format:
	@echo "🎨 Formatting code..."
	poetry run black brick_manager/ scripts/
	poetry run isort brick_manager/ scripts/

lint:
	@echo "🔍 Running linters..."
	poetry run flake8 brick_manager/
	poetry run pylint brick_manager/ --output-format=text --reports=no

security:
	@echo "🔒 Running security analysis..."
	poetry run bandit -r brick_manager/ -f json -o bandit-report.json || true
	poetry run python scripts/security_check.py brick_manager/**/*.py

test:
	@echo "🧪 Running tests..."
	poetry run pytest --tb=short -v

test-cov:
	@echo "📊 Running tests with coverage..."
	poetry run pytest --cov=brick_manager --cov-report=term-missing --cov-report=html

clean-code:
	@echo "🧹 Cleaning up generated files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ bandit-report.json
	rm -rf build/ dist/