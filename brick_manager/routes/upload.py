"""

This module handles the file upload functionality for the Brick Manager application.


It includes:
- Uploading and saving files to the server.
- Checking the validity of the uploaded files.
- Fetching predictions based on the uploaded image.
- Augmenting prediction results with additional information from the master lookup.
"""

import os  # Standard library import
from typing import Dict, List

from config import Config

# Third-party imports
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from models import PartStorage, User_Parts
from services.brickognize_service import get_predictions
from services.part_lookup_service import load_part_lookup, save_part_lookup
from services.sqlite_service import get_category_name_from_db
from werkzeug.utils import secure_filename

upload_bp = Blueprint("upload", __name__)


def get_missing_sets_for_part(part_num: str) -> List[Dict]:
    """Get list of user sets where this part is missing."""
    try:
        user_parts = (
            User_Parts.query.filter_by(part_num=part_num)
            .filter(User_Parts.have_quantity < User_Parts.quantity)
            .all()
        )

        sets_missing = []
        for user_part in user_parts:
            if user_part.user_set:
                missing_qty = user_part.quantity - user_part.have_quantity

                # Debug: Check if rebrickable_color is loaded
                color_hex = "CCCCCC"
                color_name = "Unknown"
                if user_part.rebrickable_color:
                    color_hex = user_part.rebrickable_color.rgb
                    color_name = user_part.rebrickable_color.name
                    print(f"Color for part {part_num}: {color_name} = #{color_hex}")
                else:
                    print(
                        f"Warning: No rebrickable_color for part {part_num}, color_id={user_part.color_id}"
                    )

                sets_missing.append(
                    {
                        "user_set_id": user_part.user_set.id,
                        "set_num": user_part.user_set.set_num,
                        "set_name": user_part.user_set.template_set.name
                        if user_part.user_set.template_set
                        else "Unknown Set",
                        "needed": user_part.quantity,
                        "have": user_part.have_quantity,
                        "missing": missing_qty,
                        "color_id": user_part.color_id,
                        "color_name": color_name,
                        "color_hex": color_hex,
                        "part_id": user_part.id,
                    }
                )

        return sets_missing
    except Exception as e:
        print(f"Error getting missing sets for part {part_num}: {e}")
        return []


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """

    Handle file upload, validate the file, and process predictions.


    Returns:
        Response: Renders the results template if successful, otherwise redirects to the main index.
    """
    master_lookup = load_part_lookup()

    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("main.index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)

        result = get_predictions(file_path, filename)

        if result:
            for item in result.get("items", []):
                item_id = item.get("id")

                # Try to get storage location from master_lookup first (cached)
                if item_id in master_lookup:
                    item["lookup_info"] = master_lookup[item_id]
                else:
                    # If not in cache, query database directly
                    part_storage = PartStorage.query.filter_by(part_num=item_id).first()
                    if part_storage:
                        item["lookup_info"] = {
                            "location": part_storage.location,
                            "level": part_storage.level,
                            "box": part_storage.box,
                        }

                # Add category information from the database
                # Ensure your prediction result includes 'category_id'
                part_cat_id = item.get("category_id")
                if part_cat_id:
                    item["category_name"] = get_category_name_from_db(part_cat_id)

                # Add missing sets information
                missing_sets = get_missing_sets_for_part(item_id)
                item["missing_sets"] = missing_sets

            return render_template("results.html", result=result)

        flash("Invalid result structure or no items found")
        return redirect(url_for("main.index"))

    flash("Allowed file types are png, jpg, jpeg, gi")
    return redirect(url_for("main.index"))


def allowed_file(filename):
    """

    Check if the uploaded file is of an allowed type.


    Args:
        filename (str): The name of the uploaded file.

    Returns:
        bool: True if the file is of an allowed type, False otherwise.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


@upload_bp.route("/upload/increment_part/<int:part_id>", methods=["POST"])
def increment_part(part_id):
    """Increment the have_quantity for a User_Part by 1."""
    from app import db

    try:
        user_part = User_Parts.query.get_or_404(part_id)
        user_part.have_quantity += 1
        db.session.commit()

        return {
            "success": True,
            "new_have": user_part.have_quantity,
            "new_missing": user_part.quantity - user_part.have_quantity,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}, 400


@upload_bp.route("/upload/update_part_quantity/<int:part_id>", methods=["POST"])
def update_part_quantity(part_id):
    """Update the have_quantity for a User_Part to a specific value."""
    from app import db

    try:
        user_part = User_Parts.query.get_or_404(part_id)
        data = request.get_json()
        new_have = int(data.get("have_quantity", 0))

        # Validate the new quantity
        if new_have < 0:
            return (
                jsonify({"success": False, "error": "Quantity cannot be negative"}),
                400,
            )
        if new_have > user_part.quantity:
            return (
                jsonify(
                    {"success": False, "error": "Quantity cannot exceed needed amount"}
                ),
                400,
            )

        old_have = user_part.have_quantity
        user_part.have_quantity = new_have
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "old_have": old_have,
                "new_have": user_part.have_quantity,
                "new_missing": user_part.quantity - user_part.have_quantity,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@upload_bp.route("/upload/save_storage_location", methods=["POST"])
def save_storage_location():
    """Save or update storage location for a part."""
    from app import db

    try:
        data = request.get_json()
        part_num = data.get("part_num")
        location = data.get("location")
        level = data.get("level")
        box = data.get("box")

        # Validate inputs
        if not all([part_num, location, level, box]):
            return jsonify({"success": False, "error": "All fields are required"}), 400

        # Get or create PartStorage entry
        part_storage = PartStorage.query.filter_by(part_num=part_num).first()

        if part_storage:
            # Update existing entry
            part_storage.location = str(location)
            part_storage.level = str(level)
            part_storage.box = str(box)
        else:
            # Create new entry
            part_storage = PartStorage(
                part_num=part_num,
                location=str(location),
                level=str(level),
                box=str(box),
            )
            db.session.add(part_storage)

        db.session.commit()

        # Also update the master lookup cache
        master_lookup = load_part_lookup()
        master_lookup[part_num] = {
            "location": str(location),
            "level": str(level),
            "box": str(box),
        }
        save_part_lookup(master_lookup)

        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
