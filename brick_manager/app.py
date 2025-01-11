"""
This module sets up and runs the Brick Manager Flask application.

It configures the application, registers blueprints, and loads the master lookup data.
"""

import os
import shutil
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_migrate import Migrate

from config import Config
from models import db  # Import the db instance from models
from routes.upload import upload_bp
from routes.label import label_bp
from routes.main import main_bp
from routes.storage import storage_bp
from routes.manual_entry import manual_entry_bp
from routes.part_lookup import part_lookup_bp
from routes.set_search import set_search_bp
from routes.import_rebrickable_data import import_rebrickable_data_bp
from routes.box_maintenance import box_maintenance_bp
from routes.set_maintain import set_maintain_bp
from routes.missing_parts import missing_parts_bp
from routes.dashboard import dashboard_bp
from routes.part_location import part_location_bp
from services.part_lookup_service import load_part_lookup

#pylint: disable=W0718

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set your secret key here
app.config.from_object(Config)  # Load the configuration

# Configure database
basedir = os.path.abspath(os.path.dirname(__file__))
instances_dir = os.path.join(basedir, 'instance')

# Ensure the 'instances' directory exists
os.makedirs(instances_dir, exist_ok=True)

# Update the database URI to use the 'instances' directory
db_path = os.path.join(instances_dir, 'brick_manager.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db instance with the app
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Configure logging
log_path = os.path.join(basedir, 'brick_manager.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

rotating_file_handler = RotatingFileHandler(
    log_path, maxBytes=1024 * 1024 * 5, backupCount=3
)
rotating_file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotating_file_handler.setFormatter(formatter)
app.logger.addHandler(rotating_file_handler)


def backup_database():
    """
    Backup the database at regular intervals.
    """
    try:
        db_source_path = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            'sqlite:///', '')
        backup_db_path = f"{db_source_path}.{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.backup.db"
        shutil.copyfile(db_source_path, backup_db_path)
        app.logger.info(
            "Database backed up successfully to %s", backup_db_path)
    except Exception as e:
        app.logger.error("Failed to backup database: %s", e)


# Ensure database tables are created
with app.app_context():
    db.create_all()  # Ensure tables are created
    try:
        master_lookup = load_part_lookup()
        app.logger.debug("Master lookup data loaded successfully.")
    except Exception as e:
        app.logger.error("Failed to load master lookup data: %s", e)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(label_bp)
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

# Set up the scheduler for database backup
scheduler = BackgroundScheduler()
scheduler.add_job(func=backup_database, trigger="interval",
                  hours=6)  # Backup every 6 hours
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
