"""
This module provides routes and logic for managing storage
operations in the LEGO Scanner application.

It includes:
- Loading and saving the `master_lookup.json` file.
- Adding or updating storage information for specific parts.
- Rendering the storage template for user interaction.
"""

import json
from flask import Blueprint, render_template, request, redirect, url_for, current_app

storage_bp = Blueprint('storage', __name__)


def load_master_lookup():
    """
    Load the `master_lookup.json` file.

    Returns:
        dict: The content of the `master_lookup.json` file as a dictionary.
    """
    try:
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("master_lookup.json not found, returning empty dictionary.")
        return {}


def save_master_lookup(data):
    """
    Save the updated `master_lookup.json` file.

    Args:
        data (dict): The data to be saved to `master_lookup.json`.
    """
    with open(current_app.config['MASTER_LOOKUP_PATH'], 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)
        print("master_lookup.json updated successfully.")


@storage_bp.route('/add_to_storage/<part_id>', methods=['GET', 'POST'])
def add_to_storage(part_id):
    """
    Handle the addition or update of storage information for a specific part.

    Args:
        part_id (str): The ID of the part being stored or updated.

    Returns:
        Response: Redirects to the main index page after processing the form data.
    """
    if request.method == 'POST':
        location = request.form.get('location')
        level = request.form.get('level')
        box = request.form.get('box')

        # Load the current master_lookup.json data
        master_lookup = load_master_lookup()

        # Update the entry for the given part_id
        master_lookup[part_id] = {
            'location': location,
            'level': level,
            'box': box
        }

        # Save the updated data back to master_lookup.json
        save_master_lookup(master_lookup)

        # Update the in-memory data in the application if needed
        current_app.config['MASTER_LOOKUP'] = master_lookup

        print(f"Stored item {part_id} at Location: {
              location}, Level: {level}, Box: {box}")

        return redirect(url_for('main.index'))

    return render_template('storage.html', item_id=part_id)
