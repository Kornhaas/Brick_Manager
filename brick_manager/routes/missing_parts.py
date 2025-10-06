"""
This module handles the display of all missing parts and missing minifigure parts across all sets.
"""

from flask import Blueprint, render_template
from sqlalchemy.orm import joinedload
from models import User_Set, UserMinifigurePart
from services.part_lookup_service import load_part_lookup
#pylint: disable=C0301
# Define a new Blueprint for missing parts
missing_parts_bp = Blueprint('missing_parts', __name__)


@missing_parts_bp.route('/missing_parts', methods=['GET'])
def missing_parts():
    """
    Displays all missing parts and missing minifigure parts across all sets.
    """
    missing_items = []
    master_lookup = load_part_lookup()

    # Query all User_Sets
    user_sets = User_Set.query.options(
        joinedload(User_Set.parts_in_set),  # Correct relationship name
        joinedload(User_Set.template_set)
    ).all()

    # Collect missing regular parts
    for user_set in user_sets:
        for part in user_set.parts_in_set:  # Correct relationship name
            if part.quantity > part.have_quantity:
                part_data = master_lookup.get(part.part_num, {})
                location_data = (
                    f"Location: {part_data.get('location', 'Unknown')}, "
                    f"Level: {part_data.get('level', 'Unknown')}, "
                    f"Box: {part_data.get('box', 'Unknown')}"
                    if part_data else "Not Specified"
                )
                missing_items.append({
                    'type': 'Regular Part',
                    'set_id': user_set.template_set.set_num,
                    'internal_id': user_set.id,
                    'item_id': part.part_num,
                    'name': part.rebrickable_part.name if part.rebrickable_part else "Unknown",
                    'color': part.rebrickable_color.name if part.rebrickable_color else "Unknown",
                    'is_spare': part.is_spare,
                    'missing_quantity': part.quantity - part.have_quantity,
                    'img_url': part.rebrickable_part.part_img_url if part.rebrickable_part else "/static/default_image.png",
                    'location': location_data
                })

    # Collect missing minifigure parts
    user_minifigure_parts = UserMinifigurePart.query.options(
        joinedload(UserMinifigurePart.user_set)
    ).all()
    for minifig_part in user_minifigure_parts:
        if minifig_part.quantity > minifig_part.have_quantity:
            part_data = master_lookup.get(minifig_part.part_num, {})
            location_data = (
                f"Location: {part_data.get('location', 'Unknown')}, "
                f"Level: {part_data.get('level', 'Unknown')}, "
                f"Box: {part_data.get('box', 'Unknown')}"
                if part_data else "Not Specified"
            )
            missing_items.append({
                'type': 'Minifigure Part',
                'set_id': minifig_part.user_set.template_set.set_num,
                'internal_id': minifig_part.user_set.id,
                'item_id': minifig_part.part_num,
                'name': minifig_part.rebrickable_part.name if minifig_part.rebrickable_part else "Unknown",
                'color': minifig_part.rebrickable_color.name if minifig_part.rebrickable_color else "Unknown",
                'is_spare': minifig_part.is_spare,
                'missing_quantity': minifig_part.quantity - minifig_part.have_quantity,
                'img_url': minifig_part.rebrickable_part.part_img_url if minifig_part.rebrickable_part else "/static/default_image.png",
                'location': location_data
            })

    return render_template('missing_parts.html', missing_items=missing_items)
