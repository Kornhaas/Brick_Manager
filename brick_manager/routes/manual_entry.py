"""

This module handles the manual entry of Brick parts into the master lookup.

Users can manually enter part details such as part ID, location (schrank), level (fach), and box.
The data is either added to or updated in the master lookup.
"""

from flask import Blueprint, flash, render_template, request, jsonify, url_for
from models import PartStorage, RebrickableParts, RebrickableInventoryParts
from services.part_lookup_service import load_part_lookup, save_part_lookup
from services.cache_service import cache_image

# pylint: disable=W0718

manual_entry_bp = Blueprint("manual_entry", __name__)


@manual_entry_bp.route("/manual_entry", methods=["GET", "POST"])
def manual_entry():
    """

    Handles manual entry of part information. If the part ID already exists in the master lookup,

    it shows a confirmation dialog before overwriting the entry.
    """
    try:
        master_lookup = load_part_lookup()
    except Exception as error:
        flash(f"Error loading master lookup: {error}", "danger")
        return render_template("manual_entry.html", existing_entry=None)

    if request.method == "POST":
        part_num = request.form.get("part_num")
        schrank = request.form.get("schrank")
        fach = request.form.get("fach")
        box = request.form.get("box")
        confirmed = request.form.get("confirmed")  # Track confirmation

        # Validate inputs
        if not part_num or not part_num.strip():
            flash("Part ID cannot be empty.", "danger")
        elif not all(val.isdigit() for val in [schrank, fach, box]):
            flash("Location, Level, and Box must be numeric.", "danger")
        else:
            # Check if part ID exists in storage with non-empty fields
            part_storage = PartStorage.query.filter_by(part_num=part_num).first()
            existing_entry = None
            
            # Only consider it as existing if all storage fields have values
            if part_storage and part_storage.location and part_storage.level and part_storage.box:
                existing_entry = {
                    "location": part_storage.location,
                    "level": part_storage.level,
                    "box": part_storage.box
                }
            
            if existing_entry and not confirmed:
                flash(
                    f"Part Number {part_num} already exists. Confirm overwrite.",
                    "warning",
                )
                return render_template(
                    "manual_entry.html",
                    part_num=part_num,
                    schrank=schrank,
                    fach=fach,
                    box=box,
                    existing_entry=existing_entry,
                )

            # Add or update entry in the master lookup
            master_lookup[part_num] = {"location": schrank, "level": fach, "box": box}
            action = "updated" if existing_entry else "added"
            flash(f"Part Number {part_num} successfully {action}.", "success")

            # Save changes
            try:
                save_part_lookup(master_lookup)
            except Exception as save_error:
                flash(f"Error saving master lookup: {save_error}", "danger")
                return render_template("manual_entry.html", existing_entry=None)

            # Prepare for next entry with incremented box number
            next_box = str(int(box) + 1)
            return render_template(
                "manual_entry.html",
                part_num="",
                schrank=schrank,
                fach=fach,
                box=next_box,
                existing_entry=None,
            )

    return render_template("manual_entry.html", existing_entry=None)


@manual_entry_bp.route("/manual_entry/validate_part/<part_num>", methods=["GET"])
def validate_part(part_num):
    """Validate if a part exists in Rebrickable database and check storage status."""
    try:
        # Check if part exists in Rebrickable database
        rebrickable_part = RebrickableParts.query.filter_by(part_num=part_num).first()
        
        if not rebrickable_part:
            return jsonify({
                "exists": False,
                "message": "Part not found in Rebrickable database"
            }), 404
        
        # Check if part has storage location
        part_storage = PartStorage.query.filter_by(part_num=part_num).first()
        
        has_storage = False
        storage_info = None
        
        if part_storage and part_storage.location and part_storage.level and part_storage.box:
            has_storage = True
            storage_info = {
                "location": part_storage.location,
                "level": part_storage.level,
                "box": part_storage.box
            }
        
        # Get cached image URL from rebrickable_inventory_parts (take first available)
        inventory_part = RebrickableInventoryParts.query.filter_by(
            part_num=part_num
        ).first()
        
        if inventory_part and inventory_part.img_url and inventory_part.img_url.startswith('http'):
            # Valid external URL from inventory parts - use cache_image which handles caching
            image_url = cache_image(inventory_part.img_url)
        elif rebrickable_part.part_img_url and rebrickable_part.part_img_url.startswith('http'):
            # Fallback to part_img_url if available
            image_url = cache_image(rebrickable_part.part_img_url)
        else:
            # No valid URL - use default image
            image_url = url_for("static", filename="default_image.png")
        
        return jsonify({
            "exists": True,
            "has_storage": has_storage,
            "storage_info": storage_info,
            "part_info": {
                "name": rebrickable_part.name,
                "category": rebrickable_part.category.name if rebrickable_part.category else "Unknown",
                "image_url": image_url
            }
        })
    
    except Exception as e:
        return jsonify({
            "exists": False,
            "message": f"Error validating part: {str(e)}"
        }), 500
