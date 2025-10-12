"""
This module provides a route for looking up part information in the Brick Manager application.

It includes:
- Loading and displaying part details from the database (RebrickableParts and PartStorage).
- Retrieving the storage location (schrank, fach, box) for the part from the database.
"""

from flask import Blueprint, render_template, request, flash
from models import RebrickableParts, PartStorage, RebrickablePartCategories, RebrickableInventoryParts

part_lookup_bp = Blueprint('part_lookup', __name__)


@part_lookup_bp.route('/lookup_part', methods=['GET', 'POST'])
def lookup_part():
    """
    Handle the part lookup process.

    If a POST request is received, the function attempts to retrieve the part's storage location
    and details from the database (RebrickableParts and PartStorage tables). If the part is not found, 
    a flash message is displayed.

    Returns:
        Response: Renders the lookup_part.html template with part details and storage location.
    """
    part_details = None
    schrank = fach = box = None

    if request.method == 'POST':
        part_id = request.form.get('part_id')

        # Query the RebrickableParts table for part details
        rebrickable_part = RebrickableParts.query.filter_by(
            part_num=part_id).first()

        if rebrickable_part:
            # Get part category information
            category_name = rebrickable_part.category.name if rebrickable_part.category else "Unknown"

            # Get image URL from RebrickableInventoryParts table
            # Select one entry that has an image URL (could be any color/inventory)
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part_id,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != ''
            ).first()

            part_img_url = inventory_part.img_url if inventory_part else rebrickable_part.part_img_url

            # Create part_details dictionary with database information
            part_details = {
                'part_num': rebrickable_part.part_num,
                'name': rebrickable_part.name,
                'part_cat_id': rebrickable_part.part_cat_id,
                'category_name': category_name,
                'part_material': rebrickable_part.part_material,
                'part_img_url': part_img_url,
                'part_url': f"https://rebrickable.com/parts/{rebrickable_part.part_num}/"
            }

            # Query the PartStorage table for storage location
            part_storage = PartStorage.query.filter_by(
                part_num=part_id).first()

            if part_storage:
                schrank = part_storage.location
                fach = part_storage.level
                box = part_storage.box
            else:
                flash(
                    f"Storage location for Part ID {part_id} not found in database.")
        else:
            flash(f"Part ID {part_id} not found in database.")

    return render_template('lookup_part.html',
                           part_details=part_details,
                           schrank=schrank,
                           fach=fach,
                           box=box)
