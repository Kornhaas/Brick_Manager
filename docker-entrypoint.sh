#!/bin/bash
set -e

echo "=== Bricks Manager Docker Entrypoint ==="

# Fix permissions if running as root
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, preparing mounted volume directories..."

    # Create data directories if they don't exist
    mkdir -p /app/data/uploads /app/data/cache/images /app/data/output /app/data/instance /app/data/logs

    # Do not recurse through bind mounts here.  On Docker Desktop mounts (for
    # example a OneDrive folder on Windows), recursive chmod/chown can delay
    # startup for minutes.  The application only needs its mount roots to be
    # writable to create new files and directories.
    chown appuser:appuser /app/data /app/data/uploads /app/data/cache \
        /app/data/output /app/data/instance /app/data/logs 2>/dev/null || true
    chmod 0775 /app/data /app/data/uploads /app/data/cache \
        /app/data/output /app/data/instance /app/data/logs 2>/dev/null || true

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

if [ ! -f "$DB_PATH" ]; then
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
fi

if compgen -G "$MIGRATIONS_PATH/*.sql" > /dev/null; then
    echo "Applying restart-safe SQLite migrations..."
    python -m services.migration_service "$DB_PATH" "$MIGRATIONS_PATH"
fi

echo "Starting Bricks Manager application..."
echo "Database: $SQLALCHEMY_DATABASE_URI"
echo "Working directory: $(pwd)"

# Execute the main command
exec "$@"
