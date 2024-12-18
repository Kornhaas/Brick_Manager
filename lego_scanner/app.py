"""
This module sets up and runs the LEGO Scanner Flask application.

It configures the application, registers blueprints, and loads the master lookup data.
"""
import os
from datetime import datetime
import shutil
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask
from flask_migrate import Migrate
import logging
from config import Config
from models import db  # Import the db instance from models
from routes.upload import upload_bp
from routes.label import label_bp
from routes.main import main_bp
from routes.storage import storage_bp
from routes.manual_entry import manual_entry_bp
from routes.part_lookup import part_lookup_bp
from routes.set_search import set_search_bp
from routes.load_categories import load_categories_bp
from routes.set_maintain import set_maintain_bp
from routes.missing_parts import missing_parts_bp
from routes.dashboard import dashboard_bp
from services.lookup_service import load_master_lookup

def backup_database():
    # Backup the database
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    backup_db_path = f"{db_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup.db"
    shutil.copyfile(db_path, backup_db_path)
    app.logger.info(f"Database backed up to {backup_db_path}")

    # Backup the master_lookup.json
    lookup_dir = os.path.join(basedir, 'lookup')
    master_lookup_file = os.path.join(lookup_dir, 'master_lookup.json')
    if os.path.exists(master_lookup_file):
        backup_lookup_path = f"{master_lookup_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup.json"
        shutil.copyfile(master_lookup_file, backup_lookup_path)
        app.logger.info(f"Master lookup backed up to {backup_lookup_path}")
    else:
        app.logger.warning(f"Master lookup file {master_lookup_file} does not exist.")



# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set your secret key here
app.config.from_object(Config)  # Load the configuration

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure the 'instances' directory exists
instances_dir = os.path.join(basedir, 'instance')
if not os.path.exists(instances_dir):
    os.makedirs(instances_dir)

# Update the database URI to use the 'instances' directory
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instances_dir, "lego_scanner.db")}'
print(f'sqlite:///{os.path.join(instances_dir, "lego_scanner.db")}')
# Initialize the db instance with the app
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.DEBUG)

# Ensure database tables are created
with app.app_context():
    db.create_all()  # Ensure tables are created
    try:
        master_lookup = load_master_lookup()
        app.logger.debug("Master lookup data loaded successfully.")
    except Exception as e:
        app.logger.error(f"Failed to load master lookup data: {e}")

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(label_bp)
app.register_blueprint(main_bp)
app.register_blueprint(storage_bp)
app.register_blueprint(manual_entry_bp)
app.register_blueprint(part_lookup_bp)
app.register_blueprint(set_search_bp)
app.register_blueprint(load_categories_bp)
app.register_blueprint(set_maintain_bp)
app.register_blueprint(missing_parts_bp)
app.register_blueprint(dashboard_bp)

# Set up the scheduler for database backup
scheduler = BackgroundScheduler()
#scheduler.add_job(func=backup_database, trigger="interval", hours=24)  # Backup every 24 hours
scheduler.add_job(func=backup_database, trigger="interval", hours=1)  # Backup every 24 hours
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
   
    app.run(host='0.0.0.0', port=5000, debug=True)
