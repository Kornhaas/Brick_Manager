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
    # Use gosu to switch to appuser and re-execute this script
    exec gosu appuser "$0" "$@"
fi

echo "Running as appuser ($(id -u):$(id -g))"

# Create data directories (when running as appuser after switch)
mkdir -p /app/data/uploads /app/data/cache/images /app/data/output /app/data/instance /app/data/logs

# Check if database exists
DB_PATH="/app/data/instance/brick_manager.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found. Initializing new database..."
    
    # Set the database path environment variable
    export SQLALCHEMY_DATABASE_URI="sqlite:////app/data/instance/brick_manager.db"
    
    # Navigate to the brick_manager directory for Flask commands
    cd /app/brick_manager
    
    # Initialize database
    echo "Creating database tables..."
    python -c "
from app import app, db

with app.app_context():
    # Create all tables
    db.create_all()
    print('Database tables created successfully!')
"
    
    # Run migrations if they exist
    if [ -d "/app/brick_manager/migrations" ]; then
        echo "Running database migrations..."
        flask db upgrade || echo "No migrations to run or migration failed (this might be normal for a fresh install)"
    fi
    
    echo "Database initialization completed!"
else
    echo "Database already exists at $DB_PATH"
    export SQLALCHEMY_DATABASE_URI="sqlite:////app/data/instance/brick_manager.db"
    
    # Navigate to the brick_manager directory
    cd /app/brick_manager
    
    # Run migrations for existing database
    if [ -d "/app/brick_manager/migrations" ]; then
        echo "Checking for database migrations..."
        flask db upgrade || echo "No migrations to run or migration failed"
    fi
fi

echo "Starting Bricks Manager application..."
echo "Database: $SQLALCHEMY_DATABASE_URI"
echo "Working directory: $(pwd)"

# Execute the main command
exec "$@"
