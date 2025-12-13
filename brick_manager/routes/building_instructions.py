"""
Building Instructions route for displaying and accessing instruction files
"""
import logging
import os

from flask import Blueprint, abort, current_app, render_template, send_file
from models import User_Set, db

# Create blueprint
building_instructions_bp = Blueprint("building_instructions", __name__)

# Configure logging
logger = logging.getLogger(__name__)


def get_instructions_folder():
    """Get the path to the instructions folder"""
    # Check if custom path is configured
    instructions_path = current_app.config.get("INSTRUCTIONS_FOLDER")
    if instructions_path and os.path.exists(instructions_path):
        return instructions_path

    # Default to 'data/instructions' relative to project root
    base_path = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    default_path = os.path.join(base_path, "data", "instructions")

    # Create directory if it doesn't exist
    if not os.path.exists(default_path):
        os.makedirs(default_path, exist_ok=True)
        logger.info(f"Created instructions folder at: {default_path}")

    return default_path


def get_instruction_files_for_sets(set_numbers):
    """
    Scan the instructions folder for specific set numbers only (optimized)
    Args:
        set_numbers: Set of set numbers to look for
    Returns: {set_num: [list of files]}
    """
    instructions_folder = get_instructions_folder()
    available_instructions = {}

    if not os.path.exists(instructions_folder):
        logger.warning(f"Instructions folder not found: {instructions_folder}")
        return available_instructions

    try:
        # List all folders in the instructions directory
        for folder_name in os.listdir(instructions_folder):
            folder_path = os.path.join(instructions_folder, folder_name)

            # Skip if not a directory
            if not os.path.isdir(folder_path):
                continue

            # Extract set number from folder name (first part before space or dash)
            set_num = folder_name.split("-")[0].split("_")[0].strip()

            # Only process if this set number is in our user's collection
            if set_num not in set_numbers:
                continue

            # Get all PDF and JPG files in this folder
            files = []
            for file_name in sorted(os.listdir(folder_path)):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext in [".pdf", ".jpg", ".jpeg", ".png"]:
                        files.append(
                            {
                                "name": file_name,
                                "path": os.path.join(folder_name, file_name),
                                "type": "pdf" if ext == ".pdf" else "image",
                                "size": os.path.getsize(file_path),
                            }
                        )

            if files:
                available_instructions[set_num] = files
                logger.debug(f"Found {len(files)} instruction files for set {set_num}")

    except Exception as e:
        logger.error(f"Error scanning instructions folder: {e}")

    return available_instructions


@building_instructions_bp.route("/building_instructions")
def building_instructions():
    """Display building instructions page with user's sets"""
    try:
        # Get all user sets
        user_sets = User_Set.query.order_by(User_Set.set_num).all()

        # Build list of unique base set numbers to check
        set_numbers_to_check = set()
        for user_set in user_sets:
            set_num = user_set.set_num
            # Strip variant suffix (e.g., "10751-1" becomes "10751")
            set_num_base = set_num.split("-")[0] if "-" in set_num else set_num
            set_numbers_to_check.add(set_num_base)

        # Get available instruction files (only scan for existing set numbers)
        available_instructions = get_instruction_files_for_sets(set_numbers_to_check)

        # Build list of sets with their instruction status
        sets_with_instructions = []
        for user_set in user_sets:
            set_num = user_set.set_num
            # Strip variant suffix (e.g., "10751-1" becomes "10751")
            set_num_base = set_num.split("-")[0] if "-" in set_num else set_num

            # Check if instructions exist for this set (match base number)
            if set_num_base in available_instructions:
                files = available_instructions[set_num_base]
                # Get set details from the related RebrickableSets record
                template = user_set.template_set
                theme_name = (
                    template.theme.name if template and template.theme else None
                )
                sets_with_instructions.append(
                    {
                        "id": user_set.id,
                        "set_num": set_num,
                        "set_name": template.name if template else "Unknown",
                        "year": template.year if template else None,
                        "theme": theme_name,
                        "num_parts": template.num_parts if template else None,
                        "img_url": template.img_url if template else None,
                        "has_instructions": True,
                        "files": files,
                        "file_count": len(files),
                    }
                )

        logger.info(
            f"Found instructions for {len(sets_with_instructions)} out of {len(user_sets)} sets"
        )

        return render_template(
            "building_instructions.html",
            sets=sets_with_instructions,
            total_sets=len(user_sets),
            sets_with_instructions=len(sets_with_instructions),
        )

    except Exception as e:
        logger.error(f"Error loading building instructions: {e}")
        logger.exception("Full traceback:")
        return render_template(
            "building_instructions.html",
            sets=[],
            total_sets=0,
            sets_with_instructions=0,
            error=str(e),
        )


@building_instructions_bp.route("/building_instructions/download/<path:file_path>")
def download_instruction_file(file_path):
    """Download or view an instruction file"""
    try:
        instructions_folder = get_instructions_folder()
        full_path = os.path.join(instructions_folder, file_path)

        # Security check: ensure the file is within the instructions folder
        if not os.path.abspath(full_path).startswith(
            os.path.abspath(instructions_folder)
        ):
            logger.warning(
                f"Attempted access to file outside instructions folder: {file_path}"
            )
            abort(403)

        # Check if file exists
        if not os.path.exists(full_path):
            logger.warning(f"Instruction file not found: {full_path}")
            abort(404)

        # Determine if we should display inline (PDF, images) or force download
        ext = os.path.splitext(file_path)[1].lower()
        as_attachment = ext not in [".pdf", ".jpg", ".jpeg", ".png"]

        return send_file(full_path, as_attachment=as_attachment)

    except Exception as e:
        logger.error(f"Error serving instruction file {file_path}: {e}")
        abort(500)
