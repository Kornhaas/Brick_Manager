"""
This module handles the manual entry of LEGO parts into the master lookup.
Users can manually enter part details such as part ID, location (schrank), level (fach), and box.
The data is either added to or updated in the master lookup.
"""

from flask import Blueprint, render_template, request, flash
from services.part_lookup_service import load_part_lookup, save_part_lookup

manual_entry_bp = Blueprint('manual_entry', __name__)


@manual_entry_bp.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    """
    Handles manual entry of part information. If the part ID already exists in the master lookup,
    it shows a confirmation dialog before overwriting the entry.
    """
    try:
        master_lookup = load_part_lookup()
    except Exception as e:
        flash(f"Error loading master lookup: {str(e)}", "danger")
        return render_template('manual_entry.html', existing_entry=None)

    if request.method == 'POST':
        part_id = request.form.get('id')
        schrank = request.form.get('schrank')
        fach = request.form.get('fach')
        box = request.form.get('box')
        # Hidden input to track confirmation
        confirmed = request.form.get('confirmed')

        # Input validation
        if not part_id or not part_id.strip():
            flash("Part ID cannot be empty.", "danger")
            return render_template('manual_entry.html', schrank=schrank, fach=fach, box=box, existing_entry=None)

        if not all([schrank.isdigit(), fach.isdigit(), box.isdigit()]):
            flash("Location, Level, and Box must be numeric.", "danger")
            return render_template('manual_entry.html', part_id=part_id, schrank=schrank, fach=fach, box=box, existing_entry=None)

        # Check if part ID exists
        if part_id in master_lookup:
            if not confirmed:
                # Show existing entry for confirmation
                existing_entry = master_lookup[part_id]
                flash(
                    f"Part ID {part_id} already exists. Confirm overwrite.", "warning")
                return render_template(
                    'manual_entry.html',
                    part_id=part_id,
                    schrank=schrank,
                    fach=fach,
                    box=box,
                    existing_entry=existing_entry
                )

            # Overwrite the existing entry after confirmation
            master_lookup[part_id] = {
                'location': schrank,
                'level': fach,
                'box': box
            }
            flash(f"Part ID {part_id} successfully updated.", "success")
        else:
            # Add new entry
            master_lookup[part_id] = {
                'location': schrank,
                'level': fach,
                'box': box
            }
            flash(f"Part ID {part_id} successfully added.", "success")

        # Save the changes to the file
        try:
            save_part_lookup(master_lookup)
        except Exception as e:
            flash(f"Error saving master lookup: {str(e)}", "danger")
            return render_template('manual_entry.html', existing_entry=None)

        return render_template('manual_entry.html', part_id="", schrank=schrank, fach=fach, box=str(int(box) + 1), existing_entry=None)

    return render_template('manual_entry.html', existing_entry=None)
