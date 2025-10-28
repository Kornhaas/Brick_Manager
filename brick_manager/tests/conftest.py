"""
Pytest configuration and fixtures for the Bricks Manager test suite.
"""

import os
import sys
import tempfile

import pytest
from flask import Flask

# Add the parent directory to the path so we can import from brick_manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import db


def create_test_app():
    """Create and configure a new app instance for testing."""
    # Set template and static folders relative to the main app
    import os

    basedir = os.path.abspath(os.path.dirname(__file__))
    template_folder = os.path.join(basedir, "..", "templates")
    static_folder = os.path.join(basedir, "..", "static")
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        }
    )

    db.init_app(app)

    # Register blueprints for testing
    try:
        from routes.admin_sync import admin_sync_bp
        from routes.box_maintenance import box_maintenance_bp
        from routes.dashboard import dashboard_bp
        from routes.import_rebrickable_data import import_rebrickable_data_bp
        from routes.main import main_bp
        from routes.manual_entry import manual_entry_bp
        from routes.missing_parts import missing_parts_bp
        from routes.part_location import part_location_bp
        from routes.part_lookup import part_lookup_bp
        from routes.rebrickable_sync import rebrickable_sync_bp
        from routes.set_maintain import set_maintain_bp
        from routes.set_search import set_search_bp
        from routes.storage import storage_bp
        from routes.token_management import token_management_bp
        from routes.upload import upload_bp

        app.register_blueprint(upload_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(storage_bp)
        app.register_blueprint(manual_entry_bp)
        app.register_blueprint(part_lookup_bp)
        app.register_blueprint(set_search_bp)
        app.register_blueprint(import_rebrickable_data_bp)
        app.register_blueprint(set_maintain_bp)
        app.register_blueprint(missing_parts_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(part_location_bp)
        app.register_blueprint(box_maintenance_bp)
        app.register_blueprint(token_management_bp)
        app.register_blueprint(rebrickable_sync_bp)
        app.register_blueprint(admin_sync_bp)
    except ImportError as e:
        # If blueprints can't be imported, continue without them
        pass

    return app, db_fd, db_path


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for testing."""
    test_app, db_fd, db_path = create_test_app()

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()

    # Clean up the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def setup_database(app):
    """Set up and tear down database for each test."""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
