"""

This module provides routes for the dashboard,

including viewing summaries, details, and updating quantities.
"""

from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from models import (
    NON_LOOSE_PART_STATUSES,
    RebrickableInventoryParts,
    RebrickableParts,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from services.cache_service import cache_image
from services.dashboard_service import (
    build_dashboard_data,
    load_snapshot_history,
    record_daily_snapshot,
)
from services.part_lookup_service import load_part_lookup

# pylint: disable=C0301

dashboard_bp = Blueprint("dashboard", __name__)


def enrich_part(item, master_lookup):
    """

    Enrich part data with additional information.


    Args:
        item (User_Parts | UserMinifigurePart): The part or minifigure part to enrich.
        master_lookup (dict): Lookup data for additional information.

    Returns:
        dict: Enriched part data.
    """
    part_info = RebrickableParts.query.filter_by(part_num=item.part_num).first()

    part_data = master_lookup.get(item.part_num, {})
    category = (
        part_info.category.name if part_info and part_info.category else "No Category"
    )

    # Return API endpoint for lazy loading images (don't cache during initial load)
    # Include color_id to get the correct colored part image
    color_id = item.color_id if hasattr(item, "color_id") else None
    img_url = url_for(
        "dashboard.cache_part_image_api", part_num=item.part_num, color_id=color_id or 0
    )

    location_data = (
        f"Location: {part_data.get('location', 'Unknown')}, "
        f"Level: {part_data.get('level', 'Unknown')}, "
        f"Box: {part_data.get('box', 'Unknown')}"
        if part_data
        else "Not Specified"
    )

    return {
        "part_id": item.id,
        "set_id": item.user_set.template_set.set_num if item.user_set else None,
        "internal_id": item.user_set.id if item.user_set else None,
        "part_num": item.part_num,
        "color_id": color_id,
        "name": part_info.name if part_info else "Unknown",
        "color": item.rebrickable_color.name if item.rebrickable_color else "Unknown",
        "color_rgb": item.rebrickable_color.rgb if item.rebrickable_color else None,
        "color_is_trans": (
            item.rebrickable_color.is_trans if item.rebrickable_color else False
        ),
        "total_quantity": item.quantity,
        "have_quantity": item.have_quantity,
        "category": category,
        "location": location_data,
        "image_url": img_url,
    }


@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """Display fast collection intelligence metrics and trend charts."""
    metrics = build_dashboard_data()
    record_daily_snapshot(metrics)
    history = load_snapshot_history()
    completion_rate = (
        round(metrics["owned_parts"] / metrics["required_parts"] * 100, 1)
        if metrics["required_parts"]
        else 0
    )

    return render_template(
        "dashboard.html",
        metrics=metrics,
        history=history,
        completion_rate=completion_rate,
        # Preserve established template contracts and detail links.
        total_parts=metrics["loose_owned_parts"],
        missing_parts=metrics["loose_missing_parts"],
        missing_spare_parts=metrics["missing_spare_parts"],
        missing_minifigure_parts=metrics["missing_minifigure_parts"],
        konvolut_parts=metrics["konvolut_parts"],
        missing_konvolut_parts=metrics["missing_konvolut_parts"],
        missing_konvolut_minifigure_parts=metrics["missing_konvolut_minifigure_parts"],
    )


@dashboard_bp.route("/update_quantity", methods=["POST"])
def update_quantity():
    """Batch update `have_quantity` for parts or minifigure parts."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    changes = data.get("changes")
    if not isinstance(changes, list) or not changes:
        return jsonify({"error": "At least one change is required"}), 400

    validated_changes, validation_error = _validate_quantity_changes(changes)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        updated_records = 0
        for part_id, new_quantity in validated_changes:
            part = User_Parts.query.filter_by(id=part_id).first()
            if part:
                part.have_quantity = max(0, min(part.quantity, new_quantity))
                db.session.add(part)
                updated_records += 1
            else:
                minifigure_part = UserMinifigurePart.query.filter_by(id=part_id).first()
                if minifigure_part:
                    minifigure_part.have_quantity = max(
                        0, min(minifigure_part.quantity, new_quantity)
                    )
                    db.session.add(minifigure_part)
                    updated_records += 1

        if updated_records > 0:
            db.session.commit()
            current_app.logger.info(f"Updated {updated_records} records.")
            return (
                jsonify(
                    {"message": f"{updated_records} records updated successfully!"}
                ),
                200,
            )

        current_app.logger.warning("No records were updated.")
        return jsonify({"message": "No records found to update."}), 404

    except Exception as e:
        current_app.logger.error("Failed to update quantities: %s", e)
        db.session.rollback()
        return jsonify({"error": "Failed to update quantities."}), 500


def _validate_quantity_changes(
    changes: list[object],
) -> tuple[list[tuple[int, int]], str | None]:
    """Validate every batch entry before mutating persistent collection data."""
    validated_changes: list[tuple[int, int]] = []
    for change in changes:
        if not isinstance(change, dict):
            return [], "Each change must be an object"

        part_id = change.get("part_id")
        new_quantity = change.get("new_quantity")
        if isinstance(part_id, bool) or not isinstance(part_id, int) or part_id < 1:
            return [], "part_id must be a positive integer"
        if isinstance(new_quantity, bool) or not isinstance(new_quantity, int):
            return [], "new_quantity must be an integer"
        validated_changes.append((part_id, new_quantity))
    return validated_changes, None


@dashboard_bp.route("/details/<category>", methods=["GET"])
def details(category):
    """Displays detailed data for parts or minifigure parts."""
    category = category.lower()

    master_lookup = load_part_lookup()

    if category == "missing_parts":
        data = (
            User_Parts.query.join(User_Set)
            .filter(
                User_Parts.quantity > User_Parts.have_quantity,
                ~User_Set.status.in_(NON_LOOSE_PART_STATUSES),
            )
            .all()
        )
        title = "Missing Parts"
    elif category == "missing_minifigure_parts":
        data = (
            UserMinifigurePart.query.join(User_Set)
            .filter(
                UserMinifigurePart.quantity > UserMinifigurePart.have_quantity,
                ~User_Set.status.in_(NON_LOOSE_PART_STATUSES),
            )
            .all()
        )
        title = "Missing Minifigure Parts"
    elif category == "konvolut_parts":
        data = (
            User_Parts.query.join(User_Set).filter(User_Set.status == "konvolut").all()
        )
        title = "Konvolut Parts"
    elif category == "konvolut_minifigure_parts":
        data = (
            UserMinifigurePart.query.join(User_Set)
            .filter(User_Set.status == "konvolut")
            .all()
        )
        title = "Konvolut Minifigure Parts"
    else:
        current_app.logger.error("Invalid category requested: %s", category)
        return jsonify({"error": "Invalid category"}), 400

    enriched_data = [enrich_part(item, master_lookup) for item in data]

    return render_template(
        "details.html", title=title, data=enriched_data, category=category
    )


@dashboard_bp.route("/api/missing_parts", methods=["GET"])
def api_missing_parts():
    """API endpoint to retrieve missing parts."""
    master_lookup = load_part_lookup()

    missing_parts = (
        User_Parts.query.join(User_Set)
        .filter(
            User_Parts.quantity > User_Parts.have_quantity,
            ~User_Set.status.in_(NON_LOOSE_PART_STATUSES),
        )
        .all()
    )

    enriched_data = [enrich_part(item, master_lookup) for item in missing_parts]
    return jsonify(enriched_data)


@dashboard_bp.route("/api/missing_minifigure_parts", methods=["GET"])
def api_missing_minifigure_parts():
    """API endpoint to retrieve missing minifigure parts."""
    master_lookup = load_part_lookup()

    missing_minifigure_parts = (
        UserMinifigurePart.query.join(User_Set)
        .filter(
            UserMinifigurePart.quantity > UserMinifigurePart.have_quantity,
            ~User_Set.status.in_(NON_LOOSE_PART_STATUSES),
        )
        .all()
    )

    enriched_data = [
        enrich_part(item, master_lookup) for item in missing_minifigure_parts
    ]
    return jsonify(enriched_data)


@dashboard_bp.route("/api/cache_part_image/<part_num>/<int:color_id>", methods=["GET"])
def cache_part_image_api(part_num, color_id):
    """API endpoint to cache and return a single part image URL for specific part and color combination."""
    try:
        # Get image URL from inventory_parts table using both part_num and color_id
        inventory_part = RebrickableInventoryParts.query.filter_by(
            part_num=part_num, color_id=color_id
        ).first()

        if (
            inventory_part
            and inventory_part.img_url
            and inventory_part.img_url.startswith("http")
        ):
            cached_url = cache_image(inventory_part.img_url)
            current_app.logger.debug(
                f"Part {part_num} color {color_id}: Found in inventory_parts -> {cached_url}"
            )
            return jsonify({"success": True, "url": cached_url})

        # Try without color_id as fallback
        inventory_part_any = RebrickableInventoryParts.query.filter_by(
            part_num=part_num
        ).first()
        if (
            inventory_part_any
            and inventory_part_any.img_url
            and inventory_part_any.img_url.startswith("http")
        ):
            cached_url = cache_image(inventory_part_any.img_url)
            current_app.logger.debug(
                f"Part {part_num}: Found in inventory_parts (any color) -> {cached_url}"
            )
            return jsonify({"success": True, "url": cached_url})

        # Fallback to parts table
        part_info = RebrickableParts.query.filter_by(part_num=part_num).first()
        if (
            part_info
            and part_info.part_img_url
            and part_info.part_img_url.startswith("http")
        ):
            cached_url = cache_image(part_info.part_img_url)
            current_app.logger.debug(
                f"Part {part_num}: Found in parts table -> {cached_url}"
            )
            return jsonify({"success": True, "url": cached_url})

        # No image found
        current_app.logger.debug(
            f"Part {part_num} color {color_id}: No image found, using default"
        )
        return jsonify(
            {"success": False, "url": url_for("static", filename="default_image.png")}
        )

    except Exception as e:
        current_app.logger.error(
            f"Error caching image for part {part_num} color {color_id}: {e}"
        )
        return jsonify(
            {"success": False, "url": url_for("static", filename="default_image.png")}
        )
