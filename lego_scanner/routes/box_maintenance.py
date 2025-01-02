from flask import Blueprint, jsonify, render_template, request, current_app
from models import db, PartStorage, PartInfo, Category
from services.cache_service import cache_image

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
            # Filter levels based on location
            levels = db.session.query(PartStorage.level).filter_by(location=location).distinct().all()
            return jsonify({"levels": sorted([lvl[0] for lvl in levels])})

        if location and level:
            # Filter boxes based on location and level
            boxes = db.session.query(PartStorage.box).filter_by(location=location, level=level).distinct().all()
            return jsonify({"boxes": sorted([box[0] for box in boxes])})

        return jsonify({"error": "Invalid parameters"}), 400
    except Exception as e:
        current_app.logger.error(f"Error in filter_box_data: {e}")
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
        current_app.logger.error(f"Error in get_box_data: {e}")
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
        # Debug log: Input parameters
        current_app.logger.debug(f"Fetching contents for Location: {location}, Level: {level}, Box: {box}")

        # Fetch part info based on PartStorage
        contents = db.session.query(PartInfo).join(
            PartStorage, PartInfo.part_num == PartStorage.part_num
        ).filter(
            PartStorage.location == location,
            PartStorage.level == level,
            PartStorage.box == box
        ).all()

        # Debug log: Query result
        current_app.logger.debug(f"Found {len(contents)} parts in the box.")

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
        current_app.logger.error(f"Error fetching box contents: {e}")
        return jsonify({"error": str(e)}), 500
