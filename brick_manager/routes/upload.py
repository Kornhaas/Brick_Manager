"""

This module handles the file upload functionality for the Brick Manager application.


It includes:
- Uploading and saving files to the server.
- Checking the validity of the uploaded files.
- Fetching predictions based on the uploaded image.
- Augmenting prediction results with additional information from the master lookup.
"""

import os  # Standard library import

from config import Config

# Third-party imports
from flask import Blueprint, flash, redirect, render_template, request, url_for
from models import User_Parts, User_Set, RebrickableSets
from services.brickognize_service import get_predictions
from services.part_lookup_service import load_part_lookup
from services.sqlite_service import get_category_name_from_db
from werkzeug.utils import secure_filename

upload_bp = Blueprint("upload", __name__)


def get_missing_sets_for_part(part_num):
    """
    Get a list of sets where this part is missing (have_quantity < quantity).
    
    Args:
        part_num (str): The part number to search for
        
    Returns:
        list: List of dicts containing set information where part is missing
    """
    try:
        # Query for all user parts where this part is missing
        missing_parts = (
            User_Parts.query
            .filter(User_Parts.part_num == part_num)
            .filter(User_Parts.have_quantity < User_Parts.quantity)
            .all()
        )
        
        sets_missing = []
        for user_part in missing_parts:
            # Get the user set
            user_set = User_Set.query.get(user_part.user_set_id)
            if user_set:
                # Get the rebrickable set details
                rb_set = RebrickableSets.query.filter_by(set_num=user_set.set_num).first()
                
                missing_qty = user_part.quantity - user_part.have_quantity
                sets_missing.append({
                    'set_num': user_set.set_num,
                    'set_name': rb_set.name if rb_set else 'Unknown Set',
                    'needed': user_part.quantity,
                    'have': user_part.have_quantity,
                    'missing': missing_qty,
                    'color_id': user_part.color_id,
                    'color_name': user_part.rebrickable_color.name if user_part.rebrickable_color else 'Unknown'
                })
        
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
                if item_id in master_lookup:
                    item["lookup_info"] = master_lookup[item_id]

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
