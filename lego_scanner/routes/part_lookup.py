"""
This module provides a route for looking up part information in the LEGO Scanner application.

It includes:
- Loading and displaying part details from the Rebrickable API.
- Retrieving the storage location (schrank, fach, box) for the part from the master lookup.
"""

from flask import Blueprint, render_template, request, flash
from services.part_lookup_service import load_part_lookup
from services.rebrickable_service import get_part_details

part_lookup_bp = Blueprint('part_lookup', __name__)


@part_lookup_bp.route('/lookup_part', methods=['GET', 'POST'])
def lookup_part():
    """
    Handle the part lookup process.

    If a POST request is received, the function attempts to retrieve the part's storage location
    and details from the master lookup and Rebrickable API. If the part is not found, a flash
    message is displayed.

    Returns:
        Response: Renders the lookup_part.html template with part details and storage location.
    """
    part_details = None
    schrank = fach = box = None

    if request.method == 'POST':
        part_id = request.form.get('part_id')
        master_lookup = load_part_lookup()

        if part_id in master_lookup:
            schrank = master_lookup[part_id].get('location')
            fach = master_lookup[part_id].get('level')
            box = master_lookup[part_id].get('box')
            part_details = get_part_details(part_id)
        else:
            flash(f"Part ID {part_id} not found in master lookup.")

    return render_template('lookup_part.html',
                           part_details=part_details,
                           schrank=schrank,
                           fach=fach,
                           box=box)
