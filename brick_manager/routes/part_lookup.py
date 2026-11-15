"""

This module provides a route for looking up part information in the Brick Manager application.


It includes:
- Loading and displaying part details from the database (RebrickableParts and PartStorage).
- Retrieving the storage location (schrank, fach, box) for the part from the database.
"""

from flask import Blueprint, flash, render_template, request
from models import RebrickableInventoryParts, RebrickableParts

part_lookup_bp = Blueprint("part_lookup", __name__)


@part_lookup_bp.route("/lookup_part", methods=["GET", "POST"])
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
    storage_locations = []

    schrank = fach = box = None

    if request.method == "POST":
        part_id = request.form.get("part_id")

        # Query the RebrickableParts table for part details
        rebrickable_part = RebrickableParts.query.filter_by(part_num=part_id).first()

        if rebrickable_part:
            # Get part category information
            category_name = (
                rebrickable_part.category.name
                if rebrickable_part.category
                else "Unknown"
            )

            # Get image URL from RebrickableInventoryParts table
            # Select one entry that has an image URL (could be any color/inventory)
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part_id,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
            ).first()

            part_img_url = (
                inventory_part.img_url
                if inventory_part
                else rebrickable_part.part_img_url
            )

            # Create part_details dictionary with database information
            part_details = {
                "part_num": rebrickable_part.part_num,
                "name": rebrickable_part.name,
                "part_cat_id": rebrickable_part.part_cat_id,
                "category_name": category_name,
                "part_material": rebrickable_part.part_material,
                "part_img_url": part_img_url,
                "part_url": f"https://rebrickable.com/parts/{rebrickable_part.part_num}/",
            }

            # Query the PartStorage table for storage location
            from services.storage_service import list_part_locations

            storage_locations = list_part_locations(part_id)
            if storage_locations:
                if len(storage_locations) == 1:
                    schrank = storage_locations[0]["location"]
                    fach = storage_locations[0]["level"]
                    box = storage_locations[0]["box"]
            else:
                flash(f"Storage location for Part ID {part_id} not found in database.")
        else:
            flash(f"Part ID {part_id} not found in database.")

    return render_template(
        "lookup_part.html",
        part_details=part_details,
        storage_locations=storage_locations,
        schrank=schrank,
        fach=fach,
        box=box,
    )
