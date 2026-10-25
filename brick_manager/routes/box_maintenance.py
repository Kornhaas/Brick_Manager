"""

This module provides routes for managing boxes, including filtering, fetching contents,

and generating labels for boxes.
"""

import os
from typing import cast

from config import Config
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from models import PartStorage, RebrickableInventoryParts, RebrickableParts, db
from services.cache_service import cache_image
from services.label_service import create_avery_3474_pdf, create_box_label_jpg
from werkzeug.exceptions import BadRequest, NotFound

# pylint: disable=C0301,W0718,W0719
box_maintenance_bp = Blueprint("box_maintenance", __name__)


@box_maintenance_bp.route("/box_maintenance", methods=["GET"])
def box_maintenance_page():
    """Renders the Box Maintenance page."""
    return render_template("box_maintenance_new.html")


def _parse_box_references(data):
    """Validate and deduplicate box references received from the browser."""
    if not isinstance(data, dict) or not isinstance(data.get("boxes"), list):
        raise BadRequest("A boxes list is required.")

    references = []
    seen = set()
    for item in data["boxes"]:
        if not isinstance(item, dict):
            raise BadRequest("Invalid box reference.")
        reference = tuple(item.get(field) for field in ("location", "level", "box"))
        if any(
            not isinstance(value, str) or not value.strip() or len(value) > 100
            for value in reference
        ):
            raise BadRequest("Invalid box reference.")
        normalized = tuple(cast(str, value).strip() for value in reference)
        if normalized not in seen:
            references.append(normalized)
            seen.add(normalized)
    if not references or len(references) > 240:
        raise BadRequest("Select between 1 and 240 boxes.")
    return references


def _box_label_info(location, level, box):
    """Load the catalog information needed to render one physical box label."""
    contents = (
        db.session.query(RebrickableParts)
        .join(PartStorage, RebrickableParts.part_num == PartStorage.part_num)
        .filter(
            PartStorage.location == location,
            PartStorage.level == level,
            PartStorage.box == box,
        )
        .order_by(RebrickableParts.part_num)
        .all()
    )
    if not contents:
        raise NotFound("Box not found.")

    items = []
    for part in contents:
        inventory_part = RebrickableInventoryParts.query.filter(
            RebrickableInventoryParts.part_num == part.part_num,
            RebrickableInventoryParts.img_url.isnot(None),
            RebrickableInventoryParts.img_url != "",
            RebrickableInventoryParts.img_url != "None",
        ).first()
        items.append(
            {
                "part_num": part.part_num,
                "category": part.category.name if part.category else "Unknown",
                "img_url": (
                    inventory_part.img_url
                    if inventory_part and inventory_part.img_url
                    else part.part_img_url
                ),
            }
        )
    return {
        "location": location,
        "level": level,
        "box": box,
        "items": items,
    }


@box_maintenance_bp.route("/box_maintenance/label_queue", methods=["GET"])
def get_label_queue():
    """Return one queue entry per physical storage box."""
    rows = (
        PartStorage.query.filter(
            PartStorage.location.isnot(None),
            PartStorage.level.isnot(None),
            PartStorage.box.isnot(None),
            db.func.trim(PartStorage.location) != "",
            db.func.trim(PartStorage.level) != "",
            db.func.trim(PartStorage.box) != "",
        )
        .order_by(PartStorage.location, PartStorage.level, PartStorage.box)
        .all()
    )
    grouped = {}
    for storage in rows:
        key = (storage.location, storage.level, storage.box)
        entry = grouped.setdefault(
            key,
            {
                "location": storage.location,
                "level": storage.level,
                "box": storage.box,
                "part_count": 0,
                "label_printed": True,
            },
        )
        entry["part_count"] += 1
        entry["label_printed"] = entry["label_printed"] and storage.label_printed
    return jsonify({"boxes": list(grouped.values()), "sheet_capacity": 24})


@box_maintenance_bp.route("/box_maintenance/label_sheet", methods=["POST"])
def generate_label_sheet():
    """Generate a print-ready Avery 3474 PDF for selected storage boxes."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise BadRequest("Invalid JSON payload.")
        references = _parse_box_references(data)
        start_position = data.get("start_position", 1)
        if (
            isinstance(start_position, bool)
            or not isinstance(start_position, int)
            or not 1 <= start_position <= 24
        ):
            raise BadRequest("Invalid start position.")
        horizontal_offset = data.get("horizontal_offset_mm", 0)
        vertical_offset = data.get("vertical_offset_mm", 0)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not -10 <= value <= 10
            for value in (horizontal_offset, vertical_offset)
        ):
            raise BadRequest("Print offsets must be between -10 and 10 mm.")
        boxes = [_box_label_info(*reference) for reference in references]
        pdf = create_avery_3474_pdf(
            boxes,
            start_position=start_position,
            horizontal_offset_mm=horizontal_offset,
            vertical_offset_mm=vertical_offset,
        )
        return send_file(
            pdf,
            as_attachment=True,
            download_name=(
                f"avery_3474_box_labels_x{horizontal_offset:g}_y{vertical_offset:g}.pdf"
            ),
            mimetype="application/pdf",
        )
    except (BadRequest, ValueError) as error:
        current_app.logger.info("Invalid label sheet request: %s", error)
        return jsonify({"error": str(error)}), 400
    except NotFound as error:
        return jsonify({"error": str(error)}), 404


@box_maintenance_bp.route("/box_maintenance/label_sheet/printed", methods=["POST"])
def confirm_label_sheet_printed():
    """Mark every storage row in the selected boxes as having a current label."""
    try:
        references = _parse_box_references(request.get_json(silent=True))
        updated = 0
        for location, level, box in references:
            box_updates = PartStorage.query.filter_by(
                location=location, level=level, box=box
            ).update({PartStorage.label_printed: True}, synchronize_session=False)
            if box_updates == 0:
                raise NotFound("Box not found.")
            updated += box_updates
        db.session.commit()
        return jsonify({"message": "Labels marked as printed.", "updated": updated})
    except BadRequest as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except NotFound as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 404


@box_maintenance_bp.route("/box_maintenance/filter_data", methods=["GET"])
def filter_box_data_get():
    """GET endpoint for filtering locations, levels, and boxes."""
    try:
        location = request.args.get("location")
        level = request.args.get("level")

        if not location and not level:
            # Return all locations
            locations = (
                db.session.query(PartStorage.location)
                .distinct()
                .order_by(PartStorage.location)
                .all()
            )
            return jsonify({"locations": [loc[0] for loc in locations]})

        if location and not level:
            # Return levels for the location
            levels = (
                db.session.query(PartStorage.level)
                .filter(PartStorage.location == location)
                .distinct()
                .order_by(PartStorage.level)
                .all()
            )
            return jsonify({"levels": [lvl[0] for lvl in levels]})

        if location and level:
            # Return boxes for the location and level
            boxes = (
                db.session.query(PartStorage.box)
                .filter(
                    PartStorage.location == location,
                    PartStorage.level == level,
                )
                .distinct()
                .order_by(PartStorage.box)
                .all()
            )
            return jsonify({"boxes": [box[0] for box in boxes]})

        return jsonify({"error": "Invalid parameters"}), 400
    except Exception as e:
        current_app.logger.error("Error in filter_box_data_get: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/contents", methods=["GET"])
def get_box_contents_get():
    """GET endpoint for fetching box contents."""
    try:
        location = request.args.get("location")
        level = request.args.get("level")
        box = request.args.get("box")

        if not (location and level and box):
            raise BadRequest("All fields are required.")

        contents = (
            db.session.query(RebrickableParts, PartStorage)
            .join(PartStorage, RebrickableParts.part_num == PartStorage.part_num)
            .filter(
                PartStorage.location == location,
                PartStorage.level == level,
                PartStorage.box == box,
            )
            .all()
        )

        result = []
        for part, storage in contents:
            # Use the same image lookup logic
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part.part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
                RebrickableInventoryParts.img_url != "None",
            ).first()

            if inventory_part and inventory_part.img_url:
                img_url = inventory_part.img_url
            else:
                img_url = (
                    part.part_img_url
                    if part.part_img_url
                    else "/static/default_image.png"
                )

            result.append(
                {
                    "part_num": part.part_num,
                    "img_url": img_url,
                    "category": part.category.name if part.category else "Unknown",
                    "name": part.name,
                    "storage_id": storage.id,
                }
            )

        return jsonify(result)
    except BadRequest as e:
        current_app.logger.error("BadRequest in get_box_contents_get: %s", e)
        return jsonify({"error": "Invalid request."}), 400
    except Exception as e:
        current_app.logger.error("Error in get_box_contents_get: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/filter", methods=["POST"])
def filter_box_data():
    """Filters levels and boxes based on the selected location and level."""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Invalid input data format.")

        location = data.get("location")
        level = data.get("level")

        if location and not level:
            levels = (
                db.session.query(PartStorage.level)
                .filter_by(location=location)
                .distinct()
                .all()
            )
            return jsonify({"levels": sorted([lvl[0] for lvl in levels])})

        if location and level:
            boxes = (
                db.session.query(PartStorage.box)
                .filter_by(location=location, level=level)
                .distinct()
                .all()
            )
            return jsonify({"boxes": sorted([box[0] for box in boxes])})

        raise BadRequest("Invalid parameters provided.")
    except BadRequest as e:
        current_app.logger.error("BadRequest in filter_box_data: %s", e)
        return jsonify({"error": "BadRequest in filter_box_data."}), 400
    except Exception as e:
        current_app.logger.error("Error in filter_box_data: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/data", methods=["GET"])
def get_box_data():
    """Fetches dropdown data for location, level, and box."""
    try:
        locations = db.session.query(PartStorage.location).distinct().all()
        levels = db.session.query(PartStorage.level).distinct().all()
        boxes = db.session.query(PartStorage.box).distinct().all()

        return jsonify(
            {
                "locations": sorted([loc[0] for loc in locations]),
                "levels": sorted([lvl[0] for lvl in levels]),
                "boxes": sorted([box[0] for box in boxes]),
            }
        )
    except Exception as e:
        current_app.logger.error("Error in get_box_data: %s", e)
        return jsonify({"error": "Failed to retrieve box data."}), 500


@box_maintenance_bp.route("/box_contents", methods=["POST"])
def get_box_contents():
    """

    Fetches the content of a specific box based on location, level, and box.
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Invalid input data format.")

        location = data.get("location")
        level = data.get("level")
        box = data.get("box")

        if not (location and level and box):
            raise BadRequest("All fields are required.")

        contents = (
            db.session.query(RebrickableParts, PartStorage)
            .join(PartStorage, RebrickableParts.part_num == PartStorage.part_num)
            .filter(
                PartStorage.location == location,
                PartStorage.level == level,
                PartStorage.box == box,
            )
            .all()
        )

        current_app.logger.info(
            f"Found {len(contents)} parts in box {location}-{level}-{box}"
        )

        result = []
        for part, storage in contents:
            # Use the same image lookup logic as part_lookup.py
            # First try to get image URL from RebrickableInventoryParts (inventory-specific images)
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part.part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
                RebrickableInventoryParts.img_url != "None",
            ).first()

            # Use inventory image if available, otherwise fall back to generic part image
            if inventory_part and inventory_part.img_url:
                original_img_url = inventory_part.img_url
            else:
                original_img_url = part.part_img_url

            # Handle various "empty" cases: None, empty string, or literal 'None' string
            if (
                original_img_url
                and original_img_url.strip()
                and original_img_url.strip().lower() != "none"
            ):
                cached_img_url = cache_image(original_img_url)
            else:
                cached_img_url = "/static/default_image.png"

            current_app.logger.debug(
                f"Part {part.part_num}: original_url='{original_img_url}', cached_url='{cached_img_url}'"
            )

            result.append(
                {
                    "part_num": part.part_num,
                    "image": cached_img_url,
                    "category": part.category.name if part.category else "Unknown",
                    "name": part.name,
                    "storage_id": storage.id,
                    "label_printed": storage.label_printed,
                }
            )

        return jsonify(result)
    except BadRequest as e:
        current_app.logger.error("BadRequest in get_box_contents: %s", e)
        return jsonify({"error": "BadRequest in get_box_contents."}), 400
    except Exception as e:
        current_app.logger.error("Error in get_box_contents: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/update_label_status", methods=["POST"])
def update_label_status():
    """Updates the label_printed status for a part storage entry."""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Invalid input data format.")

        storage_id = data.get("storage_id")
        label_printed = data.get("label_printed")

        if storage_id is None or label_printed is None:
            raise BadRequest("storage_id and label_printed are required.")

        storage = PartStorage.query.get(storage_id)
        if not storage:
            raise NotFound("Part storage entry not found.")

        storage.label_printed = bool(label_printed)
        db.session.commit()

        return jsonify({"message": "Label status updated successfully."}), 200
    except BadRequest as e:
        current_app.logger.error("BadRequest in update_label_status: %s", e)
        return jsonify({"error": "BadRequest in update_label_status."}), 400
    except NotFound as e:
        current_app.logger.error("NotFound in update_label_status: %s", e)
        return jsonify({"error": "Part storage entry not found."}), 404
    except Exception as e:
        current_app.logger.error("Error in update_label_status: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/label", methods=["POST"])
def generate_box_label():
    """Generates a label for a specific box containing its contents."""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Invalid input data format.")

        location = data.get("location")
        level = data.get("level")
        box = data.get("box")

        if not (location and level and box):
            raise BadRequest("All fields are required.")

        contents = (
            db.session.query(RebrickableParts)
            .join(PartStorage, RebrickableParts.part_num == PartStorage.part_num)
            .filter(
                PartStorage.location == location,
                PartStorage.level == level,
                PartStorage.box == box,
            )
            .all()
        )

        if not contents:
            raise NotFound("No items found in the specified box.")

        box_info = {"location": location, "level": level, "box": box, "items": []}

        # Apply the same improved image logic for label generation
        for part in contents:
            # First try to get image URL from RebrickableInventoryParts
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part.part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
                RebrickableInventoryParts.img_url != "None",
            ).first()

            # Use inventory image if available, otherwise fall back to generic part image
            if inventory_part and inventory_part.img_url:
                img_url = inventory_part.img_url
            else:
                img_url = part.part_img_url

            box_info["items"].append(
                {
                    "part_num": part.part_num,
                    "name": part.name,
                    "category": part.category.name if part.category else "Unknown",
                    "img_url": img_url,
                }
            )

        label_path = create_box_label_jpg(box_info)

        if not os.path.exists(label_path):
            raise FileNotFoundError("Label file could not be generated.")

        return send_from_directory(
            Config.UPLOAD_FOLDER,
            os.path.basename(label_path),
            as_attachment=True,
            download_name=f"box_label_{box}.jpg",
            mimetype="image/jpeg",
        )

    except BadRequest as e:
        current_app.logger.error("BadRequest in generate_box_label: %s", e)
        return jsonify({"error": "BadRequest in generate_box_label."}), 400

    except NotFound as e:
        current_app.logger.error("NotFound in generate_box_label: %s", e)
        return jsonify({"error": "NotFound in generate_box_label."}), 404
    except Exception as e:
        current_app.logger.error("Error in generate_box_label: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route("/box_maintenance/update_part_location", methods=["POST"])
def update_part_location():
    """Updates the storage location for a part."""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Invalid input data format.")

        storage_id = data.get("storage_id")
        new_location = data.get("location")
        new_level = data.get("level")
        new_box = data.get("box")

        if not all([storage_id, new_location, new_level, new_box]):
            raise BadRequest("All fields are required.")

        storage = PartStorage.query.get(storage_id)
        if not storage:
            raise NotFound("Part storage entry not found.")

        old_location = storage.location
        old_level = storage.level
        old_box = storage.box
        PartStorage.query.filter_by(
            location=old_location, level=old_level, box=old_box
        ).update({PartStorage.label_printed: False}, synchronize_session=False)
        storage.location = new_location
        storage.level = new_level
        storage.box = new_box
        storage.label_printed = False
        db.session.commit()

        return jsonify({"message": "Location updated successfully."}), 200
    except BadRequest as e:
        current_app.logger.error("BadRequest in update_part_location: %s", e)
        return jsonify({"error": "Invalid request."}), 400
    except NotFound as e:
        current_app.logger.error("NotFound in update_part_location: %s", e)
        return jsonify({"error": "Part storage entry not found."}), 404
    except Exception as e:
        current_app.logger.error("Error in update_part_location: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route(
    "/box_maintenance/delete_part/<int:storage_id>", methods=["DELETE"]
)
def delete_part_storage(storage_id):
    """Deletes a part from storage."""
    try:
        storage = PartStorage.query.get(storage_id)
        if not storage:
            raise NotFound("Part storage entry not found.")

        part_num = storage.part_num
        PartStorage.query.filter_by(
            location=storage.location, level=storage.level, box=storage.box
        ).update({PartStorage.label_printed: False}, synchronize_session=False)
        db.session.delete(storage)
        db.session.commit()

        return (
            jsonify({"message": f"Part {part_num} removed from storage successfully."}),
            200,
        )
    except NotFound as e:
        current_app.logger.error("NotFound in delete_part_storage: %s", e)
        return jsonify({"error": "Part storage entry not found."}), 404
    except Exception as e:
        current_app.logger.error("Error in delete_part_storage: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route(
    "/box_maintenance/location_overview/<location>", methods=["GET"]
)
def get_location_overview(location):
    """Gets an overview of all boxes in a specific location."""
    try:
        # Optimized query: Get first part_num for each box in a single query
        subquery = (
            db.session.query(
                PartStorage.level,
                PartStorage.box,
                db.func.min(PartStorage.part_num).label("first_part_num"),
                db.func.count(PartStorage.id).label("part_count"),
            )
            .filter(PartStorage.location == location)
            .group_by(PartStorage.level, PartStorage.box)
            .subquery()
        )

        # Join with RebrickableParts to get images in one query
        boxes_with_parts = (
            db.session.query(
                subquery.c.level,
                subquery.c.box,
                subquery.c.part_count,
                RebrickableParts.part_num,
                RebrickableParts.part_img_url,
            )
            .join(
                RebrickableParts, RebrickableParts.part_num == subquery.c.first_part_num
            )
            .order_by(subquery.c.level, subquery.c.box)
            .all()
        )

        result = []
        for level, box, part_count, part_num, part_img_url in boxes_with_parts:
            # Try to get cached image URL from inventory parts (color-specific)
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
                RebrickableInventoryParts.img_url != "None",
            ).first()

            if inventory_part and inventory_part.img_url:
                img_url = cache_image(inventory_part.img_url)
            elif (
                part_img_url
                and part_img_url.strip()
                and part_img_url.strip().lower() != "none"
            ):
                img_url = cache_image(part_img_url)
            else:
                img_url = "/static/default_image.png"

            result.append(
                {
                    "location": location,
                    "level": level,
                    "box": box,
                    "part_count": part_count,
                    "img_url": img_url,
                }
            )

        return jsonify(result)
    except Exception as e:
        current_app.logger.error("Error in get_location_overview: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@box_maintenance_bp.route(
    "/box_maintenance/level_overview/<location>/<level>", methods=["GET"]
)
def get_level_overview(location, level):
    """Gets an overview of all boxes in a specific location and level."""
    try:
        # Optimized query: Get first part_num for each box in a single query
        subquery = (
            db.session.query(
                PartStorage.box,
                db.func.min(PartStorage.part_num).label("first_part_num"),
                db.func.count(PartStorage.id).label("part_count"),
            )
            .filter(PartStorage.location == location, PartStorage.level == level)
            .group_by(PartStorage.box)
            .subquery()
        )

        # Join with RebrickableParts to get images in one query
        boxes_with_parts = (
            db.session.query(
                subquery.c.box,
                subquery.c.part_count,
                RebrickableParts.part_num,
                RebrickableParts.part_img_url,
            )
            .join(
                RebrickableParts, RebrickableParts.part_num == subquery.c.first_part_num
            )
            .order_by(subquery.c.box)
            .all()
        )

        result = []
        for box, part_count, part_num, part_img_url in boxes_with_parts:
            # Try to get cached image URL from inventory parts (color-specific)
            inventory_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
                RebrickableInventoryParts.img_url != "None",
            ).first()

            if inventory_part and inventory_part.img_url:
                img_url = cache_image(inventory_part.img_url)
            elif (
                part_img_url
                and part_img_url.strip()
                and part_img_url.strip().lower() != "none"
            ):
                img_url = cache_image(part_img_url)
            else:
                img_url = "/static/default_image.png"

            result.append(
                {
                    "location": location,
                    "level": level,
                    "box": box,
                    "part_count": part_count,
                    "img_url": img_url,
                }
            )

        return jsonify(result)
    except Exception as e:
        current_app.logger.error("Error in get_level_overview: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500
