"""
This module provides routes for managing boxes, including filtering, fetching contents,
and generating labels for boxes.
"""

from flask import Blueprint, jsonify, render_template, request, current_app, send_file
from models import db, PartStorage, PartInfo
from services.cache_service import cache_image
from services.label_service import create_box_label_jpg
#pylint: disable=C0301,W0718
box_maintenance_bp = Blueprint('box_maintenance', __name__)


@box_maintenance_bp.route('/box_maintenance', methods=['GET'])
def box_maintenance_page():
    """
    Renders the Box Maintenance page.
    """
    return render_template('box_maintenance.html')


@box_maintenance_bp.route('/box_maintenance/filter', methods=['POST'])
def filter_box_data():
    """
    Filters levels and boxes based on the selected location and level.
    """
    data = request.json
    location = data.get("location")
    level = data.get("level")

    try:
        if location and not level:
            levels = db.session.query(PartStorage.level).filter_by(
                location=location).distinct().all()
            return jsonify({"levels": sorted([lvl[0] for lvl in levels])})

        if location and level:
            boxes = db.session.query(PartStorage.box).filter_by(
                location=location, level=level).distinct().all()
            return jsonify({"boxes": sorted([box[0] for box in boxes])})

        return jsonify({"error": "Invalid parameters"}), 400
    except Exception as e:
        current_app.logger.error("Error in filter_box_data: %s", e)
        return jsonify({"error": str(e)}), 500


@box_maintenance_bp.route('/box_maintenance/data', methods=['GET'])
def get_box_data():
    """
    Fetches dropdown data for location, level, and box.
    """
    try:
        locations = db.session.query(PartStorage.location).distinct().all()
        levels = db.session.query(PartStorage.level).distinct().all()
        boxes = db.session.query(PartStorage.box).distinct().all()

        return jsonify({
            "locations": sorted([loc[0] for loc in locations]),
            "levels": sorted([lvl[0] for lvl in levels]),
            "boxes": sorted([box[0] for box in boxes]),
        })
    except Exception as e:
        current_app.logger.error("Error in get_box_data: %s", e)
        return jsonify({"error": str(e)}), 500


@box_maintenance_bp.route('/box_contents', methods=['POST'])
def get_box_contents():
    """
    Fetches the content of a specific box based on location, level, and box.
    """
    data = request.json
    location = data.get("location")
    level = data.get("level")
    box = data.get("box")

    if not (location and level and box):
        return jsonify({"error": "All fields are required"}), 400

    try:
        contents = db.session.query(PartInfo).join(
            PartStorage, PartInfo.part_num == PartStorage.part_num
        ).filter(
            PartStorage.location == location,
            PartStorage.level == level,
            PartStorage.box == box
        ).all()

        return jsonify([
            {
                "part_num": part.part_num,
                "image": cache_image(part.part_img_url),
                "category": part.category.name if part.category else "Unknown",
                "name": part.name,
            }
            for part in contents
        ])
    except Exception as e:
        current_app.logger.error("Error fetching box contents: %s", e)
        return jsonify({"error": str(e)}), 500


@box_maintenance_bp.route('/box_maintenance/label', methods=['POST'])
def generate_box_label():
    """
    Generates a label for a specific box containing its contents.
    """
    data = request.json
    location = data.get("location")
    level = data.get("level")
    box = data.get("box")

    if not (location and level and box):
        return jsonify({"error": "All fields are required"}), 400

    try:
        contents = db.session.query(PartInfo).join(
            PartStorage, PartInfo.part_num == PartStorage.part_num
        ).filter(
            PartStorage.location == location,
            PartStorage.level == level,
            PartStorage.box == box
        ).all()

        if not contents:
            return jsonify({"error": "No items found in the specified box"}), 404

        box_info = {
            "location": location,
            "level": level,
            "box": box,
            "items": [
                {
                    "part_num": part.part_num,
                    "name": part.name,
                    "category": part.category.name if part.category else "Unknown",
                    "img_url": part.part_img_url
                }
                for part in contents
            ]
        }

        pdf_path = create_box_label_jpg(box_info)
        return send_file(pdf_path, as_attachment=True, download_name=f"box_label_{box}.pdf", mimetype="application/pdf")

    except Exception as e:
        current_app.logger.error("Error generating box label: %s", e)
        return jsonify({"error": str(e)}), 500


@box_maintenance_bp.route('/box_maintenance/generate_labels', methods=['POST'])
def generate_labels():
    """
    Generate labels for all boxes, skipping boxes with empty location, level, or box values.
    """
    try:
        storage_parts = db.session.query(PartStorage).join(PartInfo).all()
        if not storage_parts:
            return jsonify({"message": "No matching labels to generate."}), 404

        boxes = {}
        for storage in storage_parts:
            if not storage.location or not storage.level or not storage.box:
                current_app.logger.warning(
                    "Skipping incomplete box info: %s", storage)
                continue

            box_key = (storage.location, storage.level, storage.box)
            if box_key not in boxes:
                boxes[box_key] = []
            boxes[box_key].append({
                "part_num": storage.part_num,
                "name": storage.part_info.name,
                "category": storage.part_info.category.name if storage.part_info.category else "Unknown",
                "img_url": storage.part_info.part_img_url
            })

        generated_labels = []
        for (location, level, box), items in boxes.items():
            box_info = {
                "location": location,
                "level": level,
                "box": box,
                "items": items
            }
            if not items:
                current_app.logger.warning(
                    "Skipping empty box: %s", (location, level, box))
                continue

            box_info = {"location": location,
                        "level": level, "box": box, "items": items}
            label_path = create_box_label_jpg(box_info)
            generated_labels.append(label_path)

        if not generated_labels:
            return jsonify({"message": "No labels generated."}), 404

        return jsonify({"message": "Labels generated successfully.", "labels": generated_labels}), 200

    except Exception as e:
        current_app.logger.error("Error generating labels: %s", e)
        return jsonify({"error": str(e)}), 500