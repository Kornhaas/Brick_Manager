"""
This script runs the Brick Manager Flask application with database migration support.

It imports the app and db instances and sets up Flask-Migrate for database migrations.
"""

from app import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run()
