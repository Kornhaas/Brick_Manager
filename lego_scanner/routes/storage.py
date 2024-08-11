# routes/storage.py
import json
from flask import Blueprint, render_template, request, redirect, url_for, current_app

storage_bp = Blueprint('storage', __name__)

def load_master_lookup():
    """Load the master_lookup.json file."""
    try:
        with open(current_app.config['MASTER_LOOKUP_PATH'], 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("master_lookup.json not found, returning empty dictionary.")
        return {}

def save_master_lookup(data):
    """Save the updated master_lookup.json file."""
    with open(current_app.config['MASTER_LOOKUP_PATH'], 'w') as file:
        json.dump(data, file, indent=4)
        print("master_lookup.json updated successfully.")

@storage_bp.route('/add_to_storage/<id>', methods=['GET', 'POST'])
def add_to_storage(id):
    if request.method == 'POST':
        location = request.form.get('location')
        level = request.form.get('level')
        box = request.form.get('box')
        
        # Load the current master_lookup.json data
        master_lookup = load_master_lookup()

        # Update the entry for the given id
        master_lookup[id] = {
            'location': location,
            'level': level,
            'box': box
        }

        # Save the updated data back to master_lookup.json
        save_master_lookup(master_lookup)

        # Update the in-memory data in the application if needed
        current_app.config['MASTER_LOOKUP'] = master_lookup

        print(f"Stored item {id} at Location: {location}, Level: {level}, Box: {box}")

        return redirect(url_for('main.index'))
    
    return render_template('storage.html', item_id=id)
