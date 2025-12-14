"""

This module handles the manual entry of Brick parts into the master lookup.

Users can manually enter part details such as part ID, location (schrank), level (fach), and box.
The data is either added to or updated in the master lookup.
"""

from flask import Blueprint, flash, jsonify, render_template, request, url_for
from models import PartStorage, RebrickableInventoryParts, RebrickableParts, db
from services.cache_service import cache_image
from services.part_lookup_service import load_part_lookup, save_part_lookup

# pylint: disable=W0718

manual_entry_bp = Blueprint("manual_entry", __name__)


@manual_entry_bp.route("/manual_entry", methods=["GET", "POST"])
def manual_entry():  # pylint: disable=too-many-locals,too-many-branches,too-many-statements  # noqa: C901
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
        part_num_input = request.form.get("part_num")
        schrank = request.form.get("schrank")
        fach = request.form.get("fach")
        box = request.form.get("box")
        color_id = request.form.get("color_id")  # Optional color ID
        notes = request.form.get("notes")  # Optional notes

        # Convert color_id to int or None
        color_id = (
            int(color_id)
            if color_id and color_id.strip() and color_id.isdigit()
            else None
        )
        notes = notes.strip() if notes else None

        # Validate inputs
        if not part_num_input or not part_num_input.strip():
            flash("Part ID cannot be empty.", "danger")
        elif not all(val.isdigit() for val in [schrank, fach, box]):
            flash("Location, Level, and Box must be numeric.", "danger")
        else:
            # Handle comma-separated part numbers
            part_numbers = [p.strip() for p in part_num_input.split(",") if p.strip()]

            # Validate all parts exist in Rebrickable database
            valid_parts = []
            invalid_parts = []

            for part_num in part_numbers:
                part_info = RebrickableInventoryParts.query.filter_by(
                    part_num=part_num
                ).first()
                if not part_info:
                    part_info = RebrickableParts.query.filter_by(
                        part_num=part_num
                    ).first()

                if part_info:
                    valid_parts.append(part_num)
                else:
                    invalid_parts.append(part_num)

            if invalid_parts:
                flash(
                    f"Invalid part numbers skipped: {', '.join(invalid_parts)}",
                    "warning",
                )

            if not valid_parts:
                flash("No valid part numbers to add.", "danger")
                return render_template("manual_entry.html", existing_entry=None)

            # Process all valid parts
            added_count = 0
            updated_count = 0

            for part_num in valid_parts:
                # Check if exact match exists (same location, level, box, color, notes)
                existing_storage = PartStorage.query.filter_by(
                    part_num=part_num,
                    location=schrank,
                    level=fach,
                    box=box,
                    color_id=color_id,
                    notes=notes,
                ).first()

                if existing_storage:
                    # Exact match exists - no need to add
                    updated_count += 1
                else:
                    # Create new storage entry (allows multiple locations per part)
                    new_storage = PartStorage(
                        part_num=part_num,
                        location=schrank,
                        level=fach,
                        box=box,
                        color_id=color_id,
                        notes=notes,
                    )
                    db.session.add(new_storage)
                    added_count += 1

                # Also maintain master_lookup for backward compatibility (use first/primary location)
                if part_num not in master_lookup:
                    master_lookup[part_num] = {
                        "location": schrank,
                        "level": fach,
                        "box": box,
                    }

            # Save changes
            try:
                db.session.commit()
                save_part_lookup(master_lookup)

                # Build success message
                messages = []
                if added_count > 0:
                    messages.append(f"{added_count} part(s) added")
                if updated_count > 0:
                    messages.append(f"{updated_count} part(s) updated")

                flash(f"Successfully saved: {', '.join(messages)}.", "success")

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
            return (
                jsonify(
                    {
                        "exists": False,
                        "message": "Part not found in Rebrickable database",
                    }
                ),
                404,
            )

        # Check if part has storage locations (can be multiple)
        existing_storages = (
            PartStorage.query.filter_by(part_num=part_num)
            .filter(
                PartStorage.location.isnot(None),
                PartStorage.level.isnot(None),
                PartStorage.box.isnot(None),
            )
            .all()
        )

        has_storage = len(existing_storages) > 0
        storage_info = None
        storage_list = []

        if has_storage:
            # Return list of all storage locations
            for storage in existing_storages:
                storage_entry = {
                    "id": storage.id,  # Include ID for deletion
                    "location": storage.location,
                    "level": storage.level,
                    "box": storage.box,
                    "color": storage.rebrickable_color.name
                    if storage.rebrickable_color
                    else None,
                    "color_id": storage.color_id,
                    "notes": storage.notes,
                }
                storage_list.append(storage_entry)

            # For backward compatibility, keep first one as primary
            storage_info = storage_list[0] if storage_list else None

        # Get cached image URL from rebrickable_inventory_parts (take first available)
        inventory_part = RebrickableInventoryParts.query.filter_by(
            part_num=part_num
        ).first()

        if (
            inventory_part
            and inventory_part.img_url
            and inventory_part.img_url.startswith("http")
        ):
            # Valid external URL from inventory parts - use cache_image which handles caching
            image_url = cache_image(inventory_part.img_url)
        elif rebrickable_part.part_img_url and rebrickable_part.part_img_url.startswith(
            "http"
        ):
            # Fallback to part_img_url if available
            image_url = cache_image(rebrickable_part.part_img_url)
        else:
            # No valid URL - use default image
            image_url = url_for("static", filename="default_image.png")

        return jsonify(
            {
                "exists": True,
                "has_storage": has_storage,
                "storage_info": storage_info,
                "storage_list": storage_list,  # All storage locations
                "storage_count": len(storage_list),
                "part_info": {
                    "name": rebrickable_part.name,
                    "category": rebrickable_part.category.name
                    if rebrickable_part.category
                    else "Unknown",
                    "image_url": image_url,
                },
            }
        )

    except Exception as e:
        return (
            jsonify({"exists": False, "message": f"Error validating part: {str(e)}"}),
            500,
        )


@manual_entry_bp.route(
    "/manual_entry/delete_storage/<int:storage_id>", methods=["DELETE"]
)
def delete_storage(storage_id):
    """Delete a specific storage location entry."""
    try:
        storage = PartStorage.query.get(storage_id)
        if not storage:
            return jsonify({"error": "Storage location not found"}), 404

        db.session.delete(storage)
        db.session.commit()

        return jsonify({"message": "Storage location deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error deleting storage: {str(e)}"}), 500
