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
    try:
        master_lookup = load_master_lookup()
    except Exception as e:
        flash(f"Error loading master lookup: {str(e)}", "danger")
        return render_template('manual_entry.html')

    if request.method == 'POST':
        part_id = request.form.get('id')
        schrank = request.form.get('schrank')
        fach = request.form.get('fach')
        box = request.form.get('box')

        # Input validation
        if not part_id or not part_id.strip():
            flash("Part ID cannot be empty.", "danger")
            return render_template('manual_entry.html', schrank=schrank, fach=fach, box=box)

        if not all([schrank.isdigit(), fach.isdigit(), box.isdigit()]):
            flash("Location, Level, and Box must be numeric.", "danger")
            return render_template('manual_entry.html', part_id=part_id, schrank=schrank, fach=fach, box=box)

        if part_id in master_lookup:
            flash(f"Part ID {part_id} already exists. Updating information.", "warning")
            # Update existing entry
            master_lookup[part_id]['location'] = schrank
            master_lookup[part_id]['level'] = fach
            master_lookup[part_id]['box'] = box
        else:
            flash(f"Part ID {part_id} successfully added.", "success")
            # Add new entry
            master_lookup[part_id] = {
                'location': schrank, 'level': fach, 'box': box}

        try:
            # Save the updated master lookup
            save_master_lookup(master_lookup)
        except Exception as e:
            flash(f"Error saving master lookup: {str(e)}", "danger")
            return render_template('manual_entry.html')

        # Clear part_id and increment the box number
        return render_template('manual_entry.html',
                               part_id="",
                               schrank=schrank,
                               fach=fach,
                               box=str(int(box) + 1))

    return render_template('manual_entry.html')
