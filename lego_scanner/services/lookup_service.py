import json
from flask import current_app


def load_master_lookup():
    with current_app.app_context():  # Ensures the app context is available
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'r') as file:
            return json.load(file)


def save_master_lookup(master_lookup):
    with current_app.app_context():  # Ensures the app context is available
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'w') as file:
            json.dump(master_lookup, file, indent=4)
