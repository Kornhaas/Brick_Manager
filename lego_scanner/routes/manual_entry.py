"""
This module handles the manual entry of LEGO parts into the master lookup.
Users can manually enter part details such as part ID, location (schrank), level (fach), and box.
The data is either added to or updated in the master lookup.
"""

from flask import Blueprint, render_template, request, flash
from services.lookup_service import load_master_lookup, save_master_lookup

manual_entry_bp = Blueprint('manual_entry', __name__)


@manual_entry_bp.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    """
    Handles manual entry of part information. If the part ID already exists in the master lookup,
    it updates the entry. Otherwise, it adds a new entry. The user is notified via flash messages.
    """
    master_lookup = load_master_lookup()

    if request.method == 'POST':
        part_id = request.form.get('id')
        schrank = request.form.get('schrank')
        fach = request.form.get('fach')
        box = request.form.get('box')

        if part_id in master_lookup:
            flash(f"Part ID {part_id} already exists. Updating information.")
            # Update existing entry
            master_lookup[part_id]['location'] = schrank
            master_lookup[part_id]['level'] = fach
            master_lookup[part_id]['box'] = box
        else:
            flash(f"Part ID {part_id} does not exist. Adding new entry.")
            # Add new entry
            master_lookup[part_id] = {
                'location': schrank, 'level': fach, 'box': box}

        # Save the updated master_lookup
        save_master_lookup(master_lookup)

        # Render the same template with the flash messages and form data
        return render_template('manual_entry.html',
                               part_id=part_id,
                               schrank=schrank,
                               fach=fach,
                               box=box)

    return render_template('manual_entry.html')
