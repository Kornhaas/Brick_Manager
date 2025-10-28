#!/bin/bash
# Entrypoint script for Bricks Manager Docker container
# Handles database initialization and starts the Flask application

set -e

echo "🚀 Starting Bricks Manager container..."

# Set up paths for mounted volumes
export UPLOAD_FOLDER="/app/data/uploads"
export OUTPUT_FOLDER="/app/data/output"
export CACHE_FOLDER="/app/data/cache"
export INSTANCE_FOLDER="/app/data/instance"

# Create symbolic links to mounted volumes
echo "📁 Setting up volume links..."
ln -sf /app/data/uploads /app/brick_manager/uploads
ln -sf /app/data/cache /app/brick_manager/static/cache
ln -sf /app/data/output /app/brick_manager/output

# Ensure directories exist in mounted volumes
mkdir -p "$UPLOAD_FOLDER" "$OUTPUT_FOLDER" "$CACHE_FOLDER" "$INSTANCE_FOLDER"

# Set database path to mounted volume
export SQLALCHEMY_DATABASE_URI="sqlite:////app/data/instance/brick_manager.db"

# Change to brick_manager directory for Flask commands
cd /app/brick_manager

# Check if database exists, if not create it
if [ ! -f "/app/data/instance/brick_manager.db" ]; then
    echo "🗄️  Database not found. Creating new database..."
    
    # Initialize the database
    python -c "
from app import app, db
from flask_migrate import upgrade
import os

with app.app_context():
    # Create all tables
    db.create_all()
    print('✅ Database tables created successfully!')
    
    # Run any existing migrations
    try:
        if os.path.exists('migrations'):
            upgrade()
            print('✅ Database migrations applied successfully!')
    except Exception as e:
        print(f'ℹ️  No migrations to apply or migration error (this is normal for new setups): {e}')
"
    echo "✅ Database initialization completed!"
else
    echo "✅ Database found, checking for migrations..."
    
    # Apply any pending migrations
    python -c "
from flask_migrate import upgrade
from app import app
import os

with app.app_context():
    try:
        if os.path.exists('migrations'):
            upgrade()
            print('✅ Database migrations applied successfully!')
        else:
            print('ℹ️  No migrations directory found')
    except Exception as e:
        print(f'ℹ️  Migration check completed: {e}')
"
fi

# Load master lookup data if needed
echo "📚 Loading master lookup data..."
python -c "
from app import app
from services.part_lookup_service import load_part_lookup

with app.app_context():
    try:
        load_part_lookup()
        print('✅ Master lookup data loaded successfully!')
    except Exception as e:
        print(f'⚠️  Could not load master lookup data: {e}')
        print('ℹ️  This is normal if this is the first run or if lookup files are not available')
"

echo "🌟 Starting Flask application..."

# Start the Flask application
exec python -m flask run --host=0.0.0.0 --port=5000