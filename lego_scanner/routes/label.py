"""
This module defines the routes and logic for creating and printing labels in the LEGO Scanner application.

It includes functionalities to:
- Fetch part details from the Rebrickable API.
- Generate labels with part information, including name, image, category, and box number.
- Convert the generated label to a PDF.
- Send the PDF directly to a printer using Adobe Acrobat Reader.

The module uses Flask Blueprints to define routes related to label creation.
"""

import os
import subprocess
from flask import Blueprint, redirect, url_for, flash
from config import Config
from services.label_service import create_label_image, save_image_as_pdf
from services.rebrickable_service import get_part_details, get_category_name
from services.lookup_service import load_master_lookup

# Create a Blueprint for the label routes
label_bp = Blueprint('label', __name__)
master_lookup = load_master_lookup()

def secure_filename(filename):
    """
    Ensure the filename is safe by removing or replacing any unsafe characters.

    Args:
        filename (str): The original filename.

    Returns:
        str: The sanitized filename.
    """
    return filename.replace("/", "").replace("\\", "").replace("..", "").replace(" ", "_")

def print_pdf(pdf_path):
    """
    Send a PDF file directly to the printer using Adobe Acrobat Reader.

    Args:
        pdf_path (str): The absolute path to the PDF file to be printed.
    """
    try:
        # Path to Adobe Acrobat Reader
        acrobat_path = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"

        if not os.path.exists(acrobat_path):
            print(f"Adobe Acrobat Reader not found at {acrobat_path}")
            flash("Adobe Acrobat Reader not found.")
            return

        # Command to print the PDF
        command = f'"{acrobat_path}" /t "{pdf_path}"'
        subprocess.run(command, shell=True, check=True)
        print(f"Sent {pdf_path} to the printer using Adobe Acrobat Reader.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to print {pdf_path}: {e}")
        flash(f"Failed to print the label. Error: {e}")

def get_absolute_path(relative_path):
    """
    Convert a relative file path to an absolute file path.

    Args:
        relative_path (str): The relative path to be converted.

    Returns:
        str: The absolute path.
    """
    return os.path.abspath(relative_path)

@label_bp.route('/create_label/<part_id>')
def create_label_route(part_id):
    """
    Handle the creation of a label for a specific part.

    Args:
        part_id (str): The ID of the part for which the label is to be created.

    Returns:
        Response: Redirects to the main index page.
    """
    part_details = get_part_details(part_id)

    if not part_details:
        flash(f"Failed to retrieve details for part {part_id}")
        return redirect(url_for('main.index'))

    name = part_details.get('name', 'Unknown Item')
    img_url = part_details.get('part_img_url', '')
    part_cat_id = part_details.get('part_cat_id', None)
    category = get_category_name(part_cat_id) if part_cat_id else 'Unknown Category'
    box = master_lookup.get(part_id, {}).get('box', 'Unknown Box')

    label_image_path = create_label_image(name, img_url, part_id, box, category)
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, f'label_{part_id}.pdf')
    save_image_as_pdf(label_image_path, pdf_path)
    absolute_pdf_path = get_absolute_path(pdf_path)

    # Send the PDF directly to the printer
    print_pdf(absolute_pdf_path)

    return redirect(url_for('main.index'))
