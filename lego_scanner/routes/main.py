"""
This module defines the main route for the LEGO Scanner application.

It includes:
- A route to render the index (home) page.
"""

import json
import logging
import os
from flask import Blueprint, render_template, current_app
from models import db, PartStorage
from services.part_lookup_service import save_part_lookup

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Render the index (home) page.

    Returns:
        Response: Renders the index.html template.
    """
    return render_template('index.html')

@main_bp.route('/migrate')
def migrate():
    """
    Migrate the database to the latest version.

    Returns:
        Response: A message indicating the migration was successful.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Path to the lookup.json file
    lookup_json_path = r'C:\Users\Holge\OneDrive\python\Lego_Manager\lego_scanner\lookup\master_lookup.json'

    # Load the JSON data
    if not os.path.exists(lookup_json_path):
        logger.error(f"File not found: {lookup_json_path}")
        return 'File not found', 404

    with open(lookup_json_path, 'r') as file:
        lookup_data = json.load(file)
        logger.info(f"Loaded data from {lookup_json_path}")

    errors = []

    # Save the master lookup data to the database
    try:
        save_part_lookup(lookup_data)
        logger.info("Data has been successfully moved from lookup.json to the database.")
    except Exception as e:
        logger.error(f"Error saving data to the database: {e}")
        errors.append(f"Save error: {e}")

    if errors:
        return f"Database migration completed with errors: {errors}", 500
    else:
        return 'Database migration successful'