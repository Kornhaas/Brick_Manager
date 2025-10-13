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
from routes.token_management import token_management_bp
from routes.rebrickable_sync import rebrickable_sync_bp
from routes.admin_sync import admin_sync_bp
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


def scheduled_sync_missing_parts():
    """
    Scheduled task to sync both regular and minifigure missing parts with Rebrickable every 6 hours.
    Only runs if tokens are configured.
    """
    try:
        from services.token_service import get_rebrickable_user_token, get_rebrickable_api_key
        from services.rebrickable_sync_service import sync_missing_parts_with_rebrickable, sync_missing_minifigure_parts_with_rebrickable
        
        # Check if tokens are configured
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            app.logger.info("Scheduled missing parts sync skipped - no API credentials configured")
            return
        
        app.logger.info("Starting scheduled sync for both regular and minifigure missing parts")
        batch_size = 500  # Use moderate batch size for scheduled runs
        
        # Sync regular parts
        app.logger.info("Syncing regular missing parts...")
        regular_result = sync_missing_parts_with_rebrickable(batch_size=batch_size)
        
        # Sync minifigure parts
        app.logger.info("Syncing minifigure missing parts...")
        minifig_result = sync_missing_minifigure_parts_with_rebrickable(batch_size=batch_size)
        
        # Log combined results
        if regular_result['success'] and minifig_result['success']:
            regular_summary = regular_result.get('summary', {})
            minifig_summary = minifig_result.get('summary', {})
            
            total_regular = regular_summary.get('local_missing_count', 0)
            total_minifig = minifig_summary.get('local_missing_count', 0)
            added_regular = regular_summary.get('actual_added', 0)
            added_minifig = minifig_summary.get('actual_added', 0)
            removed_regular = regular_summary.get('actual_removed', 0)
            removed_minifig = minifig_summary.get('actual_removed', 0)
            
            app.logger.info(f"Scheduled sync completed successfully:")
            app.logger.info(f"  Regular parts: {total_regular} local, {added_regular} added, {removed_regular} removed")
            app.logger.info(f"  Minifig parts: {total_minifig} local, {added_minifig} added, {removed_minifig} removed")
            app.logger.info(f"  Total: {total_regular + total_minifig} parts across both lists")
        else:
            error_messages = []
            if not regular_result['success']:
                error_messages.append(f"Regular parts: {regular_result.get('message', 'Unknown error')}")
            if not minifig_result['success']:
                error_messages.append(f"Minifig parts: {minifig_result.get('message', 'Unknown error')}")
            app.logger.error(f"Scheduled sync failed - {'; '.join(error_messages)}")
            
    except Exception as e:
        app.logger.error(f"Error during scheduled missing parts sync: {e}")


def scheduled_sync_user_sets():
    """
    Scheduled task to sync user sets with Rebrickable every 6 hours.
    Only runs if tokens are configured.
    """
    try:
        from services.token_service import get_rebrickable_user_token, get_rebrickable_api_key
        from services.rebrickable_sets_sync_service import sync_user_sets_with_rebrickable
        
        # Check if tokens are configured
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            app.logger.info("Scheduled user sets sync skipped - no API credentials configured")
            return
        
        app.logger.info("Starting scheduled user sets sync")
        result = sync_user_sets_with_rebrickable()
        
        if result['success']:
            summary = result.get('summary', {})
            app.logger.info(f"Scheduled user sets sync completed - {summary.get('sets_added', 0)} sets added, {summary.get('sets_removed', 0)} sets removed")
        else:
            app.logger.error(f"Scheduled user sets sync failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        app.logger.error(f"Error during scheduled user sets sync: {e}")


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

# Set up the scheduler for database backup and sync tasks
scheduler = BackgroundScheduler()

# Database backup every 6 hours
scheduler.add_job(func=backup_database, trigger="interval",
                  hours=6, id='backup_database')

# Rebrickable sync tasks every 6 hours (offset by 30 minutes to avoid conflicts)
scheduler.add_job(func=scheduled_sync_missing_parts, trigger="interval",
                  hours=6, minutes=30, id='sync_missing_parts')

scheduler.add_job(func=scheduled_sync_user_sets, trigger="interval", 
                  hours=6, minutes=35, id='sync_user_sets')

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
