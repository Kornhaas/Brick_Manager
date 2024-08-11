"""
This module provides functions to load and save the master lookup data
from a JSON file used in the LEGO Scanner application.

It interacts with the file system to read and write JSON data, ensuring
that the operations occur within the Flask application context.
"""

import json
from flask import current_app


def load_master_lookup():
    """
    Load the master lookup data from the JSON file specified in the
    application's configuration.

    Returns:
        dict: The master lookup data loaded from the JSON file.
    """
    with current_app.app_context():  # Ensures the app context is available
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'r', encoding='utf-8') as file:
            return json.load(file)


def save_master_lookup(master_lookup):
    """
    Save the master lookup data to the JSON file specified in the
    application's configuration.

    Args:
        master_lookup (dict): The master lookup data to be saved.
    """
    with current_app.app_context():  # Ensures the app context is available
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'w', encoding='utf-8') as file:
            json.dump(master_lookup, file, indent=4)
