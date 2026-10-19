#!/bin/bash
set -e

echo "=== Bricks Manager Docker Entrypoint ==="

# Fix permissions if running as root
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, fixing permissions for mounted volumes..."

    # Create data directories if they don't exist
    mkdir -p /app/data/uploads /app/data/cache/images /app/data/output /app/data/instance /app/data/logs

    # Fix ownership and permissions
    chown -R appuser:appuser /app/data 2>/dev/null || true
    chmod -R 777 /app/data 2>/dev/null || true

    echo "Permissions fixed. Switching to appuser..."
    # Use su-exec to switch to appuser and re-execute this script
    exec su-exec appuser "$0" "$@"
fi

echo "Running as appuser ($(id -u):$(id -g))"

# Create data directories (when running as appuser after switch)
mkdir -p /app/data/uploads /app/data/cache/images /app/data/output /app/data/instance /app/data/logs

# Check if database exists
DB_PATH="/app/data/instance/brick_manager.db"
MIGRATIONS_PATH="/app/brick_manager/migrations"

export SQLALCHEMY_DATABASE_URI="sqlite:////app/data/instance/brick_manager.db"
cd /app/brick_manager

if [ -d "$MIGRATIONS_PATH" ]; then
    echo "Applying database migrations..."
    flask db upgrade
elif [ ! -f "$DB_PATH" ]; then
    echo "Database not found. Initializing new database..."
    echo "Creating database tables..."
    python -c "
from app import app, db

with app.app_context():
    # Create all tables
    db.create_all()
    print('Database tables created successfully!')
"
    echo "Database initialization completed!"
else
    echo "Database already exists at $DB_PATH"
    echo "No migration repository is bundled; existing schema is left unchanged."
fi

echo "Starting Bricks Manager application..."
echo "Database: $SQLALCHEMY_DATABASE_URI"
echo "Working directory: $(pwd)"

# Execute the main command
exec "$@"
