"""
This module provides routes and logic for managing storage
operations in the Brick Manager application.

It includes:
- Loading and saving the `master_lookup.json` file.
- Adding or updating storage information for specific parts.
- Rendering the storage template for user interaction.
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from services.part_lookup_service import load_part_lookup, save_part_lookup

storage_bp = Blueprint('storage', __name__)


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
        master_lookup = load_part_lookup()

        # Update the entry for the given part_id
        master_lookup[part_id] = {
            'location': location,
            'level': level,
            'box': box
        }

        # Save the updated data back to master_lookup.json
        save_part_lookup(master_lookup)

        # Update the in-memory data in the application if needed
        current_app.config['MASTER_LOOKUP'] = master_lookup

        print(f"Stored item {part_id} at Location: {location}, Level: {level}, Box: {box}")

        return redirect(url_for('main.index'))

    return render_template('storage.html', item_id=part_id)
