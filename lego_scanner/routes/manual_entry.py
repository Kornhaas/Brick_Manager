from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.lookup_service import load_master_lookup, save_master_lookup

manual_entry_bp = Blueprint('manual_entry', __name__)


@manual_entry_bp.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    master_lookup = load_master_lookup()

    if request.method == 'POST':
        part_id = request.form.get('id')
        schrank = request.form.get('schrank')
        fach = request.form.get('fach')
        box = request.form.get('box')

        if part_id in master_lookup:
            flash(f"Part ID {part_id} already exists. Updating information.")
            # Update existing entry
            master_lookup[part_id]['schrank'] = schrank
            master_lookup[part_id]['fach'] = fach
            master_lookup[part_id]['box'] = box
        else:
            flash(f"Part ID {part_id} does not exist. Adding new entry.")
            # Add new entry
            master_lookup[part_id] = {
                'schrank': schrank, 'fach': fach, 'box': box}

        # Save the updated master_lookup
        save_master_lookup(master_lookup)

        return redirect(url_for('main.index'))

    return render_template('manual_entry.html')
